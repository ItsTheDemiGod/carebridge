"""POST-HOC scratch: print one medicine's ground truth, raw output and normalised output (read-only, no model calls)."""
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend")); sys.path.insert(0, str(REPO))
from app.schemas.extraction_output import ExtractionOutput
from app.services.normalisation import normalise_document
raw_dir = REPO / "eval/runs/final-test-v1/raw"
cond, doc, key = sys.argv[1:4]
gt = json.loads((REPO/"data/ground_truth"/f"{doc}.json").read_text(encoding="utf-8"))
raw = ExtractionOutput.model_validate_json((raw_dir/f"{cond}_{doc}.json").read_text(encoding="utf-8"))
nd = normalise_document(raw)
for m in gt["medications"]:
    if key.lower() in json.dumps(m).lower():
        print("GT:", json.dumps({k: m[k] for k in ("brand_name","generic_name","strength","dose","frequency","duration_days","duration_text","special_instructions")}, ensure_ascii=False))
        print("GT span:", repr(m["source_span"]["text"]))
for m in raw.medications:
    if key.lower() in m.model_dump_json().lower():
        print("RAW:", m.model_dump_json()[:900])
for m in nd.medications:
    if key.lower() in m.model_dump_json().lower():
        d = m.model_dump(mode="json")
        print("NORM:", json.dumps(d, ensure_ascii=False)[:2000])
