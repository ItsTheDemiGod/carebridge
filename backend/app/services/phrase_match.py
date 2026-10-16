"""Strict matcher for the phrase library (data/templates/phrases.json). No model, no fuzzy matching.

A line matches only if its normalised text EQUALS the canonical English or one alias, or equals one of them with the {n} slot filled by
an integer inside the phrase's [min, max]. A different number, negation, symptom or an extra clause means no match, so the line goes to the
model path. near_misses() lists very similar but unequal phrases for REPORTING only (what to add to the library); it is never used for display.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

PHRASES_PATH = Path(__file__).resolve().parents[3] / "data" / "templates" / "phrases.json"
PLACEHOLDER = re.compile(r"\{(\w+)\}")
_LEAD = re.compile(r"^[\s\-–—•·*▪◦►>\"'.,;:!?]+")
_TRAIL = re.compile(r"[\s\-–—•·*\"'.,;:!?]+$")
NEAR_MISS_RATIO = 0.8


def normalise(s: str) -> str:
    """Unicode NFKC, lower case, curly quotes straightened, whitespace collapsed, bullets and edge punctuation stripped."""
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace("‘", "'").casefold()
    return _TRAIL.sub("", _LEAD.sub("", re.sub(r"\s+", " ", s))).strip()


@dataclass(frozen=True)
class Match:
    phrase_id: str
    n: int | None
    how: str  # canonical | alias | slot


@dataclass(frozen=True)
class NearMiss:
    phrase_id: str
    ratio: float
    variant: str


@lru_cache
def library(path: str = str(PHRASES_PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def by_id(path: str = str(PHRASES_PATH)) -> dict[str, dict]:
    return {p["id"]: p for p in library(path)["phrases"]}


def variants(ph: dict) -> list[tuple[str, str]]:
    """(text, 'canonical' | 'alias') for every English wording of a phrase."""
    return [(ph["english"], "canonical"), *[(a, "alias") for a in ph["english_aliases"]]]


@lru_cache
def _index(path: str = str(PHRASES_PATH)):
    exact: dict[str, Match] = {}
    slots: list[tuple[re.Pattern, dict, str]] = []
    for ph in library(path)["phrases"]:
        for text, how in variants(ph):
            norm = normalise(text)
            if ph.get("slot"):
                rx = re.escape(norm).replace(re.escape("{n}"), r"([1-9][0-9]{0,2})")
                slots.append((re.compile(rx), ph, how))
            else:
                exact[norm] = Match(ph["id"], None, how)
    return exact, slots


def match(text: str, path: str = str(PHRASES_PATH)) -> Match | None:
    norm = normalise(text)
    exact, slots = _index(path)
    if norm in exact:
        return exact[norm]
    for rx, ph, how in slots:
        m = rx.fullmatch(norm)
        if m and ph["slot"]["min"] <= int(m.group(1)) <= ph["slot"]["max"]:
            return Match(ph["id"], int(m.group(1)), "slot")
    return None


def render(ph: dict, lang: str, n: int | None = None) -> str:
    """Library text in one language. English is the canonical wording. A slot phrase needs n; braces never survive."""
    text = ph["english"] if lang == "en" else ph[lang]["text"]
    if ph.get("slot"):
        if n is None:
            raise ValueError(f"{ph['id']} needs n")
        text = text.replace("{n}", str(n))
    return text


def near_misses(text: str, path: str = str(PHRASES_PATH), ratio: float = NEAR_MISS_RATIO) -> list[NearMiss]:
    """Phrases whose wording is >= ratio similar to the line but NOT equal (best variant per phrase). Reporting only; never displayed."""
    if match(text, path):
        return []
    norm = re.sub(r"[0-9]+", "{n}", normalise(text))
    out = []
    for ph in library(path)["phrases"]:
        scored = [(SequenceMatcher(None, norm, normalise(v)).ratio(), v) for v, _ in variants(ph)]
        best = max(scored)
        if best[0] >= ratio:
            out.append(NearMiss(ph["id"], round(best[0], 3), best[1]))
    return sorted(out, key=lambda x: -x.ratio)
