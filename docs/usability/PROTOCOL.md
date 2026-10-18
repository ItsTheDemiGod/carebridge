# Usability test protocol (Phase 7c)

**Purpose**: find out whether real people use the confirm step correctly, understand "could not check", and can find the delete function, using SYNTHETIC documents only.
**Status of the results**: five participants are a **formative check, not a statistic**. Results are reported as counts and short observation notes only: no percentages with intervals, no significance claims, no "usability score" of the product beyond the five SUS scores shown individually and as a mean with that caveat.

## Participants
- 5 adults (18+) who are not on the project team; one Tamil reader and one Hindi reader if available (they run the session in their language), the others English.
- 25 to 30 minutes each. Participation is voluntary; each may stop at any time without giving a reason. Give the information and consent sheet (`CONSENT.md`) first.
- Participants use ONLY the three prepared synthetic documents (`data/usability_samples/U1.jpg` to `U3.jpg`). Nobody uses their own medical papers or photos.

## What is recorded (and what is not)
- Recorded: participant id (P1 to P5), age band, preferred language, device, per-task outcome, errors, time, help given, picker choice correct, short neutral notes, quiz answers, SUS answers.
- NOT recorded: names, contact details, photos, video, audio, screen recordings. No key linking P1 to P5 to a person is kept. Notes contain no personal details.

## Set-up (facilitator)
1. Backend running (`cd backend; .venv\Scripts\uvicorn app.main:app`), local model loaded (`ollama ps`: at least 80 percent GPU), frontend served (`cd frontend; npm run build; npx vite preview --port 4173`) with `ALLOWED_ORIGINS` including `http://localhost:4173`. Open `http://localhost:4173`.
2. The three images on the desktop as U1, U2, U3. Printed copies of the task cards, the quiz and the SUS sheet; `session_sheet.csv` open for you.
3. Between participants: use "Delete my data" in the app and close the tab.

## Facilitator rules
- Read the task card aloud as written, nothing more. Neutral prompts only: "What are you thinking?", "What would you do next?", "What do you expect that button to do?". Never explain the interface, never hint, never say "good" or "wrong".
- Think-aloud is requested, not forced.
- Help only if the participant is stuck for more than 90 seconds on one step. Then give the smallest neutral nudge ("take your time; is there anything on the screen you have not tried?") and **record that help was given** (and what kind). If still stuck after another 60 seconds, mark the task not completed and move on.
- Time each task from the end of reading the card to the participant saying they are done (stopwatch). Count errors (a wrong or unrecoverable action, a wrong answer, a wrong picker choice) and write one neutral line.
- Do not coach on the quiz or the SUS. Do not discuss the answers until the debrief.

## Order of a session (about 25 to 30 minutes)
1. Welcome, information and consent sheet, questions answered (3 min).
2. Tasks 1 to 4 with think-aloud (15 to 18 min), see `TASKS.md`.
3. Comprehension quiz, 6 questions (3 min), see `QUIZ.md`.
4. System Usability Scale, 10 items (2 min), see `SUS.md`.
5. Debrief (2 min), see `DEBRIEF.md`.

## Observation prompts (write what you see, not what you think)
- Did the participant read the "what your check means" text before deciding? Did they compare the photo with the card?
- On the flagged medicine: did they open the picker, type, and choose a drug; did they pick the drug on their paper (correct) or another one?
- Did they leave anything unchecked and press Save anyway? What did they expect then?
- On the results: which words did they use for "could not check"? Did they say or imply it means "safe" or "fine"?
- Did they find the interaction line and read its listed level? Did they say what they would do next?
- Where did they look for "Delete my data"? How many clicks? Did they read the dialog?
- Any language or script difficulty (Tamil, Hindi), anything that looked broken.

## Data entry and analysis
Fill `session_sheet.csv` (one row per participant per task), `quiz_answers.csv` and `sus_responses.csv` (templates in this folder; copy them to a working folder and fill them there). Then run `backend\.venv\Scripts\python scripts\analyse_usability.py --dir <folder with the three filled CSVs>`; it writes `eval/results/usability-v1/summary.json` and `summary.md` (counts, picker accuracy, quiz per question, SUS per participant and mean, help counts; no free-text notes and no personal data). Report the counts and a few anonymised observation quotes. Nothing else.

## Stop rules
Stop a session at once if the participant is distressed or asks to stop. Nothing about a stopped session is analysed beyond the fact that it stopped.
