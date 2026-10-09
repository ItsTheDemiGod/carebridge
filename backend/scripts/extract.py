r"""Extract one dev document and print a compact summary.
  backend\.venv\Scripts\python backend\scripts\extract.py ds_001 --condition clean [--final-test-run]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.extraction import extract_document  # noqa: E402
from app.services.guards import REPO, check_split  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("doc_id")
ap.add_argument("--condition", default="text", choices=["text", "clean", "scan", "photo", "poor"])
ap.add_argument("--final-test-run", action="store_true")
a = ap.parse_args()
split = next(d["split"] for d in json.loads((REPO / "data/manifest.json").read_text(encoding="utf-8"))["documents"] if d["id"] == a.doc_id)
check_split(split, a.final_test_run, f"extract {a.doc_id} {a.condition}")
path = REPO / "data" / ("synthetic" if a.condition == "text" else f"rendered/{a.condition}") / f"{a.doc_id}.{'txt' if a.condition == 'text' else 'png'}"
r = extract_document(path)
print(f"ok={r.ok} cached={r.cached} calls={r.api_calls} latency={r.latency_s:.1f}s prompt_tokens={r.usage.get('prompt_tokens')} gen_tokens={r.usage.get('output_tokens')} error={r.error}")
if r.output:
    for m in r.output.medications:
        f = m.frequency
        print(f"  {m.brand_name or '-'} / {m.generic_name or '-'} | {m.strength} | {f.original_abbreviation} x{f.times_per_day} {f.timing_label.value} | {m.duration_days} | {m.confidence.value}")
    print(f"  follow_ups={len(r.output.follow_ups)} red_flags={len(r.output.red_flags)} unreadable={r.output.unreadable_parts}")
