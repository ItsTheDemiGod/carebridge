# CareBridge

## Summary and goal
Multilingual post-discharge companion. Users upload a discharge summary or prescription; the system extracts medicines, explains the document in plain English/Tamil/Hindi, verifies the explanation against the source, checks drug interactions, and builds a daily medication schedule.
End goal: a professional web app first; a mobile app only if time allows. College "AI in Healthcare" project.

## Tech stack
- Frontend: React + Vite + TypeScript, Tailwind CSS, Framer Motion, GSAP, tsParticles
- Backend: FastAPI, Python 3.12, pytest
- LLM: local-first. Default provider Ollama (`qwen3-vl:8b-instruct`, called with httpx on localhost). Gemini (`google-genai`, `gemini-3.8-flash`, GEMINI_API_KEY in backend/.env) is an optional comparison provider only; its free tier is quota-limited (about 20 requests/day), so do not rely on it.
- OCR: Tesseract or PaddleOCR
- Storage: SQLite (stdlib sqlite3), content Fernet-encrypted (`cryptography`)
- Frontend installed: react-router-dom, framer-motion, Tailwind v4, gsap, @fontsource (Fraunces, Noto Sans/Tamil/Devanagari, Noto Serif Tamil/Devanagari), vitest, @playwright/test, @axe-core/playwright. NOT installed (ask first): tsparticles, three.js, UI kits, icon libraries.

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
- Phase 4: backend/app/safety/{names,interactions,engine,guardrails}.py, schemas/safety.py, services/safety_section.py; scripts/{build_interaction_store,export_pharmacist_sheets,import_pharmacist_sheets,add_safety_templates}.py; scripts/evidence/ (rejected ATC coverage rule, archive only); data/reference/{interactions_supplement.json,review/}; eval/phase4_safety.py; docs/{SAFETY,PHARMACIST_REVIEW}.md
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
- [x] 4 Safety layer (interaction lookup, duplicates, guardrail, safety section; dev only; supplement and ta/hi strings await review; red-flag/low-confidence handling reuse Phase 2i flags)
- [x] 5 Backend API, SQLite + Fernet, consent, confirmation overlay, schedule, delete-my-data (no UI; live smoke done; ta/hi strings and DPDP checklist unreviewed)
- [x] 5c Prototype review mode: honest author self-check of the interaction supplement, notice v2, labels (docs/REVIEW_STATUS.md)
- [x] 6 Web application UI: 6a design system, 6b working flow, 6c polish and review page, 6d sample mode + "How we tested it" + header delete icon (docs/DESIGN.md, DEMO.md, TESTING_PAGE.md)
- [~] 7 Evaluation: [x] 7a harness, protocol, stress set, photo and usability packs, freeze; [ ] 7b one-shot final test run; [ ] 7c real photos, usability sessions, native/pharmacist review
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

## Review labels (Phase 5c; docs/REVIEW_STATUS.md)
- RULE: nothing may be labelled reviewed by a pharmacist or native speaker unless a real reviewer did it. Never write a person's initials into a reviewer field; never set status "reviewed" yourself; ta/hi stay draft_unreviewed.
- `author_checked` = prototype self-check by the project author against official sources (checked_by fixed `author_prototype_selfcheck`, checked_on, basis, evidence). Enabled like reviewed, source label `curated_author_checked`, text says "may interact ... not checked by a pharmacist". Import: `scripts/import_pharmacist_sheets.py FILE --author-selfcheck`; the normal mode only sets `reviewed`.
- Consent notice v2 (prototype / machine-drafted ta,hi / author-drafted interactions); contact from CONTACT_NAME, CONTACT_EMAIL (never committed).

## Safety layer (Phase 4)
- Interaction check = table lookup, no model. Exactly four statuses: interaction_found, not_checked_no_record, not_checked_unconfirmed, not_checked_database_missing. The app says "an interaction was found" or "we could not check", NEVER "safe" or "no interaction": the DDInter download is partial (groups A,B,D,H,L,P,R,V), so absence is uninformative (ATC coverage rule rejected, 96 violations; scripts/evidence/).
- Only interaction_ready medicines are checked; the curated supplement counts only when status is reviewed (a real pharmacist) or author_checked (see Phase 5c); users see found pairs one per line (severity order) plus ONE aggregated count line per kind of not-checked.
- DDInter raw files and data/reference/interactions_ddinter.json are NEVER committed (CC BY-NC-SA); missing store fails safe. Rebuild: `python scripts\build_interaction_store.py`. Tests use synthetic fixtures only.
- Guardrail (safety/guardrails.py) scans English model lines and safety messages for reassurance, dose-change and diagnosis claims; hit = fail closed. The "you have" rule ignores conditional clauses.
- Eval: `python -m eval.phase4_safety` (cached dev outputs). Silent misses not covered by a flag must be 0. Details: docs/SAFETY.md.

## Backend API (Phase 5; details docs/API.md, PRIVACY.md, CONFIRMATION.md)
- Data origin `user_upload` vs `synthetic`: user uploads go ONLY to the localhost Ollama adapter (Gemini fails closed) and NEVER write data/cache (`extract_bytes`, `narrative.NO_CACHE`). Never log document content, names, quotes or user text (PolicyFilter: ids, states, codes).
- Key rule: never open/print backend/.env. CAREBRIDGE_DATA_KEY comes from `scripts/generate_data_key.py`; if missing, stop and ask the user to run it.
- No accounts: anonymous cookie session (hash stored), consent before processing, photo discarded unless opted in, DELETE /api/v1/session erases everything (receipt), 24 h expiry.
- Confirmation overlay (`services/confirmation.py`) is pure; the safety engine runs unchanged on it. interaction_ready only with identity and resolved reasons; name reasons clear only via formulary pick; non-daily never schedule_ready; removed/not_in_list medicines are never checked. Fail closed; never say "safe".
- Tests: synthetic only, mocked providers (tests/apihelpers.py). Live: `scripts/smoke_api.py` (dev doc only). Timings: extraction 30-60 s, narrative en ~25 s, ta ~65 s.

## Safety and product rules
- CareBridge explains and organizes. It never diagnoses, never recommends changing a dose, and always tells users to confirm with their doctor.
- Every explanation line must trace to source text.
- Low-confidence output must be flagged.
- Design for India's DPDP Act: explicit consent, data minimization, a delete-my-data function.

## Frontend rules (Phase 6; details docs/DESIGN.md)
- Direction "calm clinical editorial": paper tones, pine ink, one terracotta accent, Fraunces + Noto. Forbidden: purple gradients, centred 3-card hero, emoji icons, glassmorphism, fake logos/testimonials/statistics, identical card grids, neon. Severity/status always icon + text + colour.
- ALL visible text is a `ui.*` template (en/ta/hi; ta/hi `draft_unreviewed`): edit `scripts/add_phase6a_templates.py` or `scripts/add_phase6b_templates.py` + `scripts/p6b_*.py` (ids `ui.flow.*`), run them, then `scripts/export_ui_strings.py` (stale file fails a test). Components hold no literal text (source-scan test).
- Honest copy: never write safe, safely, guaranteed, accurate, certified, clinically validated, doctor-approved (tested); never imply a pharmacist/doctor/native speaker reviewed anything; no number without a committed metrics file; ta/hi pages always show the machine-drafted note.
- Nothing loads from the network at runtime (self-hosted fonts and photos, no CDN/analytics). CLIENT STORAGE RULE: only `carebridge.language` and `carebridge.calm` in localStorage; no sessionStorage/IndexedDB/JS cookies; no document ids, names or results in the URL query, title or history state (ids only in the route path); the photo is an in-memory Blob URL only (tests: `src/privacy.test.ts`, `e2e/flow.spec.ts`).
- NEVER use `dangerouslySetInnerHTML`/`innerHTML` (tested); render server text as text nodes. The word "safe" appears only in the negated "This does not mean they are safe." (tested). Backend-owned strings (errors, confirm, schedule, results) come from `GET /strings` and `/result`, never duplicated in the frontend.
- FLOW RULES (6b): fail closed, never auto-select a medicine, never pre-fill the picker; `POST /confirmations` REPLACES the set so always send everything; no reminders/notifications are sent; unsaved decisions prompt before leaving; delete-my-data is one dialog (all or nothing). Mocked e2e: `e2e/mock.ts` validates request bodies against docs/openapi.json. Live e2e: `playwright.live.config.ts` (needs Ollama; backend `ALLOWED_ORIGINS` must include the preview origin).
- REVIEW PAGE (6c, presentation only; confirmation semantics unchanged): list order follows API `review_level` only (cards never jump when checked); a must-confirm card is always open and never hidden, auto-selected or pre-filled; saved summary with unresolved items fails closed to "attention"; photo pane (buttons, keyboard, drag, pinch) beside the cards, full-screen dialog on phones. Header: one row from 64rem (80rem in Tamil), single-DOM menu below. Public routes make NO session call (FlowProvider boots only on flow paths; tested in `e2e/quiet.spec.ts`).
- GPU rule: Canvas 2D and CSS transforms only (no WebGL, no backdrop-filter); at most 60/24 particles, DPR cap 1.5, paused when hidden, calm, reduced-motion or on processing screens (`useProcessingScreen`). Calm mode turns off particles, cursor ring, tile drift, parallax.
- Contrast is a gate: `npm run check:contrast`. Photos: `scripts/prepare_photos.py` from `assets/photo_sources.json`; missing ones in docs/PHOTOS_NEEDED.md.

## Sample mode and testing page (Phase 6d; docs/DEMO.md, TESTING_PAGE.md)
- `/demo` = pre-recorded walk-through of dev doc ds_037 (poor) from fixtures built by `scripts/build_demo_data.py` (real API in-process, cached model outputs, never a model). `demoApi` answers `api()` under /demo from memory: ZERO /api requests, no session, nothing stored (tested). Sticky label strip "Pre-recorded sample. No photo is processed and nothing you do here is saved." + "Leave the sample" on every demo page; after Save the recorded AFTER result shows whatever was chosen, with a visible note. Never present it as a live result. DDInter excerpt: at most 6 attributed pairs (names and level only), test-enforced.
- `/how-we-tested-it`: figures only from `frontend/src/data/testing.generated.json` (`scripts/build_testing_page_data.py`, committed metrics files only); no number typed into a string; test split "not yet run" until Phase 7 extends the builder.
- Header: delete icon beside Menu from 768 px when collapsed (row from 70rem, Tamil 96rem). Specs that delete use `pressDelete`/`openMenuIfCollapsed` (e2e/flowhelpers.ts). Live specs: UI steps 45 s, long waits only for backend work and commented.
- Build: `python scripts/build_demo_data.py`, `python scripts/build_testing_page_data.py` (both `--check`).

## Commands
Backend (from `backend/`; venv is `backend/.venv`, built with Python 3.12):
- Setup `py -3.12 -m venv .venv; .venv\Scripts\pip install -r requirements.txt`; run `.venv\Scripts\uvicorn app.main:app --reload` (port 8000); test `.venv\Scripts\python -m pytest`
- Dataset (from repo root): `backend\.venv\Scripts\python data\generate_synthetic.py` then `backend\.venv\Scripts\python data\validate_dataset.py`

Frontend (from `frontend/`):
- `npm install`; `npm run dev` (port 5173, proxies /api to localhost:8000); `npm run build`

Phases 2 to 7 commands (render, evaluate, re-score, DDInter, frontend tests, final test, stress set, usability): see README.md and docs/PHASE7_PLAN.md.

## Phase 7 rules (docs/FINAL_TEST_PROTOCOL.md, PHASE7_PLAN.md)
- TEST-SPLIT LOCK: the 40 test documents (ids, text, ground truth, renders, cached outputs) are never opened, printed, hashed or listed except by `eval/final_test/run_final.py` at run time in Phase 7b; tests use a synthetic fixture repo. Never use `--final-test-run` outside 7b.
- ONE-SHOT: one official run `final-test-v1`; no change to code, prompts, rules, thresholds, formulary, templates or supplement after the tag `freeze-pre-test` (`scripts/freeze_manifest.py verify`); a re-run is labelled post-hoc (`--rerun-reason`) and never overwrites. Report whatever the numbers are, with Wilson/bootstrap intervals; never "accurate/reliable/validated".
- 7a built: protocol, freeze manifest, runner, stress set `data/stress/` (`data/build_stress_set.py`, `eval/stress/run_safety_stress.py`), real-photo pack and scorer, usability pack `docs/usability/` + `scripts/analyse_usability.py`. 7b = the run, 7c = real photos, usability sessions, stress extraction mode.

