"""Phase 8a: validate .github/workflows/pages.yml with the standard library only (no YAML package is installed).
A small parser for the indentation subset the workflow uses (mappings, lists of mappings, scalars, inline lists, comments); syntax it cannot read raises ValueError.
  python scripts/check_workflow.py [FILE]"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def scalar(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [scalar(x) for x in v[1:-1].split(",") if x.strip()]
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    return {"true": True, "false": False}.get(v, int(v) if re.fullmatch(r"\d+", v) else v)


def tokens(text: str):
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError(f"line {n}: tab indentation")
        line = re.sub(r"(^|\s)#.*$", "", raw).rstrip()
        if line.strip():
            yield n, len(line) - len(line.lstrip()), line.strip()


def parse(text: str):
    toks = list(tokens(text))
    pos = 0

    def block(indent: int):
        nonlocal pos
        if toks[pos][2].startswith("- "):
            out = []
            while pos < len(toks) and toks[pos][1] == indent and toks[pos][2].startswith("- "):
                n, ind, body = toks[pos]
                body = body[2:].strip()
                if re.match(r"^[\w.\-]+:( |$)", body):  # a mapping item: rewrite the dash as indentation and read the mapping
                    toks[pos] = (n, indent + 2, body)
                    out.append(block(indent + 2))
                else:
                    out.append(scalar(body))
                    pos += 1
            return out
        out = {}
        while pos < len(toks) and toks[pos][1] == indent and not toks[pos][2].startswith("- "):
            n, _, body = toks[pos]
            m = re.match(r"^([\w.\-]+):(?: +(.*))?$", body)
            if not m:
                raise ValueError(f"line {n}: cannot read {body[:40]!r}")
            key, val = m.group(1), m.group(2)
            pos += 1
            if val in (None, ""):
                if pos < len(toks) and toks[pos][1] > indent:
                    out[key] = block(toks[pos][1])
                elif pos < len(toks) and toks[pos][1] == indent and toks[pos][2].startswith("- "):
                    out[key] = block(indent)
                else:
                    out[key] = None
            elif val in ("|", ">"):
                lines = []
                while pos < len(toks) and toks[pos][1] > indent:
                    lines.append(toks[pos][2])
                    pos += 1
                out[key] = "\n".join(lines)
            else:
                out[key] = scalar(val)
        return out

    if not toks:
        raise ValueError("empty file")
    doc = block(toks[0][1])
    if pos != len(toks):
        raise ValueError(f"line {toks[pos][0]}: unexpected indentation")
    return doc


def check(doc: dict) -> list[str]:
    """Rules of docs/DEPLOY.md; returns a list of problems."""
    bad = []
    on = doc.get("on") or doc.get(True)
    if set(on) != {"push", "workflow_dispatch"} or on["push"].get("branches") != ["master"]:
        bad.append("triggers must be push to master and workflow_dispatch only")
    if doc.get("permissions") != {"contents": "read", "pages": "write", "id-token": "write"}:
        bad.append("permissions must be exactly contents: read, pages: write, id-token: write")
    if not doc.get("concurrency", {}).get("group"):
        bad.append("a concurrency group is required")
    steps = [s for j in doc["jobs"].values() for s in j.get("steps", [])]
    for s in steps:
        u = s.get("uses")
        if u and not re.fullmatch(r"actions/[\w\-]+@v\d+", u):
            bad.append(f"action not an official actions/* pinned to a major version: {u}")
    text = repr(doc).lower()
    for word in ("secrets.", "playwright", "ollama", "uvicorn", "pytest", "gemini", "pip install"):
        if word in text:
            bad.append(f"the workflow must not use {word}")
    runs = [s.get("run", "") for s in steps]
    for need in ("npm ci", "npm test", "npm run build:demo"):
        if need not in runs:
            bad.append(f"missing step: {need}")
    if not any(s.get("uses", "").startswith("actions/upload-pages-artifact@") and s["with"]["path"] == "frontend/dist-demo" for s in steps):
        bad.append("upload-pages-artifact must upload frontend/dist-demo")
    for n in ("actions/checkout", "actions/setup-node", "actions/configure-pages", "actions/deploy-pages"):
        if not any(s.get("uses", "").startswith(n + "@") for s in steps):
            bad.append(f"missing {n}")
    return bad


if __name__ == "__main__":
    f = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / ".github" / "workflows" / "pages.yml"
    problems = check(parse(f.read_text(encoding="utf-8")))
    print("\n".join(problems) or "workflow OK")
    sys.exit(1 if problems else 0)
