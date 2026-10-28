# Stress set: extraction-mode results (Phase 7c-lite)

> **Stress set, authored, not tuned, not the test split.** 30 synthetic prescriptions written by the project, rendered in two conditions (`clean`, `photo`), 60 extractions. Small sample: every interval below is wide. Rendered synthetic documents only; no real photos, no usability sessions, no pharmacist or native-speaker review. Nothing here is a claim of accuracy, reliability, validation or safety.
> Protocol (written and committed before the run): [`STRESS_EXTRACTION_PROTOCOL.md`](STRESS_EXTRACTION_PROTOCOL.md). Source of every figure: `eval/results/stress-extraction-v1/` (`metrics.json`, `metrics.md`, `per_document.csv`, `run_manifest.json`, `SHA256SUMS`). The system under test was frozen and not changed.

## 1. Run facts and the stated deviation
| item | value |
|---|---|
| Run | `stress-extraction-v1`, 2026-10-28, 18:34:34 to 19:03:36 (1742 s, 29.0 min; estimate before the run about 35 min) |
| Calls | 60 model calls (30 documents x 2 conditions), 0 resumed from disk, 0 failed or skipped; per call mean 29.0 s, max 53.2 s (none near the 120 s stop limit) |
| Model / digest | `qwen3-vl:8b-instruct`, `0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319` (identical to `eval/final_test/model_pin.json`) |
| **Ollama version** | **running 0.40.11; pinned (official final run) 0.40.5.** Ollama updated itself. The pin file was not changed. The stress set was not part of the official run and its pass criteria are absolute, so **the stress numbers are not to be compared directly with the official `final-test-v1` numbers.** |
| GPU | `ollama ps` during the run: 10% CPU / 90% GPU at context 6144 (limit: at least 80% on GPU) |
| Settings | prompt `v1`, temperature 0, fixed seed, `num_ctx` 6144, `num_predict` 3000, image side 1280 (same code and defaults as the official run) |
| Code | protocol commit `c36ae82`; the new runner `eval/stress/run_stress_extraction.py` is additive (the Phase 7a runner is untouched) |

### Version sanity check (informative; nothing depends on it)
Five dev documents (the first five dev ids, `clean` render, dev split only) were re-extracted on 0.40.11 with the cache bypassed (`extract_document(use_cache=False)`; outputs in the gitignored `eval/runs/_version_sanity/`; the shared cache was only read). Compared with the cached outputs from the older version: **raw model output identical 1 of 5; normalised medicine lists and flags identical 2 of 5** (ds_018 and ds_020; ds_020 is also raw-identical). Differences:
- ds_006: one medicine lost a `conflict_timing_label` note (review level note to none).
- ds_008: several flag changes: three medicines lost or changed `conflict_timing_label`; two gained `name_not_in_quote` (note to must_confirm, interaction_ready and schedule_ready true to false); one gained `conflict_timing_label` and `name_not_in_quote` (none to must_confirm); one strength changed case (`18MCG` to `18mcg`).
- ds_011: a strength read as `30 MG/S ML` before and `30 MG/5 ML` now; the `unusual_strength` flag present before is absent now.

So extraction output is not reproducible across this version change (or across runs on this hardware; the two causes cannot be separated here), and flags that depend on the exact quote or strength text move with it. This is one more reason the stress numbers stand on their own.

## 2. Pass criteria (pre-registered; both conditions together, 60 readings)
| | criterion | result | passed |
|---|---|---|---|
| P1 | silent misses not covered by a flag = 0 | **0** of 204 ground-truth pair readings (Wilson 95% upper bound 0.019) | **pass** |
| P2 | no weekly or non-daily medicine is schedule_ready | **0** of 6 non-daily medicine readings (Wilson upper bound 0.39) | **pass** |
| P3 | wrong resolved_generic among interaction_ready = 0 | **0** of 113 interaction_ready readings (Wilson upper bound 0.033); 0 interaction_ready medicines without a ground-truth counterpart | **pass** |
| P4 | after the scripted overlay, every ground-truth interaction between extracted medicines is interaction_found at the right level | **204 of 204** (102 per condition) | **pass** |

All four pass, so there are no failing cases to list. These are counts on 30 authored documents (and the two renders of one document are not independent), not guarantees. Detection was perfect in both conditions (104 of 104 medicines, 0 hallucinated, raw and normalised), so P1 and P4 were never tested by a missing medicine.

## 3. Results per category
Pair counts are **ground-truth pairs**: pairs the engine reports as `interaction_found` when given the medicines by their printed formulary names (levels major/moderate/minor/unknown, DDInter-derived, aggregated counts only). "Found" = reported as `interaction_found` from the real extraction at the same level. "Strict silent" = ground-truth pair not reported as found (here all are flag-covered, so "silent not flag-covered" is 0). Overlay = after the scripted confirmation overlay (ground-truth names; testing only). 30 documents give wide intervals, and 78 of the 102 pairs per condition come from the three `long_list` documents.

Pooled per condition (Wilson 95% | document bootstrap 95%, seed 20261018, 2000 resamples):
- medicine precision and recall (raw and normalised): 104/104 each in `clean` and `photo`; Wilson [0.964, 1.000]; the bootstrap is degenerate at [1, 1] because there were no errors to resample.
- ground-truth pairs found as `interaction_found` from the real extraction: 38/102 = 0.373 in each condition; Wilson [0.285, 0.469]; document bootstrap [0.132, 0.631]. At the right level: 38 of 38 found.
- medicines needing confirmation (`must_confirm`): 48/104 clean, 47/104 photo (about 46%); `note` 6 and 7; none 50 and 50.

TABLES_HERE

## 4. Case review (descriptive; ids and short field excerpts only)
**4.1 Interactions not reported as `interaction_found`: 64 of 102 pairs in each condition.** All 64 were `not_checked_unconfirmed` (0 "medicine not extracted", 0 other statuses, 0 silent), so each was covered by a flag. The cause is a must_confirm reason on a medicine whose name was read correctly (detection 104/104); the pair is withheld until the user confirms. Causes counted per non-ready medicine in an unconfirmed pair: `clean` role_corrected 32, duplicate_name_fields 52, incomplete_quote 9, unusual_strength 2; `photo` duplicate_name_fields 54, role_corrected 23, incomplete_quote 13, unresolved_name 7, near_miss_name 7, unusual_strength 2.
- major pairs: st_01 (2 pairs; clean role_corrected on two medicines, photo duplicate_name_fields on the same two) and st_03 (3 pairs; duplicate_name_fields, plus incomplete_quote on one in clean). User-visible outcome: the two medicines carry the confirm banner and the result shows one aggregated line that pairs could not be checked until names are confirmed; the major interaction is NOT shown as an interaction line. After the user confirms it is shown (scripted overlay: 8 of 8). A user who skips confirmation never sees it.
- moderate pairs: st_04 (2; role_corrected on two, both conditions) and st_06 (2; duplicate_name_fields on two, incomplete_quote on one in clean). User-visible outcome: as above.
- supplement pair: st_09 (1; role_corrected on all three medicines, both conditions). User-visible outcome: as above.
- duplicate set: st_12 (2 pairs; duplicate_name_fields on two). User-visible outcome: pairs withheld as above; the duplicate notice itself still appeared (4.2).
- weekly set: st_17 (1 pair; role_corrected, plus non_daily_frequency on one). User-visible outcome: as above.
- unusual strength: st_19, st_20 (1 pair each; the `unusual_strength` flag withholds the pair by design; the engine does the same on perfect extraction, section 5). User-visible outcome: confirm banner on the unusual strength; the pair is shown after confirmation.
- long lists: st_25 (27 of 28 pairs withheld: six of eight medicines carry duplicate_name_fields), st_26 (15 of 25: role_corrected on three, incomplete_quote on one), st_27 (7 of 25: role_corrected on one in `clean`; in `photo` unresolved_name and near_miss_name on one medicine instead). User-visible outcome: 49 of 78 pairs withheld in `clean` across the three documents; the user sees found pairs one per line and ONE aggregated count line for the unconfirmed ones.

**4.2 Duplicates: none missed.** 3 of 3 ground-truth duplicate groups produced a duplicate notice in each condition (st_10, st_11, st_12). User-visible outcome: the "possible double dose, please confirm" notice appears; the medicine rows are also must_confirm.

**4.3 Weekly or non-daily: none scheduled.** 3 of 3 flagged `non_daily_frequency` in both conditions (st_16, st_17, st_18), 0 schedule_ready. User-visible outcome: no daily reminder is built for them; they sit in the confirm list.

**4.4 Eye drop with OD: handled.** `ambiguous_OD` fired on 3 of 3 in both conditions, 0 schedule_ready, 0 interaction_ready (timolol is not in the formulary, so it is also `unresolved_name`; documented). User-visible outcome: flagged, no daily schedule, "not checked".

**4.5 Unusual strength: flagged** 3 of 3 in both conditions (st_19, st_20, st_21). No other category produced an `unusual_strength` flag (3 flags in total per condition).

**4.6 Garbled names: flagged 3 of 3 in `clean`, 2 of 3 in `photo`.** The unflagged case is **st_15 `photo`**. Ground truth: `Ibuirofen 200 mg`. The model returned brand `Ibuprofen`, generic `Ibuprofen` and a source quote reading `Tab Ibuprofen 200 mg - ...`: it silently corrected the misspelling, in the quote as well, so no name rule or quote check can see it (the app holds no document text). Because the same name sits in both fields, `duplicate_name_fields` made the medicine must_confirm; that unrelated flag is the only reason it was not checked automatically (0 garbled medicines were interaction_ready). User-visible outcome: a confirm banner that reads as a field issue, with the name shown as "Ibuprofen", not as printed. If the user confirms as extracted, the scripted overlay produced 2 `interaction_found` lines that ground truth does not have; they belong to the real drug "Ibuprofen", while the paper says otherwise. This is the second documented quote-consistent misreading after ds_035 ([`FINAL_TEST_POSTHOC.md`](FINAL_TEST_POSTHOC.md)). In `clean` the same document was flagged (`unresolved_name`, `near_miss_name`).

**4.7 False alarms before the overlay: 0** (no `interaction_found` that ground truth does not have) in both conditions. After the overlay: `clean` 0, `photo` 2 (the st_15 case).

**4.8 Overlay equals ground-truth mode** (found pairs and levels equal to the oracle restricted to extracted medicines): 30 of 30 documents in `clean`, 29 of 30 in `photo` (st_15).

## 5. Comparison with ground-truth mode (extraction loss versus engine blindness)
Ground-truth mode ([`eval/results/stress-safety-gt-v1/`](../eval/results/stress-safety-gt-v1/metrics.md), Phase 7a) feeds the correct medicine lists to the same engine: 162 pair cells, **100 `interaction_found`, 21 `not_checked_unconfirmed` (name, weekly, unusual-strength and eye-drop flags), 41 `not_checked_no_record`**. Reading the two modes together, for the 102 ground-truth pairs of each extraction condition:
- **38 found** (37%) from the real extraction.
- **2 withheld by the engine even with perfect extraction** (the `unusual_strength` pairs in st_19 and st_20): engine behaviour, not extraction.
- **62 withheld by flags raised on correctly detected medicines** (role_corrected, duplicate_name_fields, incomplete_quote, and in `photo` name flags): the way the model fills the fields triggers a must_confirm reason, and the frozen rules then withhold the pair. This is extraction/normalisation friction, not a missed medicine, and it is what costs the shown-interaction count.
- **Engine blindness is a separate loss, not counted above by construction:** 41 of 162 pair cells (25%) have no record even with perfect extraction, and the app reports them only as "not checked". The stress set was built so each designed pair has a record, so it understates the real share (the formulary has records for 998 of 2,145 pairs, [`DDINTER_COVERAGE.md`](DDINTER_COVERAGE.md)).

## 6. What this changes in how we word the headline safety claim
1. Do not write "the app finds interactions" or "no silent misses". Write: "On 30 authored stress prescriptions (two renders each, 204 pair readings), every interaction the engine finds with perfect extraction that was not displayed was held back behind a confirmation flag (0 of 204 unflagged; 95% upper bound 1.9%)."
2. Always say how much was held back: "From the real extraction, 38 of 102 such pairs per condition (37%) were shown immediately; 64 were withheld until names or schedules were confirmed." The safety layer depends on the user doing the confirmation and on comparing the extracted list with the paper.
3. State the engine's blindness beside it: pairs without a record are only "not checked", never "no interaction".
4. Do not extend the 104/104 detection result to real photos: the renders use one font family with a mild simulated photo, and the model ran on 0.40.11, not the pinned version.
5. A quote-consistent misreading (st_15 photo here; ds_035 in the official test) is invisible to every rule. The claim "garbled names are flagged" must read "flagged in 5 of 6 readings; one was silently corrected by the model and caught only by an unrelated flag".
6. All four criteria passed on 30 documents; that is a regression check on designed cases, not a measure of how often it holds in use.

## 7. Defects and risks in frozen code (reported only; nothing changed)
- **Confirmation load:** about 46% of medicines are must_confirm on these prescriptions; `duplicate_name_fields` and `role_corrected` fire on correctly read medicines and withhold 62 of 102 pairs. Idea (not applied): do not require confirmation when identical brand and generic fields resolve exactly and appear in the quote; needs a new freeze and a new evaluation.
- **Silent correction of a garbled name** (st_15 photo, 4.6). Idea: a second independent reading of the name from the image; an instruction to copy names exactly would be an untested extraction change.
- **Reproducibility:** outputs differ between Ollama versions or runs (section 1); a pinned stack is needed for any official re-run.
- The Phase 7a `--mode extraction` in `eval/stress/run_safety_stress.py` is a minimal stub (no per-document table, no overlay step); the new `eval/stress/run_stress_extraction.py` does the work and leaves it untouched (recorded in `DECISIONS.md`).

## 8. What is not claimed
No clinical validation; no real-world accuracy; no real-photo or usability result; no pharmacist or native-speaker review; no comparison with `final-test-v1` (different Ollama version, different set).
