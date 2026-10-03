# CareBridge

## Summary and goal
Multilingual post-discharge companion. Users upload a discharge summary or prescription; the system extracts medicines, explains the document in plain English/Tamil/Hindi, verifies the explanation against the source, checks drug interactions, and builds a daily medication schedule.
End goal: a professional web app first; a mobile app only if time allows. College "AI in Healthcare" project.

## Tech stack
- Frontend: React + Vite + TypeScript, Tailwind CSS, Framer Motion, GSAP, tsParticles
- Backend: FastAPI, Python 3.12, pytest
- LLM: Google Gemini API (`google-genai`), model `gemini-3.8-flash` (GEMINI_API_KEY, GEMINI_MODEL in backend/.env)
- OCR: Tesseract or PaddleOCR
- Storage: PostgreSQL or SQLite (decided in Phase 5)
- Currently installed (Phase 0): react-router-dom, framer-motion, Tailwind v4 (@tailwindcss/vite). GSAP and tsParticles are NOT installed yet.

## Folder layout
- CLAUDE.md, README.md, .gitignore
- docs/PROGRESS.md, docs/DECISIONS.md
- backend/ : FastAPI app (app/, tests/, requirements.txt, .env.example)
- frontend/ : Vite React TS app
- data/ : reference/formulary.json (66 medicines, unverified), generate_synthetic.py, validate_dataset.py,
  manifest.json (id, type, template, difficulty, dev/test split), synthetic/<id>.txt, ground_truth/<id>.json
- backend/app/schemas/extraction.py : Pydantic schema (+ extraction.schema.json)
- docs/DRUG_DATABASE_RECOMMENDATION.md : interaction database choice (DDInter, pending approval)
- eval/ : evaluate.py, matching.py, results/<run_id>/metrics.{json,md} (committed), runs/ (raw outputs, gitignored), test_runs.log
- backend/app/{prompts,services}/ : extraction_v1.txt, extraction.py (Gemini service + cache), guards.py (privacy + test-split guards)
- backend/scripts/ : smoke_test_gemini.py, extract.py
- data/render_documents.py -> data/rendered/ (gitignored), data/cache/ (gitignored), docs/samples/render_preview.png
- data/reference/ : fetch_ddinter.py, ddinter_coverage.py; docs/DDINTER_COVERAGE.md, docs/PROMPT_LOG.md
- assets/ATTRIBUTION.md : photo credits (file, source URL, photographer, license)

## Phases
Status: [x] done, [ ] not started, [~] in progress
- [x] 0 Setup and foundation
- [x] 1 Synthetic data, schema, drug database choice
- [~] 2 Document extraction pipeline plus evaluation script (code, renders, DDInter check done; live dev run blocked by Gemini daily quota, see PROGRESS.md)
- [ ] 3 Plain-language explanation (EN/TA/HI) plus faithfulness verification
- [ ] 4 Safety layer (interactions, red flags, no-diagnosis guardrail, low-confidence flag)
- [ ] 5 Backend API, database, consent flow, encryption, delete-my-data
- [ ] 6 Web application UI
- [ ] 7 Evaluation, testing, native-speaker review, usability test
- [ ] 8 Deployment, demo, report
- [ ] 9 Stretch: PWA and mobile app

## Working rules (every session)
- Read CLAUDE.md and docs/PROGRESS.md at the start of each session.
- Work on ONE phase at a time and only what that phase's prompt asks for.
- At the end of each phase, update docs/PROGRESS.md (what was built, how to run it, how it was tested, open issues, what comes next) and the phase status here.
- Record any technical decision and its reason in docs/DECISIONS.md.
- Never read, print, or commit .env files or API keys. Only .env.example is committed.
- Never use real patient data. All documents are synthetic.
- Ask before adding any dependency not already listed in this file.
- Keep files small and well named; write tests for backend logic.

## Data and schema
- ExtractedDocument: document_type, medications[], follow_ups[], red_flags[], diet_activity_advice[], document_language.
- Medication: brand_name, generic_name, strength, form, route, dose, frequency{times_per_day, timing_label, original_abbreviation, is_prn}, duration_days, duration_text, special_instructions, source_span.
- Every item carries a SourceSpan {start, end, text}: character offsets into the document text (text == doc[start:end]).
- Ground truth keeps names, duration_text, abbreviations as written; strength/dose/frequency numbers are normalised.
- 60 synthetic docs (40 discharge summaries, 20 prescriptions), 9 case templates, 3 difficulties (clean/abbreviated/messy).
- Regenerate: `backend\.venv\Scripts\python data\generate_synthetic.py`; check: same command with `data\validate_dataset.py`.
- RULE: the 40-document TEST split (manifest.json) is NEVER used for prompt tuning or debugging. Only the 20-document DEV split is. Any extraction/evaluation on it needs `--final-test-run` and is logged to eval/test_runs.log. Do not use that flag before Phase 7.
- PRIVACY RULE: the Gemini free tier lets Google use submitted content to improve its products and human reviewers may read it. ONLY synthetic documents (data/synthetic, data/rendered) may be sent to Gemini; `guards.assert_synthetic` enforces it. Never send real patient data.
- Gemini free tier daily quota is tiny (20 requests/day/model seen on 2026-10-04). The disk cache (data/cache) makes reruns free; do not try to bypass quotas.

## Safety and product rules
- CareBridge explains and organizes. It never diagnoses, never recommends changing a dose, and always tells users to confirm with their doctor.
- Every explanation line must trace to source text.
- Low-confidence output must be flagged.
- Design for India's DPDP Act: explicit consent, data minimization, a delete-my-data function.

## Design direction (applies from Phase 6)
Must look like a professionally designed product, not an AI-generated template.
- Deliberate custom color palette via CSS variables: calm medical tone, no default purple/blue gradients.
- Real typographic pair: a serif or distinctive display font plus a clean sans.
- Consistent spacing scale.
- Animated particle background; custom cursor animation; moving tile/card effects.
- Smooth scroll and page transitions.
- Real licensed photographs from Unsplash or Pexels, tracked in assets/ATTRIBUTION.md.
- No emoji as icons; no generic stock hero layout.
- Accessible contrast; responsive, works well on phones.
- Respect prefers-reduced-motion.

## Commands
Backend (from `backend/`; venv is `backend/.venv`, built with Python 3.12):
- Setup: `py -3.12 -m venv .venv; .venv\Scripts\pip install -r requirements.txt`
- Run: `.venv\Scripts\uvicorn app.main:app --reload` (port 8000)
- Test: `.venv\Scripts\python -m pytest`
- Dataset (from repo root): `backend\.venv\Scripts\python data\generate_synthetic.py` then `backend\.venv\Scripts\python data\validate_dataset.py`

Frontend (from `frontend/`):
- Install: `npm install`
- Run: `npm run dev` (port 5173, proxies /api to localhost:8000)
- Build: `npm run build`

Phase 2 (from repo root unless noted; python = `backend\.venv\Scripts\python`):
- Render: `python dataender_documents.py` (about 4 minutes; 240 PNG + 120 PDF)
- Smoke: `python backend\scripts\smoke_test_gemini.py`; one doc: `python backend\scripts\extract.py ds_006 --condition clean`
- Evaluate (dev): `python -m eval.evaluate --split dev --conditions text,clean,scan,photo,poor [--limit N] [--run-id NAME]`; oracle (no API): add `--oracle`
- Tests: `cd backend; .venv\Scripts\python -m pytest` (live API tests: `-m live`)
- DDInter: `python dataeferenceetch_ddinter.py` then `python dataeference\ddinter_coverage.py`
