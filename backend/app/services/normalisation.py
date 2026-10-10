"""Deterministic post-extraction normalisation.

Decision rule: where the abbreviation table derives a value from the verbatim quote, the rule value is final and a
disagreement with the model is recorded (provenance "conflict" + a conflict_<field> flag). Where the rules derive
nothing, the model's value is kept. Names are never silently corrected: see app.normalisation.names.
"""

from app.normalisation.abbreviations import derive
from app.normalisation.names import resolve_names
from app.schemas.extraction_output import ExtractionOutput, OutMedication
from app.schemas.normalised import NormalisedDocument, NormalisedFrequency, NormalisedMedication, Provenance, Sourced


# Recorded in `flags` (audit trail) but they describe something already resolved, so they do not raise needs_verification
AUDIT_FLAGS = {"conflict_times_per_day", "conflict_timing_label", "conflict_is_prn", "conflict_duration_days", "role_corrected"}


def _sourced(model_value, rule_value, derived: bool, flags: list[str], name: str) -> Sourced:
    if not derived:
        return Sourced(value=model_value, provenance=Provenance.model, model_value=model_value, rule_value=None)
    if model_value is not None and model_value != rule_value:
        flags.append(f"conflict_{name}")
        return Sourced(value=rule_value, provenance=Provenance.conflict, model_value=model_value, rule_value=rule_value)
    return Sourced(value=rule_value, provenance=Provenance.rule, model_value=model_value, rule_value=rule_value)


def normalise_medication(m: OutMedication) -> NormalisedMedication:
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
    flags = list(dict.fromkeys(flags))

    reasons = [x for x in flags if x not in AUDIT_FLAGS]
    if m.confidence.value == "low":
        reasons.append("low_confidence")
    return NormalisedMedication(
        as_written_brand_name=m.brand_name, as_written_generic_name=m.generic_name,
        printed_brand=names.printed_brand, printed_generic=names.printed_generic,
        resolved_generic=names.resolved_generic, resolved_generic_provenance=names.resolved_provenance,
        brand_name=names.final_brand, generic_name=names.final_generic, name_match_type=names.match_type, near_miss_name=names.near_miss,
        strength=m.strength, form=m.form, route=m.route, dose=m.dose,
        frequency=NormalisedFrequency(times_per_day=times, timing_label=timing, is_prn=prn, original_abbreviation=f.original_abbreviation),
        duration_days=dur, duration_text=m.duration_text, special_instructions=m.special_instructions,
        source_quote=m.source_quote, confidence=m.confidence,
        flags=flags, needs_verification=bool(reasons), reasons=reasons,
    )


def normalise_document(out: ExtractionOutput) -> NormalisedDocument:
    d = out.model_dump(exclude={"medications"})
    return NormalisedDocument(**d, medications=[normalise_medication(m) for m in out.medications])
