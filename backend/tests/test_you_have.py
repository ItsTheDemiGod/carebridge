import pytest

from app.services.verification import deterministic

SRC = "Return to hospital for chest pain."


def hits(view, lang="en"):
    cand = view if lang == "en" else "x" * 40
    _, why = deterministic("warning", SRC, cand, lang, number_ref=SRC, english_view=view)
    return [w for w in why if w.startswith("forbidden_additions")]


@pytest.mark.parametrize("t", [
    "You have an infection.",
    "You have diabetes.",
    "Chest pain is common, so you have a heart problem.",  # comma ends the clause; 'if' is not in the same clause
    "You may have a stroke.",
    "If it hurts. You have an infection.",  # conditional ended by the full stop
])
def test_diagnosis_still_flagged(t):
    assert any("diagnosis" in h for h in hits(t))


@pytest.mark.parametrize("t", [
    "Get medical help straight away if you have chest tightness, trouble breathing while resting, or if you faint.",
    "Return to hospital when you have chest pain.",
    "Whenever you have a fever, call the hospital.",
    "Unless you have bleeding, rest at home.",
    "In case you have chest pain, go to hospital.",
    "Go to hospital immediately if sudden you may have chest pain.",
    "Go to hospital immediately if pain is bad you have chest pain.",  # 3 words between: still conditional
])
def test_conditional_you_have_passes(t):
    assert not any("diagnosis" in h for h in hits(t))


@pytest.mark.parametrize("lang", ["ta", "hi"])
def test_back_translation_of_conditional_warning_passes(lang):
    assert not any("diagnosis" in h for h in hits("Go back to the hospital at once if you have chest pain.", lang))
    assert any("diagnosis" in h for h in hits("You have a heart problem.", lang))
