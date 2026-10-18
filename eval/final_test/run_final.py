"""One-shot runner for the held-out TEST split (Phase 7b). Protocol: docs/FINAL_TEST_PROTOCOL.md.

  python -m eval.final_test.run_final --pin                      # 7b start: pin the Ollama version, model digest and the test-data set hash (no model call)
  python -m eval.final_test.run_final --final-test-run           # the official run (resumable from the cache with no change)
  python -m eval.final_test.run_final --final-test-run --rerun-reason "why"   # only after a complete official run: writes final-test-v1-posthoc-N

It REFUSES to run: without --final-test-run; with a dirty git tree; when the freeze manifest does not verify; without the tag `freeze-pre-test` on HEAD or an
ancestor of HEAD (and then only because the manifest verifies); when the model digest or the test-data hash differ from the pins; a second official run.
Every invocation is appended to eval/test_runs.log. Nothing in this stage reads a test file before the guards have passed. Raw model outputs go to the
gitignored eval/runs/<run-id>/; committed results go to eval/results/<run-id>/ with a SHA-256 checksum file."""
import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

OFFICIAL_ID = "final-test-v1"
TAG = "freeze-pre-test"
CONDS = ("text", "clean", "scan", "photo", "poor")
LANGS = ("en", "ta", "hi")


class Refusal(SystemExit):
    """A guard stopped the run; nothing was read or called."""


# ---------------------------------------------------------------------------------------------------------------- helpers
def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise Refusal(f"git {' '.join(args)} failed: {r.stderr.strip()[:200]}")
    return r.stdout.strip()


def git_is_clean(root: Path) -> bool:
    """Clean except for eval/test_runs.log (this runner appends to it; commit it after the run)."""
    lines = [ln for ln in git(root, "status", "--porcelain").splitlines() if ln.split(maxsplit=1)[-1].strip() != "eval/test_runs.log"]
    return not lines


def tag_ok(root: Path) -> tuple[bool, str]:
    """The tag exists and is HEAD or an ancestor of HEAD (the manifest check proves nothing frozen changed since)."""
    try:
        commit = git(root, "rev-parse", f"{TAG}^{{commit}}")
    except Refusal:
        return False, f"git tag {TAG} does not exist"
    r = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=root)
    return r.returncode == 0, commit


def ollama_info(base_url: str = "http://localhost:11434", model: str | None = None) -> dict:
    """Version and the digest of the model tag, from the LOCAL Ollama API (no generation, no model call)."""
    import httpx
    from app.llm.ollama import assert_local
    from app.config import settings
    base = assert_local(base_url)
    model = model or settings.ollama_model
    with httpx.Client(timeout=30) as c:
        ver = c.get(f"{base}/api/version").json().get("version")
        tags = c.get(f"{base}/api/tags").json().get("models", [])
    digest = next((t.get("digest") for t in tags if t.get("name") == model or t.get("model") == model), None)
    if not digest:
        raise Refusal(f"model {model} not found in the local Ollama")
    return {"ollama_version": ver, "model": model, "model_digest": digest}


def test_data_hash(root: Path, ids: list[str]) -> str:
    """One SHA-256 over the test documents, ground truth and rendered images as a set. Read only at run time (7b), after the guards."""
    h = hashlib.sha256()
    for i in sorted(ids):
        paths = [root / "data/synthetic" / f"{i}.txt", root / "data/ground_truth" / f"{i}.json", *[root / "data/rendered" / c / f"{i}.png" for c in CONDS if c != "text"]]
        for p in paths:
            h.update(p.name.encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def test_ids(root: Path) -> list[str]:
    return sorted(d["id"] for d in json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))["documents"] if d["split"] == "test")


def log_invocation(root: Path, text: str) -> None:
    p = root / "eval" / "test_runs.log"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} final_test.run_final {text}\n")


def results_dir_for(root: Path, rerun_reason: str | None) -> tuple[str, bool]:
    """(run id, official). The official id is used until its results are complete; after that only a labelled post-hoc re-run is allowed."""
    done = (root / "eval" / "results" / OFFICIAL_ID / "SHA256SUMS").exists()
    if not done:
        if rerun_reason:
            raise Refusal("--rerun-reason is only for a re-run after a COMPLETE official run; the official run has not completed")
        return OFFICIAL_ID, True
    if not rerun_reason:
        raise Refusal(f"{OFFICIAL_ID} is complete: a second OFFICIAL run is refused. A labelled post-hoc re-run needs --rerun-reason TEXT")
    n = 1
    while (root / "eval" / "results" / f"{OFFICIAL_ID}-posthoc-{n}").exists():
        n += 1
    return f"{OFFICIAL_ID}-posthoc-{n}", False


# ------------------------------------------------------------------------------------------------------------------ guards
def check_guards(root: Path, args, *, verify=None, ollama=None, is_clean=None, tag=None) -> dict:
    """Raises Refusal on the first failed guard; returns what was pinned/verified. Reads no test file except for the pinned set hash (after the other guards)."""
    verify = verify or (lambda r: __import__("freeze_manifest").verify(r))
    ollama = ollama or ollama_info
    is_clean = is_clean or git_is_clean
    tag = tag or tag_ok
    if not args.final_test_run:
        raise Refusal("refusing to run without --final-test-run (the test split is used once; see docs/FINAL_TEST_PROTOCOL.md)")
    if not is_clean(root):
        raise Refusal("refusing to run: the git working tree is not clean (commit or discard changes; nothing may change after the freeze)\n" + git(root, "status", "--porcelain")[:400])
    drift = verify(root)
    if drift:
        raise Refusal("refusing to run: the freeze manifest does not verify:\n" + "\n".join(drift[:20]))
    ok, info = tag(root)
    if not ok:
        raise Refusal(f"refusing to run: the git tag {TAG} must exist and be HEAD or an ancestor of HEAD ({info})")
    pins = {}
    for name in ("model_pin.json", "test_data_pin.json"):
        p = root / "eval" / "final_test" / name
        if not p.exists():
            raise Refusal(f"refusing to run: {name} is missing (create it with --pin and commit it before the run)")
        pins[name] = json.loads(p.read_text(encoding="utf-8"))
    live = ollama()
    if live["model_digest"] != pins["model_pin.json"]["model_digest"] or live.get("ollama_version") != pins["model_pin.json"].get("ollama_version"):
        raise Refusal("refusing to run: the Ollama version or model digest differs from the committed pin")
    if test_data_hash(root, test_ids(root)) != pins["test_data_pin.json"]["sha256"]:
        raise Refusal("refusing to run: the test documents differ from the committed pin")
    return {"tag_commit": info, "pins": pins, "ollama": live}


# ---------------------------------------------------------------------------------------------------------------- stages
def stage_extraction(root: Path, ids: list[str], runs_dir: Path, provider, cache_dir: Path, prompt_version: str):
    """200 calls (cached ones are free): writes the raw outputs, returns coverage rows. A provider failure is recorded as a skip with its reason."""
    from app.services.extraction import extract_document
    raw_dir = runs_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for cond in CONDS:
        for doc in ids:
            path = root / "data" / ("synthetic" if cond == "text" else f"rendered/{cond}") / (f"{doc}.txt" if cond == "text" else f"{doc}.png")
            res = extract_document(path, provider=provider, prompt_version=prompt_version, cache_dir=cache_dir)
            if res.quota_exhausted:
                raise Refusal("provider quota exhausted; re-run the same command to resume from the cache")
            row = {"cond": cond, "doc": doc, "skipped": bool(res.skipped or not res.ok), "reason": res.error, "latency_s": res.latency_s, "cached": res.cached}
            if row["skipped"]:
                (raw_dir / f"{cond}_{doc}.json").unlink(missing_ok=True)
            else:
                (raw_dir / f"{cond}_{doc}.json").write_text(res.raw_text or res.output.model_dump_json(), encoding="utf-8")
            rows.append(row)
    return rows


def stage_explanation(root: Path, ids: list[str], runs_dir: Path, raw_dir: Path, provider, version: str):
    """English, Tamil and Hindi narrative on the clean condition (text-only calls) for every scored document; per-document records for the Phase 3 aggregators."""
    from app.schemas.extraction_output import ExtractionOutput
    from app.services import narrative as nv
    from app.services.explain import build_explanation, model_items
    from app.services.normalisation import normalise_document
    out_dir = runs_dir / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = 0
    for doc in ids:
        f = raw_dir / f"clean_{doc}.json"
        if not f.exists():
            continue  # a skipped clean extraction has no explanation; it is listed in the skipped report
        nd = normalise_document(ExtractionOutput.model_validate_json(f.read_text(encoding="utf-8")))
        nar = nv.narrate_document(model_items(nd), provider, version=version)
        ex = build_explanation(nd, nar, document_id=doc, model=provider.model, prompt_version=version)
        rec = dict(doc=doc, explanation=ex.model_dump(mode="json"), items=[i.model_dump() for i in nar.items],
                   calls=[dict(stage=c.stage, lang=c.lang, cached=c.cached, latency_s=round(c.latency_s, 2), api_calls=c.api_calls, usage=c.usage, error=c.error) for c in nar.calls()])
        (out_dir / f"{doc}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        done += 1
    return done


def explanation_metrics(run_id: str) -> dict:
    from eval import phase3_metrics as P3, phase3e_metrics as P3E
    return {**P3.aggregate(run_id), "provenance_share": P3E.aggregate(run_id)["provenance_share"], "phase3_verified_share": P3.aggregate(run_id)["verified_share"]}


def safety_metrics(run_id: str) -> dict:
    from app.safety import interactions as I
    from eval import phase4_safety as P4
    data = I.load_data()
    m = P4.summarise(P4.evaluate(run_id, data, split="test"), run_id, data)
    m["split"] = "test"
    return m


def write_outputs(root: Path, run_id: str, official: bool, metrics: dict, counters, notes: dict) -> Path:
    from eval.final_test import report as R
    out = root / "eval" / "results" / run_id
    out.mkdir(parents=True, exist_ok=True)
    label = "OFFICIAL RUN (one-shot)" if official else f"POST-HOC re-run, NOT the official result. Reason: {notes.get('rerun_reason')}"
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    (out / "metrics.md").write_text(R.markdown(metrics, label), encoding="utf-8", newline="\n")
    R.per_document_csv(out / "per_document.csv", counters)
    (out / "skipped.json").write_text(json.dumps(metrics["skipped"], indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "figures.json").write_text(json.dumps(R.figures(metrics), indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "run_manifest.json").write_text(json.dumps(notes, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    sums = [f"{hashlib.sha256((out / n).read_bytes()).hexdigest()}  {n}" for n in ("metrics.json", "metrics.md", "per_document.csv", "skipped.json", "figures.json", "run_manifest.json")]
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8", newline="\n")  # written LAST: its presence marks a complete run
    return out


def verify_checksums(results: Path) -> bool:
    for line in (results / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        if hashlib.sha256((results / name).read_bytes()).hexdigest() != digest:
            return False
    return True


def run(root: Path, args, *, guards=None, provider_factory=None, narrative_provider_factory=None, now=time.time) -> Path:
    from app.prompts import PROMPT_VERSION
    from app.services import narrative as nv
    from eval.final_test import report as R
    guards = guards or (lambda: check_guards(root, args))
    log_invocation(root, f"invoked final_test_run={args.final_test_run} rerun_reason={getattr(args, 'rerun_reason', None)!r}")
    try:
        run_id, official = results_dir_for(root, getattr(args, "rerun_reason", None))
    except Refusal as e:
        log_invocation(root, f"REFUSED: {str(e)[:160]}")
        raise
    log_invocation(root, f"start run_id={run_id} official={official}")
    try:
        info = guards()
    except Refusal as e:
        log_invocation(root, f"REFUSED run_id={run_id}: {str(e).splitlines()[0][:160]}")
        raise
    ids = test_ids(root)  # first read of the manifest's test ids: after every guard has passed
    from app.llm.ollama import OllamaProvider
    provider = (provider_factory or OllamaProvider)()
    nprovider = (narrative_provider_factory or (lambda: provider))()
    runs_dir = root / "eval" / "runs" / run_id
    t0 = now()
    rows = stage_extraction(root, ids, runs_dir, provider, root / "data" / "cache", PROMPT_VERSION)
    counters, records, unreadable = R.per_document_counters(root, runs_dir / "raw", set(ids))
    n_expl = stage_explanation(root, ids, runs_dir, runs_dir / "raw", nprovider, nv.PROMPT_VERSION)
    skipped = [f"{r['cond']}/{r['doc']}: {r['reason']}" for r in rows if r["skipped"]] + [f"{u}: unreadable raw output" for u in unreadable]
    metrics = {
        "run_id": run_id, "official": official, "split": "test", "documents": len(ids), "conditions": list(CONDS), "skipped": skipped,
        "operational": R.operational(rows),
        "extraction": {v: R.extraction_metrics(counters, v) for v in ("raw", "normalised")},
        "flags": R.flag_metrics(records),
        "safety": R.scrub_safety(safety_metrics(run_id)),
        "explanation": explanation_metrics(run_id),
    }
    metrics["dev_vs_test"] = R.dev_vs_test(metrics, root)
    notes = {"run_id": run_id, "official": official, "rerun_reason": getattr(args, "rerun_reason", None), "tag": TAG, "tag_commit": info["tag_commit"], "pins": info["pins"],
             "ollama": info["ollama"], "head": git(root, "rev-parse", "HEAD"), "explanation_documents": n_expl, "seconds": round(now() - t0, 1),
             "freeze_manifest_sha256": hashlib.sha256((root / "eval/final_test/freeze_manifest.json").read_bytes()).hexdigest()}
    out = write_outputs(root, run_id, official, metrics, counters, notes)
    log_invocation(root, f"complete run_id={run_id} skipped={len(skipped)}")
    return out


def pin(root: Path = REPO, ollama=None) -> None:
    """7b, before the run: pin the Ollama version, the model digest and the test-data set hash. Commit the two files, then run."""
    info = (ollama or ollama_info)()
    d = root / "eval" / "final_test"
    (d / "model_pin.json").write_text(json.dumps(info, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (d / "test_data_pin.json").write_text(json.dumps({"sha256": test_data_hash(root, test_ids(root)), "documents": len(test_ids(root))}, indent=1) + "\n", encoding="utf-8", newline="\n")
    log_invocation(root, "pin (no model call)")
    print("pinned:", {k: v for k, v in info.items()})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--final-test-run", action="store_true")
    ap.add_argument("--rerun-reason")
    ap.add_argument("--pin", action="store_true")
    a = ap.parse_args(argv)
    if a.pin:
        pin()
        return 0
    out = run(REPO, a)
    print(f"done: {out.relative_to(REPO)} (checksums verify: {verify_checksums(out)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
