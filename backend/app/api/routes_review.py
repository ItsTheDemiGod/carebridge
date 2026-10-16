"""Formulary picker, medicines review and the confirmation set (docs/CONFIRMATION.md)."""
from fastapi import APIRouter, Depends, Query

from app.api.deps import Ctx, Sess, db_conn, get_ctx, get_document_or_404, require_consent, require_session
from app.api.errors import ApiError
from app.db import repo
from app.schemas.confirmation import AS_ON_LABEL, DOSE_OPTIONS, Confirmations, Overlay
from app.schemas.normalised import NormalisedDocument
from app.services import confirmation as CF
from app.services import formulary as F
from app.services import templates as T

router = APIRouter(prefix="/api/v1")
ACTIONS = ["confirm_as_extracted", "select_formulary_drug", "not_in_list", "remove"]


def load_document(ctx: Ctx, conn, did: str) -> NormalisedDocument:
    raw = repo.get_payload(conn, ctx.vault, did, "normalised")
    if raw is None:
        raise ApiError(409, "not_ready")
    return NormalisedDocument.model_validate(raw)


def load_confirmations(ctx: Ctx, conn, did: str) -> Confirmations | None:
    raw = repo.get_payload(conn, ctx.vault, did, "confirmations")
    return Confirmations.model_validate(raw) if raw is not None else None


def reason_view(rid: str, lang: str) -> dict:
    tid = f"confirm.flag.{rid}"
    ok = tid in T.load()["strings"]
    return {"id": rid, "template_id": tid if ok else None, "text": T.render(tid, lang) if ok else None, "kind": "name" if rid in CF.NAME_REASONS else "acknowledge"}


def formulary_view(e: dict) -> dict:
    return {**e, "strength_as_label_option": AS_ON_LABEL}


@router.get("/formulary/search")
def formulary_search(q: str = Query("", max_length=60), limit: int = Query(20, ge=1, le=20), s: Sess = Depends(require_session)):
    return {"results": [formulary_view(e) for e in F.search(q, limit)], "formulary_status": F.status()}  # the query itself is never echoed


@router.get("/formulary/{fid}")
def formulary_get(fid: str, s: Sess = Depends(require_session)):
    e = F.get(fid)
    if e is None:
        raise ApiError(404, "not_found")
    return {**formulary_view(e), "formulary_status": F.status()}


@router.get("/documents/{doc_id}/medicines")
def medicines(doc_id: str, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    get_document_or_404(conn, s, doc_id)
    nd = load_document(ctx, conn, doc_id)
    conf = load_confirmations(ctx, conn, doc_id)
    decisions = {d.index: d.model_dump(mode="json") for d in conf.decisions} if conf else {}
    out = []
    for i, m in enumerate(nd.medications):
        f = m.frequency
        exact = CF.has_exact_identity(m)
        out.append({
            "index": i, "ref": f"m{i}",
            "as_written": {"brand": m.as_written_brand_name, "generic": m.as_written_generic_name},
            "printed": {"brand": m.printed_brand, "generic": m.printed_generic},
            "resolved_generic": m.resolved_generic, "name_match_type": m.name_match_type,
            "strength": m.strength, "dose": m.dose, "form": m.form.value, "route": m.route.value,
            "frequency": {"times_per_day": f.times_per_day.value, "timing_label": f.timing_label.value, "is_prn": f.is_prn.value, "original_abbreviation": f.original_abbreviation},
            "duration_days": m.duration_days.value, "duration_text": m.duration_text,
            "source_quote": m.source_quote, "review_level": m.review_level, "flags": m.flags,
            "reasons": [reason_view(r, s.language) for r in CF.reason_ids(m)],
            "interaction_ready": m.interaction_ready, "schedule_ready": m.schedule_ready, "has_exact_identity": exact,
            "allowed_actions": ACTIONS, "current_decision": decisions.get(i)})
    return {"medicines": out, "added_medicines": [a.model_dump(mode="json") for a in conf.added_medicines] if conf else [],
            "dose_options": list(DOSE_OPTIONS), "strength_as_label_option": AS_ON_LABEL, "formulary_status": F.status(),
            "compare_note": T.render("picker.compare_note", s.language)}


def summary(ov: Overlay) -> list[dict]:
    return [{"ref": c.ref, "resolution": c.resolution, "interaction_ready": c.med.interaction_ready, "schedule_ready": c.med.schedule_ready,
             "review_level": c.med.review_level, "unresolved": c.unresolved, "not_checked_reason": c.not_checked_reason} for c in ov.meds]


@router.post("/documents/{doc_id}/confirmations")
def put_confirmations(doc_id: str, body: Confirmations, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Replaces the whole previous set (idempotent). The server validates every rule; nothing the user typed is used for any lookup."""
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "awaiting_confirmation":
        raise ApiError(409, "not_ready")
    nd = load_document(ctx, conn, doc_id)
    try:
        ov = CF.apply(nd, body)
    except CF.ConfirmationError:
        raise ApiError(422, "invalid_confirmation")
    repo.put_payload(conn, ctx.vault, doc_id, "confirmations", body.model_dump(mode="json"))
    audit = repo.get_payload(conn, ctx.vault, doc_id, "decisions") or []
    now = repo.now()
    audit = (audit + [{"at": now, "index": x.index, "action": x.action, "has_note": bool(x.note)} for x in body.decisions]
             + [{"at": now, "index": None, "action": "add_medicine", "has_note": False} for _ in body.added_medicines] + ([{"at": now, "index": None, "action": "clear", "has_note": False}] if not body.decisions and not body.added_medicines else []))[-200:]
    repo.put_payload(conn, ctx.vault, doc_id, "decisions", audit)
    return {"confirmed": True, "medicines": summary(ov), "removed": ov.removed}
