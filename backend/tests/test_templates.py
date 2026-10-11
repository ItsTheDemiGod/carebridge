import itertools
import json
import re

import pytest
from medfactory import med  # noqa: E402

from app.schemas.explanation import LANGS
from app.schemas.extraction import TimingLabel
from app.services import templates as T
from app.services.script import script_ok, script_share

S = T.load()["strings"]
PH = re.compile(r"\{(\w+)\}")
HEAD = "Glycomet (generic name: Metformin). Strength: 500 mg. Dose each time: 1 tablet. "
CONFIRM = "Please confirm this schedule with your doctor or pharmacist before relying on it. "


def en(**kw) -> str:
    return T.medicine_line(med(**kw), 0).text["en"].text


GOLDEN = [
    (dict(), HEAD + "2 times a day. After meals. Duration: 5 days."),
    (dict(generic="Metformin"), HEAD + "2 times a day. After meals. Duration: 5 days."),
    (dict(brand="Metformin"), "Metformin. Strength: 500 mg. Dose each time: 1 tablet. 2 times a day. After meals. Duration: 5 days."),  # resolved generic equals the name: not repeated
    (dict(resolved=None), "Glycomet. Strength: 500 mg. Dose each time: 1 tablet. 2 times a day. After meals. Duration: 5 days."),
    (dict(strength=None, dose=None), "Glycomet (generic name: Metformin). Strength: not found in the document. Dose each time: not found in the document. 2 times a day. After meals. Duration: 5 days."),
    (dict(times=1, timing="morning", days=1), HEAD + "1 time a day. In the morning. Duration: 1 day."),
    (dict(times=3, timing="before_meals", days=None), HEAD + "3 times a day. Before meals. Duration: not stated in the document."),
    (dict(times=4, timing="with_meals", days=None, days_text="till review"), HEAD + "4 times a day. With meals. Duration written in your document: till review."),
    (dict(times=1, timing="bedtime", abbr="HS"), HEAD + "1 time a day. At bedtime. Duration: 5 days."),
    (dict(times=2, timing="unspecified", sched=False),
     HEAD + "2 times a day. No meal timing was found in the document. Please check the label or ask a pharmacist. " + CONFIRM + "Duration: 5 days."),
    (dict(times=None, timing="as_needed", prn=True, abbr="SOS", sched=False, days=None), HEAD + "Only when needed, as your document says. Written in your document as: SOS. Duration: not stated in the document."),
    (dict(times=1, timing="other", abbr="alt days", sched=False), HEAD + "1 time a day. Timing written in your document: alt days. " + CONFIRM + "Duration: 5 days."),
    (dict(flags=["non_daily_frequency"], abbr="once weekly", times=None, timing="unspecified", sched=False, level="must_confirm"),
     HEAD + "This medicine is not taken every day. Your document says: once weekly. Please confirm the schedule with your doctor or pharmacist. Duration: 5 days."),
    (dict(timing="sideways", sched=False), HEAD + "2 times a day. A detail was not understood. Please check your document. " + CONFIRM + "Duration: 5 days."),
    (dict(brand=None, resolved=None), "Medicine name: not found in the document. Strength: 500 mg. Dose each time: 1 tablet. 2 times a day. After meals. Duration: 5 days."),
    (dict(special="Take with plenty of water"), HEAD + "2 times a day. After meals. Duration: 5 days. Note in your document: Take with plenty of water."),
]


@pytest.mark.parametrize("kw,expected", GOLDEN)
def test_golden_english(kw, expected):
    assert en(**kw) == expected


def test_must_confirm_banner_and_flag_notices():
    ln = T.medicine_line(med(level="must_confirm", flags=["unresolved_name", "near_miss_name", "ambiguous_OD", "conflict_timing_label"], sched=False), 3)
    assert [n.code for n in ln.notices] == ["must_confirm", "unresolved_name", "near_miss_name", "ambiguous_OD"]  # conflict_* has no notice (audit only)
    assert ln.notices[0].text["en"].text == "Please check this medicine against your document or label before using it."
    assert not ln.settled and ln.review_level == "must_confirm" and ln.source_ref == 3


def test_settled_only_when_schedule_ready_and_not_must_confirm():
    assert T.medicine_line(med(), 0).settled
    assert not T.medicine_line(med(sched=False), 0).settled
    assert not T.medicine_line(med(level="must_confirm"), 0).settled


def test_unspecified_never_implies_any_time_is_fine():
    t = en(timing="unspecified", sched=False).lower()
    assert "no meal timing was found" in t and "ask a pharmacist" in t and "any time" not in t and "anytime" not in t


def test_null_values_never_shown():
    t = en(strength=None, dose=None)
    assert "None" not in t and "null" not in t.lower()


def test_exhaustive_enum_combinations_never_raise_and_cover_all_languages():
    timings = [t.value for t in TimingLabel] + [None, "bogus"]
    times = [None, 0, 1, 2, 3, 4, 5, 6, 7, 99, "x"]
    n = 0
    for timing, tm, prn, fl, sr, days, abbr in itertools.product(timings, times, (False, True), ([], ["non_daily_frequency"], ["ambiguous_OD", "incomplete_quote"]), (True, False), (None, 0, 1, 5, -2), (None, "BD")):
        ln = T.medicine_line(med(timing=timing, times=tm, prn=prn, flags=fl, sched=sr, days=days, abbr=abbr, level="must_confirm" if fl else "none"), 0)
        assert set(ln.text) == set(LANGS)
        for lang, lt in ln.text.items():
            assert lt.text.strip() and not re.search(r"[{}]", lt.text), (lang, lt.text)
            assert "None" not in lt.text
        n += 1
    assert n > 10000


def test_every_template_in_all_languages_with_same_placeholders():
    for tid, v in S.items():
        assert set(v) == set(LANGS), tid
        base = sorted(PH.findall(v["en"]["text"]))
        for lang in LANGS:
            assert v[lang]["text"].strip(), (tid, lang)
            assert sorted(PH.findall(v[lang]["text"])) == base, (tid, lang)


def test_required_template_ids_exist():
    need = ["disclaimer", "banner.must_confirm", "fallback.notice", "not_found.line", "med.title", "med.strength_missing", "med.dose_missing", "med.duration_missing", "med.non_daily"]
    need += [f"heading.{h}" for h in ("disclaimer", "medicines", "follow_ups", "advice", "warnings", "not_found")] + [f"med.times_{n}" for n in range(1, 7)]
    need += [f"timing.{t}" for t in ("before_meals", "after_meals", "with_meals", "morning", "afternoon", "evening", "night", "bedtime", "other", "unspecified")]
    need += [f"notice.{f}" for f in T.NOTICE_FLAGS]
    assert not [n for n in need if n not in S]


def test_ta_hi_strings_are_drafts_and_in_the_right_script():
    for tid, v in S.items():
        assert v["en"]["review_status"] == "not_required"
        for lang in ("ta", "hi"):
            assert v[lang]["review_status"] == "draft_unreviewed", (tid, lang)  # no native speaker has reviewed anything yet
            bare = re.sub(r"\{\w+\}", "", v[lang]["text"])
            if tid != "med.title":  # only a placeholder
                assert script_ok(bare, lang), (tid, lang, script_share(bare, lang))


def test_digits_are_western():
    for tid, v in S.items():
        for lang in ("ta", "hi"):
            assert not re.search(r"[०-९௦-௯]", v[lang]["text"]), (tid, lang)


def test_script_helper():
    assert script_ok("இது ஒரு சோதனை Metformin 500 mg", "ta") and not script_ok("This is a test", "ta")
    assert script_ok("यह एक परीक्षण है Metformin", "hi") and not script_ok("இது ஒரு சோதனை", "hi")  # Tamil text is not Hindi
    assert script_ok("Take after meals", "en") and not script_ok("இது ஒரு சோதனை", "en")
    assert not script_ok("Metformin 500", "ta")  # no target-script letters: fails closed


def test_rendered_tamil_hindi_keep_names_and_have_no_braces():
    ln = T.medicine_line(med(), 0)
    for lang in ("ta", "hi"):
        assert "Glycomet" in ln.text[lang].text and "Metformin" in ln.text[lang].text and "500 mg" in ln.text[lang].text
        assert "{" not in ln.text[lang].text


def test_templates_file_is_valid_json_utf8():
    assert json.loads(T.TEMPLATES_PATH.read_text(encoding="utf-8"))["version"]
