# Progress

## Phase 0: Setup and foundation (complete)
**Built**
- Repo layout, CLAUDE.md, README, .gitignore, attribution table.
- Backend: FastAPI app with `GET /api/health` (`{status, app, version}`), CORS for http://localhost:5173, pydantic-settings config (optional `ANTHROPIC_API_KEY`).
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
