"""POST-HOC (Phase 7b-posthoc): breakdown by difficulty / case template, direct standardisation dev vs test, and cluster-aware intervals.

Read-only: reads eval/runs/final-test-v1 (raw outputs + explanation records), eval/runs/dev-ollama-v1 (dev raw outputs), data/manifest.json and the
ground truth through the SAME functions the official report uses (eval.final_test.report). No model call, no network. Writes only to
eval/results/final-test-v1-posthoc/. Nothing here is an official number.

  backend\\.venv\\Scripts\\python scripts\\posthoc_analyse.py
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO))
from eval.final_test import report as R  # noqa: E402
from eval.final_test.stats import wilson  # noqa: E402
from eval.matching import summarize  # noqa: E402

OUT = REPO / "eval/results/final-test-v1-posthoc"
SEED, NBOOT = 20261028, 2000
LANGS = ("en", "ta", "hi")
DIFFS = ("clean", "abbreviated", "messy")
HEAD = "POST-HOC (descriptive, done after the official run; not an official result; nothing in the system was changed in response)"

manifest = json.loads((REPO / "data/manifest.json").read_text(encoding="utf-8"))["documents"]
META = {d["id"]: d for d in manifest}


def load(run_id, split):
    ids = {d["id"] for d in manifest if d["split"] == split}
    counters, records, unr = R.per_document_counters(REPO, REPO / "eval/runs" / run_id / "raw", ids)
    assert not unr
    return ids, counters, records


def rate(a, b):
    return None if not b else round(a / b, 4)


def group_stats(docs, counters, records):
    """Pooled over all conditions for the documents in `docs`."""
    raw = sum((counters[k]["raw"] for k in counters if k[1] in docs), Counter())
    nor = sum((counters[k]["normalised"] for k in counters if k[1] in docs), Counter())
    rs = [r for r in records if r["doc"] in docs]
    sr, nm = summarize(raw), summarize(nor)
    return {
        "documents": len(docs), "medicine_mentions": raw["med_tp"] + raw["med_fn"], "readings": len(rs),
        "fully_correct_raw": rate(raw["med_fully_correct"], raw["med_tp"]), "fully_correct_raw_n": [raw["med_fully_correct"], raw["med_tp"]],
        "fully_correct_norm": rate(nor["med_fully_correct"], nor["med_tp"]), "fully_correct_norm_n": [nor["med_fully_correct"], nor["med_tp"]],
        "f1_raw": sr["med_f1"], "f1_norm": nm["med_f1"],
        "must_confirm_share": rate(sum(r["level"] == "must_confirm" for r in rs), len(rs)),
        "must_confirm_n": [sum(r["level"] == "must_confirm" for r in rs), len(rs)],
        "name_errors_remaining": sum(bool(r["name_err"]) for r in rs), "name_errors_unflagged": sum(bool(r["name_err"]) and r["level"] == "none" for r in rs),
        "brand_acc_raw": rate(raw["field_ok_brand_name"], raw["field_total_brand_name"]), "brand_acc_raw_n": [raw["field_ok_brand_name"], raw["field_total_brand_name"]],
        "brand_acc_norm": rate(nor["field_ok_brand_name"], nor["field_total_brand_name"]),
    }


def standardise(strata_target, strata_source, key_num, key_den):
    """Direct standardisation: the source split's stratum rates reweighted to the target split's denominators."""
    w = {d: strata_target[d][key_den][1] if isinstance(strata_target[d][key_den], list) else 0 for d in DIFFS}
    tot = sum(w.values())
    return round(sum(w[d] / tot * strata_source[d][key_num] for d in DIFFS), 4)


def main():
    t_ids, t_cnt, t_rec = load("final-test-v1", "test")
    d_ids, d_cnt, d_rec = load("dev-ollama-v1", "dev")
    res = {"label": HEAD, "seed": SEED, "resamples": NBOOT}

    # ---------------- breakdown by difficulty and template
    def split_docs(ids, field):
        g = defaultdict(set)
        for i in ids:
            g[META[i][field]].add(i)
        return g
    res["breakdown"] = {}
    for name, ids, cnt, rec in (("test", t_ids, t_cnt, t_rec), ("dev", d_ids, d_cnt, d_rec)):
        res["breakdown"][name] = {"all": group_stats(ids, cnt, rec),
                                  "difficulty": {k: group_stats(v, cnt, rec) for k, v in sorted(split_docs(ids, "difficulty").items())},
                                  "template": {k: group_stats(v, cnt, rec) for k, v in sorted(split_docs(ids, "template").items())},
                                  "document_type": {k: group_stats(v, cnt, rec) for k, v in sorted(split_docs(ids, "document_type").items())}}
    B = res["breakdown"]
    std = {}
    for metric, (num, den) in {"fully_correct_norm": ("fully_correct_norm", "fully_correct_norm_n"), "fully_correct_raw": ("fully_correct_raw", "fully_correct_raw_n"),
                               "brand_acc_raw": ("brand_acc_raw", "brand_acc_raw_n"), "must_confirm_share": ("must_confirm_share", "must_confirm_n")}.items():
        td, dd = B["test"]["difficulty"], B["dev"]["difficulty"]
        std[metric] = {"dev_crude": B["dev"]["all"][num], "test_crude": B["test"]["all"][num],
                       "test_standardised_to_dev_mix": standardise(dd, td, num, den),
                       "dev_standardised_to_test_mix": standardise(td, dd, num, den),
                       "dev_weights": {d: round(dd[d][den][1] / sum(dd[x][den][1] for x in DIFFS), 3) for d in DIFFS},
                       "test_weights": {d: round(td[d][den][1] / sum(td[x][den][1] for x in DIFFS), 3) for d in DIFFS}}
    res["standardised"] = std

    # ---------------- cluster-aware (document-level) bootstrap on the test split
    per_doc = defaultdict(Counter)
    for r in t_rec:
        c = per_doc[r["doc"]]
        c["n"] += 1
        c["must"] += r["level"] == "must_confirm"
        c["ir"] += bool(r["interaction_ready"])
        c["sr"] += bool(r["schedule_ready"])
        c["ws"] += bool(r["wrong_schedule"])
        c["wrg"] += bool(r["wrong_resolved"])
    for (cond, doc), v in t_cnt.items():
        per_doc[doc]["tp_raw"] += v["raw"]["med_tp"]
        per_doc[doc]["fc_raw"] += v["raw"]["med_fully_correct"]
        per_doc[doc]["tp_norm"] += v["normalised"]["med_tp"]
        per_doc[doc]["fc_norm"] += v["normalised"]["med_fully_correct"]
    expl = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((REPO / "eval/runs/final-test-v1/docs").glob("*.json"))]
    for e in expl:
        for s in e["explanation"]["sections"]:
            for ln in s["lines"]:
                if ln["kind"] in ("advice", "follow_up", "warning"):
                    per_doc[e["doc"]]["lines"] += 1
                    for lg in LANGS:
                        per_doc[e["doc"]][f"ver_{lg}"] += ln["text"][lg]["status"] == "verified"
    docs = sorted(per_doc)
    metrics = {"must-confirm share": ("must", "n"), "fully correct, raw": ("fc_raw", "tp_raw"), "fully correct, after rules": ("fc_norm", "tp_norm"),
               "interaction_ready share": ("ir", "n"), "schedule_ready share": ("sr", "n"), "wrong schedule among schedule_ready": ("ws", "sr"),
               **{f"explanation lines verified, {lg}": (f"ver_{lg}", "lines") for lg in LANGS}}
    rng = random.Random(SEED)
    draws = [[rng.randrange(len(docs)) for _ in docs] for _ in range(NBOOT)]
    cl = {}
    for name, (nk, dk) in metrics.items():
        k, n = sum(per_doc[d][nk] for d in docs), sum(per_doc[d][dk] for d in docs)
        vals = []
        for dr in draws:
            nn = sum(per_doc[docs[i]][dk] for i in dr)
            if nn:
                vals.append(sum(per_doc[docs[i]][nk] for i in dr) / nn)
        vals.sort()
        lo, hi = vals[int(0.025 * len(vals))], vals[min(len(vals) - 1, int(0.975 * len(vals)))]
        w = wilson(k, n)
        cl[name] = {"k": k, "n": n, "p": round(k / n, 4), "wilson": [round(w[0], 4), round(w[1], 4)], "cluster_bootstrap": [round(lo, 4), round(hi, 4)],
                    "width_ratio": round((hi - lo) / (w[1] - w[0]), 2)}
    res["cluster"] = cl
    ir_docs = [d for d in docs if per_doc[d]["ir"]]
    distinct = {(r["doc"], r["gt_generic"]) for r in t_rec if r["interaction_ready"] and r["gt_generic"]}
    k_wrong = sum(per_doc[d]["wrg"] for d in docs)
    res["wrong_resolved_generic"] = {
        "events": k_wrong, "interaction_ready_readings": sum(per_doc[d]["ir"] for d in docs), "distinct_medicines_ready_in_some_condition": len(distinct),
        "documents_contributing": len(ir_docs),
        "rule_of_three_readings": round(3 / sum(per_doc[d]["ir"] for d in docs), 4), "rule_of_three_distinct_medicines": round(3 / len(distinct), 4),
        "document_level_exact_upper_95_one_sided": round(1 - 0.05 ** (1 / len(ir_docs)), 4), "document_level_rule_of_three": round(3 / len(ir_docs), 4)}
    # ds_035: the same misread in the other conditions (for the case review)
    res["lookups"] = [{k: (sorted(v) if isinstance(v, set) else v) for k, v in r.items() if k in ("cond", "doc", "level", "flags", "schedule_ready", "interaction_ready", "quote")}
                      for r in t_rec if r["doc"] in ("ds_035", "ds_038") and ("VENTOLIN" in r["quote"].upper() or "AUGMENTIN" in r["quote"].upper())]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "posthoc_analysis.json").write_text(json.dumps(res, indent=1, ensure_ascii=False, default=list) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"standardised": std, "cluster": cl, "wrong_resolved_generic": res["wrong_resolved_generic"], "lookups": res["lookups"]}, indent=1, default=list)[:6000])
    print("dev check: fully_norm", B["dev"]["all"]["fully_correct_norm"], "brand_raw", B["dev"]["all"]["brand_acc_raw"], "| test", B["test"]["all"]["fully_correct_norm"], B["test"]["all"]["brand_acc_raw"])


if __name__ == "__main__":
    main()
