"""Phase 8a: read-only scan of EVERY blob reachable from any ref (standard library; only runs read-only git commands).

  python scripts/scan_repo_history.py [--repo PATH] [--json scan_output/scan_report.json] [--summary docs/REPO_SCAN.md] [--tree DIR]

Reports: (i) paths that must never be tracked and whether they ever were, (ii) secret patterns, (iii) personal-data patterns, (iv) large blobs and repository size,
(v) third-party material (DDInter data, photographs without an attribution row). NEVER outputs a matched value: a finding is pattern name, commit id, path,
in-tree flag and a redacted preview (first 3 characters plus the length; e-mail addresses only as domain counts). --tree DIR scans a plain folder (for example the built site) instead of git history."""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

BIG = 5 * 1024 * 1024
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf", ".zip", ".gz", ".mp4", ".bin", ".pyc", ".sqlite", ".db", ".avif"}
PHOTO_EXT = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif"}

# (i) paths that must never be tracked
NEVER_PATHS = [
    ("env_file", re.compile(r"(^|/)\.env($|\.)(?!example$)")), ("session_db_folder", re.compile(r"^data/app/")), ("database_file", re.compile(r"\.(db|sqlite3?|sqlite)$")),
    ("key_file", re.compile(r"\.(key|pem|p12|pfx)$")), ("ddinter_raw", re.compile(r"^data/reference/ddinter/raw/")), ("ddinter_store", re.compile(r"^data/reference/interactions_ddinter\.json$")),
    ("model_cache", re.compile(r"^data/cache/")), ("raw_runs", re.compile(r"^eval/runs/")), ("raw_photos", re.compile(r"^frontend/public/photos/raw/")), ("real_photos", re.compile(r"^data/real_photos/")),
    ("log_file", re.compile(r"\.log$")),
]
SECRETS = [
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_\-]{35}")), ("sk_token", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")), ("github_token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})")),
    ("aws_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")), ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("possible_fernet_key", re.compile(r"(?<![A-Za-z0-9+/=_\-])[A-Za-z0-9_\-]{43}=(?![A-Za-z0-9+/=_\-])")),
]
ASSIGN = re.compile(r"\b(GEMINI_API_KEY|ANTHROPIC_API_KEY|CAREBRIDGE_DATA_KEY|[A-Z][A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD))[ \t]*[=:][ \t]*['\"]?([^\s'\"#,;)]+)")
PLACEHOLDER = re.compile(r"^(?:[A-Za-z_][\w.]*\(|re\.|\$|\{|<|%|\.\.\.|os\.|settings|self\.|process\.|import\.meta|your|change|example|xxx|placeholder|none$|null$|true$|false$|\*+$|\[)", re.I)
# (iii) personal data
EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b")
PHONE = re.compile(r"(?<![0-9A-Za-z.])(?:\+91[\s\-]?)?[6-9]\d{4}[\s\-]?\d{5}(?![0-9A-Za-z.])")
REGNO = re.compile(r"\bURK\d+", re.I)
WINPATH = re.compile(r"[A-Za-z]:\\Users\\([A-Za-z0-9._\-]+)", re.I)
GENERIC_USERS = {"user", "users", "public", "default", "name", "you", "yourname", "username", "<user>", "example"}


def red(s: str) -> str:
    return f"{s[:3]}***(len {len(s)})"


def git(repo: Path, *a: str, text=True) -> str:
    r = subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=text, check=True)
    return r.stdout


class Blobs:
    """One long-lived git cat-file --batch process."""

    def __init__(self, repo: Path):
        self.p = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def get(self, sha: str) -> bytes:
        self.p.stdin.write(sha.encode() + b"\n")
        self.p.stdin.flush()
        head = self.p.stdout.readline().split()
        n = int(head[2])
        data = self.p.stdout.read(n)
        self.p.stdout.read(1)
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def scan_text(path: str, text: str, where: str, out: dict) -> None:
    """Adds findings for one text blob/file. `where` is the commit id (or 'tree')."""
    def add(cat, pat, preview=""):
        out["findings"].append(dict(category=cat, pattern=pat, commit=where, path=path, preview=preview))
    for name, rx in SECRETS:
        for m in rx.finditer(text):
            add("secret", name, red(m.group(0)))
    for m in ASSIGN.finditer(text):
        v = m.group(2)
        if len(v) >= 8 and not PLACEHOLDER.match(v):
            add("secret", "key_assignment:" + m.group(1), red(v))
    domains = Counter(m.group(1).lower() for m in EMAIL.finditer(text))
    for d, c in domains.items():
        out["email_domains"].append(dict(domain=d, count=c, commit=where, path=path))
    n = len(PHONE.findall(text))
    if n:
        add("personal", "phone_like_number", f"x{n}")
    n = len(REGNO.findall(text))
    if n:
        add("personal", "registration_number_URK", f"x{n}")
    for m in WINPATH.finditer(text):
        if m.group(1).lower() not in GENERIC_USERS:
            out["winpaths"].append(dict(commit=where, path=path))


def blob_index(repo: Path) -> dict:
    """blob sha -> (first commit short id, set of paths). Oldest commit wins."""
    info: dict[str, list] = {}
    cur = None
    log = git(repo, "log", "--all", "--reverse", "--root", "--no-renames", "--raw", "--no-abbrev", "--format=C %h")
    for line in log.splitlines():
        if line.startswith("C "):
            cur = line[2:]
        elif line.startswith(":"):
            meta, _, path = line.partition("\t")
            sha = meta.split()[3]
            if set(sha) != {"0"}:
                info.setdefault(sha, [cur, set()])[1].add(path)
    return info


def scan_repo(repo: Path) -> dict:
    out = dict(mode="git_history", findings=[], email_domains=[], winpaths=[], never_tracked=[], large_blobs=[], unusual=[], third_party=[], blobs=0, binary_skipped=0)
    head_paths = set(git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines())
    index = blob_index(repo)
    objs = [ln.split(" ", 1) for ln in git(repo, "rev-list", "--objects", "--all").splitlines() if " " in ln]
    seen: set[str] = set()
    cat = Blobs(repo)
    sizes = {}
    for ln in git(repo, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype) %(objectsize)").splitlines():
        sha, typ, size = ln.split()
        if typ == "blob":
            sizes[sha] = int(size)
    photos_seen = []
    try:
        for sha, path in objs:
            if sha in seen or sha not in sizes:
                continue
            seen.add(sha)
            out["blobs"] += 1
            commit = index.get(sha, ["?"])[0]
            ext = PurePosixPath(path).suffix.lower()
            for name, rx in NEVER_PATHS:
                if rx.search(path):
                    out["never_tracked"].append(dict(pattern=name, commit=commit, path=path, in_tree=path in head_paths))
            if sizes[sha] > BIG:
                out["large_blobs"].append(dict(commit=commit, path=path, bytes=sizes[sha], in_tree=path in head_paths))
            if "ddinter" in path.lower():
                out["third_party"].append(dict(kind="ddinter_path", commit=commit, path=path, in_tree=path in head_paths))
            if ext in PHOTO_EXT:
                photos_seen.append((path, commit, path in head_paths))
            if ext in BINARY_EXT:
                out["binary_skipped"] += 1
                continue
            if sizes[sha] > 20 * 1024 * 1024:
                out["unusual"].append(dict(commit=commit, path=path, reason="text blob over 20 MB not scanned"))
                continue
            data = cat.get(sha)
            if b"\0" in data[:8000]:
                out["binary_skipped"] += 1
                out["unusual"].append(dict(commit=commit, path=path, reason="binary content with a text extension"))
                continue
            scan_text(path, data.decode("utf-8", "replace"), commit, out)
    finally:
        cat.close()
    # photographs need an attribution row (current tree only: the file is judged by name in assets/ATTRIBUTION.md)
    try:
        attr = git(repo, "show", "HEAD:assets/ATTRIBUTION.md").lower()
    except subprocess.CalledProcessError:
        attr = ""
    for path, commit, in_tree in photos_seen:
        if in_tree and (path.startswith("assets/") or path.startswith("frontend/public/photos/")) and re.sub(r"-\d+$", "", PurePosixPath(path).stem.lower()) not in attr:
            out["third_party"].append(dict(kind="photo_without_attribution_row", commit=commit, path=path, in_tree=True))
    size = git(repo, "count-objects", "-v")
    kb = sum(int(x.split(":")[1]) for x in size.splitlines() if x.startswith(("size:", "size-pack:")))
    out["repository_size_kib"] = kb
    return out


def scan_tree(root: Path) -> dict:
    out = dict(mode="folder", findings=[], email_domains=[], winpaths=[], never_tracked=[], large_blobs=[], unusual=[], third_party=[], blobs=0, binary_skipped=0)
    total = 0
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(root).as_posix()
        total += f.stat().st_size
        out["blobs"] += 1
        for name, rx in NEVER_PATHS:
            if rx.search(rel):
                out["never_tracked"].append(dict(pattern=name, commit="tree", path=rel, in_tree=True))
        if f.stat().st_size > BIG:
            out["large_blobs"].append(dict(commit="tree", path=rel, bytes=f.stat().st_size, in_tree=True))
        if f.suffix.lower() in BINARY_EXT:
            out["binary_skipped"] += 1
            continue
        data = f.read_bytes()
        if b"\0" in data[:8000]:
            out["binary_skipped"] += 1
            continue
        scan_text(rel, data.decode("utf-8", "replace"), "tree", out)
    out["total_bytes"] = total
    return out


def counts(rep: dict) -> dict:
    by = defaultdict(Counter)
    for f in rep["findings"]:
        by[f["category"]][f["pattern"]] += 1
    dom = Counter()
    for e in rep["email_domains"]:
        dom[e["domain"]] += e["count"]
    wp = Counter(e["path"] for e in rep["winpaths"])
    return dict(secrets={k: v for k, v in by["secret"].items()}, personal={k: v for k, v in by["personal"].items()}, email_domains=dict(dom), windows_user_paths_by_file=dict(wp),
                never_tracked=dict(Counter(f"{e['pattern']} ({'in tree' if e['in_tree'] else 'history only'})" for e in rep["never_tracked"])),
                large_blobs=len(rep["large_blobs"]), third_party=dict(Counter(e["kind"] + (" (in tree)" if e["in_tree"] else " (history only)") for e in rep["third_party"])))


def summary_md(rep: dict, title="Repository history scan") -> str:
    c = counts(rep)
    L = [f"# {title}", "", "Generated by `scripts/scan_repo_history.py` (read-only). **Counts only: no secret, no personal value and no matched text appears here or in the console.** The detailed machine-readable report (pattern, commit id, path, redacted preview) is written to a gitignored folder.", "",
         f"- Mode: {rep['mode']}; blobs scanned: {rep['blobs']} ({rep['binary_skipped']} binary skipped by extension or content)."]
    if "repository_size_kib" in rep:
        L.append(f"- Repository size (loose + packed): {rep['repository_size_kib'] / 1024:.1f} MiB; blobs over 5 MB: {c['large_blobs']}.")
    if "total_bytes" in rep:
        L.append(f"- Folder size: {rep['total_bytes'] / 1024:.0f} KiB; files over 5 MB: {c['large_blobs']}.")
    L += ["", "## (i) Paths that must never be tracked", ""]
    L += [f"- {k}: {v}" for k, v in c["never_tracked"].items()] or ["- none found, in the current tree or in history"]
    L += ["", "## (ii) Secret patterns", ""]
    L += [f"- {k}: {v}" for k, v in c["secrets"].items()] or ["- none found"]
    L += ["", "## (iii) Personal-data patterns", ""]
    L += [f"- {k}: {v} occurrence(s)" for k, v in c["personal"].items()] or ["- no phone-like numbers or registration numbers found"]
    L += [f"- e-mail domains (domain and count only): {c['email_domains'] or 'none'}"]
    L += [f"- Windows user-path mentions: {sum(c['windows_user_paths_by_file'].values())} in {len(c['windows_user_paths_by_file'])} file(s)"]
    for p, n in sorted(c["windows_user_paths_by_file"].items(), key=lambda x: -x[1])[:15]:
        L.append(f"  - `{p}`: {n}")
    L += ["", "## (v) Third-party material", ""]
    L += [f"- {k}: {v}" for k, v in c["third_party"].items()] or ["- none flagged"]
    if rep["unusual"]:
        L += ["", f"## Unusual files: {len(rep['unusual'])} (listed in the JSON report)"]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--tree", help="scan a plain folder instead of git history")
    ap.add_argument("--json", default="scan_output/scan_report.json")
    ap.add_argument("--summary", default=None)
    a = ap.parse_args(argv)
    rep = scan_tree(Path(a.tree)) if a.tree else scan_repo(Path(a.repo))
    j = Path(a.json)
    j.parent.mkdir(parents=True, exist_ok=True)
    j.write_text(json.dumps(rep, indent=1), encoding="utf-8", newline="\n")
    md = summary_md(rep)
    if a.summary:
        Path(a.summary).write_text(md, encoding="utf-8", newline="\n")
    c = counts(rep)
    print(f"blobs {rep['blobs']}; secret findings {sum(c['secrets'].values())}; never-tracked {sum(len(x) for x in [rep['never_tracked']])}; personal {sum(c['personal'].values())}; windows paths {sum(c['windows_user_paths_by_file'].values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
