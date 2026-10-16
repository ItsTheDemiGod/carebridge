# Stress set (Phase 3e)

`stress_set.json` measures the verification judge and the English simplifier on data they have never seen. It is **authored from general knowledge of discharge wording only** (no dev or test document, no ground-truth file, no earlier model output was used) and is **never shipped to users**: no line from it may appear in a prompt, a template or the phrase library.

| part | size | purpose |
|---|---|---|
| `english_pairs` | 20 correct paraphrases + 20 subtly wrong (number_changed x3, negation_flipped x2 + negation_dropped x1, timing_swapped x2, clause_dropped x3, invented_advice x3, urgency_softened x2, item_merged x2, unit_changed x2) | false-reject rate and per-type detection of the deterministic checks and the judge |
| `simplify_sources` | 15 harder, clinical-sounding lines (grade 8 to 12) with numbers, negations and abbreviations; no reference answer | does Prompt A simplify, and does it lose or add facts? |
| `translation_pairs.ta / .hi` | 6 correct + 6 wrong each (number_changed, negation_flipped, timing_swapped, clause_dropped, invented_advice, urgency_softened; none involve drug names) | back-translation + judge on Tamil and Hindi |

**The Tamil and Hindi candidates were written by Claude Code and are NOT native-checked.** They only test whether the judge detects obvious faults and accepts clearly correct text; they say nothing about translation quality. The samples are small, so rates are rough (one Tamil/Hindi item moves a rate by 17 points).

Run: `python -m eval.stress.run_stress --run-id stress-v1` (local Ollama; resumable from `data/cache/narrative`). Results: `eval/results/stress-v1/metrics.{json,md}`; raw outputs in `eval/runs/stress-v1/` (gitignored).
