"""Build NormalisedMedication objects for explanation tests without running the normaliser."""

from app.schemas.normalised import NormalisedFrequency, NormalisedMedication, Sourced


def med(brand="Glycomet", generic=None, resolved="Metformin", strength="500 mg", dose="1 tablet", times=2, timing="after_meals", prn=False, abbr="BD PC", days=5,
        days_text=None, flags=(), level="none", sched=True, quote="Tab Glycomet 500 mg 1 tablet BD PC x 5 days", special=None, form="tablet", route="oral") -> NormalisedMedication:
    return NormalisedMedication(
        brand_name=brand, generic_name=generic, resolved_generic=resolved, strength=strength, form=form, route=route, dose=dose,
        frequency=NormalisedFrequency(times_per_day=Sourced(value=times), timing_label=Sourced(value=timing), is_prn=Sourced(value=prn), original_abbreviation=abbr),
        duration_days=Sourced(value=days), duration_text=days_text, special_instructions=special, source_quote=quote, confidence="high",
        flags=list(flags), review_level=level, needs_verification=level == "must_confirm", schedule_ready=sched)
