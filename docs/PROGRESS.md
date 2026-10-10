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
