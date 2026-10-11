import csv
import sys

from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from scripts import import_review_pack as ip  # noqa: E402


def rows():
    return [dict(document_id="d1", line_id="advice-0", language="ta", source_text="s", shown_text="t", status="verified", reviewer_verdict="", reviewer_comment=""),
            dict(document_id="d1", line_id="advice-1", language="ta", source_text="s", shown_text="u", status="unverified", reviewer_verdict="", reviewer_comment="")]


def test_summary_and_validation():
    orig, ret = rows(), rows()
    ret[0]["reviewer_verdict"], ret[1]["reviewer_verdict"], ret[1]["reviewer_comment"] = "correct", "wrong_meaning", "says food not stool"
    errs, md = ip.summarise(ret, orig, "AB")
    assert not errs and "| unverified | wrong_meaning | 1 |" in md and "says food not stool" in md


def test_refuses_bad_rows():
    orig = rows()
    for mutate, text in [(lambda r: r[0].update(reviewer_verdict="great"), "not one of"), (lambda r: r[0].update(reviewer_verdict="unsafe"), "needs a comment"),
                         (lambda r: r[0].update(shown_text="edited"), "shown_text differs"), (lambda r: r[0].update(line_id="zz"), "unknown line"), (lambda r: r.pop(), "missing")]:
        ret = rows()
        mutate(ret)
        errs, _ = ip.summarise(ret, orig, "AB")
        assert any(text in e for e in errs), (text, errs)


def test_real_pack_files_have_a_bom_and_columns():
    for lang in ("ta", "hi"):
        p = REPO / "docs" / "review_pack" / f"review_{lang}.csv"
        assert p.read_bytes().startswith(b"\xef\xbb\xbf")
        assert list(csv.DictReader(p.open(encoding="utf-8-sig")).fieldnames) == ["document_id", "line_id", "language", "source_text", "shown_text", "status", "reviewer_verdict", "reviewer_comment"]
