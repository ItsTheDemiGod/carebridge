"""Deterministic medicine lines from fixed, human-reviewable templates. No model. Structured fields only (never the document text).

Rules: never show a null strength or dose; an unknown value gives a safe "check your document" line (never raises, never guesses);
a medicine that is not schedule_ready is never presented as settled; non-daily frequencies show the original text and ask for confirmation.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from app.schemas.explanation import LANGS, ExplanationLine, LangText, Notice
from app.schemas.normalised import NormalisedMedication

TEMPLATES_PATH = Path(__file__).resolve().parents[3] / "data" / "templates" / "templates.json"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
TIMING_IDS = ("before_meals", "after_meals", "with_meals", "morning", "afternoon", "evening", "night", "bedtime")
NOTICE_FLAGS = ("unresolved_name", "near_miss_name", "unusual_strength", "non_daily_frequency", "incomplete_quote", "ambiguous_OD")


@lru_cache
def load(path: str = str(TEMPLATES_PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def version() -> str:
    return load()["version"]


def render(template_id: str, lang: str, **kw) -> str:
    """Fill {placeholders}. A missing template id or value raises (a bug, caught by tests), never silently leaves braces."""
    return PLACEHOLDER.sub(lambda m: str(kw[m.group(1)]), load()["strings"][template_id][lang]["text"])


def review_status(template_id: str, lang: str) -> str:
    return load()["strings"][template_id][lang]["review_status"]


def _end(s: str, lang: str) -> str:
    """Parts that end in a placeholder (original text, note) get a full stop so sentences do not run together."""
    s = s.rstrip()
    return s if s.endswith((".", "।", "?", "!")) else s + ("।" if lang == "hi" else ".")


def lang_texts(parts: list[tuple[str, dict]]) -> dict[str, LangText]:
    """Template text per language; parts = [(template_id, kwargs)] joined by a space. Review status is the weakest of the parts."""
    out = {}
    for lang in LANGS:
        rs = [review_status(t, lang) for t, _ in parts]
        status = "draft_unreviewed" if "draft_unreviewed" in rs else "reviewed" if "reviewed" in rs else "not_required"
        out[lang] = LangText(text=" ".join(_end(render(t, lang, **kw), lang) for t, kw in parts), status="template", review_status=status)
    return out


def notice(code: str, template_id: str) -> Notice:
    return Notice(code=code, text=lang_texts([(template_id, {})]))


def display_name(m: NormalisedMedication) -> tuple[str | None, str | None]:
    """(name as written in the quote, resolved generic if present and different)."""
    name = m.brand_name or m.generic_name or m.as_written_brand_name or m.as_written_generic_name
    g = m.resolved_generic
    return name, g if g and name and g.strip().lower() != name.strip().lower() else None


def medicine_parts(m: NormalisedMedication) -> list[tuple[str, dict]]:
    p: list[tuple[str, dict]] = []
    name, generic = display_name(m)
    p.append(("med.title_generic", {"name": name, "generic": generic}) if name and generic else ("med.title", {"name": name}) if name else ("med.name_missing", {}))
    p.append(("med.strength", {"strength": m.strength}) if m.strength and m.strength.strip() else ("med.strength_missing", {}))
    p.append(("med.dose", {"dose": m.dose}) if m.dose and m.dose.strip() else ("med.dose_missing", {}))

    f = m.frequency
    original = (f.original_abbreviation or "").strip() or m.source_quote
    times, timing = f.times_per_day.value, f.timing_label.value
    if "non_daily_frequency" in m.flags:
        p.append(("med.non_daily", {"original": original}))  # includes its own confirmation request
    elif f.is_prn.value is True or timing == "as_needed":
        p.append(("med.as_needed", {}))
        if (f.original_abbreviation or "").strip():
            p.append(("med.original", {"original": f.original_abbreviation.strip()}))
    else:
        if isinstance(times, int) and not isinstance(times, bool) and 1 <= times <= 6:
            p.append((f"med.times_{times}", {"n": times}))
        elif times is None:
            p.append(("med.times_missing", {}))
        else:
            p.append(("med.original", {"original": original}))  # out of range or odd value: show the original, never a guess
        if timing in TIMING_IDS:
            p.append((f"timing.{timing}", {}))
        elif timing == "unspecified":
            p.append(("timing.unspecified", {}))
        elif timing == "other":
            p.append(("timing.other", {"original": original}))
        else:
            p.append(("med.unknown_value", {}))  # None or an enum value this engine does not know
        if not m.schedule_ready:
            p.append(("med.schedule_unconfirmed", {}))

    days = m.duration_days.value
    if isinstance(days, int) and not isinstance(days, bool) and days >= 1:
        p.append(("med.duration_1", {"n": days}) if days == 1 else ("med.duration_days", {"n": days}))
    elif m.duration_text and m.duration_text.strip():
        p.append(("med.duration_text", {"text": m.duration_text.strip()}))
    elif days is None:
        p.append(("med.duration_missing", {}))
    else:
        p.append(("med.unknown_value", {}))
    if m.special_instructions and m.special_instructions.strip():
        p.append(("med.special", {"text": m.special_instructions.strip()}))
    return p


def medicine_line(m: NormalisedMedication, index: int) -> ExplanationLine:
    notices = []
    if m.review_level == "must_confirm":
        notices.append(notice("must_confirm", "banner.must_confirm"))
    notices += [notice(fl, f"notice.{fl}") for fl in NOTICE_FLAGS if fl in m.flags]
    return ExplanationLine(
        line_id=f"med-{index}", source_ref=index, kind="medicine", text=lang_texts(medicine_parts(m)), source_text=m.source_quote, status="template",
        display_mode="explanation", review_level=m.review_level, flags=list(m.flags), notices=notices,
        settled=m.review_level != "must_confirm" and m.schedule_ready)
