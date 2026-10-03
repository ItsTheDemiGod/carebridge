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
