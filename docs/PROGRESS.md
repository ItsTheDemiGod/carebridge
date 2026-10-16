# Progress

## Phase 0: Setup and foundation (complete)
**Built**
- Repo layout, CLAUDE.md, README, .gitignore, attribution table.
- Backend: FastAPI app with `GET /api/health` (`{status, app, version}`), CORS for http://localhost:5173, pydantic-settings config (optional `ANTHROPIC_API_KEY`, replaced by `GEMINI_API_KEY` in Phase 2).
- Frontend: Vite + React + TS, Tailwind v4, react-router-dom, framer-motion. Placeholder page shows "CareBridge" and "Backend connected" / "Backend unreachable" from `/api/health`. Vite proxies `/api` to port 8000.

**Run**: see Commands in CLAUDE.md.

**Tested**: `pytest` 2 passed (health endpoint, CORS header). `npm run build` succeeds.

**Open issues**
- Python 3.11 is not installed on this machine; venv uses 3.12 (compatible).
- framer-motion is installed but not yet used.
- Live end-to-end check of the proxy (both servers running) was not done in this phase.
- The project folder was not actually git-initialized at the start; `git init` was run in Phase 0.

**Next**: Phase 1 (synthetic data, schema, drug database choice).

## Phase 1: Data foundations (complete)
**Built**
- `backend/app/schemas/extraction.py` (Pydantic v2 schema with SourceSpan) and `extraction.schema.json` (regenerate: `python -m app.schemas.extraction` from `backend/`).
- `data/reference/formulary.json`: 66 medicines, marked `unverified_requires_pharmacist_review`; no doses beyond available strengths, no interaction claims.
- `data/generate_synthetic.py`: deterministic rule-based generator (seeded, no LLM) for 60 documents (40 discharge summaries, 20 prescriptions), 9 case templates (listed in the file header for clinician review), 3 difficulty levels.
- `data/validate_dataset.py` and `backend/tests/test_dataset.py`.
- `docs/DRUG_DATABASE_RECOMMENDATION.md`: recommends DDInter for interaction pairs plus our formulary for brand-to-generic.
- `.gitattributes` forces LF on dataset files, because offsets break if Git converts line endings.

**Run** (from repo root)
- `backend\.venv\Scripts\python data\generate_synthetic.py` (regenerates everything identically)
- `backend\.venv\Scripts\python data\validate_dataset.py` (prints summary table, exits 1 on errors)

**Tested**: full backend suite passes (schema tests, dataset validator, health). Validator checks parse, span text equals document text at offsets, names and strengths against formulary, manifest/file match, counts 60/40/20/20/40, difficulties in both splits, all templates in test split, 8+ docs with brand-only and generic-only medicines.

**Open issues**
- Formulary and case templates need pharmacist/clinician review before any real use.
- Synthetic text is rule-based, so it is more regular than real documents; Phase 7 should add a few real-style variations.
- Ground truth names are "as written" but strength/dose are normalised; Phase 2 evaluation must compare accordingly (case-insensitive names).
- DDInter CSV coverage of the formulary is unchecked (its 8 files omit ATC groups C, G, J, M, N); needs approval to download.

**Next (Phase 2)**: OCR/text input, LLM extraction into the schema, and an evaluation script scored on the DEV split only.

## Phase 2: Extraction pipeline and evaluation (DONE, local Ollama)
**Built**
- Data fixes: patient names now match sex (independent RNG; manifest and medication lists proven unchanged vs the Phase 1 commit by `test_data_stability.py`); new `unspecified` timing label (replaces `other` when a frequency has no time/meal relation).
- Gemini config (`GEMINI_API_KEY`, `GEMINI_MODEL=gemini-3.8-flash`, `GEMINI_MAX_REQUESTS_PER_MINUTE=5`, `GEMINI_MAX_RETRIES=5`), smoke test (passes), model choice recorded in DECISIONS.md.
- `extraction_output.py` (source_quote, confidence, unreadable_parts; accepted by Gemini structured output as-is), `extraction_v1.txt` prompt, `services/extraction.py` (text/PNG/JPG/PDF, temperature 0, validation retry once, 429/5xx backoff honouring retry hints, per-minute throttle, disk cache, latency and token usage), `services/guards.py` (synthetic-only path guard, test-split guard + log).
- `data/render_documents.py`: 4 conditions x 60 docs (+ PDFs for clean and scan), deterministic, text kept inside image bounds (asserted); preview at `docs/samples/render_preview.png`.
- `eval/evaluate.py` + `eval/matching.py`: all metrics requested, broken down by condition, difficulty and split; oracle run scores perfectly (`eval/results/oracle-dev`).
- DDInter download and coverage check (`docs/DDINTER_COVERAGE.md`): usable with a small pharmacist-reviewed supplement; 692 of 2,145 formulary pairs have no data.

**How to run**: see Commands in CLAUDE.md.

**Tested**: 37 offline tests pass (mocked Gemini: success, validation retry, backoff, daily quota, cache hit, guards; evaluator cases; render determinism and completeness). One live test (`-m live`) passes. Dataset regenerates identically.

**Dev metrics: NOT AVAILABLE.** The free tier allows only 20 requests per day for `gemini-3.8-flash` (seen in the 429 error on 2026-10-04); the full dev run needs about 100. Only 6 text-condition documents were extracted. No prompt tuning (v2/v3) was done. See docs/PROMPT_LOG.md.

**Open issues / known limitations**
- Free-tier rate limits are not published in the docs (AI Studio only); 5 requests per minute is a guess.
- Occasional 503 "high demand" errors from Gemini; the evaluator does not score those documents (reports `api_failed_not_scored`) and a rerun resumes from the cache.
- ATC groups in the DDInter check were assigned from general knowledge, not verified.
- Evaluator thresholds (name similarity 0.8, text similarity 0.6, fuzzy quote 0.9) are untuned defaults.

**Next**: finish the dev run (options in the report), then Phase 3 (plain-language explanation EN/TA/HI plus faithfulness verification).


### Phase 2 final entry (local Ollama provider)
**Built**: `app/llm/` provider layer (Gemini adapter unchanged in behaviour; new localhost-only Ollama adapter using httpx, image downscaling, thinking off, context_truncated and image_not_received guards, PDFs unsupported); provider-aware cache key; evaluator now reports attempted/scored/skipped per condition with reasons, latency median and p95, and a drug-name sanity metric (`eval/name_sanity.py`). Model `qwen3-vl:8b-instruct` (same 8B size as the thinking tag, which ignored `think:false`).
**Key fix**: the Pydantic schema marks only `document_type` as required, so the model returned empty medication lists; the adapter now sends a copy with all properties required (our validation is unchanged).
**Run**: `python -m eval.evaluate --split dev --conditions text,clean,scan,photo,poor --run-id NAME` (about 50 min, resumable from the cache). Config in CLAUDE.md.
**Dev metrics, prompt v1 (kept default)**: medicine F1 0.964 text, 0.988 clean/scan/photo/poor; 7 hallucinated medicines in 100 calls; no documents skipped; follow-up and red-flag recall 1.0. Median latency 27-30 s per call. Weak: fully-correct medicines 0.24-0.40, invented values 0.20-0.35, brand/generic accuracy 0.59-0.83, timing label 0.69-0.77 (AC/PC confusion). Drug names matching no formulary entry: 13% text, 2-5% images. Details: `eval/results/dev-ollama-v1`, prompt history in `docs/PROMPT_LOG.md` (v2, v3 tried and rejected).
**Tested**: offline suite passes (mocked Ollama and Gemini, guards, evaluator).
**Limitations**: one small model; the name-field confusion (brand vs generic) is unresolved; no Gemini baseline exists; PDFs unsupported locally; 8 GB GPU means about 30 s per document; the 1500-token image check threshold is calibrated on only a few images.
**Phase 3**: plain-language explanation (EN/TA/HI) with faithfulness verification; Phase 7 can retune the prompt (combine the AC/PC rule with v1).
**Sanity metric limit**: threshold 0.8 flags grossly wrong names only; a one-letter garble such as `AtoRavastatin` still scores 0.96 against `atorvastatin`. Exact-name accuracy against ground truth (acc_brand_name/acc_generic_name) is the stricter check.

## Phase 2h: Normalisation layer (DONE)
**Built**: `backend/app/normalisation/abbreviations.py` (deterministic frequency/timing/PRN/duration rules from the verbatim quote, ambiguity flags), `names.py` (formulary resolver; thresholds chosen from the formulary's own confusable pairs), `services/normalisation.py` + `schemas/normalised.py` (rule value final, model value and provenance kept, flags, needs_verification), `eval/rescore.py` (raw vs normalised from cached outputs, flag effectiveness). Rules and numbers: `docs/NORMALISATION.md`.
**Run**: `python -m eval.evaluate --split dev --run-id dev-ollama-v1 --rescore normalised` (no model calls).
**Dev result (prompt v1 cached outputs, all conditions, raw -> normalised)**: medicine F1 0.983 -> 0.998; fully-correct medicines 0.31 -> 0.81; timing label 0.73 -> 0.99; brand 0.67 -> 0.98; generic 0.73 -> 0.99; hallucinated medicines 7 -> 1; invented-value rate 0.29 -> 0.056. 133 of 420 medicines flagged for verification; 1 name error and 1 timing error remain unflagged.
**Tested**: 149 offline tests (67 abbreviation cases, resolver incl. every formulary name, service).
**Limits**: 66-drug formulary and synthetic names make name scores optimistic; rules depend on the model's quote being complete; flag precision is low (0.10 for names); one revision used.
**Next**: Phase 3 (explanation EN/TA/HI + faithfulness); Phase 4 will use `resolved_generic` for interaction checks.

## Phase 2i: Hardening of the normalisation layer (DONE)
**Built**: strict quote checks (`app/normalisation/quote_check.py`: normalised-exact and strict-fuzzy with digit and dosing-token gates, threshold 0.95 from the dev distribution), `incomplete_quote` flag (model output only; one revision, 60 -> 18 flagged medicines), `review_level` (must_confirm/note/none, `needs_verification` kept as alias), `interaction_ready` and `schedule_ready`, evaluator reporting (`eval/rescore.py`, output `eval/results/dev-ollama-v1-normalised-v2`). Details and numbers: `docs/NORMALISATION.md` (Phase 2i).
**Strength finding**: the ten strength mismatches are model errors on documents where the generator deliberately omits the strength; ground truth was correct, nothing changed.
**Dev result**: 194 of 420 medicines at must_confirm (46%, was 32% in 2h); all 14 remaining name errors flagged; 1 timing error (truncated quote) unflagged; interaction_ready 226 with 0 wrong resolved_generic; schedule_ready 180 with 1 wrong timing label. Quote validity pooled: exact 0.81, normalised-exact 0.92, strict 0.95.
**Tested**: 174 offline tests.
**Limits**: synthetic names use the same formulary as the resolver (optimistic); the confirm load is high for photo and poor conditions (54% and 58%); one model run.
**Next**: Phase 3 (explanations and faithfulness); Phase 4 consumes interaction_ready; Phase 6 consumes schedule_ready.

## Phase 3: Plain-language explanation EN/TA/HI and faithfulness verification (DONE on the dev set)
**Built**: explanation schema (per-language status, display mode, verification record); fixed templates (`data/templates/templates.json`, 54 ids x en/ta/hi) and a deterministic medicine-line engine; review-sheet export/import (placeholder-safe, refuses the whole file); narrative service (prompts A to D, text-only Ollama, batched, cached, retry, id reconciliation); verification (7 deterministic checks plus judge, Tamil/Hindi via back-translation); assembly with the fallback rule; corruption evaluation; English readability; review pack (10 dev documents) and `docs/TRANSLATION_REVIEW.md`. Design: `docs/EXPLANATION.md`; prompt history: `docs/EXPLANATION_PROMPT_LOG.md`.
**Run**: see README (Phase 3). Results: `eval/results/phase3-dev-clean/{metrics.md,metrics.json,corruptions.json}` (v1 numbers in `phase3-dev-clean-prompt-v1`).
**Dev result (prompt v2, 135 free-text lines, 20 docs, clean)**: verified en 1.00, hi 0.76, ta 0.27; fallback to original English ta 73%, hi 24%. Failures are judge verdicts (Tamil: 49 contradicts, 34 omits). 160 calls, 1,974 s. Corruptions: number change and wrong script caught 100% by the deterministic checks; negation drop, invented advice, dropped clause and swapped timing are caught by the judge (deterministic alone: 0% for negation and timing); false-reject on the source line itself 0%.
**Tested**: offline suite passes (golden English medicine lines, exhaustive enum combinations x 3 languages, template completeness and placeholder consistency, review-sheet import rejections, mocked model for every verification case, corruptions, readability, review pack).
**Issues found**: (1) Tamil whole-document translation hit a repetition loop until the token limit (9 of 20 docs): fixed in code with chunking, per-line retry and failure caching. (2) The English simplification returns the source unchanged for 64 of 135 lines, so English verification is nearly trivial and the simplification gain is small (FK 3.65 to 2.88). (3) The dev free-text lines have no formulary drug names and no urgency cues, so those two corruption types were measured on 10 fixed probe lines (not dev lines). (4) Tamil quality is poor (wrong nouns); the checker catches it but most Tamil lines fall back to English.
**Limits**: same model writes and judges; no native review yet; back-translation can hide an error; dev set only (test split untouched, no --final-test-run); number words are not checked; Tamil/Hindi negation and urgency rest on the judge.
**Needs the user**: send the review pack to a Tamil and a Hindi reviewer; decide whether to try a stronger model for Tamil (Phase 7).
**Next**: Phase 4 (safety layer: interactions for interaction_ready medicines, red flags, no-diagnosis guardrail).

## Phase 3e: Phrase library, provenance labels, stress set (DONE on the dev set)
**Housekeeping**: `eval/results/phase3-dev-clean-prompt-v1/metrics.json` run_id corrected to match its folder name.
**Built**: provenance + `label_key` on every text (`schemas/explanation.py`, `label.*` templates); `data/templates/phrases.json` (91 phrases: 44 advice, 34 warning, 13 follow-up; en/ta/hi, draft_unreviewed); strict matcher `services/phrase_match.py` with near-miss reporting; pipeline order library -> model -> original in `services/explain.py`; phrase review sheet export/import; stress set `eval/stress/` and `eval/phase3e_metrics.py`; review pack with provenance column; `docs/PHRASE_LIBRARY.md`.
**Run**: see README (Phase 3e). Results: `eval/results/stress-v1`, `eval/results/phase3e-dev-clean`.
**Stress (blind, small samples)**: English false-reject 1/20, detection 19/20 (judge 0.95, deterministic 0.25; missed one item_merged); Tamil false-reject 3/6, detection 6/6; Hindi false-reject 1/6, detection 6/6. Simplifier on 15 harder lines: all changed, FK median 13.9 -> 8.3, 14/15 verified, no fact lost or added per judge.
**Dev re-run**: library matches 9/135 lines (6.7%); shown in language: Hindi 81% (was 76%), Tamil 25% (was 27%, batching noise); English 100%. Stress-source coverage 4/55. 160 calls, 64 fresh.
**Issues**: (1) the `you have` diagnosis regex false-rejects correct warnings ("if you have chest pain") although the judge says supported: 3 of 7 correct warning candidates across languages; suggest limiting it to statements not introduced by if/when (needs your decision). (2) Library coverage is low; it must not be extended from dev lines. (3) Tamil judge false-rejects with `adds_information` from back-translation noise. (4) Same 8B model writes, back-translates and judges.
**Needs you**: send `docs/review_pack/review_{ta,hi}.{html,csv}`, `docs/review_pack/phrase_review_sheet.csv` and `data/templates/review_sheet.csv` to reviewers when ready (nothing is marked sent).

## Phase 4: Safety layer (DONE on the dev set)
**Built**: conditional-clause fix for the "you have" check (4-0); DDInter-derived store builder and lookup with four statuses (`app/safety/{names,interactions}.py`, `scripts/build_interaction_store.py`); 16-pair curated supplement drafted from official labels (draft_unreviewed, ignored by the app until a pharmacist reviews it) plus pharmacist export/import tools and instructions (`docs/PHARMACIST_REVIEW.md`); safety engine (pairs, duplicates, counts, overall_state, reminder), guardrail, 14 new safety templates (ta/hi draft_unreviewed) and a "safety" section in the explanation; dev evaluation (`eval/phase4_safety.py`); `docs/SAFETY.md`.
**Decision**: the ATC coverage rule was rejected (96 violations: secondary/combination ATC codes; every drug appears as a partner in all 8 files). The app says only "interaction found" or "could not check" (DECISIONS.md, DDINTER_COVERAGE.md addendum).
**Run**: see README (Phase 4). Results: `eval/results/phase4-dev/`.
**Dev result**: ground truth has 96 of 148 pairs with a DDInter interaction (moderate 21, minor 14, unknown 61, major 0). Strict silent misses 3 (evaluator could not match a garbled row), silent misses not covered by a flag 0; 328 downgrades to not_checked_unconfirmed; 0 false alarms; share of pairs not checked 0.68 (text) to 0.89 (poor); no duplicate medicines in the dev set.
**Tested**: 483 offline tests (store/lookup statuses, engine branches, guardrail families and every English template/phrase, safety section, pharmacist sheets, the "you have" rule). Guardrail rerun on cached dev lines: no verified line changed; stress false-rejects unchanged.
**Limits**: DDInter is partial, so most unchecked pairs say nothing; 11 of 16 supplement entries apply class-level label statements; ta/hi safety strings unreviewed; the extraction must see a medicine for it to be checked; dev set only.
**Needs you**: send `send_to_reviewers/pharmacist/` to the pharmacist (about Oct 19 to 25) and `send_to_reviewers/tamil_hindi/` to the native reviewers; nothing is marked sent.
**Next**: Phase 5 (backend API, database, consent, encryption, delete-my-data).

## Phase 5: Backend API, database, consent, privacy, confirmation, schedule, delete-my-data (DONE; no UI)
**Built**: FastAPI app factory (`app/main.py`), 21 paths (`docs/API.md`, `docs/openapi.json`); SQLite + Fernet (`app/db/`); sessions, consent notice v1, CSRF/Origin checks; raw-body upload with hardening; single worker with queue and timeout; medicines review and formulary picker; confirmation overlay (`docs/CONFIRMATION.md`); result, schedule (suggestions), adherence, doctor summary (counts only); delete-my-data with receipt, expiry sweep, logging policy; 91 new templates (ta/hi drafts); `docs/PRIVACY.md` (written first).
**Run**: README (Phase 5). Key: `backend\.venv\Scripts\python scripts\generate_data_key.py`; API: `cd backend; .venv\Scripts\uvicorn app.main:app`; smoke: `python scripts\smoke_api.py`.
**Tested**: 716 offline tests (was 483). Live smoke on dev ds_037, clean and poor: see `docs/smoke/phase5_live_smoke.json`. Extraction 59 s / 47 s, narrative en 24 s, ta 63-65 s (after extraction), total 147 s / 136 s; the narrative started at awaiting_confirmation and was still running when confirmation was sent; deletion left 0 rows.
**Frozen code**: only additive changes (`extract_bytes`, origin guard, `NO_CACHE`).
**Open**: ta/hi strings unreviewed (`data/templates/review_sheet_phase5_new.csv`); consent notice and DPDP checklist not lawyer-reviewed; the guardrail `you have` rule still false-flags "You have reached..."; Hindi narrative not exercised live; no auth beyond the anonymous session; single-process only.
**Next**: Phase 6 (web UI).

## Phase 5c: Prototype review mode (DONE)
**Decision**: prototype without clinical validation; no independent reviews. The review step became an honest author self-check with explicit labels (`docs/REVIEW_STATUS.md`, `docs/DECISIONS.md`).
**Built**: status `author_checked` (loader, source label `curated_author_checked`, safe fail-closed on missing audit fields); `--author-selfcheck` import mode (cannot produce `reviewed`; normal mode cannot produce `author_checked`); attribution variant, interaction-pair wording and brand-mapping notice (ta/hi drafts, `data/templates/review_sheet_phase5c_new.csv`); self-check of all 16 pairs against re-fetched official sources (`data/reference/review/interactions_supplement_selfcheck.csv`): 16 agree, 16 enabled, no severity changed; `docs/FORMULARY_STATUS.md`; consent notice v2 with prototype, machine-drafted ta/hi and author-drafted interaction statements; `CONTACT_NAME`/`CONTACT_EMAIL` settings; `docs/openapi.json` regenerated.
**Run**: `python scripts\import_pharmacist_sheets.py data\reference\review\interactions_supplement_selfcheck.csv --author-selfcheck` (already applied); `python scripts\add_phase5c_templates.py`.
**Tested**: 735 offline tests (was 716).
**Open**: no independent review exists; formulary brands unverified; UK/EU current SmPC text for domperidone was read on emc.medicines.org.uk (not a regulator domain) as corroboration, regulator sources cited are HPRA and EMA; set CONTACT_EMAIL in backend/.env if wanted.
**Next**: Phase 6 (web UI).

## Phase 6a: Frontend design system, shell, ambient motion layer, landing page (DONE; flow comes in 6b)
**Built**: tokens, self-hosted fonts, 19 hand-drawn icons, base components, wordmark (`docs/DESIGN.md`); 114 `ui.*` templates (en/ta/hi, ta/hi drafts) exported to `frontend/src/i18n/strings.generated.json`; typed API client; i18n runtime and language switching with the persistent draft note; routes `/`, `/how-it-works`, `/privacy` (live consent notice), `/start` (placeholder), 404; particle field, cursor ring, drifting tile mosaic, GSAP scroll effects, calm mode; four Commons photographs (CC0 and CC BY) with duotone; landing page. Step 0: safety re-check with the 16 author-checked supplement pairs enabled changed nothing on the dev set (`eval/results/phase4-dev-with-supplement/`: strict silent misses 3, not covered by a flag 0, false alarms 0, pairs found per condition text 48, clean 40, scan 26, photo 19, poor 16, same as before); S11 note recorded.
**Run**: `cd frontend; npm install; npm run dev` (backend on 8000 for /privacy). Strings: `python scriptsdd_phase6a_templates.py; python scripts\export_ui_strings.py`. Photos: drop files in `frontend/public/photos/raw/`, edit `assets/photo_sources.json`, `python scripts\prepare_photos.py`.
**Tested**: 855 backend tests (was 735), 18 vitest, 32 Playwright (site, axe, perf), contrast 36/36, build passes. Details and numbers in `docs/DESIGN.md`. Screenshots: `docs/screenshots/phase6a/`.
**Open**: 6 of 10 photo themes missing (`docs/PHOTOS_NEEDED.md`); ta/hi UI strings unreviewed (`data/templates/review_sheet_phase6a_new.csv`); GPU memory effect not measurable; lint shows 4 warnings (fast-refresh exports, one setState in an effect).
**Next**: Phase 6b (consent, upload, confirmation, results, schedule).

