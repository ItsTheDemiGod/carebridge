"""Script detection (standard library only). Latin tokens (drug names, units, abbreviations) are ignored for Tamil and Hindi."""

import re
import unicodedata

RANGES = {"ta": (0x0B80, 0x0BFF), "hi": (0x0900, 0x097F)}
LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9'\-/.+]*")
MIN_SHARE = {"en": 0.9, "ta": 0.8, "hi": 0.8}  # share of letters in the expected script (documented in docs/EXPLANATION.md)


def _letters(s: str):
    return [c for c in s if unicodedata.category(c)[0] in "LM"]  # letters and combining vowel signs (part of Tamil/Devanagari words)


def script_share(text: str, lang: str) -> float:
    """Share of letters in the expected script. en: Latin among all letters. ta/hi: target script among letters outside
    Latin tokens. Returns 0.0 when no letter qualifies, so a line with no target-script letters fails closed."""
    if lang == "en":
        ls = _letters(text)
        return sum(c.isascii() or "LATIN" in unicodedata.name(c, "") for c in ls) / len(ls) if ls else 0.0
    lo, hi = RANGES[lang]
    ls = _letters(LATIN_TOKEN.sub(" ", text))
    return sum(lo <= ord(c) <= hi for c in ls) / len(ls) if ls else 0.0


def script_ok(text: str, lang: str) -> bool:
    return script_share(text, lang) >= MIN_SHARE[lang]
