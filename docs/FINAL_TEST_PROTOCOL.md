# Final test protocol (pre-registered, Phase 7)

Written and committed BEFORE any code for the run (Phase 7a step 1). It fixes what is measured, how, and what may not change. The run itself is Phase 7b; the real-photo test and the usability sessions are Phase 7c.

## 1. Scope
- **Data**: the 40 held-out TEST documents of `data/manifest.json` (never used for prompts, rules, thresholds or debugging; every earlier run used the 20 dev documents only). All synthetic, generated and rendered by this project.
- **Extraction, normalisation, safety engine**: 40 documents x 5 conditions (`text`, `clean`, `scan`, `photo`, `poor`) = 200 extraction calls.
- **Explanation pipeline**: English, Tamil and Hindi on the `clean` condition for all 40 documents (narrative from the normalised extraction of that condition).
- **Model and settings** (read from `backend/app/config.py` and the adapter, recorded again at run time): provider Ollama on localhost, model `qwen3-vl:8b-instruct`, `num_ctx` 6144, `num_predict` 3000, image side cap 1280, temperature 0, seed 42, extraction prompt `v1`, extraction schema version 1, narrative prompt `v2`. The Ollama version and the model digest are recorded at the start of the run and the digest must equal the pin committed at the start of 7b (`eval/final_test/model_pin.json`).
- **Frozen artefacts**: everything listed in `eval/final_test/freeze_manifest.json` (code, prompts, templates, phrase library, formulary, interaction supplement, schemas, evaluation code, this protocol; hashes only for the dataset manifest, the test documents and ground truth as a set, and the DDInter-derived store).

## 2. Primary metrics (each RAW = model output as returned, and NORMALISED = after the rule layer, where applicable; per condition and pooled over the five conditions)
Definitions are those of `eval/matching.py`, `eval/rescore.py`, `eval/phase4_safety.py`, `eval/phase3_metrics.py`, `eval/phase3e_metrics.py` (committed before the run; no definition changes during it).
1. **Medicines**: precision, recall, F1 (one-to-one matching of predicted to ground-truth medicines by name similarity); fully-correct medicine rate (matched medicines whose every field is right); per-field accuracy over matched medicines: strength, form, dose, times_per_day, timing_label, is_prn, duration_days, brand name, generic name; hallucinated medicines (unmatched predictions).
2. **Invented values**: invented-value rate overall and by field, split into role confusion (the value is on the document under another field) versus truly invented (not on the document).
3. **Names and flags**: name errors remaining after normalisation, and how many carry no confirmation flag (unflagged); review-level load (share of medicines at `must_confirm`, in `app` mode = model output only, no document text); `interaction_ready` and `schedule_ready` counts; the number of WRONG `resolved_generic` values among `interaction_ready` medicines and wrong schedules among `schedule_ready` medicines (the target is 0; any non-zero count is reported in full with the cases).
4. **Safety engine** (normalised extraction in `app` mode, local DDInter-derived store plus the author-checked supplement as enabled at freeze): strict silent misses (a known pair that is not reported as `interaction_found`), silent misses NOT covered by a flag (per-pair one-to-one definition of Phase 4: a miss counts as covered only when a medicine of the pair carries a confirmation flag), false alarms, the share of pairs not checked. Only aggregated counts are published, never pair-by-pair DDInter levels.
5. **Explanation** (en, ta, hi, `clean`): verified share per language and per line kind (advice, follow-up, warning), fallback rate (original English shown), label distribution (provenance and review labels).
6. **Operational**: documents attempted, scored and skipped (with the reason of every skip), latency median and 95th percentile per condition.
Test and dev are reported side by side with the difference (section 4).

## 3. Uncertainty
- Proportions: Wilson 95 percent intervals (counts and denominators shown).
- F1 and the fully-correct rate: document-level bootstrap 95 percent interval (percentile method, 2000 resamples of documents with replacement, fixed seed, standard library). Per condition the resampling unit is the document; pooled, the resampling unit is the document with all its conditions together.
- With 40 documents the intervals are wide; this is stated beside every figure and differences smaller than the intervals are not described as differences.

## 4. Comparison with dev
The committed dev figures (`eval/results/dev-ollama-v1-normalised-v2`, `phase4-dev-with-supplement`, `phase3e-dev-clean`) are the reference. Dev scores are EXPECTED to be higher: rules, prompts and templates were tuned on dev. The test documents come from the SAME generator as dev (same case templates, names and layouts), so the test is held out from tuning but is NOT independent of the generator's style. A large drop would indicate overfitting to dev; a small drop does not show real-world performance.

## 5. Rules
1. ONE official run. No change to code, prompt, rule, threshold, formulary, template, phrase library or supplement between the git tag `freeze-pre-test` and the end of the run. The runner refuses to start unless the working tree is clean, the freeze manifest verifies, the tag exists and the model digest equals the pin.
2. An interrupted run may be resumed from the cache with no change; resuming is not a re-run and gives the same numbers (the model is deterministic at temperature 0, seed 42 with the cache keyed on prompt, schema, settings and image bytes).
3. Any later change followed by a re-run is labelled "post-hoc", written to `final-test-v1-posthoc-N`, reported separately and never overwrites the official results. The runner refuses a second official run.
4. Documents the model cannot process (for example `context_truncated`, `image_not_received`, timeouts) are counted and listed with their reasons; they are never dropped silently, and metrics are shown both on scored documents and with skipped documents counted as misses where that is well defined.
5. Every invocation is appended to `eval/test_runs.log`.
6. Whatever the numbers are, they are reported. Failures are reported as failures; no figure is selected after seeing results.

## 6. What is NOT claimed
No clinical validation, no real-world performance, no claim about real users, real documents or real phone photos (a separate small real-photo test, Phase 7c, measures that gap), no claim of correctness of medical content (the interaction data is a partial download plus an author-checked supplement, and Tamil/Hindi texts are machine drafts). Results describe this system on synthetic documents rendered by this project, on one local model, once.
