# CareBridge

CareBridge is a multilingual after-hospital companion. You give it a photo or text of a discharge summary or a prescription; it lists the medicines it finds, explains the document in plain English, Tamil or Hindi, checks the explanation against the source, looks for known drug interactions, and builds a daily medicine schedule.

**Status: class project prototype ("AI in Healthcare"). Not medical advice.** CareBridge explains and organises; it never diagnoses and never changes a dose. All documents in this repository are synthetic. Tamil and Hindi text is machine-drafted and has not been reviewed by a native speaker; the interaction notes have not been reviewed by a pharmacist.

## Try the sample
- Hosted pre-recorded sample (no photo is processed, nothing is saved): **https://itsthedemigod.github.io/carebridge/** (the address is expected once GitHub Pages is switched on for this repository).
- **The real flow runs only on the owner's computer, with a local model.** The hosted site is a recorded walk-through of one synthetic document, not a live service.

## What exists and what was tested
- A FastAPI backend (extraction with a local Ollama vision model, rule-based normalisation, explanation with a verification step, interaction lookup, daily schedule, anonymous session with consent and a delete-my-data function) and a React web app (English, Tamil, Hindi).
- 60 synthetic documents (40 held out for one official test run), a 30-prescription safety stress set, and written protocols. Results, with intervals and with what is **not** claimed: [`docs/FINAL_TEST_RESULTS.md`](docs/FINAL_TEST_RESULTS.md) (official one-shot run), [`docs/FINAL_TEST_POSTHOC.md`](docs/FINAL_TEST_POSTHOC.md), [`docs/STRESS_RESULTS.md`](docs/STRESS_RESULTS.md). The same figures are on the app's "How we tested it" page.
- Known limits, in one list: [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md). Not done: real-photo test, usability sessions, pharmacist and native-speaker review, clinical validation.

## Quick start (Windows, PowerShell)
Backend (http://localhost:8000; Python 3.12):

    cd backend
    py -3.12 -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
    copy .env.example .env      (never commit .env; Gemini is optional and only for comparison)
    .venv\Scripts\uvicorn app.main:app --reload

Frontend (http://localhost:5173):

    cd frontend
    npm install
    npm run dev

Sample mode needs no backend and no model: open `/demo` in the running frontend ([`docs/DEMO.md`](docs/DEMO.md)).
Real uploads need [Ollama](https://ollama.com) with `qwen3-vl:8b-instruct`, running on the same computer, and a data key from `backend\.venv\Scripts\python scripts\generate_data_key.py`.

Tests: `cd backend; .venv\Scripts\python -m pytest`, then `cd frontend; npm test; npx playwright test`. All other commands (evaluation, datasets, reviews, phases): [`docs/COMMANDS.md`](docs/COMMANDS.md).

## Repository map
| folder | purpose |
|---|---|
| `backend/` | FastAPI app (`app/`), tests (`tests/`), `requirements.txt`, `.env.example` |
| `frontend/` | Vite + React + TypeScript web app, unit tests, Playwright specs |
| `data/` | synthetic document generator, dataset, stress set, formulary, templates and reference data |
| `eval/` | evaluation code and committed results (`eval/results/`, read-only once published) |
| `scripts/` | build, import/export and check scripts |
| `docs/` | plans, decisions, protocols, results, design, privacy, limitations |
| `assets/` | photograph credits and sources |

Project plan and status: [`CLAUDE.md`](CLAUDE.md), [`docs/PROGRESS.md`](docs/PROGRESS.md), [`docs/DECISIONS.md`](docs/DECISIONS.md).

## What is not here
- No real patient data, ever.
- The DDInter interaction data is **not** redistributed (CC BY-NC-SA 4.0). Only a tiny attributed excerpt (at most six pairs) is in the sample fixtures. To rebuild the interaction store yourself, download the files from https://ddinter.scbdd.com/download/ into `data/reference/ddinter/raw/` and run `python scripts\build_interaction_store.py` ([`docs/DDINTER_COVERAGE.md`](docs/DDINTER_COVERAGE.md)).
- Model weights are not included: pull them with Ollama (`ollama pull qwen3-vl:8b-instruct`).
- No keys or `.env` files; only `backend/.env.example`.

## Licence and third-party material
The project is under the **MIT licence** ([`LICENSE`](LICENSE)). It covers the project's own source code, its documentation, and the synthetic documents and datasets authored by the project. It does **not** cover third-party material, which keeps its own licence: the small DDInter-derived excerpt in the sample fixtures (CC BY-NC-SA 4.0: non-commercial, share-alike, attribution required), the photographs (see [`assets/ATTRIBUTION.md`](assets/ATTRIBUTION.md); some require credit), the fonts, and library code. Details: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). MIT's "as is" disclaimer applies; CareBridge is a class project prototype and not medical advice.
