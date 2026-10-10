from app.schemas.extraction_output import ExtractionOutput
from app.services.normalisation import normalise_document


def doc(quote, brand=None, generic=None, times=None, timing="unspecified", prn=False, days=None, strength=None, form="tablet", conf="high"):
    return ExtractionOutput.model_validate({
        "document_type": "prescription",
        "medications": [{"brand_name": brand, "generic_name": generic, "strength": strength, "form": form, "route": "oral", "dose": "1 tablet",
                         "frequency": {"times_per_day": times, "timing_label": timing, "original_abbreviation": None, "is_prn": prn},
                         "duration_days": days, "duration_text": None, "special_instructions": None, "source_quote": quote, "confidence": conf}],
    })


def med(**kw):
    q = kw.pop("quote")
    return normalise_document(doc(q, **kw)).medications[0]


def test_rule_overrides_model_and_records_conflict():
    m = med(quote="Tab Glucophage 500 mg 1 tab BD PC", brand="Glucophage", times=2, timing="before_meals", strength="500 mg")
    t = m.frequency.timing_label
    assert (t.value, t.provenance.value, t.model_value, t.rule_value) == ("after_meals", "conflict", "before_meals", "after_meals")
    assert "conflict_timing_label" in m.flags and not m.needs_verification and m.review_level == "note"  # audit-only: the rule value is final
    assert m.frequency.times_per_day.provenance.value == "rule"  # model agreed


def test_model_value_kept_when_rules_derive_nothing():
    m = med(quote="Tab Glucophage 500 mg 1 tab in the morning x 1 month", brand="Glucophage", times=2, timing="morning", strength="500 mg", days=30)
    assert m.frequency.times_per_day.value == 2 and m.frequency.times_per_day.provenance.value == "model"
    assert m.frequency.timing_label.value == "morning" and m.duration_days.value == 30 and m.duration_days.provenance.value == "model"
    # the model's own count (2) has no token in this quote, so it is flagged rather than trusted
    assert "incomplete_quote" in m.flags and m.review_level == "must_confirm" and m.needs_verification


def test_rule_fills_what_model_left_null():
    m = med(quote="Tab Glucophage 500 mg 1 tab TDS x 5/7", brand="Glucophage", strength="500 mg")
    assert m.frequency.times_per_day.value == 3 and m.duration_days.value == 5 and m.duration_days.provenance.value == "rule"


def test_prn_forces_null_times():
    m = med(quote="Tab Dolo 650 1 tab SOS", brand="Dolo", times=1, timing="as_needed", prn=False)
    assert m.frequency.is_prn.value is True and m.frequency.times_per_day.value is None
    assert "conflict_times_per_day" in m.flags and "conflict_is_prn" in m.flags


def test_names_keep_as_written_and_resolve_separately():
    m = med(quote="Tab. Glucophage 500mg BD", brand="Tab. Glucophage 500mg", generic="Metformin", strength="500mg", times=2)
    assert m.as_written_brand_name == "Tab. Glucophage 500mg" and m.as_written_generic_name == "Metformin"
    assert m.brand_name == "Glucophage" and m.generic_name is None  # generic not printed: not copied from the model
    assert m.resolved_generic == "Metformin" and m.resolved_generic_provenance == "formulary" and "name_not_in_quote" in m.flags


def test_unknown_name_is_flagged_not_forced():
    m = med(quote="Tab Zorvex 20 mg OD", brand="Zorvex", times=1)
    assert m.resolved_generic is None and m.brand_name == "Zorvex" and "unresolved_name" in m.flags and m.needs_verification


def test_low_confidence_needs_verification():
    m = med(quote="Tab Glucophage 500 mg 1 tab", brand="Glucophage", conf="low", strength="500 mg")
    assert m.needs_verification and m.reasons == ["low_confidence"]


def test_ambiguous_od_keeps_model_value_and_flags():
    m = med(quote="Eye drops Xyz 1 drop OD", brand="Xyz", times=1, form="drops")
    assert "ambiguous_OD" in m.flags and m.frequency.times_per_day.provenance.value == "model" and m.needs_verification


def test_duplicate_name_fields_and_role_swap_both_need_confirmation():
    m = med(quote="Tab Pantoprazole 40 mg OD", brand="Pantoprazole", generic="Pantoprazole", times=1, strength="40 mg")
    assert "duplicate_name_fields" in m.flags and m.needs_verification and m.brand_name is None
    m = med(quote="Tab Pantoprazole 40 mg 1 tab OD", brand="Pantoprazole", times=1, strength="40 mg")
    assert "role_corrected" in m.flags and m.needs_verification and m.review_level == "must_confirm"  # name-related: marked a real error in the Phase 2i breakdown


def test_unknown_brand_kept_next_to_a_printed_generic():
    m = med(quote="Tab Telmisartan (Zzqx) 40 mg OD", brand="Zzqx", generic="Telmisartan", times=1, strength="40 mg")
    assert m.brand_name == "Zzqx" and m.generic_name == "Telmisartan" and m.resolved_generic == "Telmisartan"


# ---- incomplete_quote (uses only the model's output) ------------------------------------------------------------
def parts(quote, **kw):
    m = med(quote=quote, **kw)
    return m, [r for r in m.reasons if r.startswith("incomplete_quote")]


def test_incomplete_quote_negative_complete_quote():
    m, p = parts("Tab Glucophage 500 mg 1 tab BD PC x 5 days", brand="Glucophage", strength="500 mg", times=2, timing="after_meals", days=5)
    assert p == [] and "incomplete_quote" not in m.flags and m.review_level == "none"


def test_incomplete_quote_strength_missing():
    m, p = parts("Tab Glucophage 1 tab BD PC", brand="Glucophage", strength="500 mg", times=2, timing="after_meals")
    assert p == ["incomplete_quote: strength"]


def test_incomplete_quote_truncated_dropped_meal_token():
    m, p = parts("Tab Pantoprazole 40 mg 1 tab OD x 5/7", generic="Pantoprazole", strength="40 mg", times=1, timing="before_meals", days=5)
    assert p == ["incomplete_quote: timing"] and m.review_level == "must_confirm"


def test_incomplete_quote_frequency_and_duration_missing():
    m, p = parts("Tab Glucophage 500 mg", brand="Glucophage", strength="500 mg", times=2, days=7)
    assert p == ["incomplete_quote: dose,frequency,duration"]


def test_incomplete_quote_dose_number_missing():
    m, p = parts("Tab Glucophage 500 mg BD", brand="Glucophage", strength="500 mg", times=2)
    assert p == ["incomplete_quote: dose"]


def test_incomplete_quote_too_short():
    m, p = parts("Glucophage", brand="Glucophage", strength="500 mg")
    assert "too_short" in p[0] and "strength" in p[0]


def test_incomplete_quote_long_duration_phrase_and_duration_text_are_fine():
    _, p = parts("Tab Glucophage 500 mg 1 tab BD x 3 months", brand="Glucophage", strength="500 mg", times=2, days=90)
    assert p == []


# ---- readiness -------------------------------------------------------------------------------------------------
def test_exact_name_is_interaction_and_schedule_ready():
    m = med(quote="Tab Glucophage 500 mg 1 tab BD PC", brand="Glucophage", strength="500 mg", times=2, timing="after_meals")
    assert m.review_level == "none" and m.resolved_generic == "Metformin" and m.interaction_ready and m.schedule_ready


def test_garbled_name_with_other_valid_generic_in_model_field_is_never_resolved():
    m = med(quote="Tab Atorvastin 10 mg 1 tab OD", brand="Atorvastin", generic="Metformin", strength="10 mg", times=1)
    assert m.resolved_generic is None and not m.interaction_ready and m.review_level == "must_confirm"
    assert m.as_written_generic_name == "Metformin"  # kept as written, never used to resolve
    # the model's generic alone, with nothing printed, must not resolve either
    m = med(quote="Tab 10 mg 1 tab OD", generic="Metformin", strength="10 mg", times=1)
    assert m.resolved_generic is None and not m.interaction_ready


def test_fuzzy_accepted_name_is_resolved_but_not_interaction_ready():
    m = med(quote="Tab Atorvastatn 10 mg 1 tab OD", generic="Atorvastatn", strength="10 mg", times=1)
    assert m.resolved_generic == "Atorvastatin" and m.name_match_type == "fuzzy" and not m.interaction_ready and m.review_level == "must_confirm"


def test_weekly_is_not_schedule_ready():
    m = med(quote="Cap D-Rise 60000IU 1 cap once weekly x 8 weeks", brand="D-Rise", strength="60000 IU", form="capsule", times=1, timing="unspecified", days=56)
    assert "non_daily_frequency" in m.flags and not m.schedule_ready and m.review_level == "must_confirm"


def test_must_confirm_is_neither_ready():
    m = med(quote="Tab Glucophage 500 mg 1 tab BD PC", brand="Glucophage", strength="500 mg", times=2, timing="after_meals", conf="low")
    assert m.review_level == "must_confirm" and not m.interaction_ready and not m.schedule_ready


def test_prn_is_not_schedule_ready_but_can_be_interaction_ready():
    m = med(quote="Tab Dolo 650 mg 1 tab SOS", brand="Dolo", strength="650 mg", timing="as_needed", prn=True)
    assert not m.schedule_ready and m.resolved_generic is not None


def test_document_text_check_is_optional_and_flags_failures():
    q = "Tab Glucophage 500 mg 1 tab BD PC"
    ok = normalise_document(doc(q, brand="Glucophage", strength="500 mg", times=2, timing="after_meals"), "x\n" + q + "\ny").medications[0]
    assert ok.quote_check == "exact" and "quote_not_in_document" not in ok.flags
    bad = normalise_document(doc(q, brand="Glucophage", strength="500 mg", times=2, timing="after_meals"), "Tab Glucophage 50 mg 1 tab BD PC").medications[0]
    assert bad.quote_check == "failed" and bad.review_level == "must_confirm" and not bad.interaction_ready
    assert normalise_document(doc(q, brand="Glucophage", strength="500 mg", times=2, timing="after_meals")).medications[0].quote_check is None
