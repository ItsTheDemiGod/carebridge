"""Re-score cached raw extractions with and without the normalisation layer. No model calls.

  python -m eval.evaluate --split dev --run-id dev-ollama-v1 --rescore normalised
Reads eval/runs/<run-id>/raw/<condition>_<doc>.json, writes eval/results/<run-id>-normalised-v2/metrics.{json,md}.
The old folder <run-id>-normalised (Phase 2h) is left untouched.

Two normalisation modes per document: "app" (model output only, what the live app will see) and "eval" (also given the
document text, which adds the quote_not_in_document flag). Headline flag numbers are the app mode.
"""

import json
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.normalisation.names import index, key  # noqa: E402
from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402
from eval.matching import MED_FIELDS, NAME_THRESHOLD, field_value, med_similarity, one_to_one, score_document, summarize  # noqa: E402
from eval.name_sanity import _norm, formulary_names  # noqa: E402

SUFFIX = "-normalised-v2"
CONDS = ("text", "clean", "scan", "photo", "poor")
NEAR_RATIO = 0.8
HEAD = ["med_precision", "med_recall", "med_f1", "med_fully_correct_rate", "hallucinated_meds", "invented_value_rate", "followup_precision", "followup_recall",
        "redflag_precision", "redflag_recall", "quote_exact_rate", "quote_norm_exact_rate", "quote_strict_rate", "quote_fuzzy_rate"]
FIELDS = ["acc_strength", "acc_form", "acc_dose", "acc_times_per_day", "acc_timing_label", "acc_is_prn", "acc_duration_days", "acc_brand_name", "acc_generic_name",
          "exact_ci_brand_name", "exact_ci_generic_name"]


def to_prediction(nd) -> ExtractionOutput:
    """Normalised document back in prediction format (final values) so the existing scorer can be reused."""
    d = nd.model_dump(mode="json", exclude={"medications"})
    meds = []
    for m in nd.medications:
        f = m.frequency
        meds.append({
            "brand_name": m.brand_name, "generic_name": m.generic_name, "strength": m.strength, "form": m.form.value, "route": m.route.value, "dose": m.dose,
            "frequency": {"times_per_day": f.times_per_day.value, "timing_label": f.timing_label.value, "original_abbreviation": f.original_abbreviation, "is_prn": bool(f.is_prn.value)},
            "duration_days": m.duration_days.value, "duration_text": m.duration_text, "special_instructions": m.special_instructions,
            "source_quote": m.source_quote, "confidence": m.confidence.value,
        })
    return ExtractionOutput.model_validate({**d, "medications": meds})


def near_misses(pred, names):
    """Predicted names that are not an exact formulary name but are within small edit distance of one."""
    out = []
    for m in pred.medications:
        for n in (m.brand_name, m.generic_name):
            if n and _norm(n) not in names:
                best = max(((SequenceMatcher(None, _norm(n), f).ratio(), f) for f in names), default=(0, ""))
                if best[0] >= NEAR_RATIO:
                    out.append((n, best[1], round(best[0], 2)))
    return out


def gt_formulary_generic(g) -> str | None:
    """Formulary generic of a ground-truth medicine, looked up from its (as written) names."""
    for n in (g.generic_name, g.brand_name):
        e = index().get(key(_norm(n) if n else ""))
        if e:
            return e.generic.lower()
    return (g.generic_name or "").lower() or None


def records_for(nd, raw, gt, cond, doc):
    """One record per predicted medicine: review level, flags, readiness and correctness against ground truth."""
    G, P = gt.medications, to_prediction(nd).medications
    pairs = {j: i for i, j in one_to_one(len(G), len(P), lambda i, j: max(med_similarity(G[i], P[j]), med_similarity(G[i], raw.medications[j])), NAME_THRESHOLD)}
    out = []
    for j, m in enumerate(nd.medications):
        i = pairs.get(j)
        bad = [x for x in MED_FIELDS if i is None or field_value(G[i], x) != field_value(P[j], x)] if i is not None else ["unpaired"]
        r = dict(cond=cond, doc=doc, level=m.review_level, flags=set(m.flags), paired=i is not None, bad=bad,
                 name_err=i is None or any(x in bad for x in ("brand_name", "generic_name")), timing_err=i is not None and "timing_label" in bad,
                 any_err=bool(bad), interaction_ready=m.interaction_ready, schedule_ready=m.schedule_ready, resolved=m.resolved_generic, quote=m.source_quote[:70],
                 pred_names=[P[j].brand_name, P[j].generic_name], gt_names=[G[i].brand_name, G[i].generic_name] if i is not None else None,
                 pred_timing=P[j].frequency.timing_label.value, gt_timing=G[i].frequency.timing_label.value if i is not None else None,
                 gt_generic=gt_formulary_generic(G[i]) if i is not None else None, quote_check=m.quote_check)
        r["wrong_resolved"] = r["interaction_ready"] and (i is None or (r["resolved"] or "").lower() != r["gt_generic"])
        r["wrong_schedule"] = r["schedule_ready"] and (i is None or any(x in bad for x in ("times_per_day", "timing_label", "is_prn")))
        out.append(r)
    return out


def pct(a, b):
    return None if not b else round(a / b, 3)


def level_table(recs):
    """Per review level: medicines and remaining errors; must_confirm treated as the detector."""
    res = {}
    for kind, errkey in (("name", "name_err"), ("timing", "timing_err"), ("any", "any_err")):
        errs = [r for r in recs if r[errkey]]
        flagged = [r for r in recs if r["level"] == "must_confirm"]
        res[kind] = dict(
            medications=len(recs), remaining_errors=len(errs), must_confirm=len(flagged), share_must_confirm=pct(len(flagged), len(recs)),
            precision=pct(sum(r[errkey] for r in flagged), len(flagged)), recall=pct(sum(r["level"] == "must_confirm" for r in errs), len(errs)),
            errors_at_note=sum(r["level"] == "note" for r in errs), unflagged_errors=sum(r["level"] != "must_confirm" for r in errs))
    res["levels"] = {lv: dict(medications=sum(r["level"] == lv for r in recs), name_errors=sum(r["name_err"] for r in recs if r["level"] == lv),
                              timing_errors=sum(r["timing_err"] for r in recs if r["level"] == lv), any_errors=sum(r["any_err"] for r in recs if r["level"] == lv))
                     for lv in ("must_confirm", "note", "none")}
    return res


def flag_breakdown(recs):
    """Per flag type: medicines carrying it, how often the medicine really had an error, errors it caught."""
    out = {}
    for fl in sorted({f for r in recs for f in r["flags"]}):
        c = [r for r in recs if fl in r["flags"]]
        out[fl] = dict(medicines=len(c), with_any_error=sum(r["any_err"] for r in c), precision_any=pct(sum(r["any_err"] for r in c), len(c)),
                       with_name_error=sum(r["name_err"] for r in c), precision_name=pct(sum(r["name_err"] for r in c), len(c)),
                       with_timing_error=sum(r["timing_err"] for r in c), precision_timing=pct(sum(r["timing_err"] for r in c), len(c)))
    total_err = sum(r["any_err"] for r in recs)
    for fl, v in out.items():
        v["share_of_all_erroneous_medicines_caught"] = pct(v["with_any_error"], total_err)
    return out


def rescore(run_id: str, split_ids: set[str]):
    raw_dir = REPO / "eval" / "runs" / run_id / "raw"
    files = sorted(raw_dir.glob("*.json"))
    if not files:
        raise SystemExit(f"No cached raw outputs in {raw_dir}; cannot re-score without model calls.")
    names = set(formulary_names())
    groups = {v: defaultdict(Counter) for v in ("raw", "normalised")}
    near = {v: Counter() for v in ("raw", "normalised")}
    near_ex = {v: [] for v in ("raw", "normalised")}
    app, evl, skipped = [], [], []
    for f in files:
        cond, doc = f.stem.split("_", 1)
        if doc not in split_ids:
            continue
        try:
            raw = ExtractionOutput.model_validate_json(f.read_text(encoding="utf-8"))
        except ValueError:
            skipped.append(f.stem)
            continue
        gt = from_ground_truth(ExtractedDocument.model_validate_json((REPO / "data/ground_truth" / f"{doc}.json").read_text(encoding="utf-8")))
        text = (REPO / "data/synthetic" / f"{doc}.txt").read_text(encoding="utf-8")
        nd, nd_eval = normalise_document(raw), normalise_document(raw, text)
        norm = to_prediction(nd)
        for key_, c in (("raw", score_document(gt, raw, text)), ("normalised", score_document(gt, norm, text, pair_with=raw.medications))):
            groups[key_][cond] += c
            groups[key_]["all"] += c
        for key_, pred in (("raw", raw), ("normalised", norm)):
            nm = near_misses(pred, names)
            near[key_][cond] += len(nm)
            near_ex[key_] += [(cond, doc, *x) for x in nm]
        app += records_for(nd, raw, gt, cond, doc)
        evl += records_for(nd_eval, raw, gt, cond, doc)
    return groups, near, near_ex, app, evl, skipped


def write(run_id, groups, near, near_ex, app, evl, skipped):
    conds = [c for c in CONDS if c in groups["raw"]] + ["all"]
    S = {v: {c: summarize(groups[v][c]) for c in conds} for v in groups}
    sel = lambda recs, c: recs if c == "all" else [r for r in recs if r["cond"] == c]  # noqa: E731
    levels = {c: level_table(sel(app, c)) for c in conds}
    levels_eval = level_table(evl)
    breakdown = flag_breakdown(app)
    ready = {c: dict(medications=len(sel(app, c)), interaction_ready=sum(r["interaction_ready"] for r in sel(app, c)), schedule_ready=sum(r["schedule_ready"] for r in sel(app, c)),
                     wrong_resolved_generic=sum(r["wrong_resolved"] for r in sel(app, c)), wrong_schedule=sum(r["wrong_schedule"] for r in sel(app, c))) for c in conds}
    wrong_cases = [dict(cond=r["cond"], doc=r["doc"], resolved=r["resolved"], gt_generic=r["gt_generic"], quote=r["quote"]) for r in app if r["wrong_resolved"]]
    unflagged = {k: [dict(cond=r["cond"], doc=r["doc"], level=r["level"], pred=r["pred_names"] if k == "name" else r["pred_timing"], gt=r["gt_names"] if k == "name" else r["gt_timing"],
                          quote=r["quote"]) for r in app if r[f"{k}_err"] and r["level"] != "must_confirm"] for k in ("name", "timing")}
    qfail = [dict(cond=r["cond"], doc=r["doc"], quote=r["quote"]) for r in evl if r["quote_check"] == "failed"]
    old_path = REPO / "eval" / "results" / f"{run_id}-normalised" / "metrics.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))["flag_effectiveness"] if old_path.exists() else None

    result = dict(run_id=run_id + SUFFIX, source_run=run_id, skipped_unreadable_raw=skipped, conditions=conds, raw=S["raw"], normalised=S["normalised"],
                  near_miss_names={v: dict(by_condition=dict(near[v]), total=sum(near[v].values()), examples=near_ex[v][:10]) for v in near},
                  review_levels_app=levels, review_levels_with_document_text=levels_eval, flag_breakdown=breakdown, readiness=ready, wrong_resolved_generic_cases=wrong_cases,
                  unflagged_errors=unflagged, medication_quotes_failing_check=qfail, phase_2h_flag_effectiveness=old)
    out = REPO / "eval" / "results" / (run_id + SUFFIX)
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")

    L = [f"# {run_id}{SUFFIX}\n", f"Re-scored from cached raw outputs of `{run_id}` (no model calls). Medicines pair with ground truth if EITHER raw or normalised names match. Unreadable raw files: {skipped or 'none'}.\n"]
    for title, keys in (("Headline metrics", HEAD), ("Per-field accuracy", FIELDS)):
        L += [f"## {title} (raw / normalised)\n", "| metric | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
        L += [f"| {k} | " + " | ".join(f"{S['raw'][c][k]} / {S['normalised'][c][k]}" for c in conds) + " |" for k in keys]
        L.append("")
    L += ["Quote checks cover every item quote (medicines, follow-ups, red flags). exact = byte match; norm_exact = after Unicode/case/whitespace/punctuation normalisation; strict = norm_exact or a near-contiguous match (ratio >= 0.95 AND identical digits). "
          "quote_fuzzy is the OLD loose check (0.9), kept for comparison.\n", "Strict-quote failures: " + ", ".join(f"{c}: {S['raw'][c]['quote_fail_digits']} digit mismatch / {S['raw'][c]['quote_fail_similarity']} low similarity" for c in conds), ""]
    L += ["## Review levels (app mode: model output only)\n", "must_confirm is the detector. Errors are counted on the final (normalised) values; an unpaired predicted medicine counts as a name error.\n",
          "| condition | medicines | must_confirm | share | name errors | name P | name R | name unflagged | timing errors | timing P | timing R | timing unflagged |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in conds:
        v = levels[c]
        L.append(f"| {c} | {v['name']['medications']} | {v['name']['must_confirm']} | {v['name']['share_must_confirm']} | {v['name']['remaining_errors']} | {v['name']['precision']} | {v['name']['recall']} | {v['name']['unflagged_errors']} | "
                 f"{v['timing']['remaining_errors']} | {v['timing']['precision']} | {v['timing']['recall']} | {v['timing']['unflagged_errors']} |")
    a = levels["all"]["levels"]
    L += ["", "Pooled by level: " + "; ".join(f"{lv}: {x['medications']} medicines, {x['name_errors']} name / {x['timing_errors']} timing / {x['any_errors']} any errors" for lv, x in a.items()),
          f"With document text (adds quote_not_in_document): must_confirm {levels_eval['name']['must_confirm']} of {levels_eval['name']['medications']}, name unflagged {levels_eval['name']['unflagged_errors']}, timing unflagged {levels_eval['timing']['unflagged_errors']}."]
    if old:
        L.append(f"Phase 2h (all flags except audit-only): 133 of 420 flagged; name precision {old['name']['needs_verification']['flag_precision']}, name recall {old['name']['needs_verification']['flag_recall']}, "
                 f"name unflagged {old['name']['needs_verification']['unflagged_errors']}; timing precision {old['timing']['needs_verification']['flag_precision']}, recall {old['timing']['needs_verification']['flag_recall']}, timing unflagged {old['timing']['needs_verification']['unflagged_errors']}.")
    L += ["", "## Flag breakdown (app mode, pooled)\n", "precision = share of medicines carrying the flag that have any remaining error (name / timing columns are field specific)\n",
          "| flag | medicines | with any error | precision | name errors | name precision | timing errors | timing precision | share of erroneous medicines caught |", "|---|---|---|---|---|---|---|---|---|"]
    for fl, v in sorted(breakdown.items(), key=lambda kv: -kv[1]["medicines"]):
        L.append(f"| {fl} | {v['medicines']} | {v['with_any_error']} | {v['precision_any']} | {v['with_name_error']} | {v['precision_name']} | {v['with_timing_error']} | {v['precision_timing']} | {v['share_of_all_erroneous_medicines_caught']} |")
    L += ["", "## Readiness (app mode)\n", "| condition | medicines | interaction_ready | schedule_ready | WRONG resolved_generic among interaction_ready | wrong schedule among schedule_ready |", "|---|---|---|---|---|---|"]
    L += [f"| {c} | {v['medications']} | {v['interaction_ready']} | {v['schedule_ready']} | {v['wrong_resolved_generic']} | {v['wrong_schedule']} |" for c, v in ready.items()]
    L += ["", "Wrong resolved_generic cases: " + (str(wrong_cases) if wrong_cases else "none"), ""]
    for k in ("name", "timing"):
        L.append(f"### Remaining {k} errors not at must_confirm ({len(unflagged[k])}); up to 10\n")
        L += [f"- {e}" for e in unflagged[k][:10]] or ["- none"]
        L.append("")
    L.append(f"### Medicine quotes failing the document check ({len(qfail)}); up to 10\n")
    L += [f"- {e}" for e in qfail[:10]] or ["- none"]
    L += ["", "Near-miss names (not an exact formulary name, within edit distance): raw " + str(result["near_miss_names"]["raw"]["total"]) + ", normalised " + str(result["near_miss_names"]["normalised"]["total"]), ""]
    (out / "metrics.md").write_text("\n".join(L), encoding="utf-8", newline="\n")
    return result, out


def run(args):
    manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]
    ids = {d["id"] for d in manifest if args.split == "all" or d["split"] == args.split}
    if not args.run_id:
        raise SystemExit("--rescore needs --run-id of an existing run")
    return write(args.run_id, *rescore(args.run_id, ids))
