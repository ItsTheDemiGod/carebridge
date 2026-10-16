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
