"""Faithfulness verification of model-written lines. A language text is verified only if EVERY deterministic check passes
AND the judge verdict is "supported". Anything else is unverified and the app shows the original extracted English with a notice.

Deterministic checks (names are the keys of Verification.deterministic):
  id_integrity      exactly one output for the id, none missing/duplicated/extra for the batch, order preserved
  numbers           set of digit strings equals the set in the reference (en: source; ta/hi: the plain English)
  drug_names        formulary names present in the source appear verbatim in the output; none appear that the source lacks
  script            en mostly Latin (>= 0.9 of letters); ta/hi mostly Tamil/Devanagari (>= 0.8 of letters outside Latin tokens)
  length            not empty; not wildly shorter or longer than the source (bounds below)
  forbidden_additions   general phrases (advice to change/stop a dose, "you have", reassurance, reasons, diagnosis) absent from the source
  urgency           warnings only, English only: a source urgency cue needs an equivalent cue in the output
For ta/hi, forbidden_additions runs on the English back-translation. Negation and urgency in Tamil/Hindi rest on the judge.
"""

import json
import re
import unicodedata
from functools import lru_cache

from app.safety.guardrails import in_conditional_clause, scan
from app.schemas.explanation import LANGS, LangText, Verification
from app.services.guards import REPO
from app.services.narrative import Item, Narrative, Stage
from app.services.script import script_ok, script_share

FORMULARY = REPO / "data" / "reference" / "formulary.json"
# length bounds: out <= max(MAX_RATIO*src, src+SLACK) and out >= max(3, MIN_RATIO*src), in characters
LENGTH = {"en": dict(max_ratio=2.5, slack=60, min_ratio=0.3), "ta": dict(max_ratio=3.5, slack=80, min_ratio=0.25), "hi": dict(max_ratio=3.5, slack=80, min_ratio=0.25)}

FORBIDDEN = [  # (label, regex). A match fails the line only if the same regex does NOT match the source.
    ("dose_change_advice", r"\b(increase|decrease|double|halve|reduce|raise|lower|change)\b[^.]{0,25}\b(dose|dosage|medicine|medication|tablet|pill)s?\b"),
    ("stop_advice", r"\b(stop|stopping|discontinue|skip|avoid)\b[^.]{0,25}\b(taking|medicine|medication|tablet|pill|dose)s?\b"),
    ("diagnosis", r"\byou (have|may have|might have|probably have|could have|suffer from|are suffering from)\b"),
    ("reassurance", r"\b(do not worry|don't worry|no need to worry|nothing to worry|not to worry|is normal|are normal|is common|are common|nothing serious|not serious|will be fine|will go away|will get better|perfectly fine|is safe|are safe)\b"),
    ("reason", r"\b(because|so that|in order to|this helps|which helps|this is why|due to|caused by|a sign of)\b"),
    ("see_doctor", r"\b(consult|see|visit|call|contact|ask)\b[^.]{0,12}\b(a|your|the) (doctor|physician|pharmacist|nurse)\b"),
]


def _flagged(label: str, rx: str, text: str) -> bool:
    """True if rx matches text; for the diagnosis rule, matches inside a conditional clause ("if you have chest pain") do not count."""
    for m in re.finditer(rx, text, re.I):
        if label != "diagnosis":
            return True
        if not in_conditional_clause(text, m.start()):
            return True
    return False


URGENCY_SOURCE = re.compile(r"\b(return|go to|emergency|immediately|urgent(ly)?|at once|right away|straight away|ambulance)\b", re.I)
URGENCY_OUTPUT = re.compile(r"\b(return|returns|go to|come back|emergency|immediately|urgent(ly)?|at once|right away|straight away|ambulance|hospital|seek help|get help|quickly|without delay)\b", re.I)


@lru_cache
def formulary_names() -> list[str]:
    meds = json.loads(FORMULARY.read_text(encoding="utf-8"))["medicines"]
    return sorted({n for m in meds for n in (*m["brand_names"], m["generic_name"])}, key=len, reverse=True)


def _name_pattern(name: str) -> re.Pattern:
    return re.compile(r"(?<![A-Za-z0-9])" + r"\s+".join(map(re.escape, name.split())) + r"(?![A-Za-z0-9])", re.I)


def names_in(text: str) -> set[str]:
    """Formulary names found in text (whole words, case-insensitive; the longest name wins over a name inside it)."""
    found, masked = set(), text
    for n in formulary_names():
        if _name_pattern(n).search(masked):
            found.add(n.lower())
            masked = _name_pattern(n).sub(" ", masked)
    return found


def digit_strings(text: str) -> set[str]:
    """Digit runs with any Unicode decimal digits mapped to 0-9, so a Tamil or Devanagari numeral compares equal to its Western form."""
    return {"".join(str(unicodedata.digit(c)) for c in m) for m in re.findall(r"\d+", text)}


def deterministic(kind: str, source: str, text: str, lang: str, number_ref: str | None = None, english_view: str | None = None) -> tuple[dict[str, bool], list[str]]:
    """Checks 2-7 for one candidate text. number_ref: the text whose numbers must match (default: the source).
    english_view: English to run forbidden_additions/urgency on (the text itself for en, the back-translation for ta/hi)."""
    res: dict[str, bool] = {}
    why: list[str] = []

    def put(name: str, ok: bool, reason: str = ""):
        res[name] = ok
        if not ok:
            why.append(f"{name}: {reason}")

    ref = source if number_ref is None else number_ref
    a, b = digit_strings(ref), digit_strings(text)
    put("numbers", a == b, f"expected {sorted(a)} got {sorted(b)}")
    s_names, o_names = names_in(source), names_in(text)
    put("drug_names", s_names == o_names, f"missing {sorted(s_names - o_names)} invented {sorted(o_names - s_names)}")
    put("script", script_ok(text, lang), f"{lang} script share {script_share(text, lang):.2f}")
    bd, n, m = LENGTH[lang], len(text.strip()), len(source.strip())
    put("length", n >= max(3, bd["min_ratio"] * m) and n <= max(bd["max_ratio"] * m, m + bd["slack"]), f"{n} chars for a {m}-char source")
    view = text if lang == "en" else english_view
    if view is None:
        put("forbidden_additions", True)
        put("guardrail", True)
    else:
        hits = [lbl for lbl, rx in FORBIDDEN if _flagged(lbl, rx, view) and not re.search(rx, source, re.I)]
        put("forbidden_additions", not hits, f"phrases not in the source: {hits}")
        claims = scan(view, source=source)  # safety guardrail: reassurance / dose-or-medicine change / diagnosis (docs/SAFETY.md)
        put("guardrail", not claims, f"forbidden claim not in the source: {claims}")
    if kind == "warning" and lang == "en":
        put("urgency", not URGENCY_SOURCE.search(source) or bool(URGENCY_OUTPUT.search(text)), "source has an urgency cue, output has none")
    return res, why


def _why(problem: str | None) -> str:
    """Reason text: id and batch-order problems are id_integrity failures; call failures are reported as such."""
    return f"id_integrity: {problem}" if problem and problem.startswith(("id_", "extra_ids", "order_changed")) else f"no_model_text: {problem}"


def _stage_value(stage: Stage | None, item_id: str):
    """(value, problem). A batch problem fails every line; an id problem fails that line."""
    if stage is None:
        return None, "stage_not_run"
    if stage.batch_problems:
        return None, "; ".join(stage.batch_problems)
    if item_id in stage.id_problems:
        return None, stage.id_problems[item_id]
    return stage.values.get(item_id), None


def _finish(v: Verification, judge_stage: Stage | None, item_id: str) -> Verification:
    jv, jp = _stage_value(judge_stage, item_id)
    if jv is None:
        v.reason = v.reason or f"judge_unavailable: {jp}"
    else:
        v.judge_verdict, v.judge_reason = jv
    v.passed = not v.deterministic_reasons and v.judge_verdict == "supported"
    if not v.passed and not v.reason:
        v.reason = v.deterministic_reasons[0] if v.deterministic_reasons else f"judge: {v.judge_verdict} ({v.judge_reason})"
    return v


def verify_item(item: Item, nar: Narrative, lang: str) -> tuple[str | None, Verification]:
    """(candidate text or None, verification record) for one item and language."""
    v = Verification()
    plain, p1 = _stage_value(nar.simplified, item.id)
    if lang == "en":
        v.candidate = plain
        if plain is None:
            v.reason = _why(p1)
            return None, v
        v.deterministic, v.deterministic_reasons = deterministic(item.kind, item.text, plain, "en")
        v.deterministic = {"id_integrity": True, **v.deterministic}
        return plain, _finish(v, nar.judged.get("en"), item.id)

    tr, p2 = _stage_value(nar.translated.get(lang), item.id)
    v.candidate = tr
    if plain is None or tr is None:
        v.reason = _why(p1 or p2)
        return None, v
    bt, p3 = _stage_value(nar.back.get(lang), item.id)
    v.back_translation = bt
    v.deterministic, v.deterministic_reasons = deterministic(item.kind, item.text, tr, lang, number_ref=plain, english_view=bt)
    v.deterministic = {"id_integrity": True, **v.deterministic}
    if bt is None:
        v.deterministic["id_integrity"] = False
        v.deterministic_reasons.insert(0, f"id_integrity: back-translation {p3}")
    return tr, _finish(v, nar.judged.get(lang), item.id)


def verify_narrative(nar: Narrative) -> dict[str, dict[str, tuple[str | None, Verification]]]:
    """id -> lang -> (candidate, verification)."""
    return {i.id: {lang: verify_item(i, nar, lang) for lang in LANGS} for i in nar.items}


def lang_text_for(source: str, candidate: str | None, v: Verification) -> LangText:
    """Verified candidate is shown; otherwise the original extracted English, flagged original_with_notice."""
    if v.passed and candidate is not None:
        return LangText(text=candidate, status="verified", display_mode="explanation", review_status="draft_unreviewed", verification=v, provenance="model_checked")
    return LangText(text=source, status="original_only" if candidate is None else "unverified", display_mode="original_with_notice", review_status="not_required", verification=v, provenance="original_only")
