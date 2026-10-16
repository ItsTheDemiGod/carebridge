"""Confirmation overlay: the user's decisions applied to a COPY of the normalised document. The normalisation code and the safety engine are untouched;
the engine runs on the overlay. Invariants (docs/CONFIRMATION.md, enforced here and property-tested):

1. interaction_ready  <=>  a formulary identity (an EXACT printed-name match, or a formulary entry the user selected) AND no unresolved must_confirm reason.
   Name-related reasons are resolved only by select_formulary_drug, or by confirm_as_extracted on a medicine that already has an exact identity.
   Every other reason needs its id in acknowledged_flags. Unknown ids are rejected.
2. confirm_as_extracted without any identity, and not_in_list, never make a medicine checkable. User free text is never used for lookup.
3. schedule_ready needs: no unresolved reason, a daily frequency (never `non_daily_frequency`, never PRN / as_needed), a known times_per_day and timing_label.
4. Every changed field records its provenance; removed medicines are absent from the overlay (so from every pair result).
5. Added medicines come only from the formulary picker."""
from app.schemas.confirmation import AS_ON_LABEL, AddedMedicine, ConfirmedMedicine, Confirmations, MedicineDecision, Overlay, ScheduleEdit
from app.schemas.extraction import Form, Route
from app.schemas.extraction_output import Confidence
from app.schemas.normalised import NormalisedDocument, NormalisedFrequency, NormalisedMedication, Provenance, Sourced
from app.services import formulary as F
from app.services.normalisation import readiness

# Stricter than the brief's five: these also need the user to pick the drug (an acknowledgement cannot identify a medicine).
NAME_REASONS = {"unresolved_name", "near_miss_name", "role_corrected", "duplicate_name_fields", "name_not_in_quote", "missing_name", "multiple_drugs_in_quote", "possible_combination"}
ADDED_QUOTE = "Added by you from the medicine list"


class ConfirmationError(ValueError):
    """Invalid decision set. `reason` is a short slug (never user content)."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def reason_ids(m: NormalisedMedication) -> list[str]:
    return list(dict.fromkeys(r.split(":")[0].strip() for r in m.reasons))


def has_exact_identity(m: NormalisedMedication) -> bool:
    return bool(m.resolved_generic) and m.name_match_type == "exact"


def _sourced(old: Sourced, value) -> Sourced:
    return Sourced(value=value, provenance=Provenance.model, model_value=old.value, rule_value=old.rule_value)  # the true source is in ConfirmedMedicine.provenance


def _with_schedule(m: NormalisedMedication, e: ScheduleEdit, prov: dict[str, str]) -> NormalisedMedication:
    f = m.frequency
    prn = e.times_per_day == "as_needed"
    freq = NormalisedFrequency(times_per_day=_sourced(f.times_per_day, None if prn else e.times_per_day),
                               timing_label=_sourced(f.timing_label, "as_needed" if prn else e.timing_label.value),
                               is_prn=_sourced(f.is_prn, prn), original_abbreviation=f.original_abbreviation)
    prov.update({"times_per_day": "user_confirmed", "timing_label": "user_confirmed", "is_prn": "user_confirmed", "duration_days": "user_confirmed"})
    return m.model_copy(update={"frequency": freq, "duration_days": _sourced(m.duration_days, e.duration_days)})


def _finish(m: NormalisedMedication, unresolved: list[str], identity: bool) -> NormalisedMedication:
    level = "must_confirm" if unresolved else ("note" if m.review_level == "note" else "none")
    f = m.frequency
    _, sched = readiness(f.times_per_day.value, f.timing_label.value, f.is_prn.value, m.resolved_generic, m.name_match_type, m.flags, level)
    return m.model_copy(update={"review_level": level, "needs_verification": level == "must_confirm", "interaction_ready": identity and not unresolved, "schedule_ready": sched and not unresolved})


def _decide(i: int, m: NormalisedMedication, d: MedicineDecision) -> tuple[ConfirmedMedicine | None, int | None]:
    reasons, exact = reason_ids(m), has_exact_identity(m)
    unknown = [x for x in d.acknowledged_flags if x not in reasons]
    if unknown:
        raise ConfirmationError("unknown_flag")
    if d.action != "select_formulary_drug" and (d.formulary_id is not None or d.strength_choice is not None):
        raise ConfirmationError("unexpected_field")
    if d.action in ("not_in_list", "remove") and (d.schedule_edit is not None or d.acknowledged_flags):
        raise ConfirmationError("unexpected_field")
    if d.action == "remove":
        return None, i
    if d.action == "not_in_list":
        # nothing the user typed is looked up; the extracted identity is dropped so no lookup or duplicate check can use it
        mm = m.model_copy(update={"resolved_generic": None, "resolved_generic_provenance": None, "name_match_type": "none"})
        mm = _finish(mm, ["user_not_in_list"], False)
        return ConfirmedMedicine(ref=f"m{i}", source_index=i, resolution="not_in_list", med=mm, provenance={"medicine": "user_confirmed"}, unresolved=["user_not_in_list"],
                                 not_checked_reason="user_not_in_list"), None

    prov: dict[str, str] = {"medicine": "user_confirmed"}
    mm, identity = m, exact
    if d.action == "select_formulary_drug":
        entry = F.get(d.formulary_id or "")
        if entry is None:
            raise ConfirmationError("unknown_formulary_id")
        if d.strength_choice is None or (d.strength_choice != AS_ON_LABEL and d.strength_choice not in entry["available_strengths"]):
            raise ConfirmationError("invalid_strength_choice")
        upd = {"resolved_generic": entry["generic"], "resolved_generic_provenance": "user_selected", "name_match_type": "user_selected", "near_miss_name": None,
               "generic_name": entry["generic"], "printed_generic": entry["generic"], "brand_name": None, "printed_brand": None}
        if d.strength_choice != AS_ON_LABEL:
            upd["strength"] = d.strength_choice
            prov["strength"] = "user_selected"
        else:
            prov["strength"] = "user_confirmed"
        mm, identity = m.model_copy(update=upd), True
        prov.update({"resolved_generic": "user_selected", "generic_name": "user_selected", "brand_name": "user_selected"})
    if d.schedule_edit is not None:
        mm = _with_schedule(mm, d.schedule_edit, prov)
    acks = set(d.acknowledged_flags)
    unresolved = [r for r in reasons if (r not in acks if r not in NAME_REASONS else not identity)]
    # a name reason is resolved by the user's selection, or by confirming a medicine that already had an exact identity; an acknowledgement alone never identifies one
    if not identity:
        unresolved.append("not_identifiable")
    mm = _finish(mm, unresolved, identity)
    res = "selected" if d.action == "select_formulary_drug" else "confirmed"
    nc = None if mm.interaction_ready else "not_identifiable" if not identity else "needs_confirmation"
    return ConfirmedMedicine(ref=f"m{i}", source_index=i, resolution=res, med=mm, provenance=prov, unresolved=unresolved, not_checked_reason=nc), None


def _enum(cls, value, default):
    try:
        return cls(value)
    except ValueError:
        return default


def _added(k: int, a: AddedMedicine) -> ConfirmedMedicine:
    entry = F.get(a.formulary_id)
    if entry is None:
        raise ConfirmationError("unknown_formulary_id")
    if a.strength_choice != AS_ON_LABEL and a.strength_choice not in entry["available_strengths"]:
        raise ConfirmationError("invalid_strength_choice")
    prn = a.schedule.times_per_day == "as_needed"
    freq = NormalisedFrequency(times_per_day=Sourced(value=None if prn else a.schedule.times_per_day), timing_label=Sourced(value="as_needed" if prn else a.schedule.timing_label.value),
                               is_prn=Sourced(value=prn))
    m = NormalisedMedication(
        generic_name=entry["generic"], printed_generic=entry["generic"], resolved_generic=entry["generic"], resolved_generic_provenance="user_selected", name_match_type="user_selected",
        strength=None if a.strength_choice == AS_ON_LABEL else a.strength_choice, form=_enum(Form, entry["form"], Form.other), route=_enum(Route, entry["route"], Route.other), dose=a.dose,
        frequency=freq, duration_days=Sourced(value=a.schedule.duration_days), source_quote=ADDED_QUOTE, confidence=Confidence.high)
    m = _finish(m, [], True)
    prov = {k_: "user_added" for k_ in ("medicine", "resolved_generic", "generic_name", "strength", "dose", "times_per_day", "timing_label", "duration_days")}
    return ConfirmedMedicine(ref=f"a{k}", source_index=None, resolution="added", med=m, provenance=prov)


def apply(nd: NormalisedDocument, conf: Confirmations | None) -> Overlay:
    """Pure function: returns a new Overlay; `nd` is not modified."""
    conf = conf or Confirmations()
    by_index: dict[int, MedicineDecision] = {}
    for d in conf.decisions:
        if d.index >= len(nd.medications) or d.index in by_index:
            raise ConfirmationError("invalid_index")
        by_index[d.index] = d
    meds: list[ConfirmedMedicine] = []
    removed: list[int] = []
    for i, m in enumerate(nd.medications):
        if i not in by_index:
            exact = has_exact_identity(m)
            unresolved = reason_ids(m) if m.review_level == "must_confirm" else []
            nc = None if m.interaction_ready else "needs_confirmation" if exact else "not_identifiable"
            meds.append(ConfirmedMedicine(ref=f"m{i}", source_index=i, resolution="unchanged", med=m.model_copy(deep=True),
                                          provenance={"medicine": "model"}, unresolved=unresolved, not_checked_reason=nc))
            continue
        cm, rm = _decide(i, m, by_index[i])
        if rm is not None:
            removed.append(rm)
        else:
            meds.append(cm)
    meds += [_added(k, a) for k, a in enumerate(conf.added_medicines)]
    return Overlay(doc=nd.model_copy(update={"medications": [c.med for c in meds]}, deep=True), meds=meds, removed=removed)
