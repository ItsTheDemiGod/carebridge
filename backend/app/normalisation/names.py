"""Resolve drug names against the formulary, using the document's own text (source_quote) as the authority.

Never overwrites what the model wrote: as_written values are kept next to the resolved ones, and anything
uncertain is flagged instead of corrected. resolved_generic comes from the FORMULARY (provenance "formulary"),
not from the document, and is kept separate from printed_generic.
"""

import json
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

FORMULARY = Path(__file__).resolve().parents[3] / "data" / "reference" / "formulary.json"

# Highest similarity between two names of DIFFERENT formulary drugs is 0.91 (omeprazole / esomeprazole), see docs/NORMALISATION.md.
# FUZZY_MIN is above it, so a fuzzy match can never land on a different drug; MARGIN adds a second guard.
FUZZY_MIN = 0.92
MARGIN = 0.05
NEAR_MIN = 0.75  # below FUZZY_MIN: reported as a near miss only, never accepted
MIN_FUZZY_LEN = 5  # shorter names must match exactly
MAX_NGRAM = 5  # "Amoxicillin + Clavulanic acid" is 4 tokens
FORM_WORDS = {"tab", "t", "tablet", "tablets", "cap", "c", "capsule", "syp", "syrup", "inj", "injection", "inh", "inhaler", "oint", "ointment", "drops", "drop", "susp"}
# ordinary words of an entry that must never be fuzzy-matched to a drug name
STOP = {"tablet", "tablets", "capsule", "syrup", "injection", "inhaler", "ointment", "daily", "twice", "thrice", "meals", "before", "after", "morning", "night", "bedtime", "weeks", "needed",
        "required", "hours", "every", "drops", "puffs", "units"}


def key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio() if a and b else 0.0


@dataclass
class Entry:
    canonical: str
    role: str  # "brand" | "generic"
    generic: str  # formulary generic of the drug
    strengths: list[str]


@lru_cache
def index() -> dict[str, Entry]:
    out: dict[str, Entry] = {}
    for m in json.loads(FORMULARY.read_text(encoding="utf-8"))["medicines"]:
        for role, names in (("generic", [m["generic_name"]]), ("brand", m["brand_names"])):
            for n in names:
                out[key(n)] = Entry(n, role, m["generic_name"], m["available_strengths"])
    return out


@dataclass
class NameResult:
    as_written_brand: str | None
    as_written_generic: str | None
    printed_brand: str | None = None  # formulary spelling of a brand the DOCUMENT prints
    printed_generic: str | None = None  # formulary spelling of a generic the DOCUMENT prints
    resolved_generic: str | None = None  # formulary generic for the printed drug; provenance "formulary"
    resolved_provenance: str | None = None
    match_type: str = "none"  # exact | fuzzy | none
    final_brand: str | None = None
    final_generic: str | None = None
    near_miss: str | None = None  # closest formulary name when not accepted
    flags: list[str] = field(default_factory=list)


def _tokens(s: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", s or "")


def partial_combination(hits, quote: str) -> bool:
    """A '+' in the entry but no matched name is a combination: a garbled combination would match one component only."""
    return bool(hits) and "+" in quote and not any("+" in h[0].generic for h in hits)


def scan_quote(quote: str, guard: bool = True):
    """Printed formulary names in the quote: exact n-gram matches first (longest first), then guarded fuzzy matches.
    Returns (hits, near) with hits = [(entry, 'exact'|'fuzzy', token_text)] and near = [(token, closest canonical, ratio)]."""
    idx = index()
    toks = _tokens(quote)
    used = [False] * len(toks)
    hits = []
    for n in range(MAX_NGRAM, 0, -1):
        for i in range(len(toks) - n + 1):
            if any(used[i:i + n]):
                continue
            k = key("".join(toks[i:i + n]))
            if k in idx:
                hits.append((idx[k], "exact", " ".join(toks[i:i + n])))
                used[i:i + n] = [True] * n
    near = []
    for i, t in enumerate(toks):
        k = key(t)
        if used[i] or len(k) < MIN_FUZZY_LEN or not k.isalpha() or k in STOP or t.lower() in FORM_WORDS:
            continue
        scored = sorted(((ratio(k, name), name) for name in idx), reverse=True)
        best_r, best = scored[0]
        second_r = next((r for r, name in scored[1:] if idx[name].generic != idx[best].generic), 0.0)
        if best_r >= FUZZY_MIN and best_r - second_r >= MARGIN:
            hits.append((idx[best], "fuzzy", t))
        elif best_r >= NEAR_MIN:
            near.append((t, idx[best].canonical, round(best_r, 2)))
    return ([] if guard and partial_combination(hits, quote) else hits), near


def _clean(name: str) -> str:
    """Name without form words and strength tokens (those starting with a digit: 500, 500mg), so D3 or XR stay part of a name."""
    return "".join(key(t) for t in _tokens(name) if t.lower() not in FORM_WORDS and not t[0].isdigit())


def _in_quote(name: str, quote: str) -> bool:
    n, q = _clean(name), key(quote)
    if not n:
        return True
    if n in q:
        return True
    m = SequenceMatcher(None, q, n, autojunk=False)
    return sum(b.size for b in m.get_matching_blocks()) / len(n) >= 0.9


def resolve_names(brand: str | None, generic: str | None, quote: str, strength: str | None = None) -> NameResult:
    r = NameResult(as_written_brand=brand, as_written_generic=generic)
    hits, near = scan_quote(quote, guard=False)
    drugs = {h[0].generic for h in hits}
    if len(drugs) > 1:  # two different drugs in one entry: refuse to pick
        r.flags.append("multiple_drugs_in_quote")
        hits = []
    if partial_combination(hits, quote):
        r.flags.append("possible_combination")
        hits = []
    for entry, how, _ in hits:
        if entry.role == "brand" and r.printed_brand is None:
            r.printed_brand = entry.canonical
        if entry.role == "generic" and r.printed_generic is None:
            r.printed_generic = entry.canonical
        if how == "fuzzy":
            r.match_type = "fuzzy"
            if "near_miss_name" not in r.flags:
                r.flags.append("near_miss_name")
            r.near_miss = r.near_miss or entry.canonical
    if hits:
        r.resolved_generic, r.resolved_provenance = hits[0][0].generic, "formulary"
        if r.match_type != "fuzzy":
            r.match_type = "exact"
    elif "multiple_drugs_in_quote" not in r.flags and "possible_combination" not in r.flags:
        r.flags.append("unresolved_name")  # nothing in the quote is a formulary name: keep as written, never force a drug
    for t, closest, rr in near:
        if "near_miss_name" not in r.flags:
            r.flags.append("near_miss_name")
        r.near_miss = r.near_miss or closest

    # final names: only text that the document prints. Role comes from the formulary, not from the model's field choice.
    def own(name):  # a model name the formulary does not know, but which IS in the quote: keep as written, flagged
        return name if name and _in_quote(name, quote) and key(name) not in index() and key(_clean(name)) not in index() else None

    r.final_brand = r.printed_brand or own(brand)
    r.final_generic = r.printed_generic or (own(generic) if not hits else None)
    # never copy a generic into the brand field
    if r.final_brand and r.final_generic and key(r.final_brand) == key(r.final_generic):
        r.final_brand = None

    for name in (brand, generic):
        if name and not _in_quote(name, quote):
            r.flags.append("name_not_in_quote")
            break
    wrote = {"brand": key(_clean(brand or "")), "generic": key(_clean(generic or ""))}
    if wrote["brand"] and wrote["brand"] == wrote["generic"]:
        r.flags.append("duplicate_name_fields")  # same name in both fields: the other printed name was probably lost
    elif (r.printed_brand and wrote["generic"] == key(r.printed_brand)) or (r.printed_generic and wrote["brand"] == key(r.printed_generic)):
        r.flags.append("role_corrected")
    if not (r.final_brand or r.final_generic) and not {"unresolved_name", "multiple_drugs_in_quote", "possible_combination"} & set(r.flags):
        r.flags.append("missing_name")

    if strength and hits:
        allowed = {key(s) for s in hits[0][0].strengths}
        if key(strength) not in allowed:
            r.flags.append("unusual_strength")
    return r
