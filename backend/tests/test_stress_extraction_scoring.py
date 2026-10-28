"""Phase 7c-lite: the stress extraction scorer. Ground truth fed in as the 'model output' must pass all four criteria; a dropped medicine must show as a miss (mini store, no model)."""
import sys

from app.schemas.extraction_output import from_ground_truth
from app.services.guards import REPO
from tests.test_stress_set import mini_data

sys.path.insert(0, str(REPO))
from eval.stress import run_stress_extraction as X  # noqa: E402
from eval.stress.run_safety_stress import load_stress  # noqa: E402


def test_ground_truth_as_output_passes_and_dropped_medicine_is_counted():
    data = mini_data()
    docs = [(d, gt) for d, gt in load_stress() if d["category"] in ("major_pair", "weekly")]
    rows = [X.score_doc(d, gt, from_ground_truth(gt), data) for d, gt in docs]
    assert all(r.get("strict_silent_misses", 0) == r.get("unconfirmed", 0) + r.get("silent_not_covered_by_flag", 0) for r in rows)
    assert all(r.get("nondaily_schedule_ready", 0) == 0 and r.get("ir_wrong_generic", 0) == 0 for r in rows)
    assert all(r["ov_found_right_level"] == r["ov_gt_pairs_extracted"] for r in rows)
    d, gt = next((d, gt) for d, gt in docs if d["category"] == "major_pair")
    out = from_ground_truth(gt)
    out.medications = out.medications[1:]
    r = X.score_doc(d, gt, out, data)
    assert r["gt_meds"] - r["tp_norm"] == 1
    assert r.get("silent_not_covered_by_flag", 0) == r["gt_pairs"] - r.get("found", 0) - r.get("unconfirmed", 0)
