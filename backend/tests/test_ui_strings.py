"""Phase 6a: ui.* strings (honest-copy rules, generated frontend file freshness, review sheet)."""
import csv
import json
import re
import sys

from app.services import templates as T
from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import add_phase6a_templates as P6  # noqa: E402
import add_phase6b_templates as P6B  # noqa: E402
import add_phase6c_templates as P6C  # noqa: E402
import add_phase6d_templates as P6D  # noqa: E402
import export_ui_strings as E  # noqa: E402

# "safe" and "safely" as words; the others as phrases. "unsafe" and "safety" are different words and are not matched.
FORBIDDEN = re.compile(r"\b(safe|safely|guaranteed?|accurate|accurately|accuracy|certified|clinically validated|doctor-approved)\b", re.I)
UI = {tid: v for tid, v in T.load()["strings"].items() if tid.startswith("ui.")}


def test_all_new_ids_are_in_templates_as_drafts():
    assert set(P6.NEW) | set(P6B.NEW) | set(P6C.NEW) | set(P6D.NEW) == set(UI)
    assert len(P6.NEW) + len(P6B.NEW) + len(P6C.NEW) + len(P6D.NEW) == len(UI)  # no id defined twice
    for v in UI.values():
        assert v["en"]["review_status"] == "not_required" and v["ta"]["review_status"] == v["hi"]["review_status"] == "draft_unreviewed"


NEGATED_SAFE = "This does not mean they are safe."  # the ONLY allowed use of the word "safe" (same form as the backend template)


def test_english_copy_has_no_forbidden_words():
    assert [t for t, v in UI.items() if FORBIDDEN.search(v["en"]["text"].replace(NEGATED_SAFE, ""))] == []


def test_english_ui_copy_passes_guardrail():
    # the negated "does not mean they are safe" passes by negation; no allow-list entry is needed
    from app.safety.guardrails import scan
    assert [(t, scan(v["en"]["text"])) for t, v in UI.items() if scan(v["en"]["text"])] == []


def test_english_copy_does_not_claim_review_by_anyone():
    # a sentence that names a reviewer and a review verb must be negated ("not checked by", "No pharmacist has reviewed it")
    for tid, v in UI.items():
        for s in re.split(r"(?<=[.!?])\s+", v["en"]["text"]):
            if re.search(r"(pharmacist|native speaker|doctor)", s, re.I) and re.search(r"\b(reviewed|checked|verified|approved)\b", s, re.I):
                assert re.search(r"\b(not|no|never|nor)\b", s, re.I), (tid, s)


def test_generated_strings_file_is_up_to_date():
    assert E.OUT.read_text(encoding="utf-8") == E.build(), "run: python scripts/export_ui_strings.py"


def test_generated_strings_cover_all_languages_and_keep_status():
    g = json.loads(E.OUT.read_text(encoding="utf-8"))
    assert set(g) == {"en", "ta", "hi"} and set(g["en"]) == set(g["ta"]) == set(g["hi"]) == set(UI) | {"ui.sample.line"}
    assert all(g[lang][k]["review_status"] == "draft_unreviewed" for lang in ("ta", "hi") for k in g[lang])


def test_review_sheet_has_every_new_id_for_ta_and_hi():
    raw = (REPO / "data" / "templates" / "review_sheet_phase6a_new.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    assert {(r["template_id"], r["language"]) for r in rows} == {(t, lang) for t in P6.NEW for lang in ("ta", "hi")}


def test_phase6b_review_sheet_has_every_new_id_for_ta_and_hi():
    raw = (REPO / "data" / "templates" / "review_sheet_phase6b_new.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    assert {(r["template_id"], r["language"]) for r in rows} == {(t, lang) for t in P6B.NEW for lang in ("ta", "hi")}


def test_phase6c_review_sheet_has_every_new_id_for_ta_and_hi():
    raw = (REPO / "data" / "templates" / "review_sheet_phase6c_new.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    assert {(r["template_id"], r["language"]) for r in rows} == {(t, lang) for t in set(P6C.NEW) | {"ui.photo.pillbox", "ui.photo.water"} for lang in ("ta", "hi")}


def test_phase6d_review_sheet_has_every_new_and_corrected_id_for_ta_and_hi():
    raw = (REPO / "data" / "templates" / "review_sheet_phase6d_new.csv").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    assert {(r["template_id"], r["language"]) for r in rows} == {(t, lang) for t in set(P6D.NEW) | P6D.CORRECTED_PHOTOS for lang in ("ta", "hi")}


def test_corrected_photo_alt_texts_are_applied_and_drafts():
    for tid in P6D.CORRECTED_PHOTOS:
        assert UI[tid]["en"]["text"] == P6.NEW[tid][0] and UI[tid]["ta"]["text"] == P6.NEW[tid][1] and UI[tid]["hi"]["text"] == P6.NEW[tid][2]
        assert UI[tid]["ta"]["review_status"] == UI[tid]["hi"]["review_status"] == "draft_unreviewed"
