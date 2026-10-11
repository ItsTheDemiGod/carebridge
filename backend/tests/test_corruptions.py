import random
import sys

from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from eval import make_corruptions as mc  # noqa: E402
from eval.corruption_eval import det_fail, item_dropped_detection  # noqa: E402

R = random.Random(1)


def test_each_corruption_changes_the_text_as_intended():
    assert mc.number_changed("Review after 7 days.", R) == "Review after 8 days." and mc.number_changed("Rest.", R) is None
    assert mc.negation_dropped("Do not take Metformin on an empty stomach.", R) == ("Take Metformin on an empty stomach.", "dropped")
    assert mc.negation_dropped("Vomiting that does not stop.", R)[0] == "Vomiting that stop."
    assert mc.negation_dropped("Drink water.", R) == ("Do not drink water.", "inserted")
    t = mc.drug_name_swapped("Take Metformin twice.", R)
    assert t != "Take Metformin twice." and "Metformin" not in t and mc.drug_name_swapped("Drink water.", R) is None
    assert mc.timing_swapped("Take it before meals.", R) == "Take it after meals." and mc.timing_swapped("Rest.", R) is None
    assert mc.urgency_dropped("Return to hospital immediately if the fever continues.", R) == "Tell the doctor at the next visit if the fever continues."
    assert mc.urgency_dropped("Blood in stool.", R) is None
    assert mc.clause_dropped("Eat rice and drink water.", R) == "Eat rice."
    assert mc.clause_dropped("Rest.", R) is None
    assert mc.invented_advice("Rest.", R).startswith("Rest. ")


def test_build_is_deterministic_and_capped():
    pool = [dict(doc=f"d{i}", item_id=f"warning-{i}", kind="warning", source="Return to hospital immediately if fever lasts 3 days.", plain="Return to hospital immediately if fever lasts 3 days.",
                 plain_verified=True, ta="தமிழ் 3", hi="हिंदी 3", ta_back="x", hi_back="y", ta_verified=True, hi_verified=True) for i in range(60)]
    a, b = mc.build(pool), mc.build(pool)
    assert a == b
    en_counts = {t: sum(v["lang"] == "en" and v["type"] == t for v in a) for t in mc.EN_TYPES}
    assert all(n <= mc.CAP for n in en_counts.values()) and en_counts["number_changed"] == mc.CAP and en_counts["urgency_dropped"] > 0
    assert {v["type"] for v in a if v["lang"] == "ta"} == {"number_changed", "wrong_script"}  # no drug name in these lines


def test_deterministic_catches_what_it_should_and_misses_what_it_cannot():
    v = dict(kind="warning", lang="en", source="Do not take Metformin with alcohol.")
    assert det_fail({**v, "text": "Do not take Aspirin with alcohol."})  # drug swapped
    assert not det_fail({**v, "text": "Take Metformin with alcohol."})  # a dropped negation is invisible to the deterministic checks
    assert det_fail({**v, "text": "Do not take Metformin with alcohol. You may stop the medicine when you feel better."})


def test_item_dropped_is_always_detected():
    pool = [dict(doc="d1", item_id=f"advice-{i}") for i in range(3)] + [dict(doc="d2", item_id="warning-0")]
    r = item_dropped_detection(pool)
    assert r["n"] == 4 and r["deterministic"] == 1.0 and r["judge"] is None
