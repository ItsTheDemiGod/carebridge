import json
import sys

import pytest

from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth
from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from eval.matching import best_window_ratio, norm_name, norm_strength, score_document, summarize  # noqa: E402


def load(doc_id):
    gt = from_ground_truth(ExtractedDocument.model_validate_json((REPO / f"data/ground_truth/{doc_id}.json").read_text(encoding="utf-8")))
    return gt, (REPO / f"data/synthetic/{doc_id}.txt").read_text(encoding="utf-8")


def pred_of(gt):
    return ExtractionOutput.model_validate(json.loads(gt.model_dump_json()))


def metrics(gt, pred, text):
    return summarize(score_document(gt, pred, text))


def test_normalisation():
    assert norm_strength("500mg") == norm_strength("500 MG")
    assert norm_name("Tab. Metformin") == norm_name("METFORMIN") == "metformin"
    assert norm_name("Cap Amoxicillin + Clavulanic acid") == "amoxicillin clavulanic acid"


@pytest.mark.parametrize("doc_id", ["ds_001", "ds_002", "rx_003", "rx_010"])
def test_oracle_is_perfect(doc_id):
    gt, text = load(doc_id)
    m = metrics(gt, pred_of(gt), text)
    for k in ["med_precision", "med_recall", "med_f1", "med_fully_correct_rate", "followup_recall", "redflag_recall", "quote_exact_rate", "quote_fuzzy_rate"]:
        assert m[k] in (1.0, None) and (m[k] is not None or k in ("followup_recall", "redflag_recall")), k
    assert m["followup_days_accuracy"] in (1.0, None)
    assert m["hallucinated_meds"] == 0 and m["invented_value_rate"] == 0 and m["parse_failure_rate"] == 0 and m["low_confidence_rate"] == 0
    assert all(m[k] == 1.0 for k in m if k.startswith("acc_"))


def test_dropped_medication_lowers_recall_only():
    gt, text = load("ds_001")
    p = pred_of(gt)
    p.medications.pop()
    m = metrics(gt, p, text)
    assert m["med_recall"] < 1 and m["med_precision"] == 1.0


def test_invented_medication_is_hallucination():
    gt, text = load("ds_001")
    p = pred_of(gt)
    extra = p.medications[0].model_copy(deep=True)
    extra.brand_name, extra.generic_name = None, "Zzzquinol"
    p.medications.append(extra)
    m = metrics(gt, p, text)
    assert m["med_precision"] < 1 and m["med_recall"] == 1.0 and m["hallucinated_meds"] == 1


def test_wrong_strength_lowers_only_that_field():
    gt, text = load("ds_001")
    p = pred_of(gt)
    p.medications[0].strength = "999 mg"
    m = metrics(gt, p, text)
    assert m["acc_strength"] < 1 and m["med_fully_correct_rate"] < 1
    assert all(m[k] == 1.0 for k in m if k.startswith("acc_") and k != "acc_strength")


def test_null_to_value_is_invented():
    gt, text = load("ds_001")
    idx = next(i for i, m in enumerate(gt.medications) if m.duration_days is None)
    p = pred_of(gt)
    p.medications[idx].duration_days = 5
    m = metrics(gt, p, text)
    assert m["invented_value_rate"] > 0 and m["acc_duration_days"] < 1


def test_parse_failure_counts_as_empty_prediction():
    gt, text = load("ds_001")
    m = metrics(gt, None, text)
    assert m["parse_failure_rate"] == 1.0 and m["med_recall"] == 0.0


def test_quote_validity():
    gt, text = load("ds_001")
    p = pred_of(gt)
    p.medications[0].source_quote = "a quote that is nowhere in the document at all"
    m = metrics(gt, p, text)
    assert m["quote_exact_rate"] < 1 and m["quote_fuzzy_rate"] < 1
    assert best_window_ratio("Tab  Metformin", "x Tab Metformin y") == 1.0


def test_ground_truth_converter_keeps_content():
    gt, _ = load("ds_001")
    raw = json.loads((REPO / "data/ground_truth/ds_001.json").read_text(encoding="utf-8"))
    assert [m.source_quote for m in gt.medications] == [m["source_span"]["text"] for m in raw["medications"]]
    assert all(m.confidence.value == "high" for m in gt.medications) and gt.unreadable_parts == []
