import pytest

from app.normalisation import names as N
from app.normalisation.names import resolve_names, scan_quote

IDX = N.index()


def test_every_formulary_name_resolves_to_itself_and_nothing_else():
    for k, e in IDX.items():
        r = resolve_names(None, None, f"Tab. {e.canonical} 1 tab OD")
        assert r.match_type == "exact", e.canonical
        assert r.resolved_generic == e.generic and r.resolved_provenance == "formulary"
        assert (r.printed_brand if e.role == "brand" else r.printed_generic) == e.canonical
        assert (r.printed_generic if e.role == "brand" else r.printed_brand) is None  # nothing else was found
        assert "unresolved_name" not in r.flags and "near_miss_name" not in r.flags


def _mutations(s):
    s = s.lower()
    for i in range(len(s)):
        yield s[:i] + s[i + 1:]  # drop a letter
        yield s[:i] + "x" + s[i + 1:]  # substitute
        if i + 1 < len(s):
            yield s[:i] + s[i + 1] + s[i] + s[i + 2:]  # swap


def test_garbled_names_never_land_on_a_different_drug():
    for e in IDX.values():
        for g in _mutations(e.canonical.replace(" ", "")):
            if N.key(g) in IDX:  # the mutation is itself a real formulary name (e.g. losar -> olsar): an exact match is correct
                continue
            hits, _ = scan_quote(f"Tab {g} 1 tab OD")
            assert all(h[0].generic == e.generic for h in hits), (e.canonical, g)


@pytest.mark.parametrize("quote", ["Tab Glucophage 500 mg 1 tab BD", "TAB. GLUCOPHAGE 500MG 1 tab BD", "tab glucophage 500mg bd"])
def test_exact_case_and_spacing_variants(quote):
    r = resolve_names("Glucophage", None, quote, "500mg")
    assert r.printed_brand == "Glucophage" and r.resolved_generic == "Metformin" and r.match_type == "exact" and r.flags == []
    assert r.final_brand == "Glucophage" and r.final_generic is None  # document prints no generic; the formulary generic stays separate


def test_generic_only_and_both():
    r = resolve_names(None, "metformin", "Tab Metformin 500 mg BD")
    assert r.printed_generic == "Metformin" and r.printed_brand is None and r.final_brand is None
    r = resolve_names("Glucophage", "Metformin", "Tab Glucophage (Metformin) 500 mg BD")
    assert (r.printed_brand, r.printed_generic, r.resolved_generic) == ("Glucophage", "Metformin", "Metformin")


def test_generic_wrongly_placed_in_brand_field():
    r = resolve_names("Metformin", None, "Tab Metformin 500 mg BD")
    assert r.printed_brand is None and r.final_brand is None and r.final_generic == "Metformin" and "role_corrected" in r.flags


def test_brand_wrongly_placed_in_generic_field():
    r = resolve_names(None, "Glucophage", "Tab Glucophage 500 mg BD")
    assert r.printed_generic is None and r.final_generic is None and r.final_brand == "Glucophage" and "role_corrected" in r.flags


def test_same_name_in_both_fields_does_not_copy_generic_into_brand():
    r = resolve_names("Metformin", "Metformin", "Tab Metformin 500 mg BD")
    assert r.final_brand is None and r.final_generic == "Metformin"


def test_model_name_with_junk_is_cleaned_only_through_the_quote():
    r = resolve_names("Tab. Glucophage 500mg", None, "Tab. Glucophage 500mg 1 tab BD")
    assert r.as_written_brand == "Tab. Glucophage 500mg" and r.final_brand == "Glucophage"


def test_near_miss_garble_is_accepted_only_when_very_close_and_flagged():
    r = resolve_names(None, "Atorvastatn", "Tab Atorvastatn 10 mg OD")  # one letter missing: ratio >= 0.92
    assert r.match_type == "fuzzy" and r.printed_generic == "Atorvastatin" and "near_miss_name" in r.flags and r.near_miss == "Atorvastatin"
    assert r.as_written_generic == "Atorvastatn"  # never overwritten


def test_larger_garble_is_not_corrected_only_flagged():
    r = resolve_names(None, "Atorvastin", "Tab Atorvastin 10 mg OD")
    assert r.match_type == "none" and r.printed_generic is None and "unresolved_name" in r.flags and "near_miss_name" in r.flags
    assert r.near_miss == "Atorvastatin" and r.final_generic == "Atorvastin"  # kept as written


def test_unknown_names_stay_none_and_are_flagged():
    for q, b in (("Tab Zorvex 20 mg OD", "Zorvex"), ("Tab Quibblex 5 mg OD", "Quibblex")):
        r = resolve_names(b, None, q)
        assert r.match_type == "none" and r.resolved_generic is None and "unresolved_name" in r.flags and r.final_brand == b


def test_name_not_in_quote_flagged_and_not_final():
    r = resolve_names("Glucophage", "Glibenclamide", "Tab Glucophage 500 mg BD")
    assert "name_not_in_quote" in r.flags and r.final_generic is None


def test_two_drugs_in_one_entry_refused():
    r = resolve_names("Glucophage", "Atorvastatin", "Tab Glucophage + Atorvastatin")
    assert "multiple_drugs_in_quote" in r.flags and r.resolved_generic is None


def test_unusual_strength_flagged_not_changed():
    r = resolve_names("Glucophage", None, "Tab Glucophage 77 mg BD", "77 mg")
    assert "unusual_strength" in r.flags
    assert "unusual_strength" not in resolve_names("Glucophage", None, "Tab Glucophage 500 mg BD", "500 mg").flags
    assert "unusual_strength" not in resolve_names("Glucophage", None, "Tab Glucophage BD", None).flags


def test_ordinary_words_never_fuzzy_match():
    hits, near = scan_quote("Tablet twice daily after meals before food morning bedtime every hours")
    assert hits == [] and near == []


def test_multiword_names():
    r = resolve_names(None, None, "Tab Amoxicillin + Clavulanic acid 625 mg")
    assert r.printed_generic == "Amoxicillin + Clavulanic acid"
    r = resolve_names(None, None, "Tab Metolar XR 50 mg OD")
    assert r.printed_brand == "Metolar XR"


def test_garbled_combination_is_not_matched_to_one_component():
    r = resolve_names(None, None, "Tab moxicillin + clavulanicacid 625 mg")
    assert "possible_combination" in r.flags and r.resolved_generic is None
