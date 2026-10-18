"""Freeze manifest for the final test (Phase 7a).   python scripts/freeze_manifest.py [write|verify]

write : writes eval/final_test/freeze_manifest.json with SHA-256 hashes of every frozen file (see FROZEN_GLOBS), the settings, versions and the Python version.
verify: recomputes everything and reports drift (changed, added, removed files, changed settings); exit code 1 on any drift.

NOT done here (7b, at the start of the run, from `run_final.py --pin`): the Ollama version and model digest (asked from the local Ollama API) and the set hash of the
held-out test documents. In 7a no test-split file is opened, read or hashed: the manifest only records that these pins are pending.
The DDInter-derived store is hashed when present (the file stays untracked). Contents of data files are never printed."""
import hashlib
import json
import platform
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = Path("eval/final_test/freeze_manifest.json")
PINS = ("eval/final_test/model_pin.json", "eval/final_test/test_data_pin.json")  # created in 7b, committed before the run; deliberately NOT frozen files
FROZEN_GLOBS = [
    "backend/app/**/*.py", "backend/app/prompts/**/*", "backend/app/schemas/*.json",
    "data/templates/templates.json", "data/templates/phrases.json",
    "data/reference/formulary.json", "data/reference/interactions_supplement.json",
    "eval/**/*.py", "eval/stress/*",
    "scripts/freeze_manifest.py", "docs/FINAL_TEST_PROTOCOL.md",
    "backend/requirements.txt",
]
EXCLUDE_PARTS = {"__pycache__", "results", "runs"}  # eval/results and eval/runs are outputs, not code
HASH_ONLY = {  # existence-and-hash only; contents never read into logs. The test documents are NOT here (7b pins them)
    "dataset_manifest": "data/manifest.json",
    "ddinter_derived_store": "data/reference/interactions_ddinter.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def frozen_files(root: Path) -> list[Path]:
    seen = {}
    for pat in FROZEN_GLOBS:
        for p in root.glob(pat):
            rel = p.relative_to(root)
            if p.is_file() and not (set(rel.parts) & EXCLUDE_PARTS) and rel.as_posix() != MANIFEST.as_posix() and rel.as_posix() not in PINS:
                seen[rel.as_posix()] = p
    return [seen[k] for k in sorted(seen)]


def settings_snapshot(root: Path) -> dict:
    """Versions and settings read from the code (not invented). Ollama version and model digest are pinned at run time."""
    sys.path.insert(0, str(root / "backend"))
    from app.config import settings
    from app.llm import ollama as O
    from app.prompts import PROMPT_VERSION
    from app.schemas.extraction_output import SCHEMA_VERSION
    from app.services import narrative as N
    return dict(
        provider="ollama", model=settings.ollama_model, num_ctx=settings.ollama_num_ctx, num_predict=settings.ollama_num_predict, image_side_cap=settings.ollama_max_image_side,
        seed=O.SEED, temperature=0.0, extraction_prompt_version=PROMPT_VERSION, extraction_schema_version=SCHEMA_VERSION, narrative_prompt_version=N.PROMPT_VERSION,
        python=platform.python_version(), ollama_version="pinned_at_run_time", model_digest="pinned_at_run_time", test_documents="pinned_at_run_time (test_data_pin.json)",
    )


def build(root: Path = REPO, with_settings: bool = True) -> dict:
    files = {p.relative_to(root).as_posix(): sha256(p) for p in frozen_files(root)}
    norm = sorted(k for k in files if k.startswith("backend/app/normalisation/") or k == "backend/app/services/normalisation.py")
    hashed = {}
    for name, rel in HASH_ONLY.items():
        p = root / rel
        hashed[name] = {"path": rel, "sha256": sha256(p) if p.exists() else None}
    return {
        "purpose": "Freeze manifest for the one-shot final test (docs/FINAL_TEST_PROTOCOL.md). Hashes only; no data contents.",
        "files": files,
        "hash_only": hashed,
        "normalisation_version": hashlib.sha256("".join(files[k] for k in norm).encode()).hexdigest()[:16] + f" ({len(norm)} files; rules have no separate version number)",
        "settings": settings_snapshot(root) if with_settings else {},
    }


def diff(old: dict, new: dict) -> list[str]:
    out = []
    of, nf = old.get("files", {}), new.get("files", {})
    out += [f"changed: {k}" for k in sorted(of) if k in nf and of[k] != nf[k]]
    out += [f"added: {k}" for k in sorted(set(nf) - set(of))]
    out += [f"removed: {k}" for k in sorted(set(of) - set(nf))]
    for k, v in old.get("hash_only", {}).items():
        if v != new.get("hash_only", {}).get(k):
            out.append(f"hash_only changed: {k}")
    for k, v in old.get("settings", {}).items():
        if new.get("settings", {}).get(k) != v:
            out.append(f"setting changed: {k}")
    if old.get("normalisation_version") != new.get("normalisation_version"):
        out.append("normalisation code changed")
    return out


def verify(root: Path = REPO, with_settings: bool = True) -> list[str]:
    p = root / MANIFEST
    if not p.exists():
        return [f"missing {MANIFEST}"]
    return diff(json.loads(p.read_text(encoding="utf-8")), build(root, with_settings))


def main(argv: list[str]) -> int:
    mode = argv[0] if argv else "verify"
    if mode == "write":
        m = build()
        (REPO / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
        (REPO / MANIFEST).write_text(json.dumps(m, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        print(f"froze {len(m['files'])} files; ddinter store {'present' if m['hash_only']['ddinter_derived_store']['sha256'] else 'absent'}")
        return 0
    drift = verify()
    print("freeze manifest verifies: no drift" if not drift else "DRIFT:\n" + "\n".join(drift))
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
