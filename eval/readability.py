"""English readability, standard library only: Flesch-Kincaid grade, mean sentence length, share of long words.
Tamil and Hindi readability is NOT scored (no validated formula or syllable model is available for them here).

Syllable heuristic: count groups of consecutive vowels (a e i o u y) in the lower-cased word; drop a final silent "e"
(but keep it after a consonant + "le", as in "table"); drop a final "es"/"ed" that is not pronounced (not after t, d, s, x, z, c, g, h);
minimum one syllable. Words are letter runs (digits-only tokens are not words). Sentences end at . ! ? followed by a space or the end.
Known errors: words like "area", "idea", "being" are undercounted; numbers and abbreviations are ignored. Good enough for comparing two
sets of short lines, not for absolute grades. Very short lines give noisy per-line grades, so pooled values are reported next to the distribution.
"""

import re
import statistics

WORD = re.compile(r"[A-Za-z][A-Za-z'\-]*")
SENT_END = re.compile(r"[.!?]+(?:\s+|$)")
LONG = 12


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not re.search(r"[^aeiouy]le$", w) and n > 1:
        n -= 1
    elif re.search(r"[^tdsxzcgh]e[sd]$", w) and n > 1:
        n -= 1
    return max(1, n)


def stats(text: str) -> dict:
    words = WORD.findall(text)
    sents = max(1, len([s for s in SENT_END.split(text) if s.strip()]))
    if not words:
        return dict(words=0, sentences=0, fk_grade=None, mean_sentence_len=None, long_word_share=None)
    syl = sum(syllables(w) for w in words)
    return dict(words=len(words), sentences=sents, syllables=syl, fk_grade=round(0.39 * len(words) / sents + 11.8 * syl / len(words) - 15.59, 2),
                mean_sentence_len=round(len(words) / sents, 2), long_word_share=round(sum(len(re.sub(r"[^A-Za-z]", "", w)) > LONG for w in words) / len(words), 3))


def summarize(texts: list[str]) -> dict:
    """Per-line distribution plus the pooled value (all lines joined)."""
    per = [stats(t) for t in texts if WORD.search(t)]
    g = sorted(p["fk_grade"] for p in per)
    q = lambda f: g[min(len(g) - 1, int(f * len(g)))] if g else None  # noqa: E731
    pooled = stats(" ".join(t if t.rstrip().endswith((".", "!", "?")) else t.rstrip() + "." for t in texts))
    return dict(lines=len(per), fk_median=statistics.median(g) if g else None, fk_p25=q(0.25), fk_p75=q(0.75), fk_mean=round(statistics.mean(g), 2) if g else None,
                mean_sentence_len=round(statistics.mean(p["mean_sentence_len"] for p in per), 2) if per else None,
                long_word_share=round(sum(p["long_word_share"] * p["words"] for p in per) / sum(p["words"] for p in per), 3) if per else None, pooled_fk_grade=pooled["fk_grade"])
