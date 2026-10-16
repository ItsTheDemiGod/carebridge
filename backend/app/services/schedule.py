"""Suggested daily slots, for schedule_ready medicines only. Pure functions; no model, no clock.

The anchors below are SCHEDULING CONVENIENCES, not clinical statements. Every schedule shows the notice "Suggested times only; adjust them to match
your doctor's instructions" (template schedule.notice). A duration, if known, is shown as an approximate count of days and is never extended.

  anchors: breakfast 08:00, lunch 13:00, dinner 20:00, bedtime 22:00, morning 08:00, afternoon 14:00, evening 18:00, night 21:00
  meal relation (before/after/with meals): before = 30 min before the anchor, after = 30 min after, with = at the anchor
  times per day with a meal relation: 1 -> breakfast; 2 -> breakfast, dinner; 3 -> breakfast, lunch, dinner; 4 -> adds bedtime (22:00, no meal offset);
                                      5 or 6 -> not auto-scheduled, the user sets the times (override)
  time-of-day label (morning/afternoon/evening/night/bedtime), once a day -> that anchor
  unspecified timing (or a time-of-day label with several doses) -> evenly spaced between 08:00 and 22:00 (rounded to 5 minutes) with the notice that
                                      no meal timing was found in the document
  as needed, weekly/non-daily, unconfirmed -> never scheduled"""
import re
from dataclasses import dataclass, field

from app.schemas.confirmation import ConfirmedMedicine

ANCHORS = {"breakfast": "08:00", "lunch": "13:00", "dinner": "20:00", "bedtime": "22:00", "morning": "08:00", "afternoon": "14:00", "evening": "18:00", "night": "21:00"}
MEAL_SLOTS = {1: ["breakfast"], 2: ["breakfast", "dinner"], 3: ["breakfast", "lunch", "dinner"], 4: ["breakfast", "lunch", "dinner", "bedtime"]}
MEAL_OFFSET_MIN = {"before_meals": -30, "after_meals": 30, "with_meals": 0}
TIME_OF_DAY = {"morning", "afternoon", "evening", "night", "bedtime"}
KNOWN_TIMING = set(MEAL_OFFSET_MIN) | TIME_OF_DAY | {"unspecified"}  # anything else (other, unknown values) is never scheduled
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
REF = re.compile(r"^[ma]\d{1,2}$")
NOT_SCHEDULED = ("not_confirmed", "non_daily", "as_needed", "too_many_doses", "no_identity")


def hhmm(minutes: int) -> str:
    minutes %= 24 * 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def minutes(t: str) -> int:
    return int(t[:2]) * 60 + int(t[3:])


def even_times(n: int) -> list[str]:
    if n == 1:
        return [ANCHORS["morning"]]
    a, b = minutes("08:00"), minutes("22:00")
    return [hhmm(round((a + (b - a) * k / (n - 1)) / 5) * 5) for k in range(n)]


@dataclass
class Suggestion:
    times: list[str] = field(default_factory=list)
    reason: str | None = None  # a NOT_SCHEDULED id when times is empty
    no_meal_timing: bool = False
    settable: bool = False  # the user may set times by override (too_many_doses)


def suggest(c: ConfirmedMedicine) -> Suggestion:
    m, f = c.med, c.med.frequency
    times, timing, prn = f.times_per_day.value, f.timing_label.value, f.is_prn.value
    if c.unresolved or m.review_level == "must_confirm":
        return Suggestion(reason="not_confirmed")
    if "non_daily_frequency" in m.flags:
        return Suggestion(reason="non_daily")
    if prn is True or timing == "as_needed":
        return Suggestion(reason="as_needed")
    if not m.resolved_generic:
        return Suggestion(reason="no_identity")  # defensive: schedule_ready does not itself need an identity
    if not m.schedule_ready or not isinstance(times, int) or isinstance(times, bool) or times < 1 or timing not in KNOWN_TIMING:
        return Suggestion(reason="not_confirmed")
    if times > 4:
        return Suggestion(reason="too_many_doses", settable=True)
    if timing in MEAL_OFFSET_MIN:
        out = []
        for slot in MEAL_SLOTS[times]:
            base = minutes(ANCHORS[slot])
            out.append(hhmm(base + (MEAL_OFFSET_MIN[timing] if slot != "bedtime" else 0)))
        return Suggestion(times=out)
    if timing in TIME_OF_DAY and times == 1:
        return Suggestion(times=[ANCHORS[timing]])
    return Suggestion(times=even_times(times), no_meal_timing=True)  # unspecified, or a time-of-day label with several doses


def valid_times(times: list[str]) -> bool:
    return 1 <= len(times) <= 6 and len(set(times)) == len(times) and all(isinstance(t, str) and HHMM.match(t) for t in times)
