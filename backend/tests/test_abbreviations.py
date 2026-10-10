import pytest

from app.normalisation.abbreviations import derive


def got(q, form=None):
    d = derive(q, form)
    return d.times_per_day, d.timing_label, d.is_prn, d.duration_days


CASES = [
    # (quote, times, timing, prn, days)
    ("Tab X 500mg 1 tab OD", 1, "unspecified", None, None),
    ("Tab X 500mg 1 tab od", 1, "unspecified", None, None),
    ("Tab X 1 tab QD", 1, "unspecified", None, None),
    ("Tab X 1 tab BD", 2, "unspecified", None, None),
    ("Tab X 1 tab bid", 2, "unspecified", None, None),
    ("Tab X 1 tab TDS", 3, "unspecified", None, None),
    ("Tab X 1 tab TID", 3, "unspecified", None, None),
    ("Tab X 1 tab QID", 4, "unspecified", None, None),
    ("Tab X 1 tab QDS", 4, "unspecified", None, None),
    ("Tab X 1 tab b.d.", 2, "unspecified", None, None),
    ("Tab X 1 tab T.D.S.", 3, "unspecified", None, None),
    ("Tab X 1 tab q.i.d.", 4, "unspecified", None, None),
    ("Tab X 1 tab BD PC", 2, "after_meals", None, None),
    ("Tab X 1 tab BD pc", 2, "after_meals", None, None),
    ("Tab X 1 tab OD AC", 1, "before_meals", None, None),
    ("Tab X 1 tab OD a.c.", 1, "before_meals", None, None),
    ("Tab X 1 tab TDS with meals", 3, "with_meals", None, None),
    ("Tab X 1 tab BD with food", 2, "with_meals", None, None),
    ("Tab X 1 tab HS", 1, "bedtime", None, None),
    ("Tab X 1 tab at bedtime", None, "bedtime", None, None),
    ("Tab X 1 tab at night", None, "night", None, None),
    ("Tab X 1 tab in the morning", None, "morning", None, None),
    ("Tab X 1 tab SOS", None, "as_needed", True, None),
    ("Tab X 1 tab PRN", None, "as_needed", True, None),
    ("Tab X 1 tab as needed for pain", None, "as_needed", True, None),
    ("Tab X 1 tab SOS x30d", None, "as_needed", True, 30),
    ("Tab X 1 tab twice daily after meals", 2, "after_meals", None, None),
    ("Tab X 1 tablet once a day", 1, "unspecified", None, None),
    ("Tab X 1 tablet three times a day before food", 3, "before_meals", None, None),
    ("Tab X 1 tablet 2 times daily", 2, "unspecified", None, None),
    ("Tab X 1 tablet thrice daily", 3, "unspecified", None, None),
    ("Tab X 1 tablet daily", 1, "unspecified", None, None),
    ("Tab X 1 tab every 8 hours", 3, "unspecified", None, None),
    ("Tab X 1 tab q6h", 4, "unspecified", None, None),
    ("Tab X 1 tab every 12 hrs", 2, "unspecified", None, None),
    ("Tab X 1 tab every 5 hours", None, None, None, None),  # 24/5 not whole: nothing derived
    ("Tab X 1 tab 1-0-1", 2, "unspecified", None, None),
    ("Tab X 1 tab 1-1-1", 3, "unspecified", None, None),
    ("Tab X 1 tab 1-0-0", 1, "morning", None, None),
    ("Tab X 1 tab 0-0-1", 1, "night", None, None),
    ("Tab X 1 tab 1-0-0 PC", 1, "after_meals", None, None),
    ("Tab X 1 tab BD x 5 days", 2, "unspecified", None, 5),
    ("Tab X 1 tab BD x 5/7", 2, "unspecified", None, 5),
    ("Tab X 1 tab BD x5d", 2, "unspecified", None, 5),
    ("Tab X 1 tab BD for 3d", 2, "unspecified", None, 3),
    ("Tab X 1 tab BD for 3 days", 2, "unspecified", None, 3),
    ("Tab X 1 tab OD x 2/52", 1, "unspecified", None, 14),
    ("Tab X 1 tab OD for 2 weeks", 1, "unspecified", None, 14),
    ("Tab X 1 tab OD x 2 wk", 1, "unspecified", None, 14),
    ("Tab X 1 tab OD x 10 days", 1, "unspecified", None, 10),
    # nothing written -> nothing derived
    ("Tab X 500mg", None, None, None, None),
    ("", None, None, None, None),
    # whole tokens only: abbreviations inside words never match
    ("Tab Modafinil 100mg", None, None, None, None),
    ("Tab Bidmet 500 mg", None, None, None, None),
    ("Tab Tidal 5mg", None, None, None, None),
    ("Syp Acetol 5 mL", None, None, None, None),
    ("Tab Hsx 5mg", None, None, None, None),
    ("Cap Mane-D 60000IU", None, None, None, None),
    ("Tab Pcm 500mg 1 tab", None, None, None, None),
    ("Tab Odinase 5mg", None, None, None, None),
    # strengths and doses are not durations or patterns
    ("Tab X 500 mg 1 tab BD", 2, "unspecified", None, None),
    ("Inj X 40 mg - 1 injection OD - SC", 1, "unspecified", None, None),
]


@pytest.mark.parametrize("quote,times,timing,prn,days", CASES)
def test_derive(quote, times, timing, prn, days):
    assert got(quote) == (times, timing, prn, days)


def test_od_eye_is_ambiguous():
    for q, form in (("Eye drops 1 drop OD", None), ("Tab X OD right eye", None), ("Xyz 1 drop OD", "drops"), ("Ophthalmic soln 1 drop OD", None)):
        d = derive(q, form)
        assert d.times_per_day is None and "ambiguous_OD" in d.flags and d.timing_label is None


def test_od_eye_other_frequency_still_read():
    d = derive("Eye drops 1 drop BD", "drops")
    assert d.times_per_day == 2 and "ambiguous_OD" not in d.flags


def test_conflicting_frequency_derives_nothing():
    for q in ("Tab X 1 tab OD BD", "Tab X TDS twice daily", "Tab X 1 tab BD 1-0-0"):
        d = derive(q)
        assert d.times_per_day is None and "conflicting_frequency" in d.flags


def test_conflicting_meal_relation_and_duration():
    d = derive("Tab X BD AC PC")
    assert d.timing_label is None and "conflicting_meal_relation" in d.flags and d.times_per_day == 2
    d = derive("Tab X BD x 5 days then x 3 days")
    assert d.duration_days is None and "conflicting_duration" in d.flags


def test_meal_beats_time_word_and_prn():
    assert derive("Tab X OD at night after food").timing_label == "after_meals"
    assert derive("Tab X SOS at night").timing_label == "night"
    assert derive("Tab X BD morning and night").timing_label == "unspecified"  # two time words: no single label


def test_non_daily_frequency_derives_nothing_and_flags():
    for q in ("Cap X 60000IU once weekly x 8 weeks", "Tab X weekly", "Tab X twice a week", "Tab X every other day", "Tab X alternate days", "Tab X monthly"):
        d = derive(q)
        assert d.times_per_day is None and "non_daily_frequency" in d.flags, q
    assert derive("Cap X once weekly x 8 weeks").duration_days == 56
    assert "non_daily_frequency" not in derive("Tab X BD x 8 weeks").flags
