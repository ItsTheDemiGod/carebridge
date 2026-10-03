# Decisions

- **FastAPI + pytest backend**: async-friendly, automatic validation/docs, easy to test with TestClient.
- **React + Vite + TypeScript frontend**: fast dev loop, typed UI code; Vite proxy avoids CORS during dev.
- **Tailwind CSS v4 via @tailwindcss/vite**: current default for new projects; no config file needed. Custom palette/tokens will be CSS variables in Phase 6.
- **Python 3.12 venv**: 3.11 not installed locally; 3.12 is compatible with the stack.
- **pydantic-settings for config**: typed env-var loading; API key optional until LLM phases.
- **pytest.ini sets `pythonpath = .`**: lets `pytest` import `app` from `backend/`.
- **Claude API for LLM calls**: required for explanation and faithfulness verification.
- **Storage (Postgres vs SQLite) deferred to Phase 5**: not needed until persistence exists.
- **GSAP and tsParticles deferred**: installed in Phase 6 when design work begins, per instruction.
- **Spans recorded at build time**: the generator's text buffer records offsets as it appends strings, then asserts text[start:end] equals the span. Never typed by hand; the validator re-checks.
- **Ground truth conventions**: names, duration_text, abbreviations kept as written (so extraction is not rewarded for normalising); strength, dose and numeric frequency fields normalised.
- **`.gitattributes` LF for data files**: Windows autocrlf would shift offsets.
- **Dev/test split fixed in manifest.json**: 20 dev / 40 test; test is never used for tuning (rule in CLAUDE.md).
- **Prescriptions give chronic medicines a 30-day duration; discharge summaries leave them open-ended**: matches common practice and adds variety.
- **Interaction data: DDInter + own formulary mapping** (see docs/DRUG_DATABASE_RECOMMENDATION.md). RxNav interaction API was discontinued 2 Jan 2024; DrugBank academic downloads are paused.
- **Interaction checks are table lookups, never LLM memory**; an unlisted pair means "not checked", not "safe".
