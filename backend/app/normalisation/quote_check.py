"""OPTIONAL quote checks against the document text. Only the evaluator and tests on synthetic data use these:
in the live app the document text is not available, so the normalisation service never depends on them."""

import re
import unicodedata
from difflib import SequenceMatcher

from app.normalisation.abbreviations import TIMES_ABBR

STRICT_FUZZY_MIN = 0.95  # chosen from the dev distribution, see docs/NORMALISATION.md
DOSING = set(TIMES_ABBR) | {"ac", "pc", "sos", "prn"}


def norm(s: str) -> str:
    """Unicode NFKC, lowercase, all whitespace (incl. line breaks) collapsed, leading/trailing punctuation stripped."""
    t = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s or "").lower())
    return re.sub(r"^[^\w]+|[^\w]+$", "", t)


def digits(s: str) -> list[str]:
    return re.findall(r"\d+", s)


def dosing_tokens(s: str) -> list[str]:
    return sorted(t for t in re.findall(r"[a-z]+", s.lower()) if t in DOSING)


def same_content(window: str, quote_norm: str) -> bool:
    """Same digits AND same dosing abbreviations: a wrong strength/dose, or a dropped OD/BD/AC/PC, cannot pass."""
    return digits(window) == digits(quote_norm) and dosing_tokens(window) == dosing_tokens(quote_norm)


def exact(quote: str, doc: str) -> bool:
    return quote in doc


def normalised_exact(quote: str, doc: str) -> bool:
    q = norm(quote)
    return bool(q) and q in norm(doc)


def best_window(quote: str, doc: str) -> tuple[float, str]:
    """Best near-contiguous window of the document (same length as the quote) and its similarity ratio."""
    q, d = norm(quote), re.sub(r"\s+", " ", unicodedata.normalize("NFKC", doc or "").lower())
    if not q or not d:
        return 0.0, ""
    blocks = [b for b in SequenceMatcher(None, d, q, autojunk=False).get_matching_blocks() if b.size >= 2]
    starts = {max(0, b.a - b.b + k) for b in blocks for k in range(-2, 3)} or {0}
    best = (0.0, "")
    for s in starts:
        for n in range(max(1, len(q) - 3), len(q) + 4):  # the quote may lack or add a few characters
            w = d[s:s + n]
            r = SequenceMatcher(None, w, q, autojunk=False).ratio()
            if r > best[0]:
                best = (r, w)
    return best


def strict_fuzzy(quote: str, doc: str, threshold: float = STRICT_FUZZY_MIN) -> bool:
    """Near-contiguous match with a high similarity AND the same digits and dosing tokens as the matched window."""
    r, w = best_window(quote, doc)
    return r >= threshold and same_content(w, norm(quote))


def check(quote: str, doc: str) -> dict:
    r, w = best_window(quote, doc)
    return dict(exact=exact(quote, doc), normalised_exact=normalised_exact(quote, doc), ratio=round(r, 3), digits_match=digits(w) == digits(norm(quote)), dosing_match=dosing_tokens(w) == dosing_tokens(norm(quote)),
                strict_fuzzy=r >= STRICT_FUZZY_MIN and same_content(w, norm(quote)))
