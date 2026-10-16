import itertools

import pytest
from pydantic import ValidationError

from app.safety import engine as E
from app.safety import interactions as I
from app.schemas.extraction_output import Confidence
from app.schemas.confirmation import AS_ON_LABEL, AddedMedicine, Confirmations, MedicineDecision, ScheduleEdit
from app.services import confirmation as CF
from app.services.normalisation import normalise_document
from apihelpers import gt_output

STORE = {"glimepiride|metformin": {"severity": "moderate"}, "atorvastatin|metformin": {"severity": "minor"}, "glimepiride|telmisartan": {"severity": "minor"},
         "metformin|omeprazole": {"severity": "major"}, "omeprazole|telmisartan": {"severity": "unknown"}}
DATA = I.Data(STORE)


def crafted():
    """5 medicines: 0 exact+ready (Metformin), 1 garbled name (the model read Metformin as Netfornin), 2 weekly (non_daily), 3 incomplete quote + low confidence, 4 exact+ready (Telmisartan)."""
    o = gt_output("ds_037")
    metformin, amaryl, telma, atorva = o.medications
    garbled = metformin.model_copy(deep=True)
    garbled.brand_name, garbled.generic_name = "Netfornin", "Glibenclamide"
    garbled.source_quote = "Tab Netfornin 500 mg - 1 tablet twice daily after meals"
    amaryl.source_quote = "Tab Amaryl (Glimepiride) 1 mg - 1 tablet once weekly"
    atorva.strength, atorva.confidence = "99 mg", Confidence.low
    o.medications = [metformin, garbled, amaryl, atorva, telma]
    return normalise_document(o)


ND = crafted()


def test_fixture_has_the_intended_shapes():
    m = ND.medications
    assert m[0].interaction_ready and m[0].schedule_ready
    assert not m[1].interaction_ready and {"unresolved_name", "near_miss_name", "name_not_in_quote"} <= set(CF.reason_ids(m[1])) and m[1].resolved_generic is None
    assert "non_daily_frequency" in m[2].flags and not m[2].schedule_ready and m[2].interaction_ready is False
    assert {"incomplete_quote", "unusual_strength", "low_confidence"} <= set(CF.reason_ids(m[3]))
    assert m[4].interaction_ready and m[4].resolved_generic == "Telmisartan"


def dec(i, action, **kw):
    return MedicineDecision(index=i, action=action, **kw)


def run(*decisions, added=()):
    return CF.apply(ND, Confirmations(decisions=list(decisions), added_medicines=list(added)))


def meds_by_ref(ov):
    return {c.ref: c for c in ov.meds}


def test_no_decisions_changes_nothing_and_never_mutates_the_input():
    before = ND.model_dump()
    ov = CF.apply(ND, None)
    assert [c.resolution for c in ov.meds] == ["unchanged"] * 5 and ov.doc.model_dump() == before and ND.model_dump() == before
    assert [c.med.interaction_ready for c in ov.meds] == [m.interaction_ready for m in ND.medications]


def test_confirm_as_extracted_on_exact_identity_resolves_name_reasons_only():
    ov = run(dec(0, "confirm_as_extracted"))
    c = meds_by_ref(ov)["m0"]
    assert c.resolution == "confirmed" and c.med.interaction_ready and c.provenance["medicine"] == "user_confirmed" and c.unresolved == []


def test_confirm_as_extracted_without_identity_stays_not_checkable():
    c = meds_by_ref(run(dec(1, "confirm_as_extracted", acknowledged_flags=["incomplete_quote"] if False else [])))["m1"]
    assert not c.med.interaction_ready and c.med.review_level == "must_confirm" and c.not_checked_reason == "not_identifiable" and "not_identifiable" in c.unresolved
    # acknowledging every flag still cannot identify a medicine
    allflags = CF.reason_ids(ND.medications[1])
    c = meds_by_ref(run(dec(1, "confirm_as_extracted", acknowledged_flags=allflags)))["m1"]
    assert not c.med.interaction_ready and c.not_checked_reason == "not_identifiable" and c.med.resolved_generic is None


def test_not_in_list_keeps_the_medicine_unchecked_and_drops_identity():
    c = meds_by_ref(run(dec(0, "not_in_list", note="my own words")))["m0"]
    assert c.resolution == "not_in_list" and not c.med.interaction_ready and not c.med.schedule_ready and c.med.resolved_generic is None
    assert c.not_checked_reason == "user_not_in_list" and c.med.review_level == "must_confirm"
    assert "my own words" not in c.med.model_dump_json()  # the note is stored in the decision set only, never copied into data used elsewhere


def test_remove_drops_the_medicine_from_the_overlay():
    ov = run(dec(0, "remove"))
    assert ov.removed == [0] and [c.ref for c in ov.meds] == ["m1", "m2", "m3", "m4"] and len(ov.doc.medications) == 4


def test_select_formulary_drug_resolves_name_reasons_and_records_provenance():
    ov = run(dec(1, "select_formulary_drug", formulary_id="metformin", strength_choice="500 mg"))
    c = meds_by_ref(ov)["m1"]
    assert c.resolution == "selected" and c.med.resolved_generic == "Metformin" and c.med.resolved_generic_provenance == "user_selected" and c.med.name_match_type == "user_selected"
    assert c.med.interaction_ready is True and c.unresolved == [] and c.med.review_level == "none" and c.med.generic_name == "Metformin" and c.med.brand_name is None
    assert c.provenance["resolved_generic"] == c.provenance["strength"] == "user_selected" and c.med.strength == "500 mg"
    assert c.med.source_quote == ND.medications[1].source_quote  # the document's own words stay visible for comparison


def test_select_with_strength_as_on_label_keeps_the_extracted_strength():
    c = meds_by_ref(run(dec(1, "select_formulary_drug", formulary_id="metformin", strength_choice=AS_ON_LABEL)))["m1"]
    assert c.med.strength == ND.medications[1].strength and c.provenance["strength"] == "user_confirmed"


def test_other_reasons_need_their_flag_acknowledged():
    reasons = CF.reason_ids(ND.medications[3])
    c = meds_by_ref(run(dec(3, "confirm_as_extracted")))["m3"]
    assert not c.med.interaction_ready and set(c.unresolved) == set(reasons) and c.med.review_level == "must_confirm"
    c = meds_by_ref(run(dec(3, "confirm_as_extracted", acknowledged_flags=reasons[:-1])))["m3"]
    assert not c.med.interaction_ready and c.unresolved == reasons[-1:]  # one missing acknowledgement keeps it must_confirm
    c = meds_by_ref(run(dec(3, "confirm_as_extracted", acknowledged_flags=reasons)))["m3"]
    assert c.med.interaction_ready and c.unresolved == [] and c.med.review_level == "none"


def test_unknown_flag_ids_are_rejected():
    for bad in (["not_a_flag"], ["unusual_strength", "bogus"]):
        with pytest.raises(CF.ConfirmationError) as e:
            run(dec(3, "confirm_as_extracted", acknowledged_flags=bad))
        assert e.value.reason == "unknown_flag"
    with pytest.raises(CF.ConfirmationError):
        run(dec(0, "confirm_as_extracted", acknowledged_flags=["unusual_strength"]))  # a real flag id, but not a reason of this medicine


@pytest.mark.parametrize("decisions,reason", [
    ([dec(9, "confirm_as_extracted")], "invalid_index"),
    ([dec(0, "confirm_as_extracted"), dec(0, "remove")], "invalid_index"),
    ([dec(0, "select_formulary_drug", formulary_id="nope", strength_choice="500 mg")], "unknown_formulary_id"),
    ([dec(0, "select_formulary_drug", formulary_id="metformin", strength_choice="7 mg")], "invalid_strength_choice"),
    ([dec(0, "select_formulary_drug", formulary_id="metformin")], "invalid_strength_choice"),
    ([dec(0, "confirm_as_extracted", formulary_id="metformin")], "unexpected_field"),
    ([dec(0, "remove", schedule_edit=ScheduleEdit(times_per_day=1, timing_label="morning"))], "unexpected_field"),
])
def test_invalid_decision_sets_are_rejected(decisions, reason):
    with pytest.raises(CF.ConfirmationError) as e:
        run(*decisions)
    assert e.value.reason == reason


def test_strict_models_reject_unknown_fields_and_bad_values():
    for bad in ({"index": 0, "action": "confirm_as_extracted", "free_text_name": "x"}, {"index": 0, "action": "delete_all"}, {"index": 0, "action": "not_in_list", "note": "x" * 81},
                {"index": -1, "action": "remove"}, {"index": 0, "action": "confirm_as_extracted", "schedule_edit": {"times_per_day": 7, "timing_label": "morning"}},
                {"index": 0, "action": "confirm_as_extracted", "schedule_edit": {"times_per_day": 0, "timing_label": "morning"}},
                {"index": 0, "action": "confirm_as_extracted", "schedule_edit": {"times_per_day": 1, "timing_label": "whenever"}}):
        with pytest.raises(ValidationError):
            MedicineDecision.model_validate(bad)
    with pytest.raises(ValidationError):
        AddedMedicine(formulary_id="metformin", strength_choice="500 mg", dose="a handful", schedule=ScheduleEdit(times_per_day=1, timing_label="morning"))
    assert MedicineDecision(index=0, action="not_in_list", note="x" * 80)


def test_replace_semantics_are_idempotent():
    d = [dec(1, "select_formulary_drug", formulary_id="metformin", strength_choice="500 mg"), dec(2, "remove")]
    a, b = run(*d), run(*d)
    assert a.model_dump() == b.model_dump()
    assert run().model_dump() == CF.apply(ND, None).model_dump() or [c.resolution for c in run().meds] == ["unchanged"] * 5  # an empty set clears earlier decisions


def test_schedule_edit_rules():
    ready = lambda ov, ref: meds_by_ref(ov)[ref].med.schedule_ready  # noqa: E731
    e3 = ScheduleEdit(times_per_day=3, timing_label="after_meals", duration_days=7)
    ov = run(dec(0, "confirm_as_extracted", schedule_edit=e3))
    c = meds_by_ref(ov)["m0"]
    assert c.med.schedule_ready and c.med.frequency.times_per_day.value == 3 and c.med.duration_days.value == 7 and c.provenance["times_per_day"] == "user_confirmed"
    assert not ready(run(dec(0, "confirm_as_extracted", schedule_edit=ScheduleEdit(times_per_day="as_needed", timing_label="morning"))), "m0")  # as needed: never scheduled
    assert not ready(run(dec(0, "confirm_as_extracted", schedule_edit=ScheduleEdit(times_per_day=2, timing_label="other"))), "m0")
    assert ready(run(dec(0, "confirm_as_extracted", schedule_edit=ScheduleEdit(times_per_day=2, timing_label="unspecified"))), "m0")  # unspecified = known, no meal timing
    # weekly stays unscheduled even after identity, acknowledgement and an edit
    c = meds_by_ref(run(dec(2, "select_formulary_drug", formulary_id="glimepiride", strength_choice="1 mg", acknowledged_flags=CF.reason_ids(ND.medications[2]), schedule_edit=e3)))["m2"]
    assert c.med.interaction_ready and not c.med.schedule_ready and "non_daily_frequency" in c.med.flags
    assert meds_by_ref(run(dec(0, "confirm_as_extracted", schedule_edit=ScheduleEdit(times_per_day=1, timing_label="morning", duration_days=None))))["m0"].med.duration_days.value is None


def test_added_medicines_come_only_from_the_formulary():
    add = AddedMedicine(formulary_id="omeprazole", strength_choice="20 mg", dose="1 capsule", schedule=ScheduleEdit(times_per_day=1, timing_label="before_meals", duration_days=14))
    ov = run(added=[add])
    c = meds_by_ref(ov)["a0"]
    assert c.resolution == "added" and c.med.interaction_ready and c.med.schedule_ready and c.med.resolved_generic == "Omeprazole" and c.provenance["medicine"] == "user_added"
    assert c.med.source_quote == CF.ADDED_QUOTE and c.med.dose == "1 capsule" and len(ov.doc.medications) == 6
    with pytest.raises(CF.ConfirmationError):
        run(added=[AddedMedicine(formulary_id="my-own-drug", strength_choice="1 mg", dose="1 tablet", schedule=ScheduleEdit(times_per_day=1, timing_label="morning"))])
    with pytest.raises(CF.ConfirmationError):
        run(added=[AddedMedicine(formulary_id="omeprazole", strength_choice="9 mg", dose="1 capsule", schedule=ScheduleEdit(times_per_day=1, timing_label="morning"))])
    prn = AddedMedicine(formulary_id="omeprazole", strength_choice=AS_ON_LABEL, dose="1 capsule", schedule=ScheduleEdit(times_per_day="as_needed", timing_label="morning"))
    c = meds_by_ref(run(added=[prn]))["a0"]
    assert c.med.interaction_ready and not c.med.schedule_ready and c.med.strength is None


def test_adding_a_duplicate_of_an_extracted_medicine_gives_the_duplicate_notice():
    add = AddedMedicine(formulary_id="metformin", strength_choice="500 mg", dose="1 tablet", schedule=ScheduleEdit(times_per_day=2, timing_label="after_meals"))
    r = E.build_report(run(added=[add]).doc, DATA)
    assert any(d.name == "Metformin" for d in r.duplicate_notices)


# --- the synthetic garbled-name case: the model read Metformin as "Netfornin / Glibenclamide" -------------------------------------------------
def pairs(ov, data=DATA):
    r = E.build_report(ov.doc, data)
    refs = [c.ref for c in ov.meds]
    return {(refs[p.a], refs[p.b]): p for p in r.pair_results}


def test_garbled_name_pairs_are_unconfirmed_until_the_user_selects_metformin():
    p = pairs(CF.apply(ND, None))
    assert p[("m0", "m1")].status == I.UNCONFIRMED and p[("m1", "m4")].status == I.UNCONFIRMED  # nothing is looked up for a garbled name
    ov = run(dec(1, "select_formulary_drug", formulary_id="metformin", strength_choice="500 mg"))
    p = pairs(ov)
    assert p[("m1", "m4")].generic_a == "Metformin" and p[("m1", "m4")].status == I.NO_RECORD  # checked now (no record for this pair in the test store)
    assert p[("m0", "m1")].same_medicine  # Metformin twice: the duplicate notice, not an interaction
    assert E.build_report(ov.doc, DATA).duplicate_notices and E.build_report(ov.doc, DATA).duplicate_notices[0].name == "Metformin"


def test_selecting_a_different_drug_gives_results_for_that_drug():
    ov = run(dec(1, "select_formulary_drug", formulary_id="omeprazole", strength_choice="20 mg"), dec(2, "remove"), dec(3, "remove"))
    p = pairs(ov)
    assert p[("m0", "m1")].generic_b == "Omeprazole" and p[("m0", "m1")].status == I.FOUND and p[("m0", "m1")].level == "major"  # metformin + omeprazole in the test store
    assert p[("m1", "m4")].status == I.FOUND and p[("m1", "m4")].level == "unknown" and p[("m1", "m4")].generic_a == "Omeprazole"
    other = pairs(run(dec(1, "select_formulary_drug", formulary_id="metformin", strength_choice="500 mg"), dec(2, "remove"), dec(3, "remove")))
    assert other[("m0", "m1")].same_medicine  # the same document gives different answers for different selections: the user's choice decides


def test_interactions_found_after_selection_with_other_medicines():
    ov = run(dec(1, "select_formulary_drug", formulary_id="metformin", strength_choice="500 mg"), dec(2, "select_formulary_drug", formulary_id="glimepiride", strength_choice="1 mg",
                                                                                                    acknowledged_flags=CF.reason_ids(ND.medications[2])))
    p = pairs(ov)
    assert p[("m1", "m2")].status == I.FOUND and p[("m1", "m2")].level == "moderate" and p[("m2", "m4")].level == "minor"


# --- property-style test over every combination --------------------------------------------------------------------------------------------------
def subsets(xs):
    return [list(c) for r in range(len(xs) + 1) for c in itertools.combinations(xs, r)]


EDITS = [None, ScheduleEdit(times_per_day=2, timing_label="after_meals"), ScheduleEdit(times_per_day="as_needed", timing_label="morning", duration_days=3),
         ScheduleEdit(times_per_day=6, timing_label="unspecified"), ScheduleEdit(times_per_day=1, timing_label="other")]


def all_decisions(i):
    reasons = CF.reason_ids(ND.medications[i])
    for acks in subsets(reasons):
        for edit in EDITS:
            yield dec(i, "confirm_as_extracted", acknowledged_flags=acks, schedule_edit=edit)
            for fid in ("metformin", "omeprazole", "glimepiride"):
                for sc in ("500 mg", AS_ON_LABEL):
                    yield dec(i, "select_formulary_drug", formulary_id=fid, strength_choice=sc if fid == "metformin" else AS_ON_LABEL, acknowledged_flags=acks, schedule_edit=edit)
    yield dec(i, "not_in_list", note="n")
    yield dec(i, "not_in_list")
    yield dec(i, "remove")


def check_invariants(ov, decision):
    snapshot_refs = [c.ref for c in ov.meds]
    assert [c.med for c in ov.meds] == ov.doc.medications
    for c in ov.meds:
        m, f = c.med, c.med.frequency
        identity = bool(m.resolved_generic) and m.name_match_type in ("exact", "user_selected")
        if m.interaction_ready:
            assert identity and not c.unresolved and m.review_level != "must_confirm" and c.not_checked_reason is None
        if c.unresolved:
            assert not m.interaction_ready and not m.schedule_ready and m.review_level == "must_confirm"
        if "non_daily_frequency" in m.flags:
            assert not m.schedule_ready
        if m.schedule_ready:
            assert not c.unresolved and f.is_prn.value is not True and f.times_per_day.value is not None and f.timing_label.value not in (None, "as_needed", "other")
        if c.resolution == "not_in_list":
            assert not m.interaction_ready and m.resolved_generic is None and not m.schedule_ready
        if c.resolution == "confirmed" and not identity:
            assert not m.interaction_ready
        if c.resolution == "selected":
            assert m.resolved_generic_provenance == "user_selected" and c.provenance["resolved_generic"] == "user_selected"
        assert c.provenance.get("medicine")
    # the safety engine on the overlay: removed medicines are absent, not_in_list ones are never looked up, only ready ones carry a generic
    r = E.build_report(ov.doc, DATA)
    byref = {c.ref: c for c in ov.meds}
    for p in r.pair_results:
        for idx, g in ((p.a, p.generic_a), (p.b, p.generic_b)):
            c = byref[snapshot_refs[idx]]
            assert (g is not None) == c.med.interaction_ready
            if c.resolution == "not_in_list":
                assert g is None and p.status == I.UNCONFIRMED
        if p.status == I.FOUND:
            assert byref[snapshot_refs[p.a]].med.interaction_ready and byref[snapshot_refs[p.b]].med.interaction_ready
    if decision.action == "remove":
        assert decision.index not in [c.source_index for c in ov.meds] and ov.removed == [decision.index] and len(r.pair_results) == (len(ov.meds) * (len(ov.meds) - 1)) // 2


def test_property_every_action_flag_schedule_and_selection_combination():
    n = 0
    for i in range(5):
        for d in all_decisions(i):
            try:
                ov = CF.apply(ND, Confirmations(decisions=[d]))
            except CF.ConfirmationError:
                continue  # an invalid combination (for example an unknown flag) is rejected, never half-applied
            check_invariants(ov, d)
            n += 1
    assert n > 700


def test_property_all_pairs_of_decisions_on_different_medicines():
    sample = {i: list(all_decisions(i))[::7] for i in range(5)}
    n = 0
    for i, j in itertools.combinations(range(5), 2):
        for a in sample[i]:
            for b in sample[j][::3]:
                try:
                    ov = CF.apply(ND, Confirmations(decisions=[a, b]))
                except CF.ConfirmationError:
                    continue
                check_invariants(ov, a)
                n += 1
    assert n > 500
