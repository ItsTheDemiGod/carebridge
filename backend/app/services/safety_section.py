"""Turns a SafetyReport into the "safety" section lines of the explanation: fixed templates only, no model, no advice beyond the templates.

Per-pair detail stays in the SafetyReport; users see each FOUND interaction on its own line (most severe first) and ONE aggregated line per kind
of "not checked" with a count. Every assembled English message is scanned by the guardrail; a hit fails closed (fallback notice) and is recorded."""
import re

from app.safety import interactions as I
from app.safety.guardrails import scan
from app.schemas.explanation import LANGS, ExplanationLine, LangText
from app.schemas.normalised import NormalisedDocument
from app.schemas.safety import SafetyReport
from app.services import templates as T


def _name(nd: NormalisedDocument, i: int) -> str:
    """Medicine name for a message: the name as shown in the document, else the formulary generic. Document text is data: trimmed, no braces."""
    n = T.display_name(nd.medications[i])[0] or nd.medications[i].resolved_generic or "a medicine"
    return re.sub(r"[{}\r\n]", " ", n).strip()[:60] or "a medicine"


def _line(line_id: str, tid: str, events: list[str], **kw) -> ExplanationLine:
    hits = scan(T.render(tid, "en", **kw), tid)
    if hits:  # fail closed: never show text the guardrail rejects
        events.append(f"{line_id}: {tid} rejected by guardrail {hits}")
        tid, kw = "fallback.notice", {}
    return ExplanationLine(line_id=line_id, source_ref=None, kind="safety", text=T.lang_texts([(tid, kw)]), source_text="", status="template", display_mode="explanation")


def _plural(base: str, n: int) -> str:
    return f"{base}_1" if n == 1 else base


def safety_lines(nd: NormalisedDocument, report: SafetyReport) -> tuple[list[ExplanationLine], list[str]]:
    events: list[str] = []
    out: list[ExplanationLine] = []
    if report.overall_state != "ok_to_review":  # internal state name; the user text never says "ok"
        out.append(_line("safety-banner", f"banner.safety.{report.overall_state}", events))
    found = [p for p in report.pair_results if p.status == I.FOUND]
    for k, p in enumerate(found):
        out.append(_line(f"safety-pair-{k}", f"safety.level.{p.level}", events, a=_name(nd, p.a), b=_name(nd, p.b)))
    for k, d in enumerate(report.duplicate_notices):
        out.append(_line(f"safety-dup-{k}", "safety.duplicate", events, name=d.name))
    real = [p for p in report.pair_results if not p.same_medicine]
    n_missing = sum(p.status == I.DB_MISSING for p in real)
    n_none = sum(p.status == I.NO_RECORD for p in real)
    n_unc = sum(p.status == I.UNCONFIRMED for p in real)
    if n_missing:
        out.append(_line("safety-db-missing", "safety.db_missing", events))
    if n_none:
        out.append(_line("safety-not-checked", _plural("safety.not_checked", n_none), events, n=n_none))
    if n_unc:
        out.append(_line("safety-unconfirmed", _plural("safety.unconfirmed", n_unc), events, n=n_unc))
    if report.schedule_reminder:
        out.append(_line("safety-reminder", "safety.schedule_reminder", events))
    if report.counts.pairs:
        key = "safety.attribution_reviewed" if report.supplement_reviewed else "safety.attribution_unreviewed"
        text = T.load()["english_only"][key]  # English only; ta/hi show the same English text
        out.append(ExplanationLine(line_id="safety-attribution", source_ref=None, kind="safety", source_text="", status="template", display_mode="explanation",
                                   text={lang: LangText(text=text, status="template", review_status="not_required") for lang in LANGS}))
    return out, events
