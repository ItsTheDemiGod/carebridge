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


# --- Phase 5c: author self-check mode -------------------------------------------------------------------------------------------------
AUTH = dict(checked_by="author_prototype_selfcheck", checked_on="2026-10-16", basis="pair_specific_label", evidence_url="https://example.org/label",
            evidence_section="7.1 Drug interactions", evidence_note="names the other drug")


def author_sheet(ref, **kw):
    p = ref / "review" / "interactions_supplement_review.csv"
    rows = list(csv.DictReader(p.open(encoding="utf-8-sig")))
    for r in rows:
        r.update({**AUTH, **{"reviewer_verdict": "agree", "reviewer_severity": "", "reviewer_comment": "", "reviewer_initials": "", "review_date": ""}, **kw})
    out = ref / "selfcheck.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return out


def entry(ref):
    return json.loads((ref / "interactions_supplement.json").read_text())["entries"][0]


def test_author_mode_sets_author_checked_never_reviewed(ref):
    M.import_sheet(author_sheet(ref), ref, author=True)
    e = entry(ref)
    assert e["status"] == "author_checked" and e["checked_by"] == "author_prototype_selfcheck" and e["evidence"]["url"] and "reviewer_initials" not in e
    for verdict in ("agree", "change_severity", "remove", "needs_more_info"):
        M.import_sheet(author_sheet(ref, reviewer_verdict=verdict, reviewer_severity="moderate"), ref, author=True)
        assert entry(ref)["status"] in ("author_checked", "draft_unreviewed")


def test_author_mode_disabled_verdicts_stay_disabled(ref):
    for verdict in ("remove", "needs_more_info"):
        M.import_sheet(author_sheet(ref, reviewer_verdict=verdict), ref, author=True)
        assert entry(ref)["status"] == "draft_unreviewed"


def test_author_mode_refuses_other_checked_by_initials_and_missing_evidence(ref):
    for bad in (dict(checked_by="AB"), dict(reviewer_initials="AB"), dict(evidence_note=""), dict(checked_on="yesterday")):
        with pytest.raises(M.SheetError):
            M.import_sheet(author_sheet(ref, **bad), ref, author=True)
    assert entry(ref)["status"] == "draft_unreviewed"


def test_normal_mode_cannot_produce_author_checked(ref):
    with pytest.raises(M.SheetError):  # an author sheet fed to the normal mode: no initials, and checked_by is refused
        M.import_sheet(author_sheet(ref), ref)
    p = ref / "review" / "interactions_supplement_review.csv"
    fill(p, reviewer_verdict="agree", reviewer_severity="moderate", **GOOD)
    M.import_sheet(p, ref)
    assert entry(ref)["status"] == "reviewed"


def test_author_mode_can_rewrite_the_summary_and_keeps_the_old_text(ref):
    M.import_sheet(author_sheet(ref, summary_en="New wording."), ref, author=True)
    e = entry(ref)
    assert e["summary_en"] == "New wording." and e["summary_en_before_selfcheck"] == "x"
