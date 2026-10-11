import csv
import json
import shutil
import sys

import pytest

from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from scripts import export_review_sheet as ex  # noqa: E402
from scripts import import_review_sheet as im  # noqa: E402


@pytest.fixture
def tmpl(tmp_path):
    p = tmp_path / "templates.json"
    shutil.copy(ex.TEMPLATES, p)
    return p


def write_sheet(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ex.COLUMNS)
        w.writeheader()
        w.writerows(rows)


def row(tmpl, tid="med.dose", lang="ta", **kw):
    v = json.loads(tmpl.read_text(encoding="utf-8"))["strings"].get(tid) or {"en": {"text": ""}, lang: {"text": ""}}
    base = dict(template_id=tid, language=lang, english=v["en"]["text"], translation=v.get(lang, {}).get("text", ""), placeholders="", status="draft_unreviewed", reviewer_verdict="", reviewer_correction="", reviewer_comment="")
    return {**base, **kw}


def test_export_has_bom_and_all_ta_hi_rows(tmp_path):
    out = tmp_path / "s.csv"
    n = ex.export(sheet=out)
    raw = out.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") and n == 2 * len(json.loads(ex.TEMPLATES.read_text(encoding="utf-8"))["strings"])
    rows = list(csv.DictReader(out.open(encoding="utf-8-sig")))
    assert list(rows[0]) == ex.COLUMNS and {r["language"] for r in rows} == {"ta", "hi"}


def test_valid_correction_is_imported_and_marked_reviewed(tmpl, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(tmpl, reviewer_verdict="understandable_but_awkward", reviewer_correction="ஒவ்வொரு தடவையும் அளவு: {dose}."), row(tmpl, "med.strength", "hi", reviewer_verdict="correct")])
    errs, n = im.import_sheet(sheet, "AB", "2026-10-20", tmpl)
    assert not errs and n == 2
    s = json.loads(tmpl.read_text(encoding="utf-8"))["strings"]
    assert s["med.dose"]["ta"]["text"] == "ஒவ்வொரு தடவையும் அளவு: {dose}." and s["med.dose"]["ta"]["review_status"] == "reviewed"
    assert s["med.dose"]["ta"]["reviewer"] == "AB" and s["med.dose"]["ta"]["reviewed_on"] == "2026-10-20"
    assert s["med.strength"]["hi"]["review_status"] == "reviewed" and s["med.dose"]["hi"]["review_status"] == "draft_unreviewed"


def test_correction_dropping_a_placeholder_rejects_the_whole_file(tmpl, tmp_path):
    before = tmpl.read_text(encoding="utf-8")
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(tmpl, "med.strength", "hi", reviewer_verdict="correct"), row(tmpl, reviewer_verdict="wrong_meaning", reviewer_correction="ஒவ்வொரு முறையும் அளவு.")])
    errs, n = im.import_sheet(sheet, "AB", None, tmpl)
    assert n == 0 and len(errs) == 1 and "row 3" in errs[0] and "placeholders" in errs[0]
    assert tmpl.read_text(encoding="utf-8") == before  # nothing written, not even the valid row


def test_added_or_renamed_placeholder_rejected(tmpl, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(tmpl, reviewer_verdict="correct", reviewer_correction="{dose} {extra}"), row(tmpl, reviewer_verdict="correct", reviewer_correction="{doze}")])
    errs, _ = im.import_sheet(sheet, "AB", None, tmpl)
    assert len(errs) == 2


def test_unknown_template_language_verdict_and_stale_english(tmpl, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(tmpl, "nope.id", "ta", reviewer_verdict="correct"), row(tmpl, lang="fr", reviewer_verdict="correct"), row(tmpl, lang="en", reviewer_verdict="correct"),
                        row(tmpl, reviewer_verdict="fine"), row(tmpl, reviewer_verdict="correct", english="old english"), row(tmpl, reviewer_verdict="unsafe")])
    errs, n = im.import_sheet(sheet, "AB", None, tmpl)
    assert n == 0 and len(errs) == 6
    assert "unknown template_id" in errs[0] and "unknown language" in errs[1] and "unknown language" in errs[2] and "not one of" in errs[3] and "stale" in errs[4] and "needs a reviewer_correction" in errs[5]


def test_blank_rows_are_skipped_and_initials_required(tmpl, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(tmpl)])
    assert im.import_sheet(sheet, "AB", None, tmpl) == ([], 0)
    write_sheet(sheet, [row(tmpl, reviewer_verdict="correct")])
    errs, _ = im.import_sheet(sheet, " ", None, tmpl)
    assert errs == ["reviewer initials are required"]
