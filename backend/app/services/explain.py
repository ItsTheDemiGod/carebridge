"""Assemble the ExplanationDocument: disclaimer, template medicine lines, verified (or fallback) narrative lines, not-found items.

Hard rules: one output line per extracted warning (never dropped, merged or added); a must_confirm medicine always carries the confirm
banner; unverified model text is never shown as verified (the original extracted English is shown with a fallback notice instead).
"""

from app.schemas.explanation import LANGS, ExplanationDocument, ExplanationLine, LangText, Notice, Section, Verification
from app.schemas.normalised import NormalisedDocument
from app.services import templates as T
from app.services.narrative import PROMPT_VERSION, Item, Narrative
from app.services.verification import lang_text_for, verify_narrative

SECTIONS = [("disclaimer", "disclaimer"), ("medicines", "medicines"), ("follow_ups", "follow_ups"), ("advice", "advice"), ("warnings", "warnings"), ("not_found", "not_found")]


def follow_up_text(fu) -> str:
    """Extracted description, plus the extracted date text when the description does not already contain it."""
    d, dt = fu.description.strip(), (fu.date_text or "").strip()
    return f"{d} ({dt})" if dt and dt.lower() not in d.lower() else d


def narrative_items(nd: NormalisedDocument) -> list[Item]:
    """Free-text items for the model, with ids that tie each line back to its source index."""
    return ([Item(id=f"advice-{i}", kind="advice", text=t.strip()) for i, t in enumerate(nd.diet_activity_advice) if t.strip()]
            + [Item(id=f"follow_up-{i}", kind="follow_up", text=follow_up_text(f)) for i, f in enumerate(nd.follow_ups) if f.description.strip()]
            + [Item(id=f"warning-{i}", kind="warning", text=r.text.strip()) for i, r in enumerate(nd.red_flags) if r.text.strip()])


def _fallback_notice(langs: list[str]) -> Notice:
    return Notice(code="fallback", text={lang: LangText(text=T.render("fallback.notice", lang), status="template", review_status=T.review_status("fallback.notice", lang)) for lang in langs})


def _line(item: Item, ref: int, verified: dict) -> ExplanationLine:
    texts, notices = {}, []
    for lang in LANGS:
        cand, v = verified.get(item.id, {}).get(lang, (None, Verification(reason="no_model_text: narrative not run for this line")))
        texts[lang] = lang_text_for(item.text, cand, v)
    failed = [lang for lang, t in texts.items() if t.display_mode == "original_with_notice"]
    if failed:
        notices.append(_fallback_notice(failed))
    statuses = {t.status for t in texts.values()}
    status = "verified" if statuses == {"verified"} else "original_only" if statuses == {"original_only"} else "unverified"
    return ExplanationLine(line_id=item.id, source_ref=ref, kind=item.kind, text=texts, source_text=item.text, status=status,
                           display_mode="original_with_notice" if failed else "explanation", notices=notices)


def _fixed(line_id: str, kind: str, template_id: str, **kw) -> ExplanationLine:
    return ExplanationLine(line_id=line_id, source_ref=None, kind=kind, text=T.lang_texts([(template_id, kw)]), source_text="", status="template", display_mode="explanation")


def build_explanation(nd: NormalisedDocument, narrative: Narrative | None, document_id: str | None = None, model: str = "") -> ExplanationDocument:
    """narrative=None means the model did not run: every free-text line falls back to the original text."""
    verified = verify_narrative(narrative) if narrative is not None else {}
    by_id = {i.id: i for i in (narrative.items if narrative is not None else narrative_items(nd))}
    sec = {k: [] for k, _ in SECTIONS}
    sec["disclaimer"].append(_fixed("disclaimer", "disclaimer", "disclaimer"))
    sec["medicines"] = [T.medicine_line(m, i) for i, m in enumerate(nd.medications)]
    for kind, key, count in (("follow_up", "follow_ups", len(nd.follow_ups)), ("advice", "advice", len(nd.diet_activity_advice)), ("warning", "warnings", len(nd.red_flags))):
        for i in range(count):
            item = by_id.get(f"{kind}-{i}")
            if item is None:  # an empty extracted string: nothing to explain, but a warning must never disappear
                text = (nd.red_flags[i].text if kind == "warning" else nd.diet_activity_advice[i] if kind == "advice" else nd.follow_ups[i].description)
                item = Item(id=f"{kind}-{i}", kind=kind, text=text)
            sec[key].append(_line(item, i, verified))
    for key, label in (("medicines", "medicines"), ("follow_ups", "follow_ups"), ("advice", "advice"), ("warnings", "warnings")):
        if not sec[key]:
            sec["not_found"].append(ExplanationLine(
                line_id=f"not_found-{key}", source_ref=None, kind="not_found", source_text="", status="template", display_mode="explanation",
                text={lang: LangText(text=T.render("not_found.line", lang, item=T.render(f"not_found.item.{label}", lang)), status="template", review_status=T.review_status("not_found.line", lang)) for lang in LANGS}))
    assert len(sec["warnings"]) == len(nd.red_flags), "every extracted warning must produce exactly one output line"
    heads = {k: {lang: T.render(f"heading.{h}", lang) for lang in LANGS} for k, h in SECTIONS}
    return ExplanationDocument(
        document_id=document_id, document_type=nd.document_type.value, templates_version=T.version(), prompt_version=PROMPT_VERSION, model=model,
        sections=[Section(id=k, heading=heads[k], lines=sec[k]) for k, _ in SECTIONS if sec[k] or k in ("disclaimer", "medicines")])
