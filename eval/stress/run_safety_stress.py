"""Safety stress set evaluation (Phase 7a: ground-truth mode; Phase 7c: extraction mode).

  python -m eval.stress.run_safety_stress --mode gt                      # offline, no model: ground-truth lists through normalisation and the real safety engine
  python -m eval.stress.run_safety_stress --mode extraction --conds clean,photo   # 7c: local Ollama on data/stress/rendered images (needs the model)

(`eval/stress/run_stress.py` is the older Phase 3e verification-stack stress test; this file is the safety stress set of data/stress/.)
GT mode feeds each ground-truth medicine list through the REAL normalisation (names treated as printed) and the REAL safety engine, and checks invariants:
  I1 an interaction in the local store between two interaction_ready medicines is reported as interaction_found;
  I2 a pair with a garbled or otherwise unconfirmed medicine is not_checked_unconfirmed (never checked);
  I3 a weekly (non-daily) medicine is never schedule_ready;
  I4 garbled names are flagged (near_miss_name or unresolved_name), not interaction_ready, and the REAL confirmation overlay makes the designed pair checkable
     after a scripted picker choice (select_formulary_drug) and only then;
  I5 duplicates: the engine raises a duplicate notice; I6 pair categories: the designed pair is interaction_found; I7 controls: nothing found;
  I8 eye drop OD: not interaction_ready, not schedule_ready, flagged; I9 unusual strength: flagged.
Only aggregated counts are written (levels as counts per category, no pair lists). A failed invariant is listed in full and the exit code is 2."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from app.safety import interactions as I  # noqa: E402
from app.safety.engine import analyse, med_inputs  # noqa: E402
from app.schemas.confirmation import Confirmations  # noqa: E402
from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from app.services import confirmation as CF  # noqa: E402
from app.services import formulary as F  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402
from eval.matching import NAME_THRESHOLD, med_similarity, one_to_one  # noqa: E402
from eval.phase4_safety import gt_duplicate_groups, gt_inputs  # noqa: E402

STRESS = REPO / "data" / "stress"
NAME_FLAGS = {"near_miss_name", "unresolved_name"}
LEVELS = ("major", "moderate", "minor", "unknown")


def load_stress(root: Path = STRESS):
    m = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["documents"]
    return [(d, ExtractedDocument.model_validate_json((root / "ground_truth" / f"{d['id']}.json").read_text(encoding="utf-8"))) for d in m]


def real_pairs(rep):
    return [p for p in rep.pair_results if not p.same_medicine]


def formulary_id(generic: str) -> str | None:
    g = generic.lower()
    return next((e["id"] for e in F.all_entries() if e["generic"].lower() == g), None)


def gt_mode(data, root: Path = STRESS) -> dict:
    cats = defaultdict(lambda: dict(documents=0, pairs=0, statuses=Counter(), found_by_level=Counter(), duplicates_flagged=0, gt_duplicate_groups=0, flagged_medicines=Counter()))
    fails = []

    def fail(doc, inv, why):
        fails.append(dict(doc=doc["id"], category=doc["category"], invariant=inv, why=why))

    for d, gt in load_stress(root):
        c = cats[d["category"]]
        out = from_ground_truth(gt)
        nd = normalise_document(out)
        meds = med_inputs(nd)
        rep = analyse(meds, data)
        oracle = analyse(gt_inputs(gt.medications), data)
        c["documents"] += 1
        for p in real_pairs(rep):
            c["pairs"] += 1
            c["statuses"][p.status] += 1
            if p.status == I.FOUND:
                c["found_by_level"][p.level] += 1
        c["duplicates_flagged"] += len(rep.duplicate_notices)
        c["gt_duplicate_groups"] += len(gt_duplicate_groups(gt_inputs(gt.medications)))
        for m in nd.medications:
            c["flagged_medicines"].update(m.flags)
        # I1 / I2 on every pair
        for p in real_pairs(rep):
            a, b = nd.medications[p.a], nd.medications[p.b]
            if a.interaction_ready and b.interaction_ready:
                expect = I.check(a.resolved_generic, b.resolved_generic, data)
                if (expect.status == I.FOUND) != (p.status == I.FOUND):
                    fail(d, "I1", f"engine status {p.status} but store lookup says {expect.status}")
            elif p.status != I.UNCONFIRMED:
                fail(d, "I2", f"pair with an unconfirmed medicine has status {p.status}")
        # I3 a weekly (non-daily) medicine is never schedule_ready (ground truth: no times per day, not as-needed)
        for i, g in enumerate(gt.medications):
            fq = g.frequency
            if fq.times_per_day is None and not fq.is_prn and nd.medications[i].schedule_ready:
                fail(d, "I3", "a weekly or otherwise non-daily medicine is schedule_ready")
        cat = d["category"]
        found = [p for p in real_pairs(rep) if p.status == I.FOUND]
        if cat in ("major_pair", "moderate_pair", "supplement_pair"):
            designed = [p for p in real_pairs(oracle) if p.status == I.FOUND]
            if not designed:
                fail(d, "I6", "the designed pair has no record in the store")
            elif not found:
                fail(d, "I6", "the designed pair is not reported as interaction_found")
        if cat == "control" and found:
            fail(d, "I7", "a control prescription has an interaction_found pair")
        if cat == "duplicate" and not rep.duplicate_notices:
            fail(d, "I5", "no duplicate notice")
        if cat == "unusual_strength" and not any("unusual_strength" in m.flags for m in nd.medications):
            fail(d, "I9", "unusual strength not flagged")
        if cat == "eye_drop_od":
            eye = nd.medications[0]
            if eye.interaction_ready or eye.schedule_ready or not eye.flags:
                fail(d, "I8", f"eye drop: interaction_ready={eye.interaction_ready}, schedule_ready={eye.schedule_ready}, flags={eye.flags}")
        if cat == "garbled_name":
            bad = [m for m in nd.medications if set(m.flags) & NAME_FLAGS]
            if not bad:
                fail(d, "I4", "no garbled name was flagged")
            if any(m.interaction_ready for m in bad):
                fail(d, "I4", "a flagged garbled name is interaction_ready")
            before = len([p for p in real_pairs(rep) if p.status == I.FOUND])
            decisions = []
            for i, m in enumerate(nd.medications):
                reasons = CF.reason_ids(m)
                ack = [r for r in reasons if r not in CF.NAME_REASONS]
                if m in bad:
                    target = gt.medications[i].generic_name or ""
                    # the ground truth keeps the garbled text as written; the person picks the drug from the list (the designed original: the closest formulary generic)
                    pick = best_formulary(gt.medications[i])
                    fid = formulary_id(pick) if pick else None
                    if fid is None:
                        fail(d, "I4", "no formulary drug found for the scripted picker choice")
                        decisions.append(dict(index=i, action="confirm_as_extracted", acknowledged_flags=ack))
                        continue
                    decisions.append(dict(index=i, action="select_formulary_drug", formulary_id=fid, strength_choice=CF_AS_LABEL, acknowledged_flags=ack))
                else:
                    decisions.append(dict(index=i, action="confirm_as_extracted", acknowledged_flags=ack))
            ov = CF.apply(nd, Confirmations.model_validate(dict(decisions=decisions, added_medicines=[])))
            after = [p for p in real_pairs(analyse(med_inputs(ov.doc), data)) if p.status == I.FOUND]
            c["flagged_medicines"]["_overlay_pairs_found_before"] += before
            c["flagged_medicines"]["_overlay_pairs_found_after"] += len(after)
            if not after:
                fail(d, "I4", "after the scripted picker choice the designed pair is still not checkable")
            if len(after) < before:
                fail(d, "I4", "the overlay lost a pair that was found before")
    return dict(
        mode="ground_truth", documents=sum(v["documents"] for v in cats.values()), model_calls=0,
        categories={k: dict(documents=v["documents"], pairs_checked=v["pairs"], statuses=dict(v["statuses"]), interactions_found_by_level={lv: v["found_by_level"].get(lv, 0) for lv in LEVELS},
                            duplicates_flagged=v["duplicates_flagged"], ground_truth_duplicate_groups=v["gt_duplicate_groups"], flag_counts=dict(v["flagged_medicines"])) for k, v in cats.items()},
        invariants=dict(failed=len(fails), cases=fails))


CF_AS_LABEL = "as_on_my_label"


def best_formulary(g) -> str | None:
    """The formulary generic closest to a ground-truth medicine's printed names (what the person would pick: the drug on their paper)."""
    best, who = 0.0, None
    for e in F.all_entries():
        for n in (g.generic_name, g.brand_name):
            if not n:
                continue
            for cand in (e["generic"], *e["brand_names"]):
                from difflib import SequenceMatcher
                r = SequenceMatcher(None, n.lower(), cand.lower()).ratio()
                if r > best:
                    best, who = r, e["generic"]
    return who if best >= 0.8 else None


# --------------------------------------------------------------------------------------------------- extraction mode (7c)
def extraction_mode(data, root: Path, provider, conds=("clean", "photo")) -> dict:
    """Rendered images through the extraction pipeline (local provider), normalisation and the safety engine, compared with the ground-truth pairs."""
    from app.services.extraction import extract_bytes
    res = {}
    for cond in conds:
        s = Counter()
        skipped = []
        for d, gt in load_stress(root):
            png = (root / "rendered" / cond / f"{d['id']}.png").read_bytes()
            r = extract_bytes(png, "image/png", provider, origin="synthetic")
            if not r.ok:
                skipped.append(f"{d['id']}: {r.error}")
                continue
            s["documents"] += 1
            G = from_ground_truth(gt).medications
            nd = normalise_document(r.output)
            P = [m for m in nd.medications]
            pred = ExtractionOutput.model_validate(r.output.model_dump())
            pairs = {j: i for i, j in one_to_one(len(G), len(P), lambda i, j: med_similarity(G[i], pred.medications[j]), NAME_THRESHOLD)}
            s["gt_medicines"] += len(G)
            s["detected"] += len(pairs)
            s["hallucinated"] += len(P) - len(pairs)
            erep = analyse(med_inputs(nd), data)
            grep = analyse(gt_inputs(gt.medications), data)
            inv = {i: j for j, i in pairs.items()}
            eng = {(p.a, p.b): p for p in real_pairs(erep)}
            for gp in real_pairs(grep):
                if gp.status != I.FOUND:
                    continue
                s["gt_interactions"] += 1
                ra, rb = inv.get(gp.a), inv.get(gp.b)
                ep = eng.get(tuple(sorted((ra, rb)))) if ra is not None and rb is not None else None
                if ep is not None and ep.status == I.FOUND:
                    s["found"] += 1
                else:
                    s["strict_silent_misses"] += 1
                    covered = ep is not None and ep.status == I.UNCONFIRMED
                    s["silent_covered_by_flag"] += covered
                    s["silent_not_covered_by_flag"] += not covered
                    s["downgraded_unconfirmed"] += covered
            for p in real_pairs(erep):
                if p.status == I.FOUND:
                    a, b = pairs.get(p.a), pairs.get(p.b)
                    truth = a is not None and b is not None and any(g.status == I.FOUND and {g.a, g.b} == {a, b} for g in real_pairs(grep))
                    s["false_alarms"] += not truth
            s["duplicates_in_gt"] += len(gt_duplicate_groups(gt_inputs(gt.medications)))
            s["duplicate_notices"] += len(erep.duplicate_notices)
        res[cond] = dict(counts=dict(s), skipped=skipped)
    return dict(mode="extraction", conditions=res)


def markdown(m: dict) -> str:
    out = ["# Safety stress set: ground-truth mode\n", f"documents: {m['documents']}, model calls: {m['model_calls']}. Counts only; interaction levels appear as per-category counts.\n",
           "| category | docs | pairs checked | statuses | found by level | duplicates flagged / in ground truth |", "|---|---|---|---|---|---|"]
    for k, v in m["categories"].items():
        out.append(f"| {k} | {v['documents']} | {v['pairs_checked']} | {v['statuses']} | {v['interactions_found_by_level']} | {v['duplicates_flagged']} / {v['ground_truth_duplicate_groups']} |")
    out += ["", f"Invariant failures: {m['invariants']['failed']}"]
    out += [f"- {c}" for c in m["invariants"]["cases"]]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["gt", "extraction"], default="gt")
    ap.add_argument("--conds", default="clean,photo")
    ap.add_argument("--out", default="stress-safety-gt-v1")
    a = ap.parse_args(argv)
    data = I.load_data()
    if data.store is None:
        raise SystemExit("the local interaction store is missing (python scripts/build_interaction_store.py)")
    if a.mode == "gt":
        m = gt_mode(data)
        out = REPO / "eval" / "results" / a.out
        out.mkdir(parents=True, exist_ok=True)
        (out / "metrics.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8", newline="\n")
        (out / "metrics.md").write_text(markdown(m), encoding="utf-8", newline="\n")
        print(markdown(m))
        return 2 if m["invariants"]["failed"] else 0
    from app.llm.ollama import OllamaProvider
    m = extraction_mode(data, STRESS, OllamaProvider(), tuple(a.conds.split(",")))
    out = REPO / "eval" / "results" / "stress-safety-extraction-v1"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(m["conditions"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
