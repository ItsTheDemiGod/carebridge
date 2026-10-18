r"""Aggregate the usability sessions (Phase 7c).   backend\.venv\Scripts\python scripts\analyse_usability.py [--dir DIR] [--out eval/results/usability-v1]

Reads session_sheet.csv, quiz_answers.csv and sus_responses.csv from DIR (default docs/usability; copy the templates and fill them in a working folder), plus the
answer key docs/usability/quiz_key.json. Writes summary.json and summary.md: task completion counts, errors, median time, help given, picker accuracy, quiz results per
question (and the critical wrong answers), SUS per participant and the mean. Standard library only. The free-text notes column is never read or written; participant ids
are the pseudonyms P1 to P5. Five participants are a formative check, not a statistic: counts and means are shown without any significance claim."""
import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEY = REPO / "docs" / "usability" / "quiz_key.json"
YES = {"yes", "y", "true", "1"}
NO = {"no", "n", "false", "0"}
NOTE = "Five participants are a formative check, not a statistic. Counts and means only; no significance is claimed and no benchmark is applied."


def sus_score(responses: list[int]) -> float:
    """Standard SUS: odd items contribute (response - 1), even items (5 - response); the sum times 2.5 gives 0 to 100."""
    if len(responses) != 10 or any(not isinstance(r, int) or not 1 <= r <= 5 for r in responses):
        raise ValueError("SUS needs ten answers from 1 to 5")
    return sum((r - 1) if i % 2 == 0 else (5 - r) for i, r in enumerate(responses)) * 2.5


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


def yn(v: str):
    v = v.lower()
    return True if v in YES else False if v in NO else None


def analyse(folder: Path, key: dict | None = None) -> dict:
    key = key or json.loads(KEY.read_text(encoding="utf-8"))
    sess = [r for r in rows(folder / "session_sheet.csv") if r.get("completed", "") != ""]
    tasks = defaultdict(lambda: dict(rows=0, completed=0, errors_total=0, times=[], help_given=0))
    people = {}
    picker = Counter()
    for r in sess:
        t = tasks[r["task"].upper()]
        t["rows"] += 1
        c = yn(r["completed"])
        t["completed"] += bool(c)
        t["errors_total"] += int(r["errors"]) if r.get("errors", "").isdigit() else 0
        if r.get("time_seconds", "").replace(".", "", 1).isdigit():
            t["times"].append(float(r["time_seconds"]))
        t["help_given"] += bool(yn(r.get("help_given", "")))
        people[r["participant_id"]] = (r.get("age_band", ""), r.get("preferred_language", ""), r.get("device", ""))
        p = yn(r.get("picker_choice_correct", ""))
        if p is not None:
            picker["answered"] += 1
            picker["correct"] += p
    quiz_rows = [r for r in rows(folder / "quiz_answers.csv") if any(r.get(f"q{i}") for i in range(1, 7))]
    per_q = {f"q{i}": dict(answered=0, correct=0, critical_wrong=0) for i in range(1, 7)}
    scores = {}
    for r in quiz_rows:
        n = 0
        for q, ans in ((f"q{i}", r.get(f"q{i}", "").lower()) for i in range(1, 7)):
            if not ans:
                continue
            per_q[q]["answered"] += 1
            ok = ans == key["correct"][q]
            per_q[q]["correct"] += ok
            n += ok
            per_q[q]["critical_wrong"] += ans in key["critical_wrong"].get(q, [])
        scores[r["participant_id"]] = n
    sus = {}
    for r in rows(folder / "sus_responses.csv"):
        vals = [r.get(f"s{i}", "") for i in range(1, 11)]
        if all(v.isdigit() for v in vals):
            sus[r["participant_id"]] = sus_score([int(v) for v in vals])
    out = dict(
        note=NOTE,
        participants=len(people), languages=dict(Counter(v[1] for v in people.values() if v[1])), age_bands=dict(Counter(v[0] for v in people.values() if v[0])), devices=dict(Counter(v[2] for v in people.values() if v[2])),
        tasks={k: dict(participants=v["rows"], completed=v["completed"], errors_total=v["errors_total"], median_time_s=round(statistics.median(v["times"]), 1) if v["times"] else None, help_given=v["help_given"]) for k, v in sorted(tasks.items())},
        picker=dict(answered=picker["answered"], correct=picker["correct"]),
        quiz=dict(participants=len(quiz_rows), per_question=per_q, correct_per_participant=scores, critical_errors_total=sum(q["critical_wrong"] for q in per_q.values())),
        sus=dict(participants=len(sus), scores=sus, mean=round(statistics.mean(sus.values()), 1) if sus else None),
        help_given_total=sum(v["help_given"] for v in tasks.values()),
    )
    return out


def markdown(m: dict) -> str:
    out = ["# Usability test summary (formative)\n", m["note"], "", f"Participants: {m['participants']}; languages {m['languages']}; age bands {m['age_bands']}; devices {m['devices']}.\n",
           "| task | participants | completed | errors | median time s | help given |", "|---|---|---|---|---|---|"]
    out += [f"| {k} | {v['participants']} | {v['completed']} | {v['errors_total']} | {v['median_time_s']} | {v['help_given']} |" for k, v in m["tasks"].items()]
    out += ["", f"Picker choice correct: {m['picker']['correct']} of {m['picker']['answered']}.", "", "| quiz question | answered | correct | critical wrong |", "|---|---|---|---|"]
    out += [f"| {q} | {v['answered']} | {v['correct']} | {v['critical_wrong']} |" for q, v in m["quiz"]["per_question"].items()]
    out += ["", f"Quiz correct per participant: {m['quiz']['correct_per_participant']}. Critical wrong answers in total: {m['quiz']['critical_errors_total']} (question 1: believing 'could not check' means safe; question 4: acting on the list alone).",
            "", f"SUS per participant: {m['sus']['scores']}; mean {m['sus']['mean']} (n = {m['sus']['participants']}; formative only).", f"Help given in total: {m['help_given_total']}."]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(REPO / "docs" / "usability"))
    ap.add_argument("--out", default=str(REPO / "eval" / "results" / "usability-v1"))
    a = ap.parse_args(argv)
    m = analyse(Path(a.dir))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8", newline="\n")
    (out / "summary.md").write_text(markdown(m), encoding="utf-8", newline="\n")
    print(f"wrote {out}: {m['participants']} participants, {m['quiz']['participants']} quizzes, {m['sus']['participants']} SUS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
