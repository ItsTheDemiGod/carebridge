"""POST-HOC: render eval/results/final-test-v1-posthoc/posthoc_analysis.json into breakdown.md and cluster_intervals.md (no recomputation)."""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "eval/results/final-test-v1-posthoc"
r = json.loads((OUT / "posthoc_analysis.json").read_text(encoding="utf-8"))
H = "**POST-HOC (descriptive, done after the official run; not an official result; nothing in the system was changed in response).**\n"
f = lambda x: "-" if x is None else f"{x:.3f}"


def table(split, group):
    rows = ["| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in {"all": r["breakdown"][split]["all"], **r["breakdown"][split][group]}.items():
        rows.append(f"| {k} | {v['documents']} | {v['medicine_mentions']} | {f(v['fully_correct_raw'])} | {f(v['fully_correct_norm'])} | {f(v['f1_raw'])} | {f(v['f1_norm'])} | {f(v['must_confirm_share'])} | {v['name_errors_remaining']} ({v['name_errors_unflagged']}) | {f(v['brand_acc_raw'])} |")
    return "\n".join(rows)


b = [H, "Pooled over the five conditions; medicine mentions = ground-truth medicines x 5 readings. Rates are ratios of sums (fully correct: matched medicines). Dev figures are recomputed from the cached dev raw outputs (`eval/runs/dev-ollama-v1`) with the same code as the test; the pooled dev values equal the committed ones (fully correct after rules 0.8115, brand name raw 0.6731). Cells with few documents are noisy: read the `docs` column.\n"]
for split in ("test", "dev"):
    for group, label in (("difficulty", "difficulty"), ("document_type", "document type"), ("template", "case template")):
        b += [f"### {split.upper()} split by {label}\n", table(split, group), ""]
s = r["standardised"]
b += ["### Direct standardisation, dev versus test (difficulty strata)\n",
      "Each split's stratum-specific rate (clean / abbreviated / messy) is reweighted to the OTHER split's stratum weights (the share of that metric's denominator in each stratum). Only difficulty is standardised; templates are too sparse (1 to 8 documents each).\n",
      f"Document mix: dev clean {r['breakdown']['dev']['difficulty']['clean']['documents']} / abbreviated {r['breakdown']['dev']['difficulty']['abbreviated']['documents']} / messy {r['breakdown']['dev']['difficulty']['messy']['documents']}; test clean {r['breakdown']['test']['difficulty']['clean']['documents']} / abbreviated {r['breakdown']['test']['difficulty']['abbreviated']['documents']} / messy {r['breakdown']['test']['difficulty']['messy']['documents']}.\n",
      "| metric | dev crude | test crude | crude gap (test - dev) | test reweighted to dev mix | gap vs dev | dev reweighted to test mix | gap vs test |", "|---|---|---|---|---|---|---|---|"]
for k, label in (("fully_correct_norm", "fully correct, after rules"), ("fully_correct_raw", "fully correct, raw"), ("brand_acc_raw", "brand-name accuracy, raw"), ("must_confirm_share", "must_confirm share")):
    v = s[k]
    b.append(f"| {label} | {f(v['dev_crude'])} | {f(v['test_crude'])} | {v['test_crude'] - v['dev_crude']:+.3f} | {f(v['test_standardised_to_dev_mix'])} | {v['test_standardised_to_dev_mix'] - v['dev_crude']:+.3f} | {f(v['dev_standardised_to_test_mix'])} | {v['test_crude'] - v['dev_standardised_to_test_mix']:+.3f} |")
(OUT / "breakdown.md").write_text("\n".join(b) + "\n", encoding="utf-8", newline="\n")

c = [H, f"Seeded document-level cluster bootstrap on the 40 test documents (seed {r['seed']}, {r['resamples']} resamples, percentile 95%): each resample draws 40 documents with replacement and keeps all five readings (and all explanation lines) of a document together; the statistic is the ratio of sums. Wilson = the official interval (treats readings as independent). Width ratio = cluster width / Wilson width.\n",
     "| metric | k / n | proportion | official Wilson 95% | cluster bootstrap 95% | width ratio |", "|---|---|---|---|---|---|"]
for k, v in r["cluster"].items():
    c.append(f"| {k} | {v['k']} / {v['n']} | {v['p']:.3f} | [{v['wilson'][0]:.3f}, {v['wilson'][1]:.3f}] | [{v['cluster_bootstrap'][0]:.3f}, {v['cluster_bootstrap'][1]:.3f}] | {v['width_ratio']:.2f} |")
w = r["wrong_resolved_generic"]
c += ["", "### Wrong resolved_generic among interaction_ready (0 events)\n",
      f"- Readings: 0 of {w['interaction_ready_readings']}; rule of three, 95% upper bound {w['rule_of_three_readings']:.4f} (official Wilson upper bound 0.010). Treats the 389 readings as independent, which they are not.",
      f"- Distinct medicines: the 389 readings are {w['distinct_medicines_ready_in_some_condition']} distinct (document, medicine) pairs that were interaction_ready in at least one condition; rule of three on those: {w['rule_of_three_distinct_medicines']:.4f}.",
      f"- Documents: {w['documents_contributing']} of 40 documents contributed at least one interaction_ready medicine; with 0 documents showing a wrong one, the one-sided exact 95% upper bound for the share of documents is {w['document_level_exact_upper_95_one_sided']:.4f} (rule of three {w['document_level_rule_of_three']:.4f}). This is a bound on documents, not on medicines.",
      "- Reading: the per-reading figure (0.0077) is the most optimistic; the per-distinct-medicine figure (0.0283) is the more honest scale for a per-medicine statement, and the document-level figure (about 0.074) is the cautious one."]
c += ["", "### Reading the table\n",
      "- Medicine-level proportions (must_confirm, fully correct, interaction_ready, schedule_ready): the cluster interval is about 1.8 to 2.1 times as wide as the official Wilson interval. The Wilson intervals were too narrow; the cluster ones are the honest scale.",
      "- Wrong schedule among schedule_ready (2 of 285): the percentile bootstrap gives [0.000, 0.017], NARROWER than Wilson [0.002, 0.025]. With 2 events in 2 documents the percentile bootstrap is unreliable (about 13 percent of resamples contain no event at all and its lower bound is 0); do not read it as tighter evidence. At document level the events are in 2 of 40 documents (Wilson 95%: [0.014, 0.165]).",
      "- Explanation lines (n=255, 40 documents): Tamil and Hindi intervals are about as wide as Wilson (ratio 1.1); English is narrower (0.77) because it sits near 1.0 where a percentile interval is bounded by the data. The lines are clustered by document too (about 6 per document), but the dependence is weaker than for medicines."]
(OUT / "cluster_intervals.md").write_text("\n".join(c) + "\n", encoding="utf-8", newline="\n")
print("ok")
