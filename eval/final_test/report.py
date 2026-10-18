"""Analysis and reporting of the final test (offline: reads the raw model outputs of the run, never calls a model).

per_document_counters(): one raw and one normalised scoring counter per (condition, document) -> everything else (pooled figures, Wilson and bootstrap
intervals) is derived from them. Definitions are those of eval/matching.py and eval/rescore.py (protocol section 2). Pair-level DDInter levels are never
written to the committed outputs (aggregated counts only)."""
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))

from app.schemas.extraction import ExtractedDocument  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth  # noqa: E402
from app.services.normalisation import normalise_document  # noqa: E402
from eval.final_test.stats import bootstrap_ci, wilson  # noqa: E402
from eval.matching import MED_FIELDS, div, score_document, summarize  # noqa: E402
from eval.rescore import CONDS, records_for, to_prediction  # noqa: E402

LANGS = ("en", "ta", "hi")


# ---------------------------------------------------------------------------------------------------------------- scoring
def per_document_counters(root: Path, raw_dir: Path, ids: set[str]):
    """-> (counters {(cond, doc): {"raw": Counter, "normalised": Counter}}, app-mode records, unreadable raw files)."""
    counters, records, unreadable = {}, [], []
    for f in sorted(raw_dir.glob("*.json")):
        cond, doc = f.stem.split("_", 1)
        if doc not in ids or cond not in CONDS:
            continue
        try:
            raw = ExtractionOutput.model_validate_json(f.read_text(encoding="utf-8"))
        except ValueError:
            unreadable.append(f.stem)
            continue
        gt = from_ground_truth(ExtractedDocument.model_validate_json((root / "data/ground_truth" / f"{doc}.json").read_text(encoding="utf-8")))
        text = (root / "data/synthetic" / f"{doc}.txt").read_text(encoding="utf-8")
        nd = normalise_document(raw)  # app mode: model output only
        counters[(cond, doc)] = {"raw": score_document(gt, raw, text), "normalised": score_document(gt, to_prediction(nd), text, pair_with=raw.medications)}
        records += records_for(nd, raw, gt, cond, doc)
    return counters, records, unreadable


def _sum(cs):
    t = Counter()
    for c in cs:
        t += c
    return t


def _ci(k, n):
    w = wilson(k, n)
    return None if w is None else [round(w[0], 4), round(w[1], 4)]


def _boot(docs, stat):
    b = bootstrap_ci(docs, stat)
    return None if b is None else [round(b[0], 4), round(b[1], 4)]


def _f1(c):
    return summarize(c)["med_f1"]


def _fully(c):
    return summarize(c)["med_fully_correct_rate"]


def extraction_metrics(counters, variant: str) -> dict:
    """Per condition and pooled: summary + Wilson intervals for the proportions + bootstrap intervals for F1 and the fully-correct rate."""
    out = {}
    for cond in (*CONDS, "all"):
        keys = [k for k in counters if cond == "all" or k[0] == cond]
        if not keys:
            continue
        c = _sum(counters[k][variant] for k in keys)
        s = summarize(c)
        # bootstrap unit = the document (pooled: the document with all its conditions together)
        by_doc = defaultdict(Counter)
        for k in keys:
            by_doc[k[1]] += counters[k][variant]
        docs = [by_doc[d] for d in sorted(by_doc)]
        s["intervals"] = {
            "med_precision": _ci(c["med_tp"], c["med_tp"] + c["med_fp"]),
            "med_recall": _ci(c["med_tp"], c["med_tp"] + c["med_fn"]),
            "med_f1_bootstrap": _boot(docs, _f1),
            "med_fully_correct_rate": _ci(c["med_fully_correct"], c["med_tp"]),
            "med_fully_correct_rate_bootstrap": _boot(docs, _fully),
            "invented_value_rate": _ci(c["invented"], c["null_total"]),
            **{f"acc_{f}": _ci(c[f"field_ok_{f}"], c[f"field_total_{f}"]) for f in MED_FIELDS},
        }
        s["counts"] = {"med_tp": c["med_tp"], "med_fp": c["med_fp"], "med_fn": c["med_fn"], "med_fully_correct": c["med_fully_correct"], "invented": c["invented"], "null_total": c["null_total"], "documents": len(docs)}
        out[cond] = s
    return out


def flag_metrics(records) -> dict:
    """Name errors remaining, unflagged ones (review level none), review-level load, readiness and WRONG resolved generic / schedule (app mode)."""
    out = {}
    for cond in (*CONDS, "all"):
        rs = [r for r in records if cond == "all" or r["cond"] == cond]
        if not rs:
            continue
        n = len(rs)
        must = sum(r["level"] == "must_confirm" for r in rs)
        name_err = [r for r in rs if r["name_err"]]
        timing_err = [r for r in rs if r["timing_err"]]
        ir, sr = [r for r in rs if r["interaction_ready"]], [r for r in rs if r["schedule_ready"]]
        out[cond] = {
            "medicines": n, "must_confirm": must, "share_must_confirm": div(must, n), "share_must_confirm_ci": _ci(must, n),
            "name_errors_remaining": len(name_err), "name_errors_unflagged": sum(r["level"] == "none" for r in name_err),
            "name_errors_at_note_level": sum(r["level"] == "note" for r in name_err),
            "timing_errors_remaining": len(timing_err), "timing_errors_unflagged": sum(r["level"] == "none" for r in timing_err),
            "interaction_ready": len(ir), "schedule_ready": len(sr),
            "wrong_resolved_generic": sum(bool(r["wrong_resolved"]) for r in ir), "wrong_resolved_generic_ci": _ci(sum(bool(r["wrong_resolved"]) for r in ir), len(ir)),
            "wrong_schedule": sum(bool(r["wrong_schedule"]) for r in sr), "wrong_schedule_ci": _ci(sum(bool(r["wrong_schedule"]) for r in sr), len(sr)),
            "wrong_resolved_cases": [{k: r[k] for k in ("cond", "doc", "pred_names", "gt_names", "resolved", "gt_generic")} for r in ir if r["wrong_resolved"]],
        }
    return out


def operational(coverage_rows: list[dict]) -> dict:
    """coverage_rows: one dict per attempted (cond, doc): {cond, doc, skipped, reason, latency_s}."""
    out = {}
    for cond in (*CONDS, "all"):
        rows = [r for r in coverage_rows if cond == "all" or r["cond"] == cond]
        if not rows:
            continue
        lat = sorted(r["latency_s"] for r in rows if not r["skipped"] and r["latency_s"] is not None)
        reasons = Counter(r["reason"] for r in rows if r["skipped"])
        out[cond] = {"attempted": len(rows), "scored": sum(not r["skipped"] for r in rows), "skipped": sum(r["skipped"] for r in rows), "skip_reasons": dict(reasons),
                     "latency_median_s": round(statistics.median(lat), 1) if lat else None,
                     "latency_p95_s": round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 1) if lat else None}
    return out


def scrub_safety(m: dict) -> dict:
    """Aggregated counts only: drop interaction levels and pair-level case lists from the committed safety block."""
    m = json.loads(json.dumps(m))
    m["ground_truth"].pop("interactions_by_level", None)
    s = m["safety"]
    for k in ("silent_miss_cases", "downgrade_cases", "false_alarm_cases", "level_mismatch_cases", "level_mismatches"):
        s.pop(k, None)
    s["silent_misses_covered_by_a_flag"] = s["silent_misses_strict"] - s["silent_misses_not_covered_by_a_flag"]
    m["duplicates"].pop("false_cases", None)
    m["duplicates"].pop("missed_cases", None)
    m.pop("supplement_would_change_formulary_pairs", None)
    return m


# ------------------------------------------------------------------------------------------------------- dev comparison
DEV = {
    "extraction": "eval/results/dev-ollama-v1-normalised-v2/metrics.json",
    "safety": "eval/results/phase4-dev-with-supplement/metrics.json",
    "language": "eval/results/phase3e-dev-clean/metrics.json",
}


def dev_vs_test(test: dict, root: Path = REPO) -> list[dict]:
    """Rows {metric, dev, test, diff} from the COMMITTED dev metrics (never the test split) next to the test figures."""
    ex = json.loads((root / DEV["extraction"]).read_text(encoding="utf-8"))
    sf = json.loads((root / DEV["safety"]).read_text(encoding="utf-8"))
    lg = json.loads((root / DEV["language"]).read_text(encoding="utf-8"))
    rows = []

    def add(name, dev, tst):
        rows.append({"metric": name, "dev": dev, "test": tst, "diff": None if dev is None or tst is None else round(tst - dev, 4)})
    for v, label in (("raw", "raw"), ("normalised", "normalised")):
        d, t = ex[v]["all"], test["extraction"][v].get("all", {})
        for k, name in (("med_f1", "medicine F1"), ("med_fully_correct_rate", "fully-correct medicine rate"), ("invented_value_rate", "invented-value rate"), ("acc_timing_label", "timing label field"), ("acc_brand_name", "brand name field")):
            add(f"{name}, {label}", d.get(k), t.get(k))
    fl_dev = ex["review_levels_app"]["all"]["name"]
    fl = test["flags"].get("all", {})
    add("share of medicines at must_confirm", fl_dev["share_must_confirm"], fl.get("share_must_confirm"))
    add("name errors remaining, unflagged", fl_dev["unflagged_errors"], fl.get("name_errors_unflagged"))
    add("wrong resolved_generic among interaction_ready", ex["readiness"]["all"]["wrong_resolved_generic"], fl.get("wrong_resolved_generic"))
    ts = test.get("safety", {}).get("safety", {})
    add("silent misses, strict", sf["safety"]["silent_misses_strict"], ts.get("silent_misses_strict"))
    add("silent misses not covered by a flag", sf["safety"]["silent_misses_not_covered_by_a_flag"], ts.get("silent_misses_not_covered_by_a_flag"))
    add("false alarms", sf["safety"]["false_alarms"], ts.get("false_alarms"))
    for l_ in LANGS:
        add(f"share of free-text lines shown in {l_}", lg["provenance_share"][l_]["all"]["shown_in_language"], (test.get("explanation", {}).get("provenance_share", {}).get(l_, {}).get("all", {}) or {}).get("shown_in_language"))
    return rows


# ------------------------------------------------------------------------------------------------------------- outputs
def _fmt(x):
    return "-" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def _ci_s(i):
    return "" if not i else f" [{i[0]:.3f}, {i[1]:.3f}]"


def markdown(m: dict, label: str) -> str:
    head = f"# Final test results: {m['run_id']}\n\n**{label}**\n\nSynthetic documents rendered by this project, held-out TEST split, one local model, protocol docs/FINAL_TEST_PROTOCOL.md. " \
           "Proportions carry Wilson 95% intervals, F1 and fully-correct rates carry document-level bootstrap 95% intervals (2000 resamples, fixed seed); 40 documents give wide intervals.\n\n"
    out = [head, "## Coverage and latency\n", "| condition | attempted | scored | skipped | skip reasons | latency median s | latency p95 s |", "|---|---|---|---|---|---|---|"]
    for c, v in m["operational"].items():
        out.append(f"| {c} | {v['attempted']} | {v['scored']} | {v['skipped']} | {v['skip_reasons'] or '-'} | {_fmt(v['latency_median_s'])} | {_fmt(v['latency_p95_s'])} |")
    for variant in ("raw", "normalised"):
        out += ["", f"## Extraction, {variant}\n", "| condition | docs | precision | recall | F1 (bootstrap) | fully correct (bootstrap) | hallucinated | invented-value rate |", "|---|---|---|---|---|---|---|---|"]
        for c, s in m["extraction"][variant].items():
            i = s["intervals"]
            out.append(f"| {c} | {s['docs']} | {_fmt(s['med_precision'])}{_ci_s(i['med_precision'])} | {_fmt(s['med_recall'])}{_ci_s(i['med_recall'])} | {_fmt(s['med_f1'])}{_ci_s(i['med_f1_bootstrap'])} | "
                       f"{_fmt(s['med_fully_correct_rate'])}{_ci_s(i['med_fully_correct_rate_bootstrap'])} | {s['hallucinated_meds']} | {_fmt(s['invented_value_rate'])}{_ci_s(i['invented_value_rate'])} |")
        out += ["", f"Per-field accuracy ({variant}, pooled): " + "; ".join(f"{f} {_fmt(m['extraction'][variant]['all'][f'acc_{f}'])}{_ci_s(m['extraction'][variant]['all']['intervals'][f'acc_{f}'])}" for f in MED_FIELDS)]
        out += ["", f"Invented values by field ({variant}, pooled; of_null = fields the document leaves empty): " + "; ".join(f"{f}: {v['invented']}/{v['of_null']} (role confusion {v['role_confusion']}, in document {v['in_document']}, made up {v['made_up']})" for f, v in ((k[9:], m['extraction'][variant]['all'][k]) for k in m['extraction'][variant]['all'] if k.startswith('invented_') and isinstance(m['extraction'][variant]['all'][k], dict)))]
    out += ["", "## Flags, names and readiness (app mode)\n", "| condition | medicines | must_confirm (CI) | name errors remaining | unflagged | timing errors | unflagged | interaction_ready | WRONG resolved_generic | schedule_ready | wrong schedule |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, v in m["flags"].items():
        out.append(f"| {c} | {v['medicines']} | {v['must_confirm']} ({_fmt(v['share_must_confirm'])}{_ci_s(v['share_must_confirm_ci'])}) | {v['name_errors_remaining']} | {v['name_errors_unflagged']} | {v['timing_errors_remaining']} | {v['timing_errors_unflagged']} | {v['interaction_ready']} | {v['wrong_resolved_generic']} | {v['schedule_ready']} | {v['wrong_schedule']} |")
    if m["flags"].get("all", {}).get("wrong_resolved_cases"):
        out += ["", "WRONG resolved_generic cases (reported in full):", *[f"- {c}" for c in m["flags"]["all"]["wrong_resolved_cases"]]]
    sf = m.get("safety", {})
    if sf:
        s = sf["safety"]
        out += ["", "## Safety engine (aggregated counts; no pair-level interaction levels are published)\n",
                f"- strict silent misses: {s['silent_misses_strict']} (covered by a confirmation flag: {s['silent_misses_covered_by_a_flag']}; NOT covered: {s['silent_misses_not_covered_by_a_flag']})",
                f"- downgrades to not_checked_unconfirmed: {s['downgrades']}; false alarms: {s['false_alarms']}",
                f"- pairs per condition: {sf['pairs_by_condition']}; share not checked: {sf['share_not_checked_by_condition']}",
                f"- duplicates: {sf['duplicates']}"]
    ex = m.get("explanation")
    if ex:
        out += ["", "## Explanation pipeline (clean condition)\n", f"- documents {ex.get('documents')}, lines {ex.get('lines')}, by kind {ex.get('lines_by_kind')}",
                f"- verified share (Phase 3 definition): {ex.get('phase3_verified_share')}", f"- provenance and label distribution per language: {ex.get('provenance_share')}"]
    out += ["", "## Dev versus test (dev = committed dev results; expected higher on dev, see protocol section 4)\n", "| metric | dev | test | test minus dev |", "|---|---|---|---|"]
    out += [f"| {r['metric']} | {_fmt(r['dev'])} | {_fmt(r['test'])} | {_fmt(r['diff'])} |" for r in m["dev_vs_test"]]
    if m.get("skipped"):
        out += ["", "## Skipped documents (listed, never dropped)\n", *[f"- {s}" for s in m["skipped"]]]
    return "\n".join(out) + "\n"


def per_document_csv(path: Path, counters) -> None:
    cols = ["condition", "document", "variant", "med_tp", "med_fp", "med_fn", "med_fully_correct", "invented", "null_total"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for (cond, doc), v in sorted(counters.items()):
            for variant, c in v.items():
                w.writerow([cond, doc, variant, c["med_tp"], c["med_fp"], c["med_fn"], c["med_fully_correct"], c["invented"], c["null_total"]])


def figures(m: dict) -> dict:
    """Machine-readable figures for the testing page (not wired yet): id -> value, count, source."""
    fig = {}
    for variant in ("raw", "normalised"):
        a = m["extraction"][variant].get("all", {})
        fig[f"test_f1_{variant}"] = {"value": a.get("med_f1"), "ci": a.get("intervals", {}).get("med_f1_bootstrap"), "unit": "ratio"}
        fig[f"test_fully_correct_{variant}"] = {"value": a.get("med_fully_correct_rate"), "ci": a.get("intervals", {}).get("med_fully_correct_rate_bootstrap"), "unit": "ratio"}
        fig[f"test_invented_{variant}"] = {"value": a.get("invented_value_rate"), "ci": a.get("intervals", {}).get("invented_value_rate"), "unit": "ratio"}
    fl = m["flags"].get("all", {})
    for k in ("share_must_confirm", "name_errors_unflagged", "wrong_resolved_generic"):
        fig[f"test_{k}"] = {"value": fl.get(k), "of": fl.get("medicines") if k == "share_must_confirm" else fl.get("interaction_ready") if k == "wrong_resolved_generic" else fl.get("name_errors_remaining")}
    s = m.get("safety", {}).get("safety", {})
    for k in ("silent_misses_strict", "silent_misses_not_covered_by_a_flag", "false_alarms"):
        fig[f"test_{k}"] = {"value": s.get(k)}
    return {"run_id": m["run_id"], "official": m["official"], "split": "test", "figures": fig}
