# CareBridge

A multilingual post-discharge companion web app. Upload a discharge summary or prescription; CareBridge extracts the medicines, explains the document in plain English, Tamil and Hindi, verifies the explanation against the source, checks drug interactions, and builds a daily medication schedule.

Built for an "AI in Healthcare" class project. It explains and organizes; it never diagnoses or changes doses. All documents are synthetic.

## Run

Backend (http://localhost:8000):

    cd backend
    py -3.12 -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env   (Gemini is optional: set GEMINI_API_KEY only to compare; never commit it)
    uvicorn app.main:app --reload

Frontend (http://localhost:5173):

    cd frontend
    npm install
    npm run dev

Dataset (from repo root):

    backend\.venv\Scripts\python data\generate_synthetic.py
    backend\.venv\Scripts\python data\validate_dataset.py

Phase 2 (extraction runs locally with Ollama; only synthetic documents are ever sent, and only to localhost):

    ollama pull qwen3-vl:8b-instruct
    setx OLLAMA_FLASH_ATTENTION 1
    setx OLLAMA_KV_CACHE_TYPE q8_0      (then restart Ollama)

    backend\.venv\Scripts\python data\render_documents.py
    backend\.venv\Scripts\python -m eval.evaluate --split dev --run-id my-run

Normalisation re-score (no model calls, uses cached outputs of a finished run):

    backend\.venv\Scripts\python -m eval.evaluate --split dev --run-id dev-ollama-v1 --rescore normalised

The re-score writes `eval/results/<run-id>-normalised-v2/` (raw vs normalised, quote checks, review levels, readiness).

Phase 3 (explanations; local model, dev split, clean condition, resumable from the cache; python = `backend\.venv\Scripts\python`):

    python -m eval.run_narrative --run-id phase3-dev-clean            (about 35 min cold, 8 model calls per document)
    python -m eval.corruption_eval --run-id phase3-dev-clean          (known-fault detection; judge calls are cached)
    python -m eval.phase3_metrics --run-id phase3-dev-clean           (writes eval/results/phase3-dev-clean/metrics.{json,md})
    python -m eval.make_review_pack                                  (docs/review_pack/, no model calls)
    python scripts\export_review_sheet.py                            (data/templates/review_sheet.csv for native review)
    python scripts\import_review_sheet.py returned.csv --reviewer AB (refuses the whole file on any bad row)
    python scripts\import_review_pack.py returned_ta.csv --reviewer AB

Phase 4 (safety layer; no model calls; python = `backend\.venv\Scripts\python`):

    python scripts\build_interaction_store.py                         (needs data/reference/ddinter/raw/*.csv; writes the gitignored store)
    python scripts\export_pharmacist_sheets.py                        (data/reference/review/*.csv for the pharmacist)
    python scripts\import_pharmacist_sheets.py returned.csv           (refuses the whole file on any bad row; --dry-run to check)
    python scripts\add_safety_templates.py                            (idempotent; also writes data/templates/review_sheet_phase4_new.csv)
    python -m eval.phase4_safety                                      (eval/results/phase4-dev/, cached dev outputs)

Phase 3e (phrase library, stress set; same conventions):

    python -m eval.stress.run_stress --run-id stress-v1                (17 local calls, about 7 min; eval/results/stress-v1)
    python -m eval.run_narrative --run-id phase3e-dev-clean            (phrase library active)
    python -m eval.phase3e_metrics --run-id phase3e-dev-clean          (provenance shares, near-misses, comparison with Phase 3)
    python scripts\export_phrase_sheet.py                              (data/templates/phrase_review_sheet.csv)
    python scripts\import_phrase_sheet.py returned.csv --reviewer AB   (refuses the whole file on any bad row)

Phase 5 (backend API; python = `backend\.venv\Scripts\python`):

    python scripts\generate_data_key.py                              (once; writes CAREBRIDGE_DATA_KEY to backend/.env, never prints it)
    cd backend; .venv\Scripts\uvicorn app.main:app                   (API on localhost:8000; needs Ollama for real uploads)
    python scripts\smoke_api.py                                      (live flow on dev ds_037, clean and poor; needs the API and the model)
    python scripts\export_openapi.py                                 (rewrites docs/openapi.json; a test fails if it is stale)
    python scripts\add_phase5_templates.py                           (idempotent; writes data/templates/review_sheet_phase5_new.csv)

Phase 5c (prototype review mode; no independent review has taken place, see `docs/REVIEW_STATUS.md`):

    python scripts\import_pharmacist_sheets.py FILE.csv --author-selfcheck   (only sets author_checked; a pharmacist sheet without the flag sets reviewed)
    python scripts\add_phase5c_templates.py                                  (idempotent; writes data/templates/review_sheet_phase5c_new.csv)

Tests: `cd backend && .venv\Scripts\python -m pytest`. Frontend build: `cd frontend && npm run build`.

See `CLAUDE.md` for the project plan and `docs/PROGRESS.md` for status.

## Frontend (Phase 6a)
- Run: `cd frontend; npm install; npm run dev` (port 5173, proxies `/api` to the backend on 8000).
- Unit tests `npm test`; contrast gate `npm run check:contrast`; production build `npm run build`; preview `npx vite preview --port 4173`.
- End-to-end (Playwright, Chromium; first time `npx playwright install chromium`): `npx playwright test` (the privacy test needs the backend running).
- Screenshots: `node scripts/screenshots.mjs ../docs/screenshots/phase6a 45` with the preview running.
- UI strings: edit `scripts/add_phase6a_templates.py`, run it and `scripts/export_ui_strings.py`.
- Photos: see `docs/PHOTOS_NEEDED.md`; `backend\.venv\Scripts\python scripts\prepare_photos.py`.


## Frontend flow (Phase 6b)
- Dev: `cd frontend; npm run dev` (port 5173). The backend default `ALLOWED_ORIGINS` (`http://localhost:5173,http://127.0.0.1:5173`) already allows it.
- Preview and Playwright on port 4173 need the backend started with `ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173` (set it in the shell, not in a committed file).
- Mocked end-to-end (no model): `npx playwright test` (builds and previews on 4173; includes axe on 14 flow states in en, ta, hi).
- Live end-to-end with the real model (Ollama running, model on GPU, `CAREBRIDGE_DATA_KEY` set, backend on 8000): `npm run build; npx vite preview --port 4173 --strictPort` then `npx playwright test -c playwright.live.config.ts`. It uses dev document ds_037 (clean and poor) from `data/rendered/`, writes `docs/smoke/phase6b_live.json` and screenshots under `docs/screenshots/phase6b/`. Do not rebuild while it runs.
- Strings: edit `scripts/add_phase6b_templates.py` or `scripts/p6b_*.py`, run it and `scripts/export_ui_strings.py`. API types: `node frontend/scripts/gen-api-types.mjs` after `python scripts/export_openapi.py`.

## Frontend polish (Phase 6c)
- Review page, header, icons and photographs: see `docs/DESIGN.md`. Screenshots (mocked): `$env:SHOTS=1; npx playwright test e2e/shots6c.spec.ts`; the live run writes `docs/smoke/phase6c_live.json`.
- New strings: `data/templates/review_sheet_phase6c_new.csv` (ta/hi drafts for the native reviewers).

## Sample mode and testing page (Phase 6d)
- Sample (no backend, no model): run the app (`cd frontend; npm run dev`, or `npm run build; npx vite preview --port 4173`) and open `/demo`. Details and the fallback checklist: docs/DEMO.md.
- Rebuild the demo fixtures (needs the gitignored `data/rendered/` and `data/cache/`; never calls a model): `backend\.venv\Scripts\python scriptsuild_demo_data.py` (`--check` to compare).
- Rebuild the testing-page figures (committed metrics only): `backend\.venv\Scripts\python scriptsuild_testing_page_data.py` (`--check`). Page: `/how-we-tested-it` (docs/TESTING_PAGE.md).
- New UI strings: `python scriptsdd_phase6d_templates.py; python scripts\export_ui_strings.py` (review sheet: data/templates/review_sheet_phase6d_new.csv).
- Live regression (needs Ollama and the backend): `cd frontend; npx playwright test -c playwright.live.config.ts` (`LIVE_REPORT=<file>` and `LIVE_APPEND=1` for single re-runs).

## Commands for Phases 2 to 4 (moved from CLAUDE.md)
Phase 2 (from repo root unless noted; python = `backend\.venv\Scripts\python`; Ollama must be running with qwen3-vl:8b-instruct pulled):
- Render: `python data\render_documents.py` (about 4 minutes; 240 PNG + 120 PDF)
- Evaluate (dev): `python -m eval.evaluate --split dev --conditions text,clean,scan,photo,poor [--limit N] [--run-id NAME]`; oracle (no API): add `--oracle`
- Re-score with normalisation (no model calls): `python -m eval.evaluate --split dev --run-id dev-ollama-v1 --rescore normalised` -> eval/results/dev-ollama-v1-normalised
- DDInter: `python data\reference\fetch_ddinter.py` then `python data\reference\ddinter_coverage.py`
- Frontend tests: `npm test` (vitest), `npm run check:contrast`, `npx playwright test` (e2e + axe + perf; needs `npx vite preview --port 4173` or builds it; the privacy test needs the backend on 8000), `node scripts/screenshots.mjs <dir> [quality]`

## Phase 7 commands (docs/PHASE7_PLAN.md)
- Freeze: `backend\.venv\Scripts\python scriptsreeze_manifest.py write|verify`
- Stress set: `python datauild_stress_set.py [--render]`; ground-truth evaluation (offline): `python -m eval.stress.run_safety_stress --mode gt`
- Real-photo pack: `python scriptsuild_print_pack.py`; score (7c): `python scripts\score_real_photos.py`
- Usability: `python scripts\prepare_usability_samples.py`; analysis: `python scriptsnalyse_usability.py --dir <folder>`
- Final test (7b only): `python -m eval.final_test.run_final --pin`, then `--final-test-run`
