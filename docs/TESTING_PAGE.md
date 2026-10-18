# "How we tested it" page (Phase 6d)

Route `/how-we-tested-it` (header link "Testing", landing teaser). Figures come ONLY from `frontend/src/data/testing.generated.json`, built by `python scripts/build_testing_page_data.py` (`--check` for staleness; `backend/tests/test_testing_page_data.py`). No number is typed into a string: strings (`scripts/p6d_testing.py`) carry `{placeholders}` filled from each entry's params.

**Source files read (all committed)**: `eval/results/dev-ollama-v1-normalised-v2/metrics.json` (extraction raw vs rules, invented values, flags, readiness), `eval/results/stress-v1/metrics.json` (verification stack), `eval/results/phase3e-dev-clean/metrics.json` (lines shown per language), `eval/results/phase4-dev-with-supplement/metrics.json` (safety layer), the live-run file `docs/smoke/phase6d_live.json` (JSON lines), `data/reference/formulary.json` (size of the shared medicine list, used in the limits text). Dates are the day each file was committed (`RUN_DATES`); the files carry no date.

**Entry fields**: id, group, label, value, unit (ratio or count), source, measures, data (+params), caveat, split, date, optional n/of. The page shows the data line once per group when all rows share it, else per row; F1 is named only in the "what this measures" column.

**Rules**: dev figures only; the builder refuses to run if `eval/test_runs.log` exists. The page says the held-out test is "not yet run" (`final_test.run` false).

**Phase 7 adds the test-set figures**: run the final test once (`--final-test-run`), commit its metrics, extend `build_testing_page_data.py` with entries `split: "test"` from that file, set `final_test.run` true (the not-run notice then disappears), regenerate, update the limits text (no longer "mostly dev"), and rebuild strings.
