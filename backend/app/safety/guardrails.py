"""No-diagnosis / no-reassurance / no-dose-change guardrail: a negation-aware scan of ENGLISH user-facing text.

Families: reassurance ("safe to take", "no risk", "you can take"), medicine or dose changes (stop, skip, increase, reduce, double, switch ...
unless negated: "do not", "never"), diagnosis ("you have", "you are suffering from" unless in a conditional clause).
Used (1) on every English template and phrase-library entry in tests, (2) at runtime on every model-written English line (and the English
back-translation of Tamil/Hindi lines) and on every assembled safety message. A hit fails closed (caller falls back to the original text).
A model line is blamed only for families that are NOT already present in its source text (a faithful copy of the doctor's own words is not an addition).
ALLOW lists the template ids whose fixed text legitimately contains a negated or non-instruction form (reviewed by hand)."""
import re

# template ids with legitimate text: "does not mean ... safe", "Do not stop or change", "double dose" as a noun
ALLOW: dict[str, set[str]] = {
    "safety.not_checked": {"reassurance"}, "safety.not_checked_1": {"reassurance"},
    "safety.level.major": {"change"}, "safety.duplicate": {"change"},
}

REASSURANCE = re.compile(
    r"\b(safe to (take|use|combine|mix)|(is|are|be|being|remain|remains) (completely |perfectly |totally )?safe|no risk|nothing to worry|no need to worry|"
    r"do not worry|don't worry|not to worry|you can (safely )?(take|use|mix|combine)|it is fine|it's fine|is fine|are fine|perfectly fine|nothing serious|not harmful|harmless|"
    r"no (known )?interactions?|does not interact|won't interact|will not interact)\b", re.I)
_VERB = r"(stop|stopping|skip|skipping|increase|increasing|reduce|reducing|decrease|decreasing|double|doubling|halve|halving|switch|switching|change|changing|lower|raise|discontinue)"
_OBJECT = r"(dose|doses|dosage|medicine|medicines|medication|medications|tablet|tablets|pill|pills|capsule|capsules|drug|drugs|treatment|taking|using|them|it|either|both)"
CHANGE = re.compile(rf"\b{_VERB}\b(\W+\w+){{0,3}}?\W+{_OBJECT}\b", re.I)
NEGATION = re.compile(r"\b(not|never|no|don't|dont|cannot|can't|without|nor|avoid|neither)\b", re.I)
DIAGNOSIS = re.compile(
    r"\byou (?:have|may have|might have|probably have|could have|are suffering from|suffer from)\b"
    r"(?!\s+(?:been|had|to|taken|missed|received|any|a question|questions|an appointment|your|the|these|this|enough|finished|not|no|stopped|just)\b)", re.I)
CONDITIONAL = re.compile(r"\b(if|when|whenever|unless|in case)\b(\W+\w+){0,3}?\W*$", re.I)
FAMILIES = ("reassurance", "change", "diagnosis")


def clause_before(text: str, pos: int) -> str:
    return re.split(r"[.;:!?,]", text[:pos])[-1]


def in_conditional_clause(text: str, pos: int) -> bool:
    return bool(CONDITIONAL.search(clause_before(text, pos)))


def _hits(family: str, text: str) -> list[str]:
    out = []
    if family == "reassurance":
        for m in REASSURANCE.finditer(text):
            if not NEGATION.search(" ".join(clause_before(text, m.start()).split()[-4:])):
                out.append(m.group(0))
    elif family == "change":
        for m in CHANGE.finditer(text):
            before = clause_before(text, m.start())
            prev = before.split()[-1].lower() if before.split() else ""
            if prev in ("a", "an", "the", "of", "no") and m.group(1).lower() in ("double", "change", "switch"):
                continue  # noun use: "a double dose", "a change of medicine"
            if not NEGATION.search(" ".join(before.split()[-4:])):
                out.append(m.group(0))
    else:
        for m in DIAGNOSIS.finditer(text):
            if not in_conditional_clause(text, m.start()):
                out.append(m.group(0))
    return out


def scan(text: str, template_id: str | None = None, source: str | None = None) -> list[tuple[str, str]]:
    """[(family, matched text)] for forbidden claims in `text`. Families allow-listed for template_id are skipped; with `source`, a family
    already present in the source text is not blamed on the candidate."""
    skip = ALLOW.get(template_id or "", set())
    src_hit = {f for f in FAMILIES if source and _hits(f, source)}
    return [(f, h) for f in FAMILIES if f not in skip and f not in src_hit for h in _hits(f, text)]
