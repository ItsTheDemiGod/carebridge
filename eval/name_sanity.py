"""Diagnostic for misread drug names: share of predicted names matching no formulary brand/generic name."""

import difflib
import json
import re
from pathlib import Path

FORMULARY = Path(__file__).resolve().parents[1] / "data" / "reference" / "formulary.json"
THRESHOLD = 0.8
PREFIX = re.compile(r"^(tab|tablet|cap|capsule|syp|syrup|inj|injection|drops?|oint|ointment|cream|gel|susp|neb)\b\.?\s*", re.I)


def _norm(s: str) -> str:
    return PREFIX.sub("", s.strip().lower()).strip(" .")


def formulary_names() -> list[str]:
    names = set()
    for m in json.loads(FORMULARY.read_text(encoding="utf-8"))["medicines"]:
        names.update(_norm(n) for n in [m["generic_name"], *m["brand_names"]])
    return sorted(names)


def closest(name: str, names: list[str]) -> tuple[str, float]:
    n = _norm(name)
    return max(((f, difflib.SequenceMatcher(None, n, f).ratio()) for f in names), key=lambda x: x[1])


def check_names(pred, names: list[str]):
    """Yield (predicted name, closest formulary name, ratio) for every brand/generic name in a prediction."""
    for m in pred.medications:
        for n in (m.brand_name, m.generic_name):
            if n:
                f, r = closest(n, names)
                yield n, f, r
