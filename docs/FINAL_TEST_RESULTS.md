# Final test results: final-test-v1 (official, one run)

Phase 7b write-up. Source of every number below: `eval/results/final-test-v1/` (`metrics.json`, `per_document.csv`, `figures.json`, `skipped.json`, `run_manifest.json`; read-only, checksums verified). Protocol: `docs/FINAL_TEST_PROTOCOL.md`. Independent recomputation of the extraction figures: `scripts/verify_final_results.py` (see section 10). Run date: 2026-10-20 (02:35:39 to 05:00:28 local time, 8685.7 s).

## 1. What was run, and what it shows

The 40 held-out TEST documents of the project's synthetic dataset (generated and rendered by this project) were each processed in five conditions (`text`, `clean`, `scan`, `photo`, `poor`): 200 document-condition pairs and 795 medicine mentions (159 per condition), by the local model `qwen3-vl:8b-instruct` on one machine, once. The explanation pipeline (English, Tamil, Hindi) ran on the `clean` condition (255 free-text lines; the 159 medicine lines are fixed templates). Nothing was skipped.

What this shows: how this exact system, frozen before the run (tag `freeze-pre-test`), behaves on documents it was not tuned on. What it does not show: see section 9. Two limits matter most.
- The test documents come from the SAME generator as the dev documents (same case templates, name lists and layouts). They are held out from tuning but are not independent of the generator's style.
- 40 documents is small. Wilson intervals treat medicine mentions as independent although they cluster within documents, so they are somewhat too narrow; the bootstrap intervals (which resample documents) do not have that problem.

## 2. Extraction (medicine matching), per condition and pooled

"Raw" is the model output as returned. "Normalised" is after the rule layer, in `app` mode (model output only, no document text). Precision, recall and the invented-value rate carry Wilson 95 percent intervals; F1 and the fully-correct rate carry bootstrap 95 percent intervals over documents (2000 resamples, fixed seed). "Fully correct" = matched medicines whose every field is right (denominator: matched medicines). "Invented-value rate" = fields the document leaves empty that the model filled (denominator: empty fields). "Hallucinated" = predicted medicines that match no ground-truth medicine (count). Pooled rows combine the five conditions (bootstrap unit: the document with all its conditions). The column "medicine mentions" is the ground-truth count.

### Raw
| condition | medicine mentions (n) | precision | recall | F1 (bootstrap) | fully correct (bootstrap) | hallucinated | invented-value rate |
|---|---|---|---|---|---|---|---|
| text | 159 | 0.969 [0.928, 0.987] | 0.969 [0.928, 0.987] | 0.969 [0.929, 1.000] | 0.208 (32/154) [0.135, 0.280] | 5 | 0.357 (76/213) [0.295, 0.423] |
| clean | 159 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.321 (51/159) [0.234, 0.408] | 0 | 0.302 (67/222) [0.245, 0.365] |
| scan | 159 | 0.987 [0.955, 0.997] | 0.987 [0.955, 0.997] | 0.987 [0.968, 1.000] | 0.306 (48/157) [0.215, 0.402] | 2 | 0.298 (65/218) [0.241, 0.362] |
| photo | 159 | 0.969 [0.928, 0.987] | 0.969 [0.928, 0.987] | 0.969 [0.934, 0.994] | 0.247 (38/154) [0.163, 0.336] | 5 | 0.349 (76/218) [0.288, 0.414] |
| poor | 159 | 0.994 [0.965, 0.999] | 0.994 [0.965, 0.999] | 0.994 [0.980, 1.000] | 0.228 (36/158) [0.154, 0.314] | 1 | 0.339 (75/221) [0.280, 0.404] |
| all | 795 | 0.984 [0.972, 0.990] | 0.984 [0.972, 0.990] | 0.984 [0.972, 0.993] | 0.262 (205/782) [0.200, 0.328] | 13 | 0.329 (359/1092) [0.301, 0.357] |

### Normalised (after rules)
| condition | medicine mentions (n) | precision | recall | F1 (bootstrap) | fully correct (bootstrap) | hallucinated | invented-value rate |
|---|---|---|---|---|---|---|---|
| text | 159 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.937 (149/159) [0.895, 0.974] | 0 | 0.022 (5/222) [0.010, 0.052] |
| clean | 159 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.899 (143/159) [0.839, 0.950] | 0 | 0.013 (3/222) [0.005, 0.039] |
| scan | 159 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.887 (141/159) [0.821, 0.940] | 0 | 0.018 (4/222) [0.007, 0.045] |
| photo | 159 | 0.994 [0.965, 0.999] | 0.994 [0.965, 0.999] | 0.994 [0.980, 1.000] | 0.880 (139/158) [0.819, 0.932] | 1 | 0.023 (5/220) [0.010, 0.052] |
| poor | 159 | 1.000 [0.976, 1.000] | 1.000 [0.976, 1.000] | 1.000 [1.000, 1.000] | 0.837 (133/159) [0.778, 0.892] | 0 | 0.032 (7/222) [0.015, 0.064] |
| all | 795 | 0.999 [0.993, 1.000] | 0.999 [0.993, 1.000] | 0.999 [0.996, 1.000] | 0.888 (705/794) [0.845, 0.927] | 1 | 0.022 (24/1108) [0.015, 0.032] |

### Per-field accuracy over matched medicines (pooled; 782 raw / 794 normalised matched medicines; Wilson)
| field | raw, pooled | normalised, pooled |
|---|---|---|
| strength | 0.978 [0.966, 0.986] | 0.979 [0.966, 0.987] |
| form | 0.992 [0.983, 0.997] | 0.992 [0.984, 0.997] |
| dose | 0.955 [0.938, 0.968] | 0.956 [0.939, 0.968] |
| times_per_day | 0.943 [0.924, 0.957] | 0.989 [0.979, 0.994] |
| timing_label | 0.734 [0.702, 0.764] | 0.990 [0.980, 0.995] |
| is_prn | 0.989 [0.978, 0.994] | 0.991 [0.982, 0.996] |
| duration_days | 0.971 [0.956, 0.980] | 0.998 [0.991, 0.999] |
| brand_name | 0.495 [0.460, 0.530] | 0.979 [0.966, 0.987] |
| generic_name | 0.738 [0.706, 0.767] | 0.985 [0.974, 0.991] |

Reading it: the model finds the medicines almost always (raw recall 0.984 pooled), but the raw fully-correct rate is low (0.262) because two fields are usually wrong or filled from the wrong place (brand name 0.495, timing label 0.734). The rule layer repairs most of this (fully correct 0.888 after rules). Quote checks (raw, pooled): strict quote rate 0.964, 9 quotes failed on digits, 44 on similarity. Follow-up and red-flag recall and precision were 1.000 raw; follow-up days accuracy 0.843.

## 3. Names, flags, readiness (app mode)

Denominator is the number of medicine mentions in the condition (159; pooled 795). A "name error remaining" is a medicine whose resolved name is wrong after the rules; "unflagged" means it carries no confirmation flag.
| condition | medicines | at must_confirm (Wilson) | name errors remaining | of which unflagged | timing errors remaining | of which unflagged | interaction_ready | wrong resolved_generic | schedule_ready | wrong schedule |
|---|---|---|---|---|---|---|---|---|---|---|
| text | 159 | 76 = 0.478 [0.402, 0.555] | 1 | 1 | 1 | 0 | 83 | 0 | 61 | 0 |
| clean | 159 | 76 = 0.478 [0.402, 0.555] | 2 | 0 | 2 | 0 | 83 | 0 | 60 | 0 |
| scan | 159 | 74 = 0.465 [0.390, 0.543] | 4 | 0 | 2 | 1 | 85 | 0 | 64 | 2 |
| photo | 159 | 87 = 0.547 [0.470, 0.623] | 7 | 0 | 2 | 0 | 72 | 0 | 54 | 0 |
| poor | 159 | 93 = 0.585 [0.507, 0.659] | 12 | 0 | 1 | 0 | 66 | 0 | 46 | 0 |
| all | 795 | 406 = 0.511 [0.476, 0.545] | 26 | 1 | 8 | 1 | 389 | 0 | 285 | 2 |

- Wrong `resolved_generic` among `interaction_ready` medicines: 0 of 389 (target met; Wilson 95 percent upper bound 0.010).
- Wrong schedules among `schedule_ready` medicines: **2 of 285** (both in `scan`: 2 of 64; pooled Wilson [0.002, 0.025]). The target was 0, so this is a miss. `metrics.json` records the count but not the cases, and finding them would require opening test ground truth, which this write-up did not do. The cases are therefore not described here.
- Name errors remaining: 26 of 795 (3.3 percent), of which 1 unflagged (condition `text`).
- One timing error is unflagged (condition `scan`). It may be linked to the wrong schedules above, but the results files do not say.
- Review-level load: 406 of 795 medicines (0.511, Wilson [0.476, 0.545]) are at `must_confirm`, so about half of all medicines would ask the user to confirm something. It is higher in the image conditions (photo 0.547, poor 0.585) than in `text` and `clean` (0.478 each).

## 4. Dev versus test

Dev values are from the committed dev results (20 documents; rules, prompts and templates were tuned on them, so dev is expected to look better). The last column asks whether the DEV point value lies outside the TEST 95 percent interval of the same metric (F1 and fully-correct: bootstrap; other proportions: Wilson; free-text lines: Wilson on 255 lines). This is a rough descriptive check, not a hypothesis test: dev has its own uncertainty (20 documents) and the Wilson intervals are optimistic.
| metric | dev (20 docs) | test (40 docs) | test minus dev | test 95% interval | dev value outside the test interval? |
|---|---|---|---|---|---|
| medicine F1, raw | 0.983 | 0.984 | +0.000 | [0.972, 0.993] | no |
| fully-correct medicine rate, raw | 0.307 | 0.262 | -0.045 | [0.200, 0.328] | no |
| invented-value rate, raw | 0.286 | 0.329 | +0.043 | [0.301, 0.357] | yes |
| timing label field, raw | 0.729 | 0.734 | +0.005 | [0.702, 0.764] | no |
| brand name field, raw | 0.673 | 0.495 | -0.178 | [0.460, 0.530] | yes |
| medicine F1, normalised | 0.998 | 0.999 | +0.001 | [0.996, 1.000] | no |
| fully-correct medicine rate, normalised | 0.811 | 0.888 | +0.076 | [0.845, 0.927] | yes |
| invented-value rate, normalised | 0.056 | 0.022 | -0.035 | [0.015, 0.032] | yes |
| timing label field, normalised | 0.991 | 0.990 | -0.001 | [0.980, 0.995] | no |
| brand name field, normalised | 0.979 | 0.979 | +0.000 | [0.966, 0.987] | no |
| share of medicines at must_confirm | 0.462 | 0.511 | +0.049 | [0.476, 0.545] | yes |
| name errors remaining, unflagged | 0 | 1 | +1 | counts, no interval | n/a (counts) |
| wrong resolved_generic among interaction_ready | 0 | 0 | +0 | counts, no interval | n/a (counts) |
| silent misses, strict | 3 | 3 | +0 | counts, no interval | n/a (counts) |
| silent misses not covered by a flag | 0 | 0 | +0 | counts, no interval | n/a (counts) |
| false alarms | 0 | 0 | +0 | counts, no interval | n/a (counts) |
| share of free-text lines shown in en | 1.000 | 0.996 | -0.004 | [0.978, 0.999] | yes |
| share of free-text lines shown in ta | 0.252 | 0.239 | -0.013 | [0.191, 0.295] | no |
| share of free-text lines shown in hi | 0.807 | 0.725 | -0.082 | [0.668, 0.777] | yes |

Dev values outside the test interval: invented-value rate, raw; brand name field, raw; fully-correct medicine rate, normalised; invented-value rate, normalised; share of medicines at must_confirm; share of free-text lines shown in en; share of free-text lines shown in hi. Plainly:
- Some gaps go in the direction "test is worse than dev", as expected after tuning on dev: the raw brand-name field (0.673 on dev, 0.495 on test), the raw invented-value rate (0.286 against 0.329) and the share of medicines at `must_confirm` (0.462 against 0.511).
- Others go the other way: the normalised fully-correct rate is HIGHER on test (0.888 against 0.811) and the normalised invented-value rate lower (0.022 against 0.056). We did not investigate; it may mean the dev set contained harder cases or it may be sampling. It should not be read as an improvement.
- The one count that worsened is name errors remaining without a confirmation flag: 0 on dev, 1 on test (one medicine).
- Free-text lines shown in Hindi fell from 0.807 to 0.725. English lines shown are listed only because dev was 1.000 (a Wilson interval on 255 lines cannot contain 1.000 when one line fell back); the difference is one line.
- Medicine F1 (raw and normalised), the timing-label field, the normalised brand-name field, Tamil lines shown, and the safety counts do not differ beyond the test interval.

## 5. Safety results (aggregated counts; no pair-level interaction levels are published)

Definitions are those of `eval/phase4_safety.py` and `docs/SAFETY.md`. The engine ran on the normalised extraction in `app` mode with the local DDInter-derived store (partial: groups A, B, D, H, L, P, R, V) plus the 16 author-checked supplement pairs. The ground truth has 262 medicine pairs per condition (195 with a known interaction, 67 with none recorded).
| condition | pairs (n) | interaction_found | not_checked_unconfirmed | not_checked_no_record | share not checked |
|---|---|---|---|---|---|
| text | 262 | 41 | 197 | 24 | 0.844 |
| clean | 262 | 55 | 186 | 21 | 0.790 |
| scan | 262 | 54 | 185 | 23 | 0.794 |
| photo | 262 | 39 | 202 | 21 | 0.851 |
| poor | 262 | 30 | 216 | 16 | 0.885 |

- **Strict silent misses: 3** (over 1310 pair-condition cells), of which **0 are not covered by a flag** (all 3 involve a medicine that carries a confirmation flag). "Strict" means a known pair that is not reported as `interaction_found`, which includes an evaluator-side failure to match a garbled name (see `docs/SAFETY.md`). The results file does not say in which condition or document they lie. That dev also had 3 is a coincidence of counts that could not be examined without opening test cases.
- False alarms: 0. Duplicate-medicine flags: 0 (ground truth also has 0 duplicates, so duplicate detection was not exercised).
- Missed entirely (medicine or interaction with no corresponding output at all): 0 in every condition.
- Share of pairs not checked: 0.790 (`clean`) to 0.885 (`poor`). Most are `not_checked_unconfirmed` (names the user must confirm first): 753 downgrades in total.
- The application never says "no interaction" or "safe". A high not-checked share is the system failing closed, not a finding about the medicines.
- `interaction_ready` 389 of 795 and `schedule_ready` 285 of 795 medicines.

## 6. Explanation pipeline (condition `clean`, 40 documents)

"Verified" = all deterministic checks pass AND the judge says supported (model-written lines only); otherwise the original English is shown with a notice. A further 0.059 of lines (15) are library phrases shown without a model call. The same local model writes and judges, so the judge is weak. No Tamil or Hindi speaker has reviewed any text; all Tamil and Hindi strings are `draft_unreviewed` machine drafts, and "verified" means "passed software checks", NOT "correct". Wilson 95 percent intervals; denominators are lines.
| language | all lines (n=255) | advice (n=118) | follow-up (n=42) | warning (n=95) | fallback to original English |
|---|---|---|---|---|---|
| en | 0.937 (239/255) [0.901, 0.961] | 0.873 (103/118) [0.801, 0.921] | 0.976 (41/42) [0.877, 0.996] | 1.000 (95/95) [0.961, 1.000] | 0.004 (1/255) |
| ta | 0.180 (46/255) [0.138, 0.232] | 0.254 (30/118) [0.184, 0.340] | 0.286 (12/42) [0.172, 0.436] | 0.042 (4/95) [0.016, 0.103] | 0.761 (194/255) |
| hi | 0.667 (170/255) [0.607, 0.722] | 0.754 (89/118) [0.669, 0.823] | 0.762 (32/42) [0.615, 0.865] | 0.516 (49/95) [0.417, 0.614] | 0.275 (70/255) |

- English: 239 of 255 lines verified; 1 fell back (forbidden additions).
- Tamil is the weak spot: 46 of 255 verified, 194 fall back to English. Judge verdicts (line counts, over all model lines): contradicts 92, omits information 77, adds information 12, supported 51, no verdict 23. Deterministic failures: forbidden additions 8, drug names 5, no model text 8.
- Hindi: 170 verified, 70 fall back. Judge verdicts: supported 177, contradicts 27, omits information 22, adds information 14. Warning lines verify least often (0.516 Hindi, 0.042 Tamil), so safety-relevant warnings are mostly shown in original English in Tamil.
- Calls: 320 model calls, 2 failed (`context_truncated`), 402107 tokens, 3235 s of model time.
- Readability of the English output (Flesch-Kincaid grade, median): source text 4.00, plain-English output 3.67 (English only).
- Medicine lines are fixed templates (no model) and are not part of these shares.

## 7. Operational numbers

| condition | attempted | scored | skipped | latency median s | latency p95 s |
|---|---|---|---|---|---|
| text | 40 | 40 | 0 | 26.5 | 40.2 |
| clean | 40 | 40 | 0 | 28.7 | 41.8 |
| scan | 40 | 40 | 0 | 29.0 | 42.2 |
| photo | 40 | 40 | 0 | 28.9 | 42.0 |
| poor | 40 | 40 | 0 | 29.4 | 42.2 |
| all | 200 | 200 | 0 | 27.6 | 41.8 |

Skipped: none (`skipped.json` is an empty list; 200 of 200 extraction calls and 40 of 40 explanation documents completed). Timings come from one machine (RTX 4060 8 GB, Ollama 0.40.5, pinned model digest) and say nothing about other hardware. Total 8685.7 s (about 2 h 25 min).

## 8. POST-HOC: descriptive error analysis

Labelled post-hoc: done after seeing the results, from the aggregated results files and `per_document.csv` only. No test documents, ground truth or renders were opened, so this says WHERE errors occur (condition, field, document id), not what is on the page. Nothing in the system was changed in response. Case templates are not in the results files and were not looked up, so concentration by template is not reported.

1. **Brand name filled from the wrong place (raw).** 276 of 313 brand-name fields that the document leaves empty were filled (pooled raw), 269 of them classed as role confusion (the value is another name on the document). Raw brand-name accuracy 0.495. After the rules: 5 of 314 (4 made up). Present in every condition (raw invented-value rate 0.298 to 0.357 by condition).
2. **Timing label wrong (raw).** Raw accuracy 0.734 pooled ([0.702, 0.764]) against 0.990 after rules; the rules raised 167 timing-label conflict flags. This is the main reason the raw fully-correct rate is 0.262.
3. **Generic name filled wrongly (raw).** 62 of 211 empty generic-name fields filled (role confusion 40, made up 20, in document 2); after rules 3 of 215 (all made up). Raw accuracy 0.738; normalised 0.985.
4. **Medicines read too differently to match, and names wrong in image conditions.** Unmatched ("hallucinated") medicines: 13 raw, 1 normalised. The 13 raw are each paired with a missed medicine (13 false positives and 13 false negatives): a medicine read so differently that it does not match. By condition: `text` 5, `photo` 5, `scan` 2, `poor` 1. By document: ds_010 (photo 2, poor 1), ds_024 (text 2), rx_009 (text 2), and one each in ds_028, ds_031, rx_002 (photo), ds_038, ds_039 (scan), rx_020 (text). The one normalised case is ds_028 in `photo`. Name errors remaining after the rules, by condition: text 1, clean 2, scan 4, photo 7, poor 12 (26 in total); they rise as image quality falls.
5. **Tamil (and less so Hindi) text not passing verification.** Tamil: 194 of 255 lines fell back (judge: contradicts 92, omits 77, adds 12, over model lines). Hindi: 70 fell back (contradicts 27, omits 22, adds 14). The judge is the same model as the writer, so these may be real translation problems or judge errors; they cannot be told apart without native reviewers.

Also noted: the 2 wrong schedules in `scan`; the normalised fully-correct rate is lowest in `poor` (0.837) and highest in `text` (0.937); 15 of 40 documents have every matched medicine fully correct after rules in all five conditions.

Ideas for future work (NOT applied and NOT part of the official system): check that brand and generic fields never hold the same value before the rule layer; a second reader pass for medicine names in photo and poor conditions; inspect the two wrong schedules by hand in a new, labelled run; have a native speaker review Tamil failures before anything is tuned.

## 9. What is not claimed

- Not clinical validation; no claim about patients, doctors or use in care.
- No claim about real documents or real phone photos (a separate real-photo test is Phase 7c).
- No claim that medicine information, explanations or interaction data are correct: the interaction store is a partial download plus an author-checked supplement that no pharmacist has reviewed, and no native speaker has reviewed any Tamil or Hindi text.
- The words accurate, reliable and validated are not used for this system.
- No claim that these numbers hold for other models, hardware, generators or document styles.
- Zero wrong `resolved_generic` among 389 `interaction_ready` medicines and zero false alarms are counts on this sample only, not guarantees.
- Differences smaller than the intervals are not described as differences, and no figure was selected after seeing the results.

## 10. Verification and integrity

- `sha256sum -c SHA256SUMS` in `eval/results/final-test-v1/`: all 6 files OK. The only commits after the tag `freeze-pre-test` before this write-up were the two pin files and the results folder.
- Pins equal the run: Ollama 0.40.5, model `qwen3-vl:8b-instruct`, digest `0533d743...c96319`; the freeze-manifest hash in `run_manifest.json` equals the file on disk. Settings (num_ctx 6144, num_predict 3000, image side 1280, seed 42, temperature 0, prompts v1 and v2) come from the freeze manifest; the run manifest does not repeat them.
- `eval/test_runs.log`: one pin entry, one official run, one refused second attempt (copy in `eval/results/final-test-v1-audit/`).
- `scripts/verify_final_results.py` recomputed precision, recall, F1, fully-correct rate, hallucinated count, invented-value rate and their intervals (Wilson and bootstrap), both variants, per condition and pooled, from `per_document.csv`: identical to `metrics.json` except 3 bootstrap bounds that differ by 0.0001 (`eval/matching.py` rounds precision and recall before computing F1). It also checked that pooled flag counts are the sums of the conditions, that shares and their intervals follow from the counts, and that attempted = scored + skipped. Name errors, silent misses, safety and explanation figures cannot be recomputed from the CSV (it holds medicine counters only), so they are quoted from `metrics.json`.

## 11. Wording the project may use

Each sentence keeps its scope and interval.
1. "On 40 held-out synthetic test documents (200 document-condition pairs, 795 medicine mentions) the local model found the medicines with raw precision and recall of 0.984 (95% Wilson [0.972, 0.990]) and, after the rule layer, 0.999 [0.993, 1.000]; 13 and 1 predicted medicines respectively matched no ground-truth medicine."
2. "Raw output was fully correct for 205 of 782 matched medicines (0.262, bootstrap 95% [0.200, 0.328]); after the rule layer for 705 of 794 (0.888, [0.845, 0.927])."
3. "After the rule layer 26 of 795 medicine names were wrong, 25 of them carrying a confirmation flag; none of the 389 medicines marked ready for interaction checks had a wrong resolved generic name; 2 of 285 schedule-ready medicines had a wrong schedule (both in the scan condition)."
4. "About half of the medicines (406 of 795, 0.511 [0.476, 0.545]) ask the user for a confirmation."
5. "The interaction check had 3 strict misses over 1310 pair cells, all involving a medicine that carried a confirmation flag, and 0 false alarms; 79 to 89 percent of pairs were reported as not checked rather than as a result."
6. "Of 255 free-text lines, 239 in English, 46 in Tamil and 170 in Hindi passed the software checks; the others are shown in the original English or come from the phrase library. The same model writes and judges, and no native speaker has reviewed the text."
7. "Results are for synthetic documents rendered by this project, from the same generator as the dev set, on one machine, in one run; they are not clinical validation."
