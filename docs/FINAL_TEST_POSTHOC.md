# Final test: post-hoc case review (Phase 7b-posthoc)

**POST-HOC. Descriptive only. Not an official result.** Written after the official run `final-test-v1` (2026-10-20) and after its write-up (`docs/FINAL_TEST_RESULTS.md`). The system is frozen: nothing was changed in response (no prompt, rule, threshold, formulary, template, normalisation or code edit), no model was called, no re-run was made, and no new official number exists. Looking at specific test cases was allowed for this phase because it is descriptive; findings below are limitations or future work, none applied. The official folder `eval/results/final-test-v1/` (and its audit copy) was only read; its SHA256SUMS still verify. All outputs are in `eval/results/final-test-v1-posthoc/`; scripts are `scripts/posthoc_*.py`. Test documents are synthetic; only ids, conditions and field-level excerpts appear here.

## 1. Freeze-drift proof for templates.json

`scripts/freeze_manifest.py verify` reports exactly one drifted file out of 98 hashed files: `data/templates/templates.json`. Against the tag `freeze-pre-test` (`scripts/posthoc_freeze_drift.py`, output `freeze_drift.md`): 698 -> 800 strings, **102 added keys, all under `ui.*`**; 0 removed; 2 changed, both `ui.*` testing-page sentences that said the final test "has not been run yet" (`ui.testing.method.test`, `ui.testing.limits.l2`); no other top-level field changed; nothing outside `ui.*` changed. The pipeline (extraction, normalisation, explanation, safety) reads none of these keys, so the drift is on the page-text side only.

## 2. The specific cases

Detail in `eval/results/final-test-v1-posthoc/cases.md`. The cases reproduce the official counts exactly.

- **(a) 2 wrong schedules (both `scan`, both abbreviated discharge summaries).** ds_035: the document says `SOS` for Ventolin, the model read `OD`; the derived schedule is once daily with unspecified timing, with no flag (the quote agrees with the misreading, and in app mode there is no document text to compare it with). ds_038: the document says `BD PC` for Augmentin 625 mg, the model's quote dropped `PC`; times per day (2) is right but the timing is "unspecified" instead of "after meals"; a `conflict_timing_label` note fired (level "note", not "must confirm") and the medicine stayed schedule_ready. *User-visible outcome: a daily reminder time for an as-needed inhaler with no warning at all, and spread-out dose times instead of after-meal times for Augmentin with only a "Note" marker.*
- **(b) 3 strict silent misses.** One document and condition: ds_028 `photo`, pairs of the first medicine with each of the other three (1 moderate, 2 unknown). The first row was read as "Performin", which the evaluator could not pair with Metformin. All 3 are flag-covered: the row is must_confirm and not interaction_ready, so its pairs are `not_checked_unconfirmed`. *User-visible outcome: the Performin card asks for confirmation and its pairs are counted as not checked until the name is confirmed; no interaction is shown or called safe.*
- **(c) 1 unflagged name error (`text`).** ds_024: the model put the whole line "cap. racecadotril 100 mg" in the brand field and left the generic empty; the normaliser resolved the formulary generic exactly, so no flag fired. Identity (Racecadotril), strength, frequency and duration are right; the evaluator counts it because the brand field differs from ground truth (empty). *User-visible outcome: the right medicine with correct times, but the brand slot shows the printed line instead of nothing; no flag and no wrong identity.* ("1 unflagged wrong name" therefore overstates it: it is an unflagged brand-field placement error with the identity correct.)
- **(d) 1 remaining hallucinated medicine.** ds_028 `photo`: the "Performin" row of (b) (generic "Glimipride" copied from the next row, 500 mg, dose line matching the Metformin row). A misread, not an invented drug; the true Metformin counts as missed. Flags `unresolved_name`, `near_miss_name`, `name_not_in_quote`; must_confirm. *User-visible outcome: a must-confirm card for an unrecognised name that cannot be scheduled or checked until the user picks the medicine from the list.*
- **(e) 2 `context_truncated` calls.** Both Tamil translation calls: ds_024 (4 lines: follow_up-0, advice-0..2) and rx_019 (4 lines: follow_up-0, advice-0, advice-1, warning-0). Confirmed in the cached records and `services/explain.py`: status `original_only`, display `original_with_notice`. *User-visible outcome: in Tamil those 8 lines appear in the original English with the Tamil notice that no automatic explanation is available.*
- **(f) ds_010, ds_024, rx_009** (7 of the 13 raw unmatched medicines): t2dm_htn/clean/discharge summary, gastro/messy/discharge summary, cap/messy/prescription. Common pattern: brand, generic and form text in one field, which the name matcher scores as a poor match; the rule layer separates them. *User-visible outcome: none of the 7 raw misses reaches the user as a missing medicine; the raw numbers describe the model output before the rule layer.*

## 3. Breakdown by difficulty and case template (test and dev)

Test: 16 clean, 11 abbreviated, 13 messy documents. Dev: 5 clean, 9 abbreviated, 6 messy.

Pooled over the five conditions; medicine mentions = ground-truth medicines x 5 readings. Rates are ratios of sums (fully correct: matched medicines). Dev figures are recomputed from the cached dev raw outputs (`eval/runs/dev-ollama-v1`) with the same code as the test; the pooled dev values equal the committed ones (fully correct after rules 0.8115, brand name raw 0.6731). Cells with few documents are noisy: read the `docs` column.

#### TEST split by difficulty

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 40 | 795 | 0.262 | 0.888 | 0.984 | 0.999 | 0.511 | 26 (1) | 0.495 |
| abbreviated | 11 | 225 | 0.302 | 0.782 | 0.987 | 1.000 | 0.422 | 8 (0) | 0.635 |
| clean | 16 | 355 | 0.251 | 0.966 | 0.986 | 0.997 | 0.623 | 12 (0) | 0.317 |
| messy | 13 | 215 | 0.238 | 0.870 | 0.977 | 1.000 | 0.419 | 6 (1) | 0.643 |

#### TEST split by document type

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 40 | 795 | 0.262 | 0.888 | 0.984 | 0.999 | 0.511 | 26 (1) | 0.495 |
| discharge_summary | 26 | 520 | 0.237 | 0.873 | 0.983 | 0.998 | 0.517 | 23 (1) | 0.477 |
| prescription | 14 | 275 | 0.310 | 0.916 | 0.986 | 1.000 | 0.498 | 3 (0) | 0.528 |

#### TEST split by case template

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 40 | 795 | 0.262 | 0.888 | 0.984 | 0.999 | 0.511 | 26 (1) | 0.495 |
| appendix | 4 | 80 | 0.392 | 0.988 | 0.988 | 1.000 | 0.550 | 0 (0) | 0.405 |
| cap | 4 | 80 | 0.237 | 0.875 | 0.950 | 1.000 | 0.338 | 4 (0) | 0.566 |
| cardiac | 5 | 150 | 0.273 | 0.967 | 1.000 | 1.000 | 0.540 | 2 (0) | 0.340 |
| copd | 3 | 90 | 0.211 | 0.789 | 1.000 | 1.000 | 0.667 | 3 (0) | 0.544 |
| dengue | 8 | 120 | 0.152 | 0.892 | 0.983 | 1.000 | 0.392 | 1 (0) | 0.669 |
| fracture | 1 | 20 | 0.050 | 0.550 | 1.000 | 1.000 | 0.850 | 1 (0) | 0.600 |
| gastro | 6 | 95 | 0.409 | 0.926 | 0.979 | 1.000 | 0.432 | 2 (1) | 0.602 |
| t2dm_htn | 6 | 120 | 0.276 | 0.866 | 0.967 | 0.992 | 0.533 | 12 (0) | 0.431 |
| uti | 3 | 40 | 0.175 | 0.775 | 1.000 | 1.000 | 0.625 | 1 (0) | 0.375 |

#### DEV split by difficulty

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 20 | 420 | 0.307 | 0.811 | 0.983 | 0.998 | 0.462 | 14 (0) | 0.673 |
| abbreviated | 9 | 190 | 0.246 | 0.810 | 0.984 | 1.000 | 0.479 | 7 (0) | 0.706 |
| clean | 5 | 110 | 0.426 | 0.973 | 0.982 | 0.991 | 0.446 | 4 (0) | 0.537 |
| messy | 6 | 120 | 0.297 | 0.667 | 0.983 | 1.000 | 0.450 | 3 (0) | 0.746 |

#### DEV split by document type

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 20 | 420 | 0.307 | 0.811 | 0.983 | 0.998 | 0.462 | 14 (0) | 0.673 |
| discharge_summary | 14 | 290 | 0.267 | 0.813 | 0.983 | 0.997 | 0.497 | 10 (0) | 0.642 |
| prescription | 6 | 130 | 0.398 | 0.808 | 0.985 | 1.000 | 0.385 | 4 (0) | 0.742 |

#### DEV split by case template

| group | docs | medicine mentions | fully correct raw | fully correct after rules | F1 raw | F1 after rules | must_confirm share | name errors remaining (unflagged) | brand-name acc. raw |
|---|---|---|---|---|---|---|---|---|---|
| all | 20 | 420 | 0.307 | 0.811 | 0.983 | 0.998 | 0.462 | 14 (0) | 0.673 |
| appendix | 1 | 20 | 0.550 | 1.000 | 1.000 | 1.000 | 0.300 | 0 (0) | 0.600 |
| cap | 4 | 80 | 0.179 | 0.850 | 0.975 | 1.000 | 0.537 | 1 (0) | 0.577 |
| cardiac | 1 | 30 | 0.379 | 1.000 | 0.967 | 1.000 | 0.567 | 0 (0) | 0.414 |
| copd | 4 | 120 | 0.336 | 0.825 | 0.992 | 1.000 | 0.483 | 4 (0) | 0.798 |
| fracture | 3 | 60 | 0.237 | 0.567 | 0.983 | 1.000 | 0.533 | 2 (0) | 0.678 |
| gastro | 1 | 15 | 0.400 | 1.000 | 1.000 | 1.000 | 0.333 | 0 (0) | 0.667 |
| t2dm_htn | 2 | 40 | 0.436 | 0.923 | 0.975 | 0.975 | 0.400 | 4 (0) | 0.667 |
| uti | 4 | 55 | 0.259 | 0.691 | 0.982 | 1.000 | 0.309 | 3 (0) | 0.704 |

#### Direct standardisation, dev versus test (difficulty strata)

Each split's stratum-specific rate (clean / abbreviated / messy) is reweighted to the OTHER split's stratum weights (the share of that metric's denominator in each stratum). Only difficulty is standardised; templates are too sparse (1 to 8 documents each).

Document mix: dev clean 5 / abbreviated 9 / messy 6; test clean 16 / abbreviated 11 / messy 13.

| metric | dev crude | test crude | crude gap (test - dev) | test reweighted to dev mix | gap vs dev | dev reweighted to test mix | gap vs test |
|---|---|---|---|---|---|---|---|
| fully correct, after rules | 0.811 | 0.888 | +0.076 | 0.855 | +0.044 | 0.844 | +0.044 |
| fully correct, raw | 0.307 | 0.262 | -0.045 | 0.270 | -0.037 | 0.340 | -0.078 |
| brand-name accuracy, raw | 0.673 | 0.495 | -0.178 | 0.554 | -0.119 | 0.641 | -0.146 |
| must_confirm share | 0.462 | 0.511 | +0.049 | 0.474 | +0.012 | 0.456 | +0.055 |

### What the standardisation says

- **The test split is easier by mix.** Clean documents are 45 percent of the test medicines against 26 percent of the dev medicines, and clean documents score highest after rules (test 0.966, dev 0.973; abbreviated 0.782 and 0.811; messy 0.870 and 0.667). Part of the headline gap in the after-rules fully-correct rate (0.888 test against 0.811 dev, +0.076) is therefore the mix.
- **After-rules fully correct: the gap shrinks but does not vanish.** +0.076 crude; +0.044 when the test is reweighted to the dev mix and +0.044 when the dev is reweighted to the test mix (about 42 percent smaller). Within strata, clean is the same on both splits, abbreviated is slightly LOWER on test (0.782 against 0.811), and the remaining gap sits in the messy stratum (0.870 on 13 test documents against 0.667 on 6 dev documents). The template mix also differs (dev holds 3 fracture and 4 uti documents, the two lowest-scoring templates on dev, 0.567 and 0.691; test holds 1 and 3); with 1 to 8 documents per template this cannot be separated from chance.
- **Raw brand-name accuracy: a gap remains.** -0.178 crude; -0.119 and -0.146 after reweighting (the mix explains roughly a fifth to a third). The gap is largest in the clean stratum (0.317 test against 0.537 dev), which is also the largest test stratum. We did not investigate why.
- **Raw fully correct** (-0.045 crude; -0.037 and -0.078 reweighted) and **must_confirm share** (+0.049 crude; +0.012 and +0.055) change with the direction of reweighting, so the mix alone does not settle them.
- **Reading the dev-versus-test comparison.** Dev was expected to look better because it was tuned on, but the after-rules fully-correct rate is higher on test, partly because the test has more clean documents. That is not evidence of "no overfitting" or "better generalisation"; it supports only "no large drop on a test with an easier mix, with the abbreviated stratum slightly lower". Dev strata are small (5 to 9 documents); no stratum-level difference is claimed.

## 4. Cluster-aware intervals

The official Wilson intervals treat the 795 readings (159 distinct medicines read five times) as independent. Below, the unit is the document.

Seeded document-level cluster bootstrap on the 40 test documents (seed 20261028, 2000 resamples, percentile 95%): each resample draws 40 documents with replacement and keeps all five readings (and all explanation lines) of a document together; the statistic is the ratio of sums. Wilson = the official interval (treats readings as independent). Width ratio = cluster width / Wilson width.

| metric | k / n | proportion | official Wilson 95% | cluster bootstrap 95% | width ratio |
|---|---|---|---|---|---|
| must-confirm share | 406 / 795 | 0.511 | [0.476, 0.545] | [0.436, 0.578] | 2.04 |
| fully correct, raw | 205 / 782 | 0.262 | [0.233, 0.294] | [0.202, 0.333] | 2.13 |
| fully correct, after rules | 705 / 794 | 0.888 | [0.864, 0.908] | [0.846, 0.926] | 1.83 |
| interaction_ready share | 389 / 795 | 0.489 | [0.455, 0.524] | [0.423, 0.564] | 2.02 |
| schedule_ready share | 285 / 795 | 0.358 | [0.326, 0.392] | [0.293, 0.432] | 2.09 |
| wrong schedule among schedule_ready | 2 / 285 | 0.007 | [0.002, 0.025] | [0.000, 0.017] | 0.74 |
| explanation lines verified, en | 239 / 255 | 0.937 | [0.900, 0.961] | [0.914, 0.961] | 0.77 |
| explanation lines verified, ta | 46 / 255 | 0.180 | [0.138, 0.232] | [0.130, 0.232] | 1.09 |
| explanation lines verified, hi | 170 / 255 | 0.667 | [0.607, 0.722] | [0.607, 0.732] | 1.08 |

### Wrong resolved_generic among interaction_ready (0 events)

- Readings: 0 of 389; rule of three, 95% upper bound 0.0077 (official Wilson upper bound 0.010). Treats the 389 readings as independent, which they are not.
- Distinct medicines: the 389 readings are 106 distinct (document, medicine) pairs that were interaction_ready in at least one condition; rule of three on those: 0.0283.
- Documents: 39 of 40 documents contributed at least one interaction_ready medicine; with 0 documents showing a wrong one, the one-sided exact 95% upper bound for the share of documents is 0.0739 (rule of three 0.0769). This is a bound on documents, not on medicines.
- Reading: the per-reading figure (0.0077) is the most optimistic; the per-distinct-medicine figure (0.0283) is the more honest scale for a per-medicine statement, and the document-level figure (about 0.074) is the cautious one.

### Reading the table

- Medicine-level proportions (must_confirm, fully correct, interaction_ready, schedule_ready): the cluster interval is about 1.8 to 2.1 times as wide as the official Wilson interval. The Wilson intervals were too narrow; the cluster ones are the honest scale.
- Wrong schedule among schedule_ready (2 of 285): the percentile bootstrap gives [0.000, 0.017], NARROWER than Wilson [0.002, 0.025]. With 2 events in 2 documents the percentile bootstrap is unreliable (about 13 percent of resamples contain no event at all and its lower bound is 0); do not read it as tighter evidence. At document level the events are in 2 of 40 documents (Wilson 95%: [0.014, 0.165]).
- Explanation lines (n=255, 40 documents): Tamil and Hindi intervals are about as wide as Wilson (ratio 1.1); English is narrower (0.77) because it sits near 1.0 where a percentile interval is bounded by the data. The lines are clustered by document too (about 6 per document), but the dependence is weaker than for medicines.

## 5. What this changes in how we word the headline results

No official number or sentence changed. For quoting from now on:
1. Pooled medicine-level proportions (must_confirm share, interaction_ready, schedule_ready, raw fully correct) carry the cluster interval, roughly twice as wide as Wilson, e.g. "about half of the medicine readings (406 of 795, 0.511, document-cluster bootstrap 95% [0.436, 0.578]) ask for a confirmation". The after-rules fully-correct interval (0.888 [0.845, 0.927]) was already document-level.
2. "0 wrong resolved_generic" is stated as "0 of 389 readings (106 distinct medicines in 39 documents); upper 95% bound by the rule of three 0.8% per reading, 2.8% per distinct medicine, 7.4% of documents", not as a guarantee.
3. The 2 wrong schedules are "2 of 285 readings, in 2 of 40 documents (both scan)", with the Wilson bound only; the bootstrap interval is not used for a rare event.
4. The 3 strict silent misses are one misread row in one document and condition, not three independent events.
5. "1 unflagged wrong name" is "1 unflagged brand-field placement error with the identity correct".
6. The dev-versus-test comparison is quoted with the mix statement of section 3; the test split is not described as better than dev.
7. The Tamil figure is unchanged (46 of 255 verified); 8 of its 194 fallbacks were truncation failures rather than verification failures.

## 6. Limitations and future work derived from the cases (none applied)

1. **A quote-consistent misreading is invisible to the rules** (ds_035: SOS read as OD). The app has no document text, so no check can disagree. Future: a second independent reading of dosing abbreviations from the image; never defaulting an inhaler or other as-needed form to a daily schedule without a confirmation.
2. **A model-versus-rule timing conflict is only a "note" and does not block scheduling** (ds_038). Future: treat a timing conflict as a reason to require confirmation before a schedule is suggested (cost: more confirmation load; the conflict flag fired 167 times pooled).
3. **A whole line in the brand field is not flagged when the generic resolves exactly** (ds_024). Future: flag a brand field that carries digits, units or a form prefix.
4. **A misread name plus a copied neighbouring generic** (ds_028: "Performin" with "Glimipride") shows the model can produce a plausible-looking pair. It was flag-covered here; the second reading in item 1 would help.
5. **Tamil translation calls can truncate** (2 of 320 explanation calls, 4-line chunks, after 4 and 5 requests). The fallback worked. Future: smaller chunks or a larger context for Tamil (needs a new freeze).
6. **The splits are not stratified by difficulty or template** (dev 26 percent clean, test 45 percent; fracture 3 against 1 documents). Future: stratified splits for any new evaluation.
7. **Wilson intervals on pooled medicine readings are too narrow**; cluster intervals are reported here, but the percentile bootstrap is unreliable for rare events (2 wrong schedules). Future: exact document-level bounds for counts.
8. **The 389 interaction_ready readings are 106 distinct medicines** from 39 documents; the evidence for "0 wrong identities" is smaller than 389 suggests.
9. **Not yet done (Phase 7c):** real phone photos, usability sessions, native-speaker and pharmacist review.

## 7. Verification

Official folder SHA256SUMS verified before and after this phase. Freeze manifest: one expected drift (section 1). The cases reproduce the official counts exactly, and the dev rates recomputed here equal the committed dev values (fully correct after rules 0.8115, raw brand name 0.6731). Cluster bootstrap: seed 20261028, 2000 resamples. Test suites: see `docs/PROGRESS.md`.
