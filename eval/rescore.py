"""Re-score cached raw extractions with and without the normalisation layer. No model calls.

  python -m eval.evaluate --split dev --run-id dev-ollama-v1 --rescore normalised
Reads eval/runs/<run-id>/raw/<condition>_<doc>.json, writes eval/results/<run-id>-normalised/metrics.{json,md}.
"""

import json
import os
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402
from eval.matching import NAME_THRESHOLD, field_value, med_similarity, norm_name, one_to_one, score_document, summarize  # noqa: E402
from eval.name_sanity import _norm, formulary_names  # noqa: E402

NAME_FLAGS = {"unresolved_name", "near_miss_name", "name_not_in_quote", "multiple_drugs_in_quote", "possible_combination", "missing_name"}
TIMING_FLAGS = {"conflict_timing_label", "conflicting_meal_relation"}
NEAR_RATIO = 0.8
HEAD = ["med_precision", "med_recall", "med_f1", "med_fully_correct_rate", "hallucinated_meds", "invented_value_rate", "followup_precision", "followup_recall",
        "redflag_precision", "redflag_recall", "quote_exact_rate", "quote_fuzzy_rate"]
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
            if not n:
                continue
            k = _norm(n)
            if k in names:
                continue
            best = max(((SequenceMatcher(None, k, f).ratio(), f) for f in names), default=(0, ""))
            if best[0] >= NEAR_RATIO:
                out.append((n, best[1], round(best[0], 2)))
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
    meds = Counter()  # flag-effectiveness counters
    unflagged = {"name": [], "timing": []}
    flag_counts, skipped = Counter(), []
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
        nd = normalise_document(raw)
        norm = to_prediction(nd)
        for key, c in (("raw", score_document(gt, raw, text)), ("normalised", score_document(gt, norm, text, pair_with=raw.medications))):
            groups[key][cond] += c
            groups[key]["all"] += c
        for key, pred in (("raw", raw), ("normalised", norm)):
            nm = near_misses(pred, names)
            near[key][cond] += len(nm)
            near_ex[key] += [(cond, doc, *x) for x in nm]

        # flag effectiveness on the normalised medications
        G, P = gt.medications, norm.medications
        pairs = {j: i for i, j in one_to_one(len(G), len(P), lambda i, j: max(med_similarity(G[i], P[j]), med_similarity(G[i], raw.medications[j])), NAME_THRESHOLD)}
        for j, m in enumerate(nd.medications):
            flagged, fl = m.needs_verification, set(m.flags)
            flag_counts.update(fl)
            i = pairs.get(j)
            name_err = i is None or any(field_value(G[i], x) != field_value(P[j], x) for x in ("brand_name", "generic_name"))
            time_err = i is not None and field_value(G[i], "timing_label") != field_value(P[j], "timing_label")
            for kind, err, spec in (("name", name_err, bool(fl & NAME_FLAGS)), ("timing", time_err, bool(fl & TIMING_FLAGS))):
                meds[f"{kind}_meds"] += 1
                meds[f"{kind}_errors"] += err
                meds[f"{kind}_flagged_any"] += flagged
                meds[f"{kind}_flagged_any_and_err"] += flagged and err
                meds[f"{kind}_flagged_spec"] += spec
                meds[f"{kind}_flagged_spec_and_err"] += spec and err
                meds[f"{kind}_err_and_flagged_any"] += err and flagged
                meds[f"{kind}_err_and_flagged_spec"] += err and spec
                if err and not flagged:
                    unflagged[kind].append(dict(condition=cond, doc=doc, predicted=[P[j].brand_name, P[j].generic_name] if kind == "name" else P[j].frequency.timing_label.value,
                                                ground_truth=[G[i].brand_name, G[i].generic_name] if kind == "name" and i is not None else (G[i].frequency.timing_label.value if i is not None else None),
                                                quote=m.source_quote[:70]))
            meds["meds"] += 1
            meds["flagged_any"] += flagged
            if "conflict_timing_label" in fl:
                meds["timing_rule_overrides"] += 1
    return groups, near, near_ex, meds, unflagged, flag_counts, skipped


def pct(a, b):
    return None if not b else round(a / b, 3)


def flag_report(meds, unflagged):
    out = {}
    for kind in ("name", "timing"):
        e = meds[f"{kind}_errors"]
        out[kind] = dict(
            medications=meds[f"{kind}_meds"], remaining_errors=e,
            needs_verification=dict(flag_recall=pct(meds[f"{kind}_err_and_flagged_any"], e), flag_precision=pct(meds[f"{kind}_flagged_any_and_err"], meds[f"{kind}_flagged_any"]),
                                    flagged=meds[f"{kind}_flagged_any"], unflagged_errors=e - meds[f"{kind}_err_and_flagged_any"]),
            field_specific_flags=dict(flag_recall=pct(meds[f"{kind}_err_and_flagged_spec"], e), flag_precision=pct(meds[f"{kind}_flagged_spec_and_err"], meds[f"{kind}_flagged_spec"]),
                                      flagged=meds[f"{kind}_flagged_spec"], unflagged_errors=e - meds[f"{kind}_err_and_flagged_spec"]),
            unflagged_examples=unflagged[kind][:10])
    return out


def write(run_id, groups, near, near_ex, meds, unflagged, flag_counts, skipped):
    conds = [c for c in ("text", "clean", "scan", "photo", "poor") if c in groups["raw"]] + ["all"]
    S = {v: {c: summarize(groups[v][c]) for c in conds} for v in groups}
    fr = flag_report(meds, unflagged)
    result = dict(run_id=run_id + "-normalised", source_run=run_id, skipped_unreadable_raw=skipped, conditions=conds, raw=S["raw"], normalised=S["normalised"],
                  near_miss_names={v: dict(by_condition=dict(near[v]), total=sum(near[v].values()), examples=near_ex[v][:10]) for v in near},
                  flag_effectiveness=fr, flag_counts=dict(flag_counts.most_common()), medications_total=meds["meds"], medications_needing_verification=meds["flagged_any"],
                  timing_rule_overrides=meds["timing_rule_overrides"])
    out = REPO / "eval" / "results" / f"{run_id}-normalised"
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")

    L = [f"# {run_id}-normalised\n", f"Re-scored from cached raw outputs of `{run_id}` (no model calls). Medicines are paired with ground truth if EITHER their raw or their normalised names match. "
         f"Documents unreadable: {skipped or 'none'}.\n"]
    for title, keys in (("Headline metrics", HEAD), ("Per-field accuracy", FIELDS)):
        L += [f"## {title} (raw / normalised)\n", "| metric | " + " | ".join(conds) + " |", "|---|" + "---|" * len(conds)]
        for k in keys:
            L.append(f"| {k} | " + " | ".join(f"{S['raw'][c][k]} / {S['normalised'][c][k]}" for c in conds) + " |")
        L.append("")
    L += ["## Near-miss names (not an exact formulary name, within edit distance)\n", f"raw total {result['near_miss_names']['raw']['total']}, normalised total {result['near_miss_names']['normalised']['total']}", ""]
    L += ["Examples (normalised): " + "; ".join(f"{c}/{d}: {n} ~ {f} ({r})" for c, d, n, f, r in near_ex["normalised"][:10]) if near_ex["normalised"] else "Examples (normalised): none", ""]
    L += ["## Invented values by field (raw / normalised): role confusion | in document, wrong field | made up (appears nowhere in the document); out of ground-truth-null cells\n",
          "| field | of null | raw invented | raw role | raw in_doc | raw made_up | norm invented | norm role | norm in_doc | norm made_up |", "|---|---|---|---|---|---|---|---|---|---|"]
    for f in ("strength", "dose", "times_per_day", "duration_days", "brand_name", "generic_name"):
        a, b = S["raw"]["all"][f"invented_{f}"], S["normalised"]["all"][f"invented_{f}"]
        L.append(f"| {f} | {a['of_null']} | {a['invented']} | {a['role_confusion']} | {a['in_document']} | {a['made_up']} | {b['invented']} | {b['role_confusion']} | {b['in_document']} | {b['made_up']} |")
    L += ["", "## Flag effectiveness (normalised, all conditions)\n", "Detector A = needs_verification (any flag or low confidence); detector B = only the flags specific to that field.\n",
          "| field | meds | remaining errors | A recall | A precision | A unflagged | B recall | B precision | B unflagged |", "|---|---|---|---|---|---|---|---|---|"]
    for k, v in fr.items():
        a, b = v["needs_verification"], v["field_specific_flags"]
        L.append(f"| {k} | {v['medications']} | {v['remaining_errors']} | {a['flag_recall']} | {a['flag_precision']} | {a['unflagged_errors']} | {b['flag_recall']} | {b['flag_precision']} | {b['unflagged_errors']} |")
    L += ["", f"Medications needing verification: {meds['flagged_any']} of {meds['meds']}. Rule overrode a model timing label {meds['timing_rule_overrides']} times.", "", "Flag counts: " + ", ".join(f"{k}={v}" for k, v in flag_counts.most_common()), ""]
    for k in ("name", "timing"):
        L.append(f"### Unflagged {k} errors ({fr[k]['needs_verification']['unflagged_errors']}); up to 10 examples\n")
        L += [f"- {e}" for e in unflagged[k][:10]] or ["- none"]
        L.append("")
    (out / "metrics.md").write_text("\n".join(L), encoding="utf-8", newline="\n")
    return result, out


def run(args):
    manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]
    ids = {d["id"] for d in manifest if args.split == "all" or d["split"] == args.split}
    if not args.run_id:
        raise SystemExit("--rescore needs --run-id of an existing run")
    return write(args.run_id, *rescore(args.run_id, ids))
