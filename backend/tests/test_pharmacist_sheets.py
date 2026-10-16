import csv
import json
import sys

import pytest

from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import export_pharmacist_sheets as X  # noqa: E402
import import_pharmacist_sheets as M  # noqa: E402

GOOD = dict(reviewer_initials="AB", review_date="2026-10-20")


@pytest.fixture
def ref(tmp_path):
    r = tmp_path / "ref"
    r.mkdir()
    form = {"medicines": [{"generic_name": "Ramipril", "brand_names": ["Cardace"], "available_strengths": ["5 mg"], "form": "capsule", "route": "oral"},
                          {"generic_name": "Spironolactone", "brand_names": ["Aldactone"], "available_strengths": ["25 mg"], "form": "tablet", "route": "oral"}]}
    (r / "formulary.json").write_text(json.dumps(form))
    sup = {"entries": [{"pair_id": "S01", "drug_a": "Ramipril", "drug_b": "Spironolactone", "proposed_severity": "unclassified", "summary_en": "x",
                        "source_url": "u", "source_section": "s", "supporting_sources": [], "status": "draft_unreviewed"}]}
    (r / "interactions_supplement.json").write_text(json.dumps(sup))
    X.main(r, r / "review")
    return r


def fill(path, **kw):
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    for r in rows:
        r.update(kw)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_export_has_bom_and_columns(ref):
    p = ref / "review" / "interactions_supplement_review.csv"
    assert p.read_bytes().startswith(b"\xef\xbb\xbf")
    assert list(csv.DictReader(p.open(encoding="utf-8-sig")).fieldnames)[:3] == ["pair_id", "drug_a", "drug_b"]
    assert "reviewer_correction" in (ref / "review" / "formulary_review.csv").read_text(encoding="utf-8-sig").splitlines()[0]


def test_supplement_import_sets_reviewed(ref):
    p = ref / "review" / "interactions_supplement_review.csv"
    fill(p, reviewer_verdict="change_severity", reviewer_severity="moderate", **GOOD)
    M.import_sheet(p, ref)
    e = json.loads((ref / "interactions_supplement.json").read_text())["entries"][0]
    assert e["status"] == "reviewed" and e["reviewer_severity"] == "moderate"


def test_needs_more_info_is_not_reviewed(ref):
    p = ref / "review" / "interactions_supplement_review.csv"
    fill(p, reviewer_verdict="needs_more_info", **GOOD)
    M.import_sheet(p, ref)
    assert json.loads((ref / "interactions_supplement.json").read_text())["entries"][0]["status"] == "draft_unreviewed"


@pytest.mark.parametrize("kw", [
    dict(reviewer_verdict="change_severity", reviewer_severity="catastrophic"),  # invalid severity
    dict(reviewer_verdict=""),  # missing verdict
    dict(reviewer_verdict="agree"),  # proposed 'unclassified' and no severity given
    dict(reviewer_verdict="maybe", reviewer_severity="minor"),
])
def test_invalid_supplement_rows_refuse_whole_file(ref, kw):
    p = ref / "review" / "interactions_supplement_review.csv"
    before = (ref / "interactions_supplement.json").read_text()
    fill(p, **(GOOD | kw))
    with pytest.raises(M.SheetError):
        M.import_sheet(p, ref)
    assert (ref / "interactions_supplement.json").read_text() == before


def test_missing_initials_or_date_and_unknown_id(ref):
    p = ref / "review" / "interactions_supplement_review.csv"
    fill(p, reviewer_verdict="remove", reviewer_initials="", review_date="20/10/2026")
    with pytest.raises(M.SheetError) as e:
        M.import_sheet(p, ref)
    assert len(e.value.problems) == 2
    fill(p, reviewer_verdict="remove", pair_id="S99", **GOOD)
    with pytest.raises(M.SheetError, match="unknown pair_id"):
        M.import_sheet(p, ref)


def test_formulary_sheet(ref):
    p = ref / "review" / "formulary_review.csv"
    fill(p, reviewer_verdict="agree", **GOOD)
    M.import_sheet(p, ref)
    assert set(json.loads((ref / "formulary_review.json").read_text())) == {"Ramipril", "Spironolactone"}
    fill(p, reviewer_verdict="correct", **GOOD)  # correction missing
    with pytest.raises(M.SheetError, match="needs reviewer_correction"):
        M.import_sheet(p, ref)
    fill(p, reviewer_verdict="agree", generic_name="Notadrug", **GOOD)
    with pytest.raises(M.SheetError, match="unknown generic"):
        M.import_sheet(p, ref)
