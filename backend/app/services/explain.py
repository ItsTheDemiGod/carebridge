"""Assemble the ExplanationDocument: disclaimer, template medicine lines, verified (or fallback) narrative lines, not-found items.

Hard rules: one output line per extracted warning (never dropped, merged or added); a must_confirm medicine always carries the confirm
banner; unverified model text is never shown as verified (the original extracted English is shown with a fallback notice instead).
"""

from app.safety import interactions as I
from app.safety.engine import build_report
from app.schemas.explanation import LANGS, ExplanationDocument, ExplanationLine, LangText, Notice, Section, Verification
from app.schemas.normalised import NormalisedDocument
from app.services import phrase_match as PM
from app.services import templates as T
from app.services.narrative import PROMPT_VERSION, Item, Narrative
from app.services.safety_section import safety_lines
from app.services.verification import lang_text_for, verify_narrative

SECTIONS = [("disclaimer", "disclaimer"), ("medicines", "medicines"), ("safety", "safety"), ("follow_ups", "follow_ups"), ("advice", "advice"), ("warnings", "warnings"), ("not_found", "not_found")]


def follow_up_text(fu) -> str:
    """Extracted description, plus the extracted date text when the description does not already contain it."""
    d, dt = fu.description.strip(), (fu.date_text or "").strip()
    return f"{d} ({dt})" if dt and dt.lower() not in d.lower() else d


def narrative_items(nd: NormalisedDocument) -> list[Item]:
    """Free-text items for the model, with ids that tie each line back to its source index."""
    return ([Item(id=f"advice-{i}", kind="advice", text=t.strip()) for i, t in enumerate(nd.diet_activity_advice) if t.strip()]
            + [Item(id=f"follow_up-{i}", kind="follow_up", text=follow_up_text(f)) for i, f in enumerate(nd.follow_ups) if f.description.strip()]
            + [Item(id=f"warning-{i}", kind="warning", text=r.text.strip()) for i, r in enumerate(nd.red_flags) if r.text.strip()])


def library_matches(items: list[Item]) -> dict[str, PM.Match]:
    """Strict phrase-library matches by item id (step A of the pipeline: library, then model, then original English)."""
    return {i.id: m for i in items if (m := PM.match(i.text))}


def model_items(nd: NormalisedDocument, use_library: bool = True) -> list[Item]:
    """Items that go to the model path: everything the library does not match exactly. Matched lines never cost a model call."""
    items = narrative_items(nd)
    hit = library_matches(items) if use_library else {}
    return [i for i in items if i.id not in hit]


LABEL_ID = {"native_reviewed": "label.native_reviewed", "draft_unreviewed": "label.draft_unreviewed", "machine_checked": "label.machine_checked"}


def with_label(t: LangText, lang: str) -> LangText:
    """Attach the rendered trust label. Original-only text carries the fallback notice instead; authored English has no label."""
    key = t.label_key
    if key in LABEL_ID:
        t.label = T.render("label.machine_checked_en" if key == "machine_checked" and lang == "en" else LABEL_ID[key], lang)
    return t


def _library_line(item: Item, ref: int, m: PM.Match) -> ExplanationLine:
    ph = PM.by_id()[m.phrase_id]
    texts = {lang: with_label(LangText(text=PM.render(ph, lang, m.n), status="template", review_status="not_required" if lang == "en" else ph[lang]["review_status"], provenance="phrase_library"), lang)
             for lang in LANGS}
    return ExplanationLine(line_id=item.id, source_ref=ref, kind=item.kind, text=texts, source_text=item.text, status="template", display_mode="explanation", provenance="phrase_library")


def _fallback_notice(langs: list[str]) -> Notice:
    return Notice(code="fallback", text={lang: LangText(text=T.render("fallback.notice", lang), status="template", review_status=T.review_status("fallback.notice", lang)) for lang in langs})


def _line(item: Item, ref: int, verified: dict) -> ExplanationLine:
    texts, notices = {}, []
    for lang in LANGS:
        cand, v = verified.get(item.id, {}).get(lang, (None, Verification(reason="no_model_text: narrative not run for this line")))
        texts[lang] = with_label(lang_text_for(item.text, cand, v), lang)
    failed = [lang for lang, t in texts.items() if t.display_mode == "original_with_notice"]
    if failed:
        notices.append(_fallback_notice(failed))
    statuses = {t.status for t in texts.values()}
    status = "verified" if statuses == {"verified"} else "original_only" if statuses == {"original_only"} else "unverified"
    prov = "model_checked" if any(t.provenance == "model_checked" for t in texts.values()) else "original_only"
    return ExplanationLine(line_id=item.id, source_ref=ref, kind=item.kind, text=texts, source_text=item.text, status=status, provenance=prov,
                           display_mode="original_with_notice" if failed else "explanation", notices=notices)


def _fixed(line_id: str, kind: str, template_id: str, **kw) -> ExplanationLine:
    return ExplanationLine(line_id=line_id, source_ref=None, kind=kind, text=T.lang_texts([(template_id, kw)]), source_text="", status="template", display_mode="explanation")


def build_explanation(nd: NormalisedDocument, narrative: Narrative | None, document_id: str | None = None, model: str = "", prompt_version: str = PROMPT_VERSION,
                      use_library: bool = True, safety_data: I.Data | None = None) -> ExplanationDocument:
    """Pipeline per free-text line: (A) strict phrase-library match, (B) verified model text, (C) original English with a notice.
    narrative=None means the model did not run: every line the library does not match falls back to the original text.
    The narrative must hold only the items model_items(nd) returned; a library-matched line never reads it."""
    verified = verify_narrative(narrative) if narrative is not None else {}
    all_items = narrative_items(nd)
    hits = library_matches(all_items) if use_library else {}
    by_id = {i.id: i for i in all_items}
    by_id.update({i.id: i for i in (narrative.items if narrative is not None else [])})
    sec = {k: [] for k, _ in SECTIONS}
    sec["disclaimer"].append(_fixed("disclaimer", "disclaimer", "disclaimer"))
    sec["medicines"] = [T.medicine_line(m, i) for i, m in enumerate(nd.medications)]
    report = build_report(nd, safety_data)
    sec["safety"], events = safety_lines(nd, report)
    for kind, key, count in (("follow_up", "follow_ups", len(nd.follow_ups)), ("advice", "advice", len(nd.diet_activity_advice)), ("warning", "warnings", len(nd.red_flags))):
        for i in range(count):
            item = by_id.get(f"{kind}-{i}")
            if item is None:  # an empty extracted string: nothing to explain, but a warning must never disappear
                text = (nd.red_flags[i].text if kind == "warning" else nd.diet_activity_advice[i] if kind == "advice" else nd.follow_ups[i].description)
                item = Item(id=f"{kind}-{i}", kind=kind, text=text)
            sec[key].append(_library_line(item, i, hits[item.id]) if item.id in hits else _line(item, i, verified))
    for key, label in (("medicines", "medicines"), ("follow_ups", "follow_ups"), ("advice", "advice"), ("warnings", "warnings")):
        if not sec[key]:
            sec["not_found"].append(ExplanationLine(
                line_id=f"not_found-{key}", source_ref=None, kind="not_found", source_text="", status="template", display_mode="explanation",
                text={lang: LangText(text=T.render("not_found.line", lang, item=T.render(f"not_found.item.{label}", lang)), status="template", review_status=T.review_status("not_found.line", lang)) for lang in LANGS}))
    assert len(sec["warnings"]) == len(nd.red_flags), "every extracted warning must produce exactly one output line"
    heads = {k: {lang: T.render(f"heading.{h}", lang) for lang in LANGS} for k, h in SECTIONS}
    return ExplanationDocument(
        document_id=document_id, document_type=nd.document_type.value, templates_version=T.version(), prompt_version=prompt_version, model=model,
        safety=report, guardrail_events=events,
        sections=[Section(id=k, heading=heads[k], lines=sec[k]) for k, _ in SECTIONS if sec[k] or k in ("disclaimer", "medicines")])
