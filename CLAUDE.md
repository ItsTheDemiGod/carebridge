# CareBridge

## Summary and goal
Multilingual post-discharge companion. Users upload a discharge summary or prescription; the system extracts medicines, explains the document in plain English/Tamil/Hindi, verifies the explanation against the source, checks drug interactions, and builds a daily medication schedule.
End goal: a professional web app first; a mobile app only if time allows. College "AI in Healthcare" project.

## Tech stack
- Frontend: React + Vite + TypeScript, Tailwind CSS, Framer Motion, GSAP, tsParticles
- Backend: FastAPI, Python 3.12, pytest
- LLM: local-first. Default provider Ollama (`qwen3-vl:8b-instruct`, called with httpx on localhost). Gemini (`google-genai`, `gemini-3.8-flash`, GEMINI_API_KEY in backend/.env) is an optional comparison provider only; its free tier is quota-limited (about 20 requests/day), so do not rely on it.
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
- backend/app/llm/ : base.py (Provider interface), ollama.py (localhost-only), gemini.py; LLM_PROVIDER selects (get_provider)
- backend/app/{prompts,services}/ : extraction_v1..v3.txt (v1 is the default), extraction.py (provider-agnostic service + cache), guards.py (privacy + test-split guards)
- backend/scripts/ : smoke_test_gemini.py, extract.py
- eval/name_sanity.py : drug-name sanity diagnostic (names matching no formulary entry); eval/rescore.py : raw vs normalised re-scoring from cached outputs
- backend/app/normalisation/{abbreviations,names}.py, services/normalisation.py, schemas/normalised.py : rule-based normalisation (docs/NORMALISATION.md)
- data/render_documents.py -> data/rendered/ (gitignored), data/cache/ (gitignored), docs/samples/render_preview.png
- data/reference/ : fetch_ddinter.py, ddinter_coverage.py; docs/DDINTER_COVERAGE.md, docs/PROMPT_LOG.md
- assets/ATTRIBUTION.md : photo credits (file, source URL, photographer, license)
- Phase 3: backend/app/schemas/explanation.py; services/{templates,narrative,verification,explain,script}.py; prompts/narrative_v{1,2}/ (A simplify, B translate, C back-translate, D judge; v2 default); data/templates/{templates.json,review_sheet.csv}; scripts/{export_review_sheet,import_review_sheet,import_review_pack}.py; eval/{run_narrative,corruption_eval,make_corruptions,phase3_metrics,readability,make_review_pack}.py; docs/{EXPLANATION,EXPLANATION_PROMPT_LOG,TRANSLATION_REVIEW}.md; docs/review_pack/
- Phase 3e: data/templates/{phrases.json,phrase_review_sheet.csv}; services/phrase_match.py; scripts/{export,import}_phrase_sheet.py; eval/stress/{stress_set.json,run_stress.py,README.md}; eval/phase3e_metrics.py; docs/PHRASE_LIBRARY.md

## Phases
Status: [x] done, [ ] not started, [~] in progress
- [x] 0 Setup and foundation
- [x] 1 Synthetic data, schema, drug database choice
- [x] 2 Document extraction pipeline plus evaluation script (local Ollama provider; dev run done, prompt v1 kept; see PROGRESS.md)
- [x] 2h Normalisation layer (rules, formulary name resolver, flags; dev re-score from cache, no model calls)
- [x] 2i Hardening: strict quote checks, incomplete_quote flag, review levels, interaction_ready / schedule_ready
- [x] 3 Plain-language explanation (EN/TA/HI) plus faithfulness verification (dev only; Tamil/Hindi quality not yet reviewed by natives)
- [x] 3e Phrase library (91 phrases), provenance labels, stress set, dev re-run (no native review yet; send review sheets before Phase 7)
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
- Gemini free tier daily quota is tiny (20 requests/day/model seen on 2026-10-04); it is only an optional comparison provider. The disk cache (data/cache) makes reruns free; do not try to bypass quotas.
- LOCAL-ONLY RULE: the Ollama adapter refuses any OLLAMA_BASE_URL host other than localhost/127.0.0.1. PDFs are unsupported by it (images and text only).
- Ollama config (backend/.env.example): LLM_PROVIDER (default ollama), OLLAMA_BASE_URL, OLLAMA_MODEL (qwen3-vl:8b-instruct; the plain qwen3-vl:8b tag is a thinking model that ignores think:false), OLLAMA_NUM_CTX 6144, OLLAMA_NUM_PREDICT 3000, OLLAMA_TIMEOUT_SECONDS, OLLAMA_KEEP_ALIVE 30m, OLLAMA_MAX_IMAGE_SIDE 1280.
- GPU findings (RTX 4060 8 GB, OLLAMA_FLASH_ATTENTION=1, OLLAMA_KV_CACHE_TYPE=q8_0 set by the user): instruct tag is 91% GPU at ctx 6144, 89% at 8192. Longest dev doc uses about 2.2k prompt + 1.4k generated tokens, so 6144 is enough. About 30 s per call; a 100-call dev run takes about 50 minutes.
- Guards: Ollama calls fail as context_truncated (output cut off or prompt+output reached num_ctx) or image_not_received (too few prompt tokens; without the image the model invents medicines). The evaluator reports such documents as skipped, never silently drops them.
- NORMALISATION RULES: where the abbreviation table derives timing/frequency/duration from the verbatim source_quote, the RULE value is final (a disagreement is kept as a conflict flag); the model never sets a final value when a rule applies. Names are never silently corrected: as_written, printed (formulary spelling) and resolved_generic (provenance formulary) are kept apart; unknown names are flagged `unresolved_name`, never forced onto a drug. Synthetic names are all in the 66-drug formulary, so name scores are optimistic.
- READINESS RULE: each normalised medicine has review_level (must_confirm/note/none; needs_verification = alias of must_confirm), interaction_ready and schedule_ready. Interaction checks run ONLY for interaction_ready medicines (resolved_generic from an EXACT printed formulary name, never from the model's generic field); all others are reported "not checked". Reminders are built ONLY for schedule_ready medicines (daily, known times/timing, not PRN, never weekly); the user confirms the rest. Any new flag is must_confirm unless explicitly listed as note.
- The normalisation service uses only the model's output; document text is optional (evaluation and tests only).

## Explanation pipeline (Phase 3, 3e)
- Per free-text line, in order: (A) strict phrase-library match (exact, no model) -> (B) local model with verification -> (C) original English with notice. Matched lines make no model call.
- LABEL RULE: a model-written line is `machine_checked` (software only) and may NEVER carry a human-review label; only a template/library text with review_status `reviewed` is `native_reviewed`. Provenance: template | phrase_library | model_checked | original_only (per language on LangText).
- PHRASE LIBRARY RULE: near-misses are reported, NEVER displayed; the library is never extended from dev or stress lines (keeps coverage honest). Library ta/hi are draft_unreviewed until the native import.
- Dev 3e: 9/135 lines match the library (6.7%); stress-set sources 4/55. The stress set is authored, never shipped, never used as prompt examples.
- Works from the NORMALISED extraction only (never document text). Medicine lines: fixed templates (en/ta/hi), no model. Advice, follow-ups, warnings: local text-only model (A simplify en, B translate ta/hi, C back-translate, D judge).
- A language text is "verified" only if ALL deterministic checks pass (id integrity, numbers, drug names, script, length, forbidden additions, urgency) AND the judge says supported. Otherwise the user sees the ORIGINAL extracted English with a fallback notice. Unverified text is never shown as verified. Each language falls back on its own.
- Warning lines in output == extracted warnings (never dropped or merged). must_confirm medicines always carry the confirm banner; a medicine that is not schedule_ready is never "settled".
- Every ta/hi string and model-written line is draft_unreviewed until the native-speaker CSV import (docs/TRANSLATION_REVIEW.md). Tamil is translated in chunks of 4 with per-line retry (repetition loops); deterministic failures are cached.
- Dev numbers (v2): verified en 1.00, hi 0.76, ta 0.27. The same model writes and judges (weak judge). Cache: data/cache/narrative/. Run: `python -m eval.run_narrative --run-id phase3-dev-clean`.

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

Phase 2 (from repo root unless noted; python = `backend\.venv\Scripts\python`; Ollama must be running with qwen3-vl:8b-instruct pulled):
- Render: `python data\render_documents.py` (about 4 minutes; 240 PNG + 120 PDF)
- Smoke: `python backend\scripts\smoke_test_gemini.py`; one doc: `python backend\scripts\extract.py ds_006 --condition clean`
- Evaluate (dev): `python -m eval.evaluate --split dev --conditions text,clean,scan,photo,poor [--limit N] [--run-id NAME]`; oracle (no API): add `--oracle`
- Re-score with normalisation (no model calls): `python -m eval.evaluate --split dev --run-id dev-ollama-v1 --rescore normalised` -> eval/results/dev-ollama-v1-normalised
- Tests: `cd backend; .venv\Scripts\python -m pytest` (live API tests: `-m live`)
- DDInter: `python data\reference\fetch_ddinter.py` then `python data\reference\ddinter_coverage.py`
