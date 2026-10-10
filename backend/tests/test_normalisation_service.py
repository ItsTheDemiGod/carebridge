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
    assert "conflict_timing_label" in m.flags and m.needs_verification
    assert m.frequency.times_per_day.provenance.value == "rule"  # model agreed


def test_model_value_kept_when_rules_derive_nothing():
    m = med(quote="Tab Glucophage 500 mg", brand="Glucophage", times=2, timing="morning", strength="500 mg", days=7)
    assert m.frequency.times_per_day.value == 2 and m.frequency.times_per_day.provenance.value == "model"
    assert m.frequency.timing_label.value == "morning" and m.duration_days.value == 7 and m.flags == [] and not m.needs_verification


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
    m = med(quote="Tab Glucophage 500 mg", brand="Glucophage", conf="low", strength="500 mg")
    assert m.needs_verification and m.reasons == ["low_confidence"]


def test_ambiguous_od_keeps_model_value_and_flags():
    m = med(quote="Eye drops Xyz 1 drop OD", brand="Xyz", times=1, form="drops")
    assert "ambiguous_OD" in m.flags and m.frequency.times_per_day.provenance.value == "model" and m.needs_verification
