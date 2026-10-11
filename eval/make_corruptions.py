"""Deterministic corruptions (fixed seed) of dev-set lines, to measure how well the verifier detects known faults.

English variants are built from two bases per line: the model's plain English and the extracted source line itself, and are checked
against the extracted source. Tamil/Hindi variants are built from the translations that were verified in the dev run and only use
corruptions that can be generated without a native speaker: number_changed, drug_name_swapped, wrong_script, item_dropped.
Negation and urgency changes in Tamil or Hindi cannot be generated or checked deterministically: they rely on the back-translation judge
and native review, and are NOT measured here.
"""

import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from app.services.verification import URGENCY_OUTPUT, URGENCY_SOURCE, _name_pattern, formulary_names, names_in  # noqa: E402

SEED = 20261011
CAP = 40  # variants per type and language (seeded sample), to bound model calls
INVENTED = ["Take an extra tablet if the pain continues.", "Do not worry, this is normal.", "You may stop the medicine when you feel better.",
            "This is a sign of infection.", "Avoid all exercise for one month.", "Drink warm milk before going to bed."]
NEG = re.compile(r"\b(do not|does not|did not|don't|doesn't|not|never|no|cannot|can't|without)\b", re.I)
AUX = [(" is ", " is not "), (" are ", " are not "), (" should ", " should not "), (" can ", " cannot "), (" will ", " will not ")]
TIMING = re.compile(r"\b(before|after)\b(?=[^.]{0,25}\b(?:meals?|food|eating|breakfast|lunch|dinner)\b)", re.I)
EN_TYPES = ["number_changed", "negation_dropped", "drug_name_swapped", "invented_advice", "urgency_dropped", "timing_swapped", "clause_dropped"]
TAHI_TYPES = ["number_changed", "drug_name_swapped", "wrong_script"]  # item_dropped is batch-level, handled by the evaluator


def number_changed(t, rng):
    m = re.search(r"[0-9]+", t)
    return t[:m.start()] + str(int(m.group()) + 1) + t[m.end():] if m else None


def negation_dropped(t, rng):
    """Drop the first negation word; if there is none, insert one. Returns (text, subtype)."""
    m = NEG.search(t)
    if m:
        out = re.sub(r"\s{2,}", " ", t[:m.start()] + t[m.end():]).strip()
        return (out[:1].upper() + out[1:], "dropped") if out else None
    for a, b in AUX:
        if a in t:
            return t.replace(a, b, 1), "inserted"
    return "Do not " + t[:1].lower() + t[1:], "inserted"


def drug_name_swapped(t, rng):
    present = names_in(t)
    if not present:
        return None
    name = max(present, key=len)
    other = rng.choice([n for n in formulary_names() if n.lower() not in names_in(t) and n.lower() != name])
    return _name_pattern(name).sub(other, t, count=1)


def invented_advice(t, rng):
    return t.rstrip() + " " + INVENTED[rng.randrange(len(INVENTED))]


def urgency_dropped(t, rng):
    if not URGENCY_OUTPUT.search(t):
        return None
    m = re.search(r"\bif\b(.*)", t, re.I | re.S)
    if m:
        return "Tell the doctor at the next visit if" + m.group(1)
    return "Mention this at the next visit: " + re.sub(r"\b(immediately|urgently|at once|right away|straight away)\b", "", t, flags=re.I).strip()


def timing_swapped(t, rng):
    return TIMING.sub(lambda m: "after" if m.group(1).lower() == "before" else "before", t, count=1) if TIMING.search(t) else None


def clause_dropped(t, rng):
    """Drop the last clause or sentence (split at ". ", "; ", ", " or " and ")."""
    t = t.strip()
    seps = list(re.finditer(r"(?<=[.;])\s+|,\s+|\s+and\s+", t))
    if not seps or seps[-1].start() < 4:
        return None
    head = t[:seps[-1].start()].rstrip(" ,;")
    return head if head.endswith(".") else head + "."


FN = dict(number_changed=number_changed, negation_dropped=negation_dropped, drug_name_swapped=drug_name_swapped, invented_advice=invented_advice,
          urgency_dropped=urgency_dropped, timing_swapped=timing_swapped, clause_dropped=clause_dropped)


PROBES = [  # fixed general lines (not from any dev document): the dev free-text lines contain no formulary drug names and no urgency cues, so these two types would otherwise be unmeasurable
    ("warning", "Return to hospital immediately if you have chest pain."), ("warning", "Go to the emergency room at once if you faint."),
    ("warning", "Call the doctor urgently if the wound becomes red and swollen."), ("warning", "Return immediately if the fever lasts more than 3 days."),
    ("advice", "Do not take Metformin on an empty stomach."), ("advice", "Take Pantoprazole 30 minutes before breakfast."), ("advice", "Take Paracetamol only if the fever is above 100 F."),
    ("advice", "Take Glycomet after meals."), ("advice", "Take Amlodipine before food and do not skip it."), ("advice", "Do not drink alcohol while taking Metronidazole."),
]


def probe_pool() -> list[dict]:
    return [dict(doc="probe", item_id=f"probe-{i}", kind=k, source=t, plain=t, plain_verified=True, ta=None, hi=None, ta_back=None, hi_back=None, ta_verified=False, hi_verified=False) for i, (k, t) in enumerate(PROBES)]


def load_pool(run_id: str) -> list[dict]:
    """One record per free-text line of the run: source, plain English, translations and their back-translations, verified flags."""
    pool = []
    for f in sorted((REPO / "eval" / "runs" / run_id / "docs").glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        for s in rec["explanation"]["sections"]:
            for ln in s["lines"]:
                if ln["kind"] in ("advice", "follow_up", "warning"):
                    t = ln["text"]
                    pool.append(dict(doc=rec["doc"], item_id=ln["line_id"], kind=ln["kind"], source=ln["source_text"],
                                     plain=t["en"]["verification"]["candidate"], plain_verified=t["en"]["status"] == "verified",
                                     **{f"{lg}": t[lg]["verification"]["candidate"] for lg in ("ta", "hi")},
                                     **{f"{lg}_back": t[lg]["verification"]["back_translation"] for lg in ("ta", "hi")},
                                     **{f"{lg}_verified": t[lg]["status"] == "verified" for lg in ("ta", "hi")}))
    return pool


def _mk(p, typ, lang, base_kind, text, sub=None, extra=None):
    return dict(vid=f"{p['item_id']}~{typ}~{base_kind}", doc=p["doc"], item_id=p["item_id"], kind=p["kind"], lang=lang, type=typ, sub=sub, base=base_kind, source=p["source"], text=text, **(extra or {}))


def build(pool: list[dict], seed: int = SEED, cap: int = CAP) -> list[dict]:
    rng = random.Random(seed)
    out: list[dict] = []
    for p in pool:  # English: two bases per line
        for base_kind, base in (("plain", p["plain"]), ("source", p["source"])):
            if not base:
                continue
            for typ in EN_TYPES:
                if typ == "urgency_dropped" and (p["kind"] != "warning" or not URGENCY_SOURCE.search(p["source"])):
                    continue
                r = FN[typ](base, rng)
                text, sub = r if isinstance(r, tuple) else (r, None)
                if text and text.strip() != base.strip():
                    out.append(_mk(p, typ, "en", base_kind, text, sub))
    for lg in ("ta", "hi"):  # Tamil / Hindi: verified translations only
        for p in pool:
            base = p[lg]
            if not base or not p[f"{lg}_verified"]:
                continue
            extra = dict(plain=p["plain"])
            for typ in ("number_changed", "drug_name_swapped"):
                text = FN[typ](base, rng)
                if text and text != base:
                    out.append(_mk(p, typ, lg, "translation", text, None, extra))
            if p["plain"]:
                out.append(_mk(p, "wrong_script", lg, "translation", p["plain"], None, extra))  # the English plain text where Tamil/Hindi was expected
    sampled = []
    for key in sorted({(v["lang"], v["type"]) for v in out}):
        group = [v for v in out if (v["lang"], v["type"]) == key]
        sampled += rng.sample(group, min(cap, len(group))) if len(group) > cap else group
    return sorted(sampled, key=lambda v: (v["doc"], v["lang"], v["vid"]))
