# CareBridge

## Summary and goal
Multilingual post-discharge companion. Users upload a discharge summary or prescription; the system extracts medicines, explains the document in plain English/Tamil/Hindi, verifies the explanation against the source, checks drug interactions, and builds a daily medication schedule.
End goal: a professional web app first; a mobile app only if time allows. College "AI in Healthcare" project.

## Tech stack
- Frontend: React + Vite + TypeScript, Tailwind CSS, Framer Motion, GSAP, tsParticles
- Backend: FastAPI, Python 3.11+, pytest
- LLM: Claude API
- OCR: Tesseract or PaddleOCR
- Storage: PostgreSQL or SQLite (decided in Phase 5)
- Currently installed (Phase 0): react-router-dom, framer-motion, Tailwind v4 (@tailwindcss/vite). GSAP and tsParticles are NOT installed yet.

## Folder layout
- CLAUDE.md, README.md, .gitignore
- docs/PROGRESS.md, docs/DECISIONS.md
- backend/ : FastAPI app (app/, tests/, requirements.txt, .env.example)
- frontend/ : Vite React TS app
- data/synthetic/, data/ground_truth/ : synthetic documents and their labels
- eval/ : evaluation scripts
- assets/ATTRIBUTION.md : photo credits (file, source URL, photographer, license)

## Phases
Status: [x] done, [ ] not started, [~] in progress
- [x] 0 Setup and foundation
- [ ] 1 Synthetic data, schema, drug database choice
- [ ] 2 Document extraction pipeline plus evaluation script
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

Frontend (from `frontend/`):
- Install: `npm install`
- Run: `npm run dev` (port 5173, proxies /api to localhost:8000)
- Build: `npm run build`
