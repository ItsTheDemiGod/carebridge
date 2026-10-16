"""Assemble the result for one document: the existing explanation pipeline (templates, phrase library, verified narrative with fallback, safety engine)
run on the OVERLAY (the user's confirmations applied to a copy), plus the data the UI needs: narrative status per language, "you confirmed this" labels,
the confirm-first state. Strings are returned as data; the server never produces HTML."""
from app.db import repo
from app.safety import interactions as I
from app.safety.guardrails import scan
from app.schemas.confirmation import Confirmations, Overlay
from app.schemas.explanation import ExplanationDocument, LangText
from app.schemas.normalised import NormalisedDocument
from app.services import confirmation as CF
from app.services import explain as E
from app.services import templates as T
from app.services.pipeline import narrative_from_json

FREE_TEXT_SECTIONS = ("follow_ups", "advice", "warnings")
RESOLUTION_LABEL = {"confirmed": "confirm.you_confirmed", "selected": "confirm.you_selected", "added": "confirm.you_added"}
PENDING = ("pending", "running")


def safety_data() -> I.Data:
    return I.load_data()  # tests replace this with a synthetic store


def checked(tid: str, lang: str, events: list[str], **kw) -> str:
    """Render a template; every English message is scanned by the guardrail first. A hit fails closed (the fallback notice) and is recorded."""
    hits = scan(T.render(tid, "en", **kw), tid)
    if hits:
        events.append(f"{tid} rejected by guardrail {hits}")
        return T.render("fallback.notice", lang)
    return T.render(tid, lang, **kw)


def load_overlay(ctx, conn, doc_id: str) -> tuple[NormalisedDocument, Overlay, Confirmations | None]:
    nd = NormalisedDocument.model_validate(repo.get_payload(conn, ctx.vault, doc_id, "normalised"))
    raw = repo.get_payload(conn, ctx.vault, doc_id, "confirmations")
    conf = Confirmations.model_validate(raw) if raw is not None else None
    return nd, CF.apply(nd, conf), conf


def _label(tid: str, lang: str, events: list[str]) -> dict:
    return {"template_id": tid, "text": checked(tid, lang, events)}


def _pending_text(lang: str) -> dict:
    return LangText(text=T.render("status.narrative_preparing", lang), status="template", review_status=T.review_status("status.narrative_preparing", lang)).model_dump(mode="json")


def assemble(ctx, conn, doc: dict, lang: str) -> dict:
    nd, ov, conf = load_overlay(ctx, conn, doc["id"])
    raw_nar = repo.get_payload(conn, ctx.vault, doc["id"], "narrative")
    nar = narrative_from_json(raw_nar) if raw_nar else None
    status = {k: doc["progress"].get("narrative", {}).get(k, "not_started") for k in ("en", "ta", "hi")}
    ex: ExplanationDocument = E.build_explanation(ov.doc, nar, document_id=doc["id"], model=ctx.settings.ollama_model, safety_data=safety_data())
    out = ex.model_dump(mode="json")
    events: list[str] = list(out["guardrail_events"])

    # only the requested language is returned; a narrative that is not ready is marked "still preparing", never filled with guesses
    for sec in out["sections"]:
        for line in sec["lines"]:
            pending = sec["id"] in FREE_TEXT_SECTIONS and line["provenance"] != "phrase_library" and status[lang] in PENDING
            line["narrative_pending"] = pending
            line["text"] = {lang: _pending_text(lang) if pending else line["text"][lang]}
            for n in line["notices"]:
                n["text"] = {lang: n["text"][lang]} if lang in n["text"] else {}
            line["notices"] = [n for n in line["notices"] if n["text"] and not (pending and n["code"] == "fallback")]
            if pending:
                line["display_mode"] = "explanation" if not line["notices"] else line["display_mode"]
        sec["heading"] = {lang: sec["heading"][lang]}

    meds = []
    for k, c in enumerate(ov.meds):
        labels = []
        if c.resolution in RESOLUTION_LABEL:
            labels.append(_label(RESOLUTION_LABEL[c.resolution], lang, events))
        if c.not_checked_reason == "user_not_in_list":
            labels.append(_label("confirm.flag.user_not_in_list", lang, events))
        elif c.not_checked_reason == "not_identifiable":
            labels.append(_label("confirm.flag.not_identifiable", lang, events))
        meds.append({"line_id": f"med-{k}", "ref": c.ref, "source_index": c.source_index, "resolution": c.resolution, "provenance": c.provenance, "unresolved": c.unresolved,
                     "not_checked_reason": c.not_checked_reason, "interaction_ready": c.med.interaction_ready, "schedule_ready": c.med.schedule_ready, "labels": labels})
    safety = ex.safety
    return {"document_id": doc["id"], "language": lang, "confirmed": conf is not None, "confirm_first": bool(safety and safety.overall_state == "confirm_first"),
            "narrative_status": status, "explanation": out, "medicines_meta": meds, "removed": ov.removed, "guardrail_events": events}
