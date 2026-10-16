import json
import re

import pytest

from app.safety.guardrails import scan
from app.services import templates as T
from app.services import verification as V
from app.services.guards import REPO

FILL = dict(a="Metformin", b="Omeprazole", n=3, name="Metformin")
STRINGS = T.load()["strings"]
PHRASES = json.loads((REPO / "data" / "templates" / "phrases.json").read_text(encoding="utf-8"))["phrases"]


def fams(text, tid=None, source=None):
    return {f for f, _ in scan(text, tid, source)}


@pytest.mark.parametrize("tid", sorted(STRINGS))
def test_every_english_template_passes(tid):
    assert scan(re.sub(r"\{(\w+)\}", lambda m: str(FILL.get(m.group(1), "x")), STRINGS[tid]["en"]["text"]), tid) == []


def test_english_only_strings_pass():
    assert all(scan(t) == [] for t in T.load()["english_only"].values())


def test_every_phrase_library_entry_and_alias_passes():
    bad = []
    for p in PHRASES:
        for t in [p["english"], *p.get("english_aliases", [])]:
            t = re.sub(r"\{(\w+)\}", "3", t)
            if scan(t):
                bad.append((p["id"], t, scan(t)))
    assert not bad, bad


def test_allow_list_is_narrow():
    # the same text without its template id is judged on its own merits; negated forms still pass by negation
    assert scan("This does not mean they are safe.") == []  # negated reassurance passes
    assert fams("They are safe to take together.") == {"reassurance"}
    assert fams("This could mean a double dose.") == set()  # noun use


@pytest.mark.parametrize("t", [
    "It is safe to take them together.", "There is no risk.", "Nothing to worry about.", "You can take both.", "It is fine to combine them.",
    "No need to worry.", "Do not worry, they are perfectly fine.", "Both medicines are safe.", "There are no interactions.",
])
def test_reassurance_flagged(t):
    assert "reassurance" in fams(t)


@pytest.mark.parametrize("t", [
    "This does not mean they are safe.", "It is not safe to take them together.", "Never assume it is fine.", "You cannot take both without asking.",
])
def test_negated_reassurance_passes(t):
    assert "reassurance" not in fams(t)


@pytest.mark.parametrize("t", [
    "Stop taking the tablets.", "Skip the evening dose.", "Increase the dose to two tablets.", "Reduce your medicine.", "Double the dose.",
    "Switch to another medicine.", "You should stop it.", "Change the dosage.",
])
def test_dose_change_flagged(t):
    assert "change" in fams(t)


@pytest.mark.parametrize("t", [
    "Do not stop or change either medicine on your own.", "Never skip a dose.", "Please do not increase the dose.", "Take rest and drink fluids.",
    "Do not double the dose if you miss one.", "Skipping meals is not advised.", "This could mean a double dose.", "Bleeding that does not stop needs a doctor.",
])
def test_dose_change_negated_or_unrelated_passes(t):
    assert "change" not in fams(t)


@pytest.mark.parametrize("t", ["You have an infection.", "You have diabetes.", "You are suffering from asthma.", "You may have a stroke.", "Chest pain is common, so you have a heart problem."])
def test_diagnosis_flagged(t):
    assert "diagnosis" in fams(t)


@pytest.mark.parametrize("t", [
    "Go to hospital if you have chest pain.", "When you have a fever, call the hospital.", "In case you have bleeding, go to hospital.",
    "You have been given two medicines.", "If you have any questions, ask your pharmacist.", "You have to take it after meals.",
])
def test_diagnosis_conditional_or_other_use_passes(t):
    assert "diagnosis" not in fams(t)


def test_source_family_is_not_blamed_on_the_candidate():
    src = "Stop taking aspirin 3 days before the operation."
    assert fams("Stop taking aspirin 3 days before surgery.", source=src) == set()
    assert fams("Stop taking aspirin 3 days before surgery.") == {"change"}
    assert fams("Stop taking aspirin 3 days before surgery. It is safe to take paracetamol.", source=src) == {"reassurance"}


def test_runtime_check_in_verification_fails_closed():
    res, why = V.deterministic("advice", "Rest at home.", "Rest at home. You can take any painkiller.", "en")
    assert res["guardrail"] is False and any(w.startswith("guardrail") for w in why)
    res, _ = V.deterministic("advice", "Rest at home.", "Rest at home and sleep well.", "en")
    assert res["guardrail"] is True
    res, why = V.deterministic("advice", "Rest.", "x" * 40, "ta", english_view="It is safe to take.")  # back-translation is scanned too
    assert res["guardrail"] is False
