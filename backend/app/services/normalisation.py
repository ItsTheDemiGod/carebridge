"""Deterministic post-extraction normalisation.

Decision rule: where the abbreviation table derives a value from the verbatim quote, the rule value is final and a
disagreement with the model is recorded (provenance "conflict" + a conflict_<field> flag). Where the rules derive
nothing, the model's value is kept. Names are never silently corrected: see app.normalisation.names.

Review levels: must_confirm (the user must confirm with the document/doctor), note (audit information, no action), none.
Every flag that is not explicitly in NOTE_FLAGS is must_confirm, so a new flag is safe by default.
The service works from the model's output only. Document text is optional and used only for evaluation and tests.
"""

import re

from app.normalisation.abbreviations import Derived, derive
from app.normalisation.names import key, resolve_names
from app.schemas.extraction_output import ExtractionOutput, OutMedication
from app.schemas.normalised import NormalisedDocument, NormalisedFrequency, NormalisedMedication, Provenance, Sourced

# Information only: the rule value is final (derived from the verbatim quote). role_corrected is NOT here: it is name-related and marked a real error in the Phase 2i breakdown. They stay in `flags` (audit trail).
NOTE_FLAGS = {"conflict_times_per_day", "conflict_timing_label", "conflict_is_prn", "conflict_duration_days"}
MEAL_LABELS = {"before_meals", "after_meals", "with_meals"}
SPECIFIC_TIMING = MEAL_LABELS | {"bedtime", "night", "morning", "afternoon", "evening"}
LONG_DURATION = re.compile(r"\d+\s*(?:months?|mths?|mos?|years?|yrs?)\b", re.I)


def _sourced(model_value, rule_value, derived: bool, flags: list[str], name: str) -> Sourced:
    if not derived:
        return Sourced(value=model_value, provenance=Provenance.model, model_value=model_value, rule_value=None)
    if model_value is not None and model_value != rule_value:
        flags.append(f"conflict_{name}")
        return Sourced(value=rule_value, provenance=Provenance.conflict, model_value=model_value, rule_value=rule_value)
    return Sourced(value=rule_value, provenance=Provenance.rule, model_value=model_value, rule_value=rule_value)


def incomplete_quote_parts(m: OutMedication, rule: Derived, names) -> list[str]:
    """Which returned values have no matching token in the model's own quote (uses only the model's output).
    A truncated or mis-copied quote shows up here, because the model returned values its quote cannot support."""
    q, qk, f, parts = m.source_quote, key(m.source_quote), m.frequency, []
    if m.strength and key(m.strength) not in qk:
        parts.append("strength")
    num = re.search(r"\d+(?:\.\d+)?", m.dose or "")
    if num and not re.search(rf"(?<![\d.]){re.escape(num.group())}(?![\d])", q):
        parts.append("dose")
    no_freq_evidence = rule.times_per_day is None and rule.is_prn is None and not ({"non_daily_frequency", "conflicting_frequency", "ambiguous_OD"} & set(rule.flags))
    once_by_word = f.times_per_day == 1 and not f.is_prn and rule.timing_label in ("bedtime", "night")  # "at bedtime" / "at night" mean once daily
    if no_freq_evidence and (f.times_per_day is not None or f.is_prn) and not once_by_word:
        parts.append("frequency")
    tl = f.timing_label.value
    if tl in MEAL_LABELS:  # a meal relation the quote does not show (the quote may have lost AC/PC); a different meal token is a conflict, not a gap
        if rule.timing_label not in MEAL_LABELS:
            parts.append("timing")
    elif tl in SPECIFIC_TIMING | {"as_needed"} and rule.timing_label is None and not (tl == "as_needed" and rule.is_prn):
        parts.append("timing")  # an unsupported time word that SURVIVES into the final value (when a rule overrides it, the final value is quote-derived)
    if m.duration_days is not None and rule.duration_days is None and not (m.duration_text and key(m.duration_text) in qk) and not LONG_DURATION.search(q) and "conflicting_duration" not in rule.flags:
        parts.append("duration")
    name_len = max((len(key(n)) for n in (names.printed_brand, names.printed_generic, names.final_brand, names.final_generic) if n), default=0)
    if name_len and len(qk) < name_len + len(key(m.strength or "")):
        parts.append("too_short")
    return parts


def review_level(flags: list[str], low_confidence: bool) -> str:
    if low_confidence or any(x not in NOTE_FLAGS for x in flags):
        return "must_confirm"
    return "note" if flags else "none"


def readiness(m_times, m_timing, m_prn, resolved_generic, match_type, flags, level) -> tuple[bool, bool]:
    """interaction_ready: formulary generic from an EXACT printed name. schedule_ready: known daily schedule, not PRN."""
    ok = level != "must_confirm"
    interaction = ok and resolved_generic is not None and match_type == "exact"
    daily = "non_daily_frequency" not in flags
    schedule = ok and daily and not m_prn and m_times is not None and m_timing not in (None, "as_needed", "other")
    return interaction, schedule


def normalise_medication(m: OutMedication, document_text: str | None = None) -> NormalisedMedication:
    flags: list[str] = []
    f = m.frequency
    rule = derive(m.source_quote, m.form.value)
    flags += rule.flags

    prn_rule = rule.is_prn is True
    # PRN entries keep times_per_day null (schema convention), so a model count there is a disagreement
    times = _sourced(f.times_per_day, rule.times_per_day, rule.times_per_day is not None or prn_rule, flags, "times_per_day")
    timing = _sourced(f.timing_label.value, rule.timing_label, rule.timing_label is not None, flags, "timing_label")
    prn = _sourced(f.is_prn, True if prn_rule else None, prn_rule, flags, "is_prn")
    dur = _sourced(m.duration_days, rule.duration_days, rule.duration_days is not None, flags, "duration_days")

    names = resolve_names(m.brand_name, m.generic_name, m.source_quote, m.strength)
    flags += names.flags
    parts = incomplete_quote_parts(m, rule, names)
    reasons = []
    if parts:
        flags.append("incomplete_quote")
        reasons.append("incomplete_quote: " + ",".join(parts))
    qc = None
    if document_text is not None:  # evaluation/tests only
        from app.normalisation import quote_check

        k = quote_check.check(m.source_quote, document_text)
        qc = "exact" if k["exact"] else "normalised_exact" if k["normalised_exact"] else "strict_fuzzy" if k["strict_fuzzy"] else "failed"
        if qc == "failed":
            flags.append("quote_not_in_document")
    flags = list(dict.fromkeys(flags))

    low = m.confidence.value == "low"
    level = review_level(flags, low)
    reasons = [x for x in flags if x not in NOTE_FLAGS and x != "incomplete_quote"] + reasons + (["low_confidence"] if low else [])
    interaction, schedule = readiness(times.value, timing.value, prn.value, names.resolved_generic, names.match_type, flags, level)
    return NormalisedMedication(
        as_written_brand_name=m.brand_name, as_written_generic_name=m.generic_name,
        printed_brand=names.printed_brand, printed_generic=names.printed_generic,
        resolved_generic=names.resolved_generic, resolved_generic_provenance=names.resolved_provenance,
        brand_name=names.final_brand, generic_name=names.final_generic, name_match_type=names.match_type, near_miss_name=names.near_miss,
        strength=m.strength, form=m.form, route=m.route, dose=m.dose,
        frequency=NormalisedFrequency(times_per_day=times, timing_label=timing, is_prn=prn, original_abbreviation=f.original_abbreviation),
        duration_days=dur, duration_text=m.duration_text, special_instructions=m.special_instructions,
        source_quote=m.source_quote, confidence=m.confidence,
        flags=flags, review_level=level, needs_verification=level == "must_confirm", reasons=reasons,
        interaction_ready=interaction, schedule_ready=schedule, quote_check=qc,
    )


def normalise_document(out: ExtractionOutput, document_text: str | None = None) -> NormalisedDocument:
    d = out.model_dump(exclude={"medications"})
    return NormalisedDocument(**d, medications=[normalise_medication(m, document_text) for m in out.medications])
