# Phase 7 plan

Three stages. 7a (done) built everything and froze the system. Nothing changes after the tag `freeze-pre-test` except what is listed under 7b/7c as pins, results and reports.

| stage | what | model? | who |
|---|---|---|---|
| **7a** | protocol, freeze manifest, one-shot runner, intervals, report builder; safety stress set (ground-truth mode run); real-photo print pack and scorer; usability pack and analysis script; freeze + tag | no | done |
| **7b** | the ONE official run on the 40 held-out test documents | yes (local Ollama) | you start it, it runs about 3 hours |
| **7c** | stress extraction mode, real-photo test, usability sessions, native-speaker and pharmacist review, final write-up | yes for stress and photos | you + helpers |

## What you must do
- **Before 7b**: nothing to prepare except a quiet machine (no other GPU load), Ollama running with `qwen3-vl:8b-instruct` loaded, the data rendered (`data/rendered/` exists, it does), a clean git tree.
- **For 7c**: print and photograph the pack (`docs/real_photo_test/PROTOCOL.md`, 25 photos); recruit five adults (one Tamil and one Hindi reader if possible); run the sessions (`docs/usability/PROTOCOL.md`); send the review sheets (`send_to_reviewers/`) to the pharmacist and the Tamil/Hindi reviewers.

## Order of commands
7b (repo root, `python` = `backend\.venv\Scripts\python`):
1. `git status` must be clean; `python scripts\freeze_manifest.py verify` must say no drift; `git tag` must list `freeze-pre-test`.
2. `ollama ps` shows the model loaded (at least 80 percent GPU).
3. `python -m eval.final_test.run_final --pin` (asks the local Ollama for version and model digest, hashes the test data as a set; no model call), then `git add eval/final_test/model_pin.json eval/final_test/test_data_pin.json; git commit -m "Phase 7b: pins"`.
4. `python -m eval.final_test.run_final --final-test-run` (one official run; if interrupted, run the same command again: it resumes from the cache with identical results).
5. Read `eval/results/final-test-v1/metrics.md`; `git add eval/results/final-test-v1 eval/test_runs.log; git commit`.
6. Only then, anything further is post-hoc: `... --final-test-run --rerun-reason "why"` writes `final-test-v1-posthoc-N`.

7c: `python -m eval.stress.run_safety_stress --mode extraction` (stress images; render first with `python data\build_stress_set.py --render`), `python scripts\score_real_photos.py` (backend running), `python scripts\analyse_usability.py --dir <filled csv folder>`; wire the final figures into the testing page by extending `scripts/build_testing_page_data.py` (docs/TESTING_PAGE.md).

## Expected durations
- Extraction: 200 calls at about 30 s = about 100 minutes (cached calls are free on resume).
- Narrative (en, ta, hi on clean for 40 documents): about 60 to 90 minutes (English about 25 s, Tamil about 65 s per document).
- Scoring and report: seconds. Total about 3 hours.
- Real photos: 25 photos at 40 to 60 s = about 20 minutes. Stress extraction: 60 images = about 30 minutes. Usability: 5 x 30 minutes.

## Rule: nothing changes after the freeze
No code, prompt, rule, threshold, formulary, template, phrase-library or supplement change between the tag and the end of the 7b run. If a defect is found, report it and decide separately; a fix means a new freeze and the result of the old freeze stays in the record. Resuming an interrupted run from the cache is not a re-run. The test split is never used for debugging.
