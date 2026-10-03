# CareBridge

A multilingual post-discharge companion web app. Upload a discharge summary or prescription; CareBridge extracts the medicines, explains the document in plain English, Tamil and Hindi, verifies the explanation against the source, checks drug interactions, and builds a daily medication schedule.

Built for an "AI in Healthcare" class project. It explains and organizes; it never diagnoses or changes doses. All documents are synthetic.

## Run

Backend (http://localhost:8000):

    cd backend
    py -3.12 -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    uvicorn app.main:app --reload

Frontend (http://localhost:5173):

    cd frontend
    npm install
    npm run dev

Dataset (from repo root):

    backend\.venv\Scripts\python data\generate_synthetic.py
    backend\.venv\Scripts\python data\validate_dataset.py

Tests: `cd backend && .venv\Scripts\python -m pytest`. Frontend build: `cd frontend && npm run build`.

See `CLAUDE.md` for the project plan and `docs/PROGRESS.md` for status.
