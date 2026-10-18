"""Phase 7a: the usability analysis script (synthetic CSVs; standard library)."""
import json
import sys

import pytest

from app.services.guards import REPO

sys.path.insert(0, str(REPO / "scripts"))
import analyse_usability as U  # noqa: E402


def test_sus_formula_known_values():
    assert U.sus_score([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]) == 100.0
    assert U.sus_score([3] * 10) == 50.0
    assert U.sus_score([1, 5, 1, 5, 1, 5, 1, 5, 1, 5]) == 0.0
    assert U.sus_score([4, 2, 4, 1, 5, 2, 4, 1, 5, 2]) == 85.0  # (3+3+4+3+4 + 3+4+3+4+3) x 2.5
    for bad in ([3] * 9, [3] * 11, [0] + [3] * 9, [6] + [3] * 9):
        with pytest.raises(ValueError):
            U.sus_score(bad)


def write(folder, name, text):
    (folder / name).write_text(text, encoding="utf-8")


def test_analysis_counts_without_personal_data(tmp_path):
    write(tmp_path, "session_sheet.csv",
          "participant_id,age_band,preferred_language,device,task,completed,errors,time_seconds,help_given,picker_choice_correct,notes\n"
          "P1,25-34,en,laptop,T1,yes,0,95,no,na,SECRET NOTE ABOUT A PERSON\n"
          "P1,25-34,en,laptop,T2,yes,1,140,yes,yes,x\n"
          "P2,45-54,ta,laptop,T1,yes,0,120,no,na,\n"
          "P2,45-54,ta,laptop,T2,no,2,300,yes,no,\n"
          "P3,,,,T4,yes,0,40,no,na,\n")
    write(tmp_path, "quiz_answers.csv", "participant_id,q1,q2,q3,q4,q5,q6\nP1,b,b,b,b,b,b\nP2,a,b,b,d,a,b\n")
    write(tmp_path, "sus_responses.csv", "participant_id,s1,s2,s3,s4,s5,s6,s7,s8,s9,s10\nP1,5,1,5,1,5,1,5,1,5,1\nP2,3,3,3,3,3,3,3,3,3,3\nP3,,,,,,,,,,\n")
    m = U.analyse(tmp_path)
    assert m["participants"] == 3 and m["languages"] == {"en": 1, "ta": 1}
    assert m["tasks"]["T1"] == {"participants": 2, "completed": 2, "errors_total": 0, "median_time_s": 107.5, "help_given": 0}
    assert m["tasks"]["T2"]["completed"] == 1 and m["tasks"]["T2"]["errors_total"] == 3 and m["tasks"]["T2"]["help_given"] == 2
    assert m["picker"] == {"answered": 2, "correct": 1}
    assert m["quiz"]["per_question"]["q1"] == {"answered": 2, "correct": 1, "critical_wrong": 1}  # P2 believed "could not check" means safe
    assert m["quiz"]["per_question"]["q4"]["critical_wrong"] == 1
    assert m["quiz"]["correct_per_participant"] == {"P1": 6, "P2": 3} and m["quiz"]["critical_errors_total"] == 2
    assert m["sus"]["scores"] == {"P1": 100.0, "P2": 50.0} and m["sus"]["mean"] == 75.0  # P3 left the SUS empty: not scored
    assert m["help_given_total"] == 2
    dumped = json.dumps(m)
    assert "SECRET" not in dumped and "notes" not in dumped
    assert "formative check, not a statistic" in m["note"]


def test_main_writes_summary_files(tmp_path):
    write(tmp_path, "session_sheet.csv", "participant_id,age_band,preferred_language,device,task,completed,errors,time_seconds,help_given,picker_choice_correct,notes\nP1,,en,,T1,yes,0,60,no,na,\n")
    out = tmp_path / "out"
    assert U.main(["--dir", str(tmp_path), "--out", str(out)]) == 0
    assert (out / "summary.json").exists() and "Usability test summary" in (out / "summary.md").read_text(encoding="utf-8")


def test_empty_templates_give_zero_counts():
    m = U.analyse(REPO / "docs" / "usability")
    assert m["participants"] == 0 and m["quiz"]["participants"] == 0 and m["sus"]["mean"] is None


def test_the_committed_key_has_a_question_that_fails_on_not_checked_means_safe():
    key = json.loads((REPO / "docs" / "usability" / "quiz_key.json").read_text(encoding="utf-8"))
    assert key["correct"]["q1"] == "b" and "a" in key["critical_wrong"]["q1"]
