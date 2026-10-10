"""Derive frequency, timing and duration from the VERBATIM text of a medication entry (its source_quote).

Standard prescription shorthand only. Whole tokens only, case-insensitive, dots tolerated (b.d., T.D.S.).
Nothing is guessed: anything not written is returned as None. Precedence for timing_label:
meal relation > one time-of-day word (morning/afternoon/evening/night/bedtime) > as_needed > unspecified (frequency known) > None.
"""

import re
from dataclasses import dataclass, field

# --- tables -----------------------------------------------------------------------------------------------
TIMES_ABBR = {"od": 1, "qd": 1, "bd": 2, "bid": 2, "tds": 3, "tid": 3, "qid": 4, "qds": 4, "hs": 1}  # HS = once, at bedtime
NUMBER_WORDS = {"once": 1, "one": 1, "twice": 2, "two": 2, "thrice": 3, "three": 3, "four": 4}
PRN_RE = r"(?:sos|prn|as needed|as required|when needed|when required|if needed|if required)"
MEAL = {  # label -> patterns
    "before_meals": [r"ac", r"before (?:food|meals?|breakfast|lunch|dinner|eating)"],
    "after_meals": [r"pc", r"after (?:food|meals?|breakfast|lunch|dinner|eating)"],
    "with_meals": [r"with (?:food|meals?)"],
}
TIME_WORDS = {  # label -> patterns (hs / at bedtime = bedtime, "night" = night)
    "bedtime": [r"hs", r"bed ?time", r"before sleep"],
    "night": [r"nocte", r"night"],
    "morning": [r"morning"],
    "afternoon": [r"afternoon"],
    "evening": [r"evening"],
}
EYE_RE = re.compile(r"(?<![a-z0-9])(?:eyes?|ocular|ophthalmic)(?![a-z0-9])")


@dataclass
class Derived:
    times_per_day: int | None = None
    timing_label: str | None = None
    is_prn: bool | None = None  # True only if written; absence is not evidence
    duration_days: int | None = None
    flags: list[str] = field(default_factory=list)


def _clean(text: str) -> str:
    t = text.lower()
    # b.d. / t.d.s. / q.i.d. / a.c. -> bd / tds / qid / ac (two or more single letters, each followed by a dot)
    t = re.sub(r"(?<![a-z0-9])((?:[a-z]\.){2,4})(?![a-z])", lambda m: m.group(1).replace(".", ""), t)
    return re.sub(r"\s+", " ", t)


def _tok(p: str) -> str:
    return rf"(?<![a-z0-9]){p}(?![a-z0-9])"


def _take(pattern: str, t: str):
    """Find all matches; return (matches, text with them blanked so later rules cannot re-match)."""
    ms = list(re.finditer(pattern, t))
    for m in reversed(ms):
        t = t[: m.start()] + " " * (m.end() - m.start()) + t[m.end():]
    return ms, t


def _frequencies(t: str, eye: bool, flags: list[str]) -> set[int]:
    found: set[int] = set()
    # 1-0-1 style (morning-noon-night): number of non-zero slots; "5/7" is a duration, never a pattern
    ms, t = _take(r"(?<![\d/.])(\d)\s*[-+]\s*(\d)\s*[-+]\s*(\d)(?:\s*[-+]\s*(\d))?(?![\d/.]|\s*(?:mg|ml|mcg|iu|g)\b)", t)
    for m in ms:
        found.add(sum(1 for g in m.groups() if g and g != "0"))
    # every N hours / qNh
    ms, t = _take(_tok(r"(?:every|q)\s*(\d+)\s*(?:hours?|hrs?|h)"), t)
    for m in ms:
        n = int(m.group(1))
        if n and 24 % n == 0:
            found.add(24 // n)
    # "3 times a day", "three times daily", "twice a day", "once daily", "2 times per day"
    words = "|".join(NUMBER_WORDS)
    ms, t = _take(_tok(rf"(?:(\d+)|({words}))(?: times?)?(?: (?:a|per|each) day| daily)"), t)
    for m in ms:
        found.add(int(m.group(1)) if m.group(1) else NUMBER_WORDS[m.group(2)])
    # abbreviations (OD is ambiguous for eye medicines: right eye)
    ms, t = _take(_tok("(" + "|".join(TIMES_ABBR) + ")"), t)
    for m in ms:
        if m.group(1) == "od" and eye:
            if "ambiguous_OD" not in flags:
                flags.append("ambiguous_OD")
            continue
        found.add(TIMES_ABBR[m.group(1)])
    ms, t = _take(_tok(r"(?:daily|every ?day|each day)"), t)
    if ms:
        found.add(1)
    return found


def _durations(t: str) -> set[int]:
    found: set[int] = set()
    ms, t = _take(r"(?<![a-z0-9/])(?:x\s*)?(\d+)\s*/\s*(7|52)(?![0-9])", t)  # x 5/7 = days, x 2/52 = weeks
    for m in ms:
        found.add(int(m.group(1)) * (1 if m.group(2) == "7" else 7))
    ms, t = _take(_tok(r"(?:x\s*)?(\d+)\s*(?:weeks?|wks?)"), t)
    for m in ms:
        found.add(int(m.group(1)) * 7)
    ms, t = _take(_tok(r"(?:x\s*)?(\d+)\s*(?:days?|d)"), t)
    for m in ms:
        found.add(int(m.group(1)))
    return found


def _labels(table: dict, t: str) -> set[str]:
    return {label for label, pats in table.items() for p in pats if re.search(_tok(p), t)}


def derive(quote: str, form: str | None = None) -> Derived:
    """Rule-derived values from verbatim entry text. `form` (model's) is used only to spot eye medicines for the OD ambiguity."""
    t = _clean(quote or "")
    d = Derived()
    eye = form == "drops" or bool(EYE_RE.search(t))

    freqs = _frequencies(t, eye, d.flags)
    prn = bool(re.search(_tok(PRN_RE), t))
    d.is_prn = True if prn else None
    if len(freqs) > 1:
        d.flags.append("conflicting_frequency")
    elif len(freqs) == 1 and not prn:  # PRN: times_per_day stays null (schema convention)
        d.times_per_day = next(iter(freqs))

    meals = _labels(MEAL, t)
    times = _labels(TIME_WORDS, t)
    pat = re.search(r"(?<![\d/.])([01])\s*[-+]\s*([01])\s*[-+]\s*([01])(?![\d/.])", t)
    if pat and sum(map(int, pat.groups())) == 1:  # single-slot pattern: 1-0-0 morning, 0-1-0 afternoon, 0-0-1 night
        times.add(("morning", "afternoon", "night")[pat.groups().index("1")])
    if len(meals) > 1:
        d.flags.append("conflicting_meal_relation")
    elif len(meals) == 1:
        d.timing_label = next(iter(meals))
    elif len(times) == 1:
        d.timing_label = next(iter(times))
    elif prn:
        d.timing_label = "as_needed"
    elif d.times_per_day is not None:
        d.timing_label = "unspecified"

    durs = _durations(t)
    if len(durs) > 1:
        d.flags.append("conflicting_duration")
    elif durs:
        d.duration_days = next(iter(durs))
    return d
