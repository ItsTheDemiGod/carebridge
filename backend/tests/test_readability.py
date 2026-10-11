import sys

import pytest

from app.services.guards import REPO

sys.path.insert(0, str(REPO))
from eval import readability as r  # noqa: E402


@pytest.mark.parametrize("w,n", [("the", 1), ("water", 2), ("table", 2), ("medicine", 3), ("tablet", 2), ("hospital", 3), ("rice", 1), ("banana", 3), ("pharmacist", 3), ("drink", 1), ("wanted", 2), ("makes", 1)])
def test_syllable_heuristic(w, n):
    assert r.syllables(w) == n


def test_known_sentence_matches_the_formula():
    s = r.stats("The cat sat on the mat.")  # 6 words, 6 syllables, 1 sentence: 0.39*6 + 11.8*1 - 15.59
    assert s["words"] == 6 and s["syllables"] == 6 and s["fk_grade"] == pytest.approx(-1.45, abs=0.01) and s["mean_sentence_len"] == 6


def test_harder_text_scores_higher():
    easy = r.stats("Drink water. Rest at home.")["fk_grade"]
    hard = r.stats("Gastrointestinal haemorrhage necessitates immediate hospitalisation and comprehensive investigation.")["fk_grade"]
    assert hard > easy + 10


def test_long_word_share_and_sentences():
    s = r.stats("Take it now. Immunosuppressant medication continues.")
    assert s["sentences"] == 2 and s["long_word_share"] == pytest.approx(1 / 6, abs=0.001)  # "immunosuppressant" has 17 letters


def test_summarize_and_empty():
    out = r.summarize(["Drink water.", "Rest at home.", "123"])
    assert out["lines"] == 2 and out["fk_median"] is not None
    assert r.stats("") ["fk_grade"] is None
