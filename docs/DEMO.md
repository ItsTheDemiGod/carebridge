# Sample (demo) mode (Phase 6d)

**What it is**: `/demo` is a pre-recorded walk-through of ONE synthetic dev document (ds_037, condition `poor`: a deliberately blurry scan). The real pages (review with picker, result in en/ta/hi, schedule, doctor summary) run on recorded API responses. No photo is processed, no model runs, nothing is saved. It must never look like the result of the visitor's own upload.

**How the fixtures are built**: `python scripts/build_demo_data.py` (`--check` compares with the committed files). It runs the REAL FastAPI app in-process on a throw-away database and key, replays the cached extraction output of ds_037/poor (run dev-ollama-v1) and the cached narrative (data/cache/narrative, a provider that raises on any miss), and drives the real endpoints with scripted decisions that follow docs/CONFIRMATION.md (the garbled "Netfornin" is resolved by picking Metformin from the formulary, the duplicate-name row by picking Atorvastatin, other reasons by acknowledging). Output: `frontend/src/demo/fixtures/*.json`, each with a header (source document, condition, synthetic, script version, date), deterministic (random ids and times replaced). It fails loudly on a missing cache entry or interaction store; it never calls a model. Needs the gitignored `data/rendered/` and `data/cache/`. Refresh: re-run the script, bump `BUILT_ON`, `python -m pytest backend/tests/test_demo_data.py`.

**Zero-network guarantee**: under `/demo`, `api()` (frontend/src/api/client.ts) is answered by `demoApi` (frontend/src/demo/demoApi.ts) from memory. Only static app files are fetched: the fixture chunk and `/demo/sample-document.png`. Tests: vitest (`demoApi.test.ts`, fetch stub) and Playwright (`e2e/demo.spec.ts`: every request recorded in en/ta/hi, offline after first load, localStorage only language and calm, no cookies). The pre-recorded AFTER result is returned after Save whatever was chosen, and the page says so. Marks (taken/skipped) and edited times live in memory and reset on leaving.

**Must never claim**: that the photo was processed, that anything was saved or can be deleted, that the result reflects the visitor's choices, speed, accuracy, or that anyone reviewed anything. The label "Pre-recorded sample. No photo is processed and nothing you do here is saved." sits in the sticky header strip of every demo page; ta/hi keep the machine-draft note. Sample-only wording replaces "saved" texts (`ui.demo.alt.*`, I18n.tsx).

**DDInter excerpt**: 5 attributed pairs (names and level only); see docs/DDINTER_COVERAGE.md.

**Fallback checklist (class demonstration)**
1. Before the day: `npm run build`, `npx vite preview --port 4173`, open `/demo` once online and click through (the app also works from any static host).
2. If the model or backend fails: say so, open `/demo` ("Try a sample document" on the landing page and on the unreachable message), and say it is pre-recorded.
3. Walk: Start the sample, pick Metformin for the flagged row, Save, Results (switch language), Schedule, Summary.
4. Do not present the sample as a live result or its timings or counts as performance.

**Hosted sample (Phase 8a)**: the same sample is published with GitHub Pages at https://itsthedemigod.github.io/carebridge/ (expected address) from a demo-only build: `docs/DEPLOY.md`. Under that build every real-flow route shows a plain "sample only" page, the Privacy page uses a static copy of the consent notice, and nothing calls an API. Licence note for the DDInter excerpt: `frontend/src/demo/fixtures/README.md`.


## Deterministic fixtures (clock)
`doctor_summary_*.json` used to depend on the time of day: with no events the API's summary covers "today" and counts a slot as missed once its time has passed. The builder now requests the fully elapsed day 2026-01-01 (`SUMMARY_DAY`), so every slot counts as missed whatever the clock says. This is the value the sample page recomputes anyway (`summaryView` in `demoApi.ts`). Backend code is unchanged. `test_fixtures_do_not_depend_on_the_time_of_day` rebuilds under a fake clock at 00:01, 12:00 and 23:59.
