import csv
import json
import shutil
import sys

import pytest

from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from scripts import export_phrase_sheet as ex  # noqa: E402
from scripts import import_phrase_sheet as im  # noqa: E402


@pytest.fixture
def lib(tmp_path):
    p = tmp_path / "phrases.json"
    shutil.copy(ex.PHRASES, p)
    return p


def by_id(lib):
    return {p["id"]: p for p in json.loads(lib.read_text(encoding="utf-8"))["phrases"]}


def write_sheet(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ex.COLUMNS)
        w.writeheader()
        w.writerows(rows)


def row(lib, pid="adv.001", lang="ta", **kw):
    p = by_id(lib)[pid]
    return {**dict(phrase_id=pid, kind=p["kind"], language=lang, english=p["english"], translation=p[lang]["text"], placeholders="", status="draft_unreviewed",
                   reviewer_verdict="", reviewer_correction="", reviewer_comment=""), **kw}


SLOT = "adv.003"  # Drink {n} litres of water every day.
FIXED_NUM = "fu.002"  # Review after 1 week.


def test_ids_used_below_are_the_expected_phrases(lib):
    assert by_id(lib)[SLOT]["english"] == "Drink {n} litres of water every day." and by_id(lib)[FIXED_NUM]["english"] == "Review after 1 week."


def test_export_has_bom_columns_and_two_rows_per_phrase(tmp_path):
    out = tmp_path / "s.csv"
    n = ex.export(sheet=out)
    assert out.read_bytes().startswith(b"\xef\xbb\xbf") and n == 2 * len(by_id(ex.PHRASES))
    rows = list(csv.DictReader(out.open(encoding="utf-8-sig")))
    assert list(rows[0]) == ex.COLUMNS and {r["language"] for r in rows} == {"ta", "hi"} and any(r["placeholders"] == "n" for r in rows)


def test_valid_rows_are_imported_with_initials_and_date(lib, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(lib, SLOT, "hi", reviewer_verdict="understandable_but_awkward", reviewer_correction="हर दिन {n} लीटर पानी पिएँ।"), row(lib, "adv.001", "ta", reviewer_verdict="correct")])
    errs, n = im.import_sheet(sheet, "AB", "2026-10-20", lib)
    assert not errs and n == 2
    p = by_id(lib)
    assert p[SLOT]["hi"]["text"] == "हर दिन {n} लीटर पानी पिएँ।" and p[SLOT]["hi"]["review_status"] == "reviewed"
    assert p[SLOT]["hi"]["reviewer"] == "AB" and p[SLOT]["hi"]["reviewed_on"] == "2026-10-20"
    assert p["adv.001"]["ta"]["review_status"] == "reviewed" and p["adv.001"]["hi"]["review_status"] == "draft_unreviewed"


@pytest.mark.parametrize("bad,msg", [
    ("தினமும் தண்ணீர் குடிக்கவும்.", "placeholders"),  # drops {n}
    ("தினமும் {n} லிட்டர் தண்ணீர் மற்றும் 2 பழங்கள் உண்ணவும்.", "numbers"),  # adds a digit that is not in the English
])
def test_corrections_that_drop_a_placeholder_or_add_a_digit_reject_the_whole_file(lib, tmp_path, bad, msg):
    before = lib.read_text(encoding="utf-8")
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(lib, "adv.001", "hi", reviewer_verdict="correct"), row(lib, SLOT, "ta", reviewer_verdict="wrong_meaning", reviewer_correction=bad)])
    errs, n = im.import_sheet(sheet, "AB", None, lib)
    assert n == 0 and len(errs) == 1 and "row 3" in errs[0] and msg in errs[0]
    assert lib.read_text(encoding="utf-8") == before


def test_literal_number_may_not_be_dropped_or_changed(lib, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(lib, FIXED_NUM, "hi", reviewer_verdict="wrong_meaning", reviewer_correction="2 हफ़्ते बाद दोबारा जाँच के लिए आएँ।")])
    errs, _ = im.import_sheet(sheet, "AB", None, lib)
    assert len(errs) == 1 and "numbers" in errs[0]
    write_sheet(sheet, [row(lib, FIXED_NUM, "hi", reviewer_verdict="wrong_meaning", reviewer_correction="1 हफ़्ते बाद फिर से जाँच के लिए आएँ।")])
    assert im.import_sheet(sheet, "AB", None, lib) == ([], 1)


def test_unknown_id_language_verdict_stale_english_missing_correction_and_wrong_script(lib, tmp_path):
    rows = [row(lib, "adv.001", "ta", phrase_id="adv.999", reviewer_verdict="correct"), row(lib, language="fr", reviewer_verdict="correct"), row(lib, reviewer_verdict="fine"),
            row(lib, english="Something else.", reviewer_verdict="correct"), row(lib, reviewer_verdict="unsafe"),
            row(lib, reviewer_verdict="wrong_meaning", reviewer_correction="Drink plenty of fluids."), row(lib, reviewer_verdict="wrong_meaning", reviewer_correction="நிறைய ௩ திரவங்களைக் குடிக்கவும்.")]
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, rows)
    errs, n = im.import_sheet(sheet, "AB", None, lib)
    assert n == 0 and len(errs) == 7
    assert "unknown phrase_id" in errs[0] and "unknown language" in errs[1] and "reviewer_verdict" in errs[2] and "stale" in errs[3] and "needs a reviewer_correction" in errs[4] and "script" in errs[5] and "0 to 9" in errs[6]


def test_reviewer_initials_required_and_empty_rows_skipped(lib, tmp_path):
    sheet = tmp_path / "r.csv"
    write_sheet(sheet, [row(lib), row(lib, "adv.002", "hi", reviewer_verdict="correct")])
    assert im.import_sheet(sheet, "  ", None, lib)[0] == ["reviewer initials are required"]
    assert im.import_sheet(sheet, "AB", None, lib) == ([], 1)
