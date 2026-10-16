"""Phase 3 dev run: explanations for the cached, normalised extraction of the DEV split (condition clean). Text-only local calls, resumable from the cache.

  python -m eval.run_narrative --run-id phase3-dev-clean [--doc ds_006] [--limit N] [--prompt-version v1]
Reads eval/runs/dev-ollama-v1/raw/clean_<doc>.json (no extraction is re-run), writes eval/runs/<run-id>/docs/<doc>.json (gitignored).
Only the dev split; the test split is never read. Only the local Ollama adapter is used (localhost only); no Gemini.
"""

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.llm.ollama import OllamaProvider  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput  # noqa: E402
from app.services import narrative as nv  # noqa: E402
from app.services.explain import build_explanation, model_items, narrative_items  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402

SOURCE_RUN = "dev-ollama-v1"
CONDITION = "clean"


def dev_docs() -> list[str]:
    return [d["id"] for d in json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"] if d["split"] == "dev"]


def run_doc(doc: str, provider, out_dir: Path, version: str, use_library: bool = True) -> dict:
    raw = ExtractionOutput.model_validate_json((REPO / "eval" / "runs" / SOURCE_RUN / "raw" / f"{CONDITION}_{doc}.json").read_text(encoding="utf-8"))
    nd = normalise_document(raw)  # app mode: model output only, no document text
    nar = nv.narrate_document(model_items(nd, use_library), provider, version=version)
    ex = build_explanation(nd, nar, document_id=doc, model=provider.model, prompt_version=version, use_library=use_library)
    rec = dict(doc=doc, explanation=ex.model_dump(mode="json"),
               calls=[dict(stage=c.stage, lang=c.lang, cached=c.cached, latency_s=round(c.latency_s, 2), api_calls=c.api_calls, usage=c.usage, error=c.error) for c in nar.calls()],
               items=[i.model_dump() for i in nar.items])
    (out_dir / f"{doc}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="phase3-dev-clean")
    ap.add_argument("--doc")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--prompt-version", default=nv.PROMPT_VERSION)
    a = ap.parse_args()
    docs = dev_docs()
    assert len(docs) == 20, "expected the 20 dev documents"
    docs = [a.doc] if a.doc else docs[: a.limit]
    if a.doc and a.doc not in dev_docs():
        raise SystemExit(f"{a.doc} is not in the dev split; the test split is never used here")
    out_dir = REPO / "eval" / "runs" / a.run_id / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    provider, t0, calls = OllamaProvider(), time.perf_counter(), 0
    for n, doc in enumerate(docs, 1):
        t = time.perf_counter()
        rec = run_doc(doc, provider, out_dir, a.prompt_version)
        fresh = sum(1 for c in rec["calls"] if not c["cached"])
        calls += len(rec["calls"])
        slow = max((c["latency_s"] / max(c["api_calls"], 1) for c in rec["calls"]), default=0)  # merged chunk calls: average per API call
        st = [ln["status"] for s in rec["explanation"]["sections"] for ln in s["lines"] if ln["kind"] in ("advice", "follow_up", "warning")]
        print(f"[{n}/{len(docs)}] {doc}: {len(rec['calls'])} calls ({fresh} fresh, max {slow:.0f}s), lines {len(st)}, verified {st.count('verified')}, {time.perf_counter() - t:.0f}s", flush=True)
        if slow > 120:
            print("STOP: a single call exceeded 2 minutes", flush=True)
            break
    print(f"done: {calls} calls, {time.perf_counter() - t0:.0f}s wall")


if __name__ == "__main__":
    main()
