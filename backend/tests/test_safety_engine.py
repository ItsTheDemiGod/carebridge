import json

from app.safety import engine as E
from app.safety import interactions as I
from app.schemas.normalised import NormalisedDocument
from tests.medfactory import med

STORE = {"metformin|omeprazole": {"severity": "minor"}, "acetylsalicylic acid|clopidogrel": {"severity": "major"},
         "furosemide|metformin": {"severity": "moderate"}, "atenolol|metformin": {"severity": "unknown"}}


def doc(*meds):
    return NormalisedDocument(document_type="discharge_summary", medications=list(meds))


def m(resolved, ready=True, level="none", printed=None, **kw):
    x = med(brand=printed or resolved, resolved=resolved, level=level, **kw)
    x.interaction_ready = ready
    x.printed_brand = printed
    return x


def run(*meds, data=None):
    return E.build_report(doc(*meds), data or I.Data(STORE))


def by_pair(r):
    return {(p.a, p.b): p for p in r.pair_results}


def test_garbled_name_is_not_checked_unconfirmed():
    r = run(m("Metformin"), m(None, ready=False, level="must_confirm", printed=None))
    p = r.pair_results[0]
    assert p.status == I.UNCONFIRMED and p.generic_b is None and r.overall_state == "confirm_first"


def test_ready_flag_false_blocks_lookup_even_with_a_generic():
    r = run(m("Metformin"), m("Omeprazole", ready=False))
    assert r.pair_results[0].status == I.UNCONFIRMED


def test_found_pair_and_no_record_pair_never_safe():
    r = run(m("Metformin"), m("Omeprazole"), m("Ramipril"))
    bp = by_pair(r)
    assert bp[(0, 1)].status == I.FOUND and bp[(0, 1)].level == "minor" and bp[(0, 1)].source == "ddinter"
    assert bp[(0, 2)].status == bp[(1, 2)].status == I.NO_RECORD
    assert r.counts.pairs == 3 and r.counts.pairs_by_status == {I.FOUND: 1, I.NO_RECORD: 2} and r.counts.interactions_by_level == {"minor": 1}
    assert r.overall_state == "ok_to_review"
    assert all(p.status in I.STATUSES for p in r.pair_results)


def test_same_drug_twice_is_a_duplicate_notice():
    r = run(m("Metformin", printed="Glycomet"), m("Metformin", printed="Glucophage"))
    assert [d.indices for d in r.duplicate_notices] == [[0, 1]] and r.duplicate_notices[0].basis == "resolved_generic"
    assert r.pair_results[0].same_medicine is True


def test_same_printed_name_without_generic_is_a_duplicate():
    r = run(m(None, ready=False, level="must_confirm", printed="Zzzcort"), m(None, ready=False, level="must_confirm", printed="zzzcort"))
    assert r.duplicate_notices[0].basis == "printed_name"


def test_no_duplicates_for_different_drugs_or_class_members():
    assert run(m("Losartan"), m("Telmisartan")).duplicate_notices == []


def test_ordering_most_severe_first():
    r = run(m("Metformin"), m("Omeprazole"), m("Furosemide"), m("Atenolol"), m("Ramipril"))
    levels = [p.level for p in r.pair_results if p.status == I.FOUND]
    assert levels == ["moderate", "minor", "unknown"]
    assert [p.status for p in r.pair_results[:3]] == [I.FOUND] * 3 and all(p.status != I.FOUND for p in r.pair_results[3:])
    assert r.pair_results[0].level == "moderate"


def test_overall_state_branches():
    assert run(m("Aspirin"), m("Clopidogrel")).overall_state == "review_interactions"  # major found
    assert run(m("Metformin"), m("Furosemide")).overall_state == "review_interactions"  # moderate
    assert run(m("Metformin"), m("Atenolol")).overall_state == "ok_to_review"  # unknown level only
    assert run(m("Aspirin"), m("Clopidogrel"), m("Zz", ready=False, level="must_confirm")).overall_state == "confirm_first"
    assert run().overall_state == "ok_to_review" and run().counts.pairs == 0


def test_missing_store_fails_safe(tmp_path):
    r = run(m("Metformin"), m("Omeprazole"), data=I.load_data(tmp_path / "x.json", tmp_path / "y.json"))
    assert r.pair_results[0].status == I.DB_MISSING and r.overall_state == "ok_to_review"


def _sup(tmp_path, status):
    p = tmp_path / "s.json"
    e = {"pair_id": "S1", "drug_a": "Ramipril", "drug_b": "Spironolactone", "proposed_severity": "moderate", "status": status}
    p.write_text(json.dumps({"entries": [e]}))
    return I.Data(STORE, *I.load_supplement(p))


def test_reviewed_supplement_used(tmp_path):
    r = run(m("Ramipril"), m("Spironolactone"), data=_sup(tmp_path, "reviewed"))
    assert r.pair_results[0].source == "curated_reviewed" and r.overall_state == "review_interactions"
    assert r.supplement_reviewed is True and r.supplement_ignored == 0


def test_unreviewed_supplement_ignored(tmp_path):
    r = run(m("Ramipril"), m("Spironolactone"), data=_sup(tmp_path, "draft_unreviewed"))
    assert r.pair_results[0].status == I.NO_RECORD and r.supplement_reviewed is False and r.supplement_ignored == 1


def test_reminder_points_to_unspecified_or_non_daily():
    r = run(m("Metformin"), m("Omeprazole", timing="unspecified"), m("Ramipril", flags=["non_daily_frequency"]), m("Atenolol", times=None, timing="after_meals"))
    assert r.schedule_reminder == [1, 2, 3]
    assert run(m("Metformin")).schedule_reminder == []


def test_report_has_no_advice_or_safe_words():
    s = run(m("Metformin"), m("Omeprazole")).model_dump_json().lower()
    assert "safe" not in s.replace("same_medicine", "")
