"""Phase 4 safety evaluation on the cached DEV outputs (no model calls, test split never touched).

  python -m eval.phase4_safety [--run-id dev-ollama-v1] [--out phase4-dev]

Runs the safety engine on the normalised cached extractions (5 conditions x 20 dev docs) and, as reference, on the ground-truth medicine lists
(every ground-truth medicine treated as interaction_ready with its formulary generic). Per-pair comparison uses the same one-to-one medicine matching as
eval/rescore.py. SAFETY METRICS: silent misses (ground truth interaction_found shown as anything except interaction_found or not_checked_unconfirmed, or
with no entry at all) must be 0; downgrades; false alarms; duplicates."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.safety import interactions as I  # noqa: E402
from app.safety.engine import MedInput, analyse, med_inputs  # noqa: E402
from app.safety.names import canonical  # noqa: E402
from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402
from eval.matching import NAME_THRESHOLD, med_similarity, one_to_one  # noqa: E402
from eval.rescore import CONDS, gt_formulary_generic, to_prediction  # noqa: E402

LEVELS = ("major", "moderate", "minor", "unknown")


def gt_inputs(G) -> list[MedInput]:
    out = []
    for g in G:
        c = canonical(gt_formulary_generic(g))
        out.append(MedInput(resolved_generic=c, interaction_ready=c is not None))
    return out


def gt_duplicate_groups(meds: list[MedInput]) -> set[frozenset]:
    by = defaultdict(set)
    for i, m in enumerate(meds):
        if m.resolved_generic:
            by[m.resolved_generic.lower()].add(i)
    return {frozenset(v) for v in by.values() if len(v) > 1}


def evaluate(run_id: str, data: I.Data):
    manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]
    dev = {d["id"] for d in manifest if d["split"] == "dev"}  # the test split is never read
    raw_dir = REPO / "eval" / "runs" / run_id / "raw"
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No cached raw outputs in {raw_dir}; this evaluation never calls a model.")
    stat = {c: Counter() for c in CONDS}
    state = {c: Counter() for c in CONDS}
    docs_n = {c: 0 for c in CONDS}
    gt_stat, gt_levels, gt_docs = Counter(), Counter(), 0
    silent, uncovered, down, down_causes, false_alarms, level_mismatch = [], [], [], Counter(), [], []
    missed = {c: dict(medicines=0, interactions=0) for c in CONDS}
    dup = dict(flagged=0, true=0, false=[], gt=0, missed=[])
    gt_done = set()
    skipped = []
    for f in files:
        cond, doc = f.stem.split("_", 1)
        if doc not in dev:
            continue
        try:
            raw = ExtractionOutput.model_validate_json(f.read_text(encoding="utf-8"))
        except ValueError:
            skipped.append(f.stem)
            continue
        gt = from_ground_truth(ExtractedDocument.model_validate_json((REPO / "data/ground_truth" / f"{doc}.json").read_text(encoding="utf-8")))
        nd = normalise_document(raw)
        G, P = gt.medications, to_prediction(nd).medications
        gmeds = gt_inputs(G)
        grep = analyse(gmeds, data)
        if doc not in gt_done:  # ground truth counted once per document
            gt_done.add(doc)
            gt_docs += 1
            for p in grep.pair_results:
                if not p.same_medicine:
                    gt_stat[p.status] += 1
                if p.status == I.FOUND:
                    gt_levels[p.level] += 1
            dup["gt"] += len(gt_duplicate_groups(gmeds))
        emeds = med_inputs(nd)
        erep = analyse(emeds, data)
        docs_n[cond] += 1
        state[cond][erep.overall_state] += 1
        for p in erep.pair_results:
            if not p.same_medicine:
                stat[cond][p.status] += 1
        pairs = {j: i for i, j in one_to_one(len(G), len(P), lambda i, j: max(med_similarity(G[i], P[j]), med_similarity(G[i], raw.medications[j])), NAME_THRESHOLD)}
        inv = {i: j for j, i in pairs.items()}
        eidx = {}
        for p in erep.pair_results:
            if p.a in pairs and p.b in pairs:
                eidx[tuple(sorted((pairs[p.a], pairs[p.b])))] = p
        gt_pairs = {(p.a, p.b): p for p in grep.pair_results}
        # (b) one-to-one assignment of unmatched ground-truth medicines to unmatched extracted rows that are NOT interaction_ready (best name similarity first)
        free = [j for j in range(len(P)) if j not in pairs and not nd.medications[j].interaction_ready]
        cand = sorted(((med_similarity(G[i], P[j]), i, j) for i in range(len(G)) if i not in inv for j in free), reverse=True)
        ext_row, used = dict(inv), set()
        for _, i, j in cand:
            if i not in ext_row and j not in used:
                ext_row[i] = j
                used.add(j)
        eng = {(p.a, p.b): p for p in erep.pair_results}
        gone = {i for i in range(len(G)) if i not in ext_row}  # extraction never saw this medicine (or only matched rows that are ready)
        missed[cond]["medicines"] += len(gone)
        missed[cond]["interactions"] += sum(1 for (i1, i2), gp in gt_pairs.items() if gp.status == I.FOUND and ({i1, i2} & gone))

        def covered_by_flag(i1, i2):
            r1, r2 = ext_row.get(i1), ext_row.get(i2)
            if r1 is None or r2 is None:
                return False
            return eng[tuple(sorted((r1, r2)))].status in (I.FOUND, I.UNCONFIRMED)
        for (i1, i2), gp in gt_pairs.items():
            if gp.status != I.FOUND:
                continue
            ep = eidx.get((i1, i2))
            tag = dict(cond=cond, doc=doc, gt=[gp.generic_a, gp.generic_b], gt_level=gp.level)
            if ep is None:
                silent.append(tag | dict(why="no entry (a medicine was not extracted or not matched)", covered_by_flag=covered_by_flag(i1, i2)))
            elif ep.status == I.FOUND:
                if ep.level != gp.level:
                    level_mismatch.append(tag | dict(ext_level=ep.level))
            elif ep.status == I.UNCONFIRMED:
                causes = []
                for j in (inv[i1], inv[i2]):
                    m = nd.medications[j]
                    if not m.interaction_ready:
                        causes += [f"{x}" for x in (m.flags or ["no_resolved_generic"])]
                down.append(tag | dict(causes=sorted(set(causes))))
                down_causes.update(set(causes))
            else:
                silent.append(tag | dict(why=ep.status, covered_by_flag=False))
        for (j1, j2), ep in ((((p.a, p.b), p) for p in erep.pair_results)):
            if ep.status != I.FOUND:
                continue
            if j1 in pairs and j2 in pairs:
                g = gt_pairs.get(tuple(sorted((pairs[j1], pairs[j2]))))
                if g is not None and g.status == I.FOUND:
                    continue
            false_alarms.append(dict(cond=cond, doc=doc, ext=[ep.generic_a, ep.generic_b], level=ep.level))
        gdups = gt_duplicate_groups(gmeds)
        covered = set()
        for n in erep.duplicate_notices:
            dup["flagged"] += 1
            mapped = frozenset(pairs[i] for i in n.indices if i in pairs)
            hit = next((gd for gd in gdups if len(mapped) == len(n.indices) and mapped <= gd), None)
            if hit:
                dup["true"] += 1
                covered.add(hit)
            else:
                dup["false"].append(dict(cond=cond, doc=doc, name=n.name, basis=n.basis))
        dup["missed"] += [dict(cond=cond, doc=doc, indices=sorted(gd)) for gd in gdups - covered]
    return dict(stat=stat, state=state, docs_n=docs_n, gt_stat=gt_stat, gt_levels=gt_levels, gt_docs=gt_docs, silent=silent, missed=missed, down=down, down_causes=down_causes,
                false_alarms=false_alarms, level_mismatch=level_mismatch, dup=dup, skipped=skipped)


def supplement_impact(data: I.Data):
    """How many formulary pairs (of 2,145) and how many extraction-based dev pairs would change if every supplement entry became reviewed."""
    from itertools import combinations

    from app.safety.names import formulary_generics
    path = REPO / "data" / "reference" / "interactions_supplement.json"
    entries = json.loads(path.read_text(encoding="utf-8"))["entries"] if path.exists() else []
    pretend = I.Data(data.store, {I.pair_key(e["drug_a"], e["drug_b"]): e for e in entries}, 0)
    return sum(I.check(a, b, data).status != I.check(a, b, pretend).status for a, b in combinations(formulary_generics(), 2)), len(entries)


def pct(a, b):
    return round(a / b, 3) if b else None


def summarise(r, run_id, data):
    pairs_total = {c: sum(r["stat"][c].values()) for c in CONDS}
    not_checked = {c: pct(sum(v for k, v in r["stat"][c].items() if k != I.FOUND), pairs_total[c]) for c in CONDS}
    sup_pairs, sup_n = supplement_impact(data)
    gt_total = sum(r["gt_stat"].values())
    return dict(
        run_id=run_id, split="dev", model_calls=0, documents=r["gt_docs"], skipped=r["skipped"], docs_by_condition=r["docs_n"],
        store_available=data.store is not None, supplement_entries_ignored=data.supplement_pending, supplement_reviewed_entries=len(data.supplement),
        pairs_by_condition={c: pairs_total[c] for c in CONDS}, pair_statuses_by_condition={c: dict(r["stat"][c]) for c in CONDS},
        share_not_checked_by_condition=not_checked,
        ground_truth=dict(pairs=gt_total, statuses=dict(r["gt_stat"]), interactions_by_level={k: r["gt_levels"].get(k, 0) for k in LEVELS}),
        safety=dict(silent_misses_strict=len(r["silent"]), silent_misses_not_covered_by_a_flag=sum(not c["covered_by_flag"] for c in r["silent"]),
                    silent_miss_cases=r["silent"], missed_entirely_by_condition=r["missed"], downgrades=len(r["down"]), downgrade_causes=dict(r["down_causes"]),
                    downgrade_cases=r["down"], false_alarms=len(r["false_alarms"]), false_alarm_cases=r["false_alarms"][:50], level_mismatches=len(r["level_mismatch"]),
                    level_mismatch_cases=r["level_mismatch"]),
        duplicates=dict(flagged=r["dup"]["flagged"], true_flagged=r["dup"]["true"], false_flagged=len(r["dup"]["false"]), false_cases=r["dup"]["false"][:20],
                        ground_truth_duplicates=r["dup"]["gt"], missed_cases=r["dup"]["missed"][:20]),
        overall_state={c: dict(r["state"][c]) for c in CONDS},
        confirm_first_share={c: pct(r["state"][c]["confirm_first"], r["docs_n"][c]) for c in CONDS},
        confirm_first_share_all=pct(sum(r["state"][c]["confirm_first"] for c in CONDS), sum(r["docs_n"].values())),
        supplement_would_change_formulary_pairs=sup_pairs, supplement_entries=sup_n)


def markdown(m):
    L = [f"# Phase 4 safety evaluation ({m['run_id']}, dev split)", "",
         f"No model calls. {m['documents']} dev documents x 5 conditions (cached extractions, normalisation v2, app mode). Store available: {m['store_available']}. "
         f"Supplement: {m['supplement_reviewed_entries']} reviewed entries used, {m['supplement_entries_ignored']} ignored (not reviewed).", "",
         "## Pair statuses by condition (extraction-based; duplicate-medicine pairs excluded)", "",
         "| condition | docs | pairs | interaction_found | not_checked_no_record | not_checked_unconfirmed | not_checked_database_missing | share not checked |", "|---|---|---|---|---|---|---|---|"]
    for c in CONDS:
        s = m["pair_statuses_by_condition"][c]
        L.append(f"| {c} | {m['docs_by_condition'][c]} | {m['pairs_by_condition'][c]} | {s.get(I.FOUND, 0)} | {s.get(I.NO_RECORD, 0)} | {s.get(I.UNCONFIRMED, 0)} | "
                 f"{s.get(I.DB_MISSING, 0)} | {m['share_not_checked_by_condition'][c]} |")
    g = m["ground_truth"]
    L += ["", "## Ground truth (reference; every medicine treated as interaction_ready)", "",
          f"{g['pairs']} medicine pairs in {m['documents']} documents; statuses {g['statuses']}; interactions found by level {g['interactions_by_level']}.", "",
          "## Safety metrics (extraction-based vs ground truth, per pair)", "", "| metric | count |", "|---|---|"]
    s = m["safety"]
    L += [f"| silent misses, STRICT (per-pair name matching only) | {s['silent_misses_strict']} |",
          f"| silent misses NOT covered by a flag (must be 0) | {s['silent_misses_not_covered_by_a_flag']} |", f"| downgrades to not_checked_unconfirmed (acceptable) | {s['downgrades']} |",
          f"| false alarms | {s['false_alarms']} |", f"| level mismatches among found | {s['level_mismatches']} |", ""]
    if s["downgrade_causes"]:
        L.append(f"Downgrade causes (flags on the unconfirmed medicine): {s['downgrade_causes']}")
    L += ["", "The strict count comes from the evaluator failing to match a garbled extracted row (for example Netfornin/Glibenclamide for Metformin) to its ground-truth medicine; "
          "in the real engine that row is not interaction_ready and its pairs are not_checked_unconfirmed. A ground-truth interaction counts as covered only if both of its medicines "
          "have an extracted row (matched, or assigned one-to-one from the unmatched not-ready rows) and the engine pair status is interaction_found or not_checked_unconfirmed. "
          "The document-level banner is NOT used.", "", "Ground-truth medicines the extraction never saw (no extracted row), and the ground-truth interactions they affect:", "",
          "| condition | medicines missed entirely | interactions affected |", "|---|---|---|"]
    L += [f"| {c} | {s['missed_entirely_by_condition'][c]['medicines']} | {s['missed_entirely_by_condition'][c]['interactions']} |" for c in CONDS]
    L += ["A medicine the extraction never saw cannot be warned about; the app depends on the user comparing the list with the document.", ""]
    if s["silent_miss_cases"]:
        L += ["", "STRICT SILENT MISS CASES (covered_by_flag says whether the per-pair rule covers them):", "```", json.dumps(s["silent_miss_cases"], indent=1), "```"]
    d = m["duplicates"]
    L += ["", "## Duplicates", "", f"Ground-truth duplicate groups: {d['ground_truth_duplicates']}. Flagged: {d['flagged']} (true {d['true_flagged']}, false {d['false_flagged']}). Missed: {len(d['missed_cases'])}.", "",
          "## overall_state by condition", "", "| condition | confirm_first | review_interactions | ok_to_review | confirm_first share |", "|---|---|---|---|---|"]
    for c in CONDS:
        o = m["overall_state"][c]
        L.append(f"| {c} | {o.get('confirm_first', 0)} | {o.get('review_interactions', 0)} | {o.get('ok_to_review', 0)} | {m['confirm_first_share'][c]} |")
    L += ["", f"Share of documents showing the confirm_first banner (all conditions): {m['confirm_first_share_all']}.", "",
          f"Supplement: if all {m['supplement_entries']} drafted entries became reviewed, {m['supplement_would_change_formulary_pairs']} of the 2,145 formulary pairs would change from not_checked_no_record to interaction_found."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="dev-ollama-v1")
    ap.add_argument("--out", default="phase4-dev")
    a = ap.parse_args()
    data = I.load_data()
    m = summarise(evaluate(a.run_id, data), a.run_id, data)
    out = REPO / "eval" / "results" / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
    (out / "metrics.md").write_text(markdown(m), encoding="utf-8")
    print(f"strict silent misses {m['safety']['silent_misses_strict']}, not covered by a flag {m['safety']['silent_misses_not_covered_by_a_flag']}, downgrades {m['safety']['downgrades']}, false alarms {m['safety']['false_alarms']} -> {out}")
    if m["safety"]["silent_misses_not_covered_by_a_flag"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
