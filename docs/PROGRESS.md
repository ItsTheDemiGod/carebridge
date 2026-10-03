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
