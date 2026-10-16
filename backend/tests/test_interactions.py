import json
import sys

import pytest

from app.safety import interactions as I
from app.safety.names import components
from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import build_interaction_store as B  # noqa: E402

STORE = {"metformin|omeprazole": {"severity": "minor"}, "acetylsalicylic acid|clopidogrel": {"severity": "moderate"},
         "amoxicillin|metformin": {"severity": "major"}, "cholecalciferol|metformin": {"severity": "unknown"}}


def data(**kw):
    return I.Data(STORE, **kw)


def test_found_and_order_independent():
    assert I.check("Metformin", "Omeprazole", data()) == I.check("Omeprazole", "Metformin", data()) == I.Result(I.FOUND, "minor", "ddinter")


def test_renamed_generic_goes_through_the_map_only():
    assert I.check("Aspirin", "Clopidogrel", data()).level == "moderate"
    assert components("Acetylsalicylic acid") == []


def test_no_record_is_never_found_or_safe():
    r = I.check("Metformin", "Ramipril", data())
    assert r == I.Result(I.NO_RECORD) and r.level is None and I.STATUSES == (I.FOUND, I.NO_RECORD, I.UNCONFIRMED, I.DB_MISSING)


def test_unconfirmed_when_either_is_none():
    assert I.check(None, "Metformin", data()).status == I.check("Metformin", None, data()).status == I.UNCONFIRMED


def test_unknown_generic_has_no_record():
    assert I.check("Metformin", "Notadrug", data()).status == I.NO_RECORD


def test_missing_store_fails_safe(tmp_path):
    d = I.load_data(tmp_path / "nope.json", tmp_path / "nope2.json")
    assert d.store is None and I.check("Metformin", "Omeprazole", d).status == I.DB_MISSING
    (tmp_path / "bad.json").write_text("{not json")
    assert I.load_store(tmp_path / "bad.json") is None


def test_combination_checks_each_component_and_takes_highest():
    r = I.check("Amoxicillin + Clavulanic acid", "Metformin", data())
    assert r == I.Result(I.FOUND, "major", "ddinter")
    r = I.check("Calcium carbonate + Vitamin D3", "Metformin", data())
    assert r.level == "unknown" and r.status == I.FOUND
    assert I.check("Budesonide + Formoterol", "Ramipril", data()).status == I.NO_RECORD


def sup(status, **kw):
    e = {"pair_id": "s1", "drug_a": "Ramipril", "drug_b": "Spironolactone", "proposed_severity": "moderate", "status": status}
    return e | kw


def write_sup(tmp_path, entries):
    p = tmp_path / "s.json"
    p.write_text(json.dumps({"entries": entries}))
    return p


def test_reviewed_supplement_used_unreviewed_ignored(tmp_path):
    ok, ignored = I.load_supplement(write_sup(tmp_path, [sup("reviewed"), sup("draft_unreviewed", pair_id="s2", drug_a="Atenolol", drug_b="Amlodipine")]))
    d = I.Data(STORE, ok, ignored)
    assert ignored == 1
    assert I.check("Spironolactone", "Ramipril", d) == I.Result(I.FOUND, "moderate", "curated_reviewed")
    assert I.check("Atenolol", "Amlodipine", d).status == I.NO_RECORD


def test_reviewer_severity_and_remove_and_unclassified(tmp_path):
    ok, _ = I.load_supplement(write_sup(tmp_path, [sup("reviewed", reviewer_severity="major"), sup("reviewed", pair_id="s2", drug_a="Atenolol", drug_b="Amlodipine", reviewer_verdict="remove"),
                                                    sup("reviewed", pair_id="s3", drug_a="Losartan", drug_b="Enalapril", proposed_severity="unclassified")]))
    d = I.Data(STORE, ok)
    assert I.check("Ramipril", "Spironolactone", d).level == "major"
    assert I.check("Atenolol", "Amlodipine", d).status == I.NO_RECORD
    assert I.check("Losartan", "Enalapril", d).level == "unknown"


def test_supplement_never_lowers_ddinter_level(tmp_path):
    ok, _ = I.load_supplement(write_sup(tmp_path, [sup("reviewed", drug_a="Amoxicillin", drug_b="Metformin", proposed_severity="minor")]))
    assert I.check("Metformin", "Amoxicillin", I.Data(STORE, ok)).level == "major"


def test_builder_keeps_highest_and_counts_conflicts(tmp_path):
    hdr = "DDInterID_A,Drug_A,DDInterID_B,Drug_B,Level\n"
    (tmp_path / "ddinter_downloads_code_A.csv").write_text(hdr + "1,Metformin,2,Omeprazole,Minor\n1,Metformin,3,Zzz,Major\n", encoding="utf-8")
    (tmp_path / "ddinter_downloads_code_B.csv").write_text(hdr + "2,omeprazole,1,metformin,Major\n", encoding="utf-8")
    res = B.build(tmp_path, {"metformin", "omeprazole"})
    assert res["pairs"] == {"metformin|omeprazole": {"severity": "major", "files": ["A", "B"], "conflicts": 1}}


def test_case_is_handled_through_the_formulary_map_only():
    assert I.check("metformin", "OMEPRAZOLE", data()).level == "minor"
    assert components("aspirin") == ["acetylsalicylic acid"] and components("Notadrug") == []
