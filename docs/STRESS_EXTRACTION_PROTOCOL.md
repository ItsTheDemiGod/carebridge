# Stress extraction protocol (Phase 7c-lite, pre-registered)

Label for everything produced under this protocol: **stress set, authored, not tuned, not the test split.**
Written and committed BEFORE any stress image was rendered or sent to the model.

## 1. Scope
- Data: the 30 synthetic prescriptions in `data/stress/` (10 categories x 3: DDInter major pair, moderate pair, author-checked supplement pair, duplicate, garbled name, weekly dosing, unusual strength, eye drop with OD, 8-medicine list, control). Conditions: `clean` and `photo` renders, deterministic renderer (`python data\build_stress_set.py --render`). 60 extractions.
- System under test: FROZEN, identical to the official final run: extraction prompt `v1` (`app.prompts.PROMPT_VERSION`), the Ollama schema copy, model `qwen3-vl:8b-instruct`, temperature 0, fixed seed, `num_ctx` / `num_predict` / image side from the same settings object (`app/config`, `.env.example` defaults), then the real normalisation, safety engine and confirmation overlay. No code of the system is changed.
- The stress set is not the dev split and not the test split; it was authored blind to the model and nothing was tuned on it.
- One official stress run (`stress-extraction-v1`). Resuming from the raw-output folder after an interruption is allowed. Any later re-run is labelled post-hoc and never overwrites the first.
- Only synthetic data. Images go only to the local Ollama adapter.

## 2. Deviation: Ollama version (stated in advance)
- The official final run (`final-test-v1`) used Ollama **0.40.5** (pinned in `eval/final_test/model_pin.json`).
- This stress run uses Ollama **0.40.11** (Ollama updated itself). The pin file is NOT changed and no version is recorded in any pin.
- The model digest is identical to the pin: `0533d74300e4f9bc367d675d4e64ffd073d50ff16a2b4096cc2e8a1cf8c96319`.
- The stress set was not part of the official run and its pass criteria are absolute, so comparability with `final-test-v1` is not required. **Stress numbers are not to be compared directly with the official ones.**
- Both versions and the digest are recorded in the run manifest, `metrics.md`, `docs/STRESS_RESULTS.md` and `docs/LIMITATIONS.md`.
- Version sanity check (informative only): 5 dev documents (clean condition) are re-extracted into a gitignored scratch folder, never the shared cache, and compared with the cached outputs of the older version. Result reported, no consequence for the criteria.

## 3. Metrics (per category and pooled, per condition)
Every count carries its denominator. Proportions get Wilson 95% intervals; document-level bootstrap intervals (seed 20261018, 2000 resamples, `eval/final_test/stats.py`) for pooled rates. 30 documents give wide intervals; this is said wherever figures appear.
1. Medicine detection: precision, recall, F1, raw (model output) and normalised (after the rules); matching as in `eval/matching.py` (one-to-one, name threshold).
2. Review-level load: medicines per `review_level` (must_confirm / note / none).
3. For each ground-truth interaction pair (pairs the engine finds with perfect extraction, `analyse` on ground-truth names): outcome in the extraction-based result: `interaction_found` at the same level; `not_checked_unconfirmed` with the flag that caused it; other outcomes (including a missing medicine). Counts per level and per outcome.
4. Strict silent misses (a ground-truth pair not reported as interaction_found) and silent misses NOT covered by a flag (the extraction-side pair is not `not_checked_unconfirmed`; per-pair one-to-one definition from Phase 4, as in `run_safety_stress.extraction_mode`).
5. False alarms: interaction_found that ground truth does not have.
6. Duplicates: ground-truth duplicate groups, duplicate notices produced, missed.
7. Weekly or non-daily medicines: how many are `schedule_ready` (must be 0).
8. Eye drop with OD: whether `ambiguous_OD` fired; whether a daily schedule was produced (schedule_ready).
9. Unusual strengths: flagged (`unusual_strength`) or not.
10. Garbled names: flagged (`near_miss_name` / `unresolved_name`) or not.
11. After the SCRIPTED confirmation overlay (real `services/confirmation.py`; scripted choices use ground-truth names, testing only; hallucinated medicines are removed): whether previously unconfirmed pairs became checkable and whether the found pairs and levels equal the ground-truth-mode result restricted to medicines that were extracted.
12. Wrong `resolved_generic` among interaction_ready medicines (compared with the ground-truth formulary generic; a medicine outside the formulary that is interaction_ready counts as wrong).
13. Operational: calls, skipped/failed calls with reason, latency.
DDInter-derived outcomes are committed as AGGREGATED counts only (per level and per status); no pair-by-pair levels or pair lists.

## 4. Pass criteria (each is reported whether it passes or not)
- **P1** silent misses not covered by a flag = 0.
- **P2** no weekly or non-daily medicine is `schedule_ready`.
- **P3** wrong `resolved_generic` among interaction_ready medicines = 0.
- **P4** after the scripted overlay, every ground-truth interaction between medicines that were extracted is reported as `interaction_found` at the right level.
No thresholds for anything else; all other figures are descriptive. If a criterion fails: every failing case is listed with ids, the system is NOT changed, and what the user would have seen is described.

## 5. Not claimed
No clinical validation and no real-world accuracy. The set is small (30 documents) and authored by the project; results are on rendered synthetic prescriptions with one font family and a deterministic photo simulation. The real-photo test and the usability test were not done. Pass criteria passing on 30 documents is not evidence of safety.
