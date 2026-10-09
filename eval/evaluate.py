"""Evaluate extraction against ground truth.

  backend\\.venv\\Scripts\\python -m eval.evaluate --split dev --conditions text,clean,scan,photo,poor [--limit N] [--run-id NAME]
  add --oracle to score ground truth converted to prediction format (no API calls; must score perfectly).
The test split needs --final-test-run (logged to eval/test_runs.log).
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from app.prompts import PROMPT_VERSION  # noqa: E402
from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import from_ground_truth  # noqa: E402
from app.services.guards import check_split  # noqa: E402
from eval.name_sanity import THRESHOLD, check_names, formulary_names  # noqa: E402
from eval.matching import MED_FIELDS, score_document, summarize  # noqa: E402

CONDITIONS = ["text", "clean", "scan", "photo", "poor"]
HEADLINE = ["med_precision", "med_recall", "med_f1", "med_fully_correct_rate", "followup_recall", "followup_days_accuracy", "redflag_recall",
            "hallucinated_meds", "invented_value_rate", "quote_exact_rate", "quote_fuzzy_rate", "parse_failure_rate", "low_confidence_rate"]


def doc_path(doc_id, cond):
    return REPO / "data" / ("synthetic" if cond == "text" else f"rendered/{cond}") / (f"{doc_id}.txt" if cond == "text" else f"{doc_id}.png")


def tables(groups):
    """groups: {dimension: {value: counters}} -> markdown."""
    out = []
    for dim, vals in groups.items():
        rows = {k: summarize(v) for k, v in vals.items()}
        cols = HEADLINE + [f"acc_{f}" for f in MED_FIELDS]
        out.append(f"### By {dim}\n")
        out.append("| metric | " + " | ".join(rows) + " |")
        out.append("|---|" + "---|" * len(rows))
        for col in ["docs"] + cols:
            out.append(f"| {col} | " + " | ".join("-" if r[col] is None else str(r[col]) for r in rows.values()) + " |")
        out.append("")
    return "\n".join(out)


def run(args):
    manifest = json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]
    docs = [d for d in manifest if args.split == "all" or d["split"] == args.split][: args.limit]
    conds = args.conditions.split(",")
    run_id = args.run_id or f"{datetime.now():%Y%m%d-%H%M%S}-{PROMPT_VERSION}{'-oracle' if args.oracle else ''}"
    raw_dir = REPO / "eval" / "runs" / run_id / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if not args.oracle:
        from app.services.extraction import extract_document

    groups = {"overall": defaultdict(Counter), "condition": defaultdict(Counter), "difficulty": defaultdict(Counter), "split": defaultdict(Counter)}
    meta = Counter()
    latencies, incomplete = [], False
    attempted, skips, lat = Counter(), defaultdict(Counter), defaultdict(list)  # per condition
    name_tot, name_bad, bad_examples = Counter(), Counter(), []
    fnames = formulary_names()
    for cond in conds:
        for d in docs:
            gt = from_ground_truth(ExtractedDocument.model_validate_json((REPO / "data/ground_truth" / f"{d['id']}.json").read_text(encoding="utf-8")))
            text = (REPO / "data/synthetic" / f"{d['id']}.txt").read_text(encoding="utf-8")
            if args.oracle:
                pred, res = gt, None
            else:
                attempted[cond] += 1
                res = extract_document(doc_path(d["id"], cond), prompt_version=args.prompt_version)
                if res.quota_exhausted:
                    incomplete = True
                    break
                pred = res.output
                if res.skipped:  # provider/model failure (503, context_truncated, image_not_received...): not scored, listed in the report
                    skips[cond][res.error] += 1
                    meta["api_failed"] += 1
                    meta["api_calls"] += res.api_calls
                    continue
                (raw_dir / f"{cond}_{d['id']}.json").write_text(res.raw_text or json.dumps({"error": res.error}), encoding="utf-8")
                meta["api_calls"] += res.api_calls
                meta["cached"] += res.cached
                meta["tokens"] += res.usage.get("total_tokens", 0)
                if not res.cached:
                    latencies.append(res.latency_s)
                lat[cond].append(res.latency_s)  # cached runs keep the original latency
                for n, f, r in check_names(pred, fnames) if pred else ():
                    name_tot[cond] += 1
                    if r < THRESHOLD:
                        name_bad[cond] += 1
                        bad_examples.append((cond, d["id"], n, f, round(r, 2)))
            c = score_document(gt, pred, text)
            for dim, key in (("overall", "all"), ("condition", cond), ("difficulty", d["difficulty"]), ("split", d["split"])):
                groups[dim][key] += c
        if incomplete:
            break
    pct = lambda xs, q: round(sorted(xs)[min(len(xs) - 1, int(q * len(xs)))], 1) if xs else None  # noqa: E731
    coverage = {c: dict(attempted=attempted[c], scored=groups["condition"][c]["docs"], skipped=sum(skips[c].values()), skip_reasons=dict(skips[c]),
                        latency_median_s=pct(lat[c], 0.5), latency_p95_s=pct(lat[c], 0.95)) for c in conds}
    sanity = {c: dict(names=name_tot[c], unmatched=name_bad[c], unmatched_rate=round(name_bad[c] / name_tot[c], 3) if name_tot[c] else None) for c in conds}
    result = dict(run_id=run_id, split=args.split, conditions=conds, prompt_version=args.prompt_version, oracle=args.oracle, incomplete=incomplete,
                  api_calls=meta["api_calls"], api_failed_not_scored=meta["api_failed"], cache_hits=meta["cached"], total_tokens=meta["tokens"],
                  mean_latency_s=round(sum(latencies) / len(latencies), 2) if latencies else None,
                  coverage=coverage, drug_name_sanity=dict(threshold=THRESHOLD, by_condition=sanity, examples=bad_examples[:10]),
                  metrics={dim: {k: summarize(v) for k, v in vals.items()} for dim, vals in groups.items()})
    out = REPO / "eval" / "results" / run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    head = (f"# Run {run_id}\n\nsplit={args.split} prompt={args.prompt_version} oracle={args.oracle} docs={len(docs)} api_calls={meta['api_calls']} api_failed_not_scored={meta['api_failed']} "
            f"cache_hits={meta['cached']} tokens={meta['tokens']} mean_latency_s={result['mean_latency_s']}"
            + ("\n\n**INCOMPLETE: daily quota exhausted. Re-run the same command to resume from the cache.**" if incomplete else "") + "\n\n")
    cov = ["### Coverage (documents attempted / scored / SKIPPED)\n", "| condition | attempted | scored | skipped | skip reasons | latency median s | latency p95 s |", "|---|---|---|---|---|---|---|"]
    cov += [f"| {c} | {v['attempted']} | {v['scored']} | {v['skipped']} | {v['skip_reasons'] or '-'} | {v['latency_median_s']} | {v['latency_p95_s']} |" for c, v in coverage.items()]
    san = [f"\n### Drug-name sanity (predicted names with no formulary match >= {THRESHOLD})\n", "| condition | names | unmatched | rate |", "|---|---|---|---|"]
    san += [f"| {c} | {v['names']} | {v['unmatched']} | {v['unmatched_rate']} |" for c, v in sanity.items()]
    san += ["", "Examples (condition, doc, predicted, closest formulary, ratio):", *[f"- {e}" for e in bad_examples[:10]]]
    (out / "metrics.md").write_text(head + "\n".join(cov + san) + "\n\n" + tables(groups) + "\n", encoding="utf-8", newline="\n")
    return result, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--run-id")
    ap.add_argument("--prompt-version", default=PROMPT_VERSION)
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--final-test-run", action="store_true")
    args = ap.parse_args()
    check_split(args.split, args.final_test_run, "evaluate " + " ".join(sys.argv[1:]))
    result, out = run(args)
    o = result["metrics"]["overall"]["all"]
    print(f"{result['run_id']}: F1={o['med_f1']} recall={o['med_recall']} halluc={o['hallucinated_meds']} calls={result['api_calls']} cached={result['cache_hits']} -> {out}")


if __name__ == "__main__":
    main()
