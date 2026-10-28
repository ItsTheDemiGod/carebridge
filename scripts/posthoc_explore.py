"""POST-HOC scratch: locate the specific cases of the final test (read-only; no model calls)."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO))
from eval.final_test import report as R
from eval.final_test.run_final import test_ids
from app.schemas.extraction_output import ExtractionOutput
from app.services.normalisation import normalise_document
ids = set(test_ids(REPO)); raw_dir = REPO / "eval/runs/final-test-v1/raw"
counters, records, unr = R.per_document_counters(REPO, raw_dir, ids)
if __name__ == "__main__":
    print(len(records), unr)
    for r in records:
        if r["wrong_schedule"] or (r["name_err"] and r["level"] == "none") or (r["timing_err"] and r["level"]=="none") or (not r["paired"] and r["level"]!="x"):
            print({k: (sorted(v) if isinstance(v,set) else v) for k,v in r.items()})
