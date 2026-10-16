"""Safety engine: pairwise interaction lookup, duplicate notices, overall state. No model, no advice (docs/SAFETY.md).

HARD RULES: a pair is looked up only when BOTH medicines are interaction_ready; any other pair is not_checked_unconfirmed. A pair that is not
found is "not checked", never safe. Results are ordered most severe first. The report holds data only; user text comes from fixed templates."""
from collections import Counter
from dataclasses import dataclass
from itertools import combinations

from app.safety import interactions as I
from app.schemas.normalised import NormalisedDocument
from app.schemas.safety import Counts, DuplicateNotice, PairResult, SafetyReport

LEVEL_ORDER = {"major": 0, "moderate": 1, "minor": 2, "unknown": 3}
STATUS_ORDER = {I.FOUND: 0, I.NO_RECORD: 1, I.DB_MISSING: 2, I.UNCONFIRMED: 3}


@dataclass
class MedInput:
    """What the engine needs from one medicine row."""
    resolved_generic: str | None = None
    interaction_ready: bool = False
    must_confirm: bool = False
    printed_names: tuple[str, ...] = ()
    unspecified_or_non_daily: bool = False


def med_inputs(nd: NormalisedDocument) -> list[MedInput]:
    out = []
    for m in nd.medications:
        f = m.frequency
        names = tuple(n.strip().lower() for n in (m.printed_brand, m.printed_generic) if n and n.strip())
        out.append(MedInput(m.resolved_generic, m.interaction_ready, m.review_level == "must_confirm", names,
                            "non_daily_frequency" in m.flags or f.timing_label.value == "unspecified"
                            or (f.times_per_day.value is None and f.is_prn.value is not True)))
    return out


def _duplicates(meds: list[MedInput]) -> list[DuplicateNotice]:
    """Exact matches only (resolved generic, or the same printed name); no class-level logic."""
    groups: dict[tuple[str, str], list[int]] = {}
    shown: dict[tuple[str, str], str] = {}  # display spelling of the group key
    for i, m in enumerate(meds):
        if m.resolved_generic:
            groups.setdefault(("resolved_generic", m.resolved_generic.lower()), []).append(i)
            shown.setdefault(("resolved_generic", m.resolved_generic.lower()), m.resolved_generic)
        for n in set(m.printed_names):
            groups.setdefault(("printed_name", n), []).append(i)
    out, seen = [], set()
    for (basis, name), idx in groups.items():
        key = frozenset(idx)
        if len(key) > 1 and key not in seen:
            seen.add(key)
            out.append(DuplicateNotice(indices=sorted(key), name=shown.get((basis, name), name), basis=basis))
    return sorted(out, key=lambda d: d.indices)


def analyse(meds: list[MedInput], data: I.Data) -> SafetyReport:
    pairs = []
    for i, j in combinations(range(len(meds)), 2):
        a, b = meds[i], meds[j]
        ga = a.resolved_generic if a.interaction_ready and a.resolved_generic else None
        gb = b.resolved_generic if b.interaction_ready and b.resolved_generic else None
        r = I.check(ga, gb, data)
        same = bool(ga and gb and ga.lower() == gb.lower())
        pairs.append(PairResult(a=i, b=j, generic_a=ga, generic_b=gb, status=r.status, level=r.level, source=r.source, same_medicine=same))
    pairs.sort(key=lambda p: (STATUS_ORDER[p.status], LEVEL_ORDER.get(p.level or "", 9), p.a, p.b))
    counts = Counts(
        medicines=len(meds), must_confirm=sum(m.must_confirm for m in meds), interaction_ready=sum(m.interaction_ready for m in meds), pairs=len(pairs),
        pairs_by_status=dict(Counter(p.status for p in pairs)), interactions_by_level=dict(Counter(p.level for p in pairs if p.status == I.FOUND)))
    if counts.must_confirm:
        state = "confirm_first"
    elif any(p.level in ("major", "moderate") for p in pairs if p.status == I.FOUND):
        state = "review_interactions"
    else:
        state = "ok_to_review"
    return SafetyReport(
        pair_results=pairs, duplicate_notices=_duplicates(meds), counts=counts, overall_state=state,
        schedule_reminder=[i for i, m in enumerate(meds) if m.unspecified_or_non_daily],
        supplement_reviewed=bool(data.supplement) and data.supplement_pending == 0, supplement_ignored=data.supplement_pending)


def build_report(nd: NormalisedDocument, data: I.Data | None = None) -> SafetyReport:
    return analyse(med_inputs(nd), data if data is not None else I.load_data())
