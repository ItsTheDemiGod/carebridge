"""Upload (raw body), job state, list, kept photo, retry, extra narrative language."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from app.api.deps import Ctx, Sess, db_conn, get_ctx, get_document_or_404, require_consent
from app.api.errors import ApiError
from app.db import repo
from app.services import consent as C
from app.services import templates as T
from app.services.uploads import UploadError, process_image

router = APIRouter(prefix="/api/v1")
ERROR_CODES = ("ollama_unavailable", "image_unreadable", "context_truncated", "image_not_received", "timeout", "interrupted", "provider_not_allowed")


class LanguageIn(BaseModel):
    language: Literal["en", "ta", "hi"]


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def doc_view(conn, d: dict, lang: str) -> dict:
    p = d["progress"]
    code = d["error_code"]
    return {"id": d["id"], "state": d["state"], "error_code": code,
            "error_message": T.render(f"job.failed.{code}", lang) if code in ERROR_CODES else None,
            "created_at": iso(d["created_at"]), "updated_at": iso(d["updated_at"]), "image_kept": d["image_kept"],
            "narrative": p.get("narrative", {}), "timings": {**p.get("timings", {}), **{f"narrative_{k}_s": v for k, v in p.get("narrative_done_at", {}).items()}},
            "retry_possible": d["state"] == "failed" and d["image_kept"], "confirmed": repo.has_payload(conn, d["id"], "confirmations")}


async def read_body(request: Request, limit: int) -> bytes:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit:
        raise ApiError(413, "upload_too_large")
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise ApiError(413, "upload_too_large")
        chunks.append(chunk)
    return b"".join(chunks)


BINARY = {"schema": {"type": "string", "format": "binary"}}


@router.post("/documents", status_code=202, openapi_extra={"requestBody": {"required": True, "content": {"image/png": BINARY, "image/jpeg": BINARY}}})
async def upload(request: Request, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Raw image bytes as the body (Content-Type image/png or image/jpeg). The photo is processed and discarded unless keep_photo_for_session was consented."""
    cfg = ctx.settings
    if repo.count_documents(conn, s.id) >= cfg.max_docs_per_session:
        raise ApiError(429, "too_many_documents")
    if not ctx.worker.has_room():
        raise ApiError(429, "queue_full", {"Retry-After": "60"})
    ctype = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if ctype == "application/pdf":
        raise ApiError(415, "pdf_not_supported")
    if ctype not in ("image/png", "image/jpeg"):
        raise ApiError(415, "unsupported_file")
    data = await read_body(request, cfg.max_upload_bytes)
    try:
        clean, mime = await run_in_threadpool(process_image, data, ctype, cfg.max_image_pixels)
    except UploadError as e:
        raise ApiError(e.status, e.code)
    del data
    keep = "keep_photo_for_session" in (repo.get_consent(conn, s.id, C.NOTICE_VERSION) or {}).get("purposes", [])
    did = repo.create_document(conn, s.id, keep)
    repo.update_document(conn, did, merge={"mime": mime})
    if keep:
        repo.put_payload(conn, ctx.vault, did, "images", clean)  # encrypted; only because the user opted in
    ctx.pipeline.hold(did, clean, mime)
    if not ctx.worker.submit_extraction(did):  # lost a race for the last queue slot
        ctx.pipeline.forget([did])
        c = conn.execute("DELETE FROM documents WHERE id=?", (did,))
        raise ApiError(429, "queue_full", {"Retry-After": "60"})
    return doc_view(conn, repo.get_document(conn, s.id, did), s.language)


@router.get("/documents")
def list_documents(s: Sess = Depends(require_consent), conn=Depends(db_conn)):
    return {"documents": [doc_view(conn, d, s.language) for d in repo.list_documents(conn, s.id)]}


@router.get("/documents/{doc_id}")
def get_document(doc_id: str, s: Sess = Depends(require_consent), conn=Depends(db_conn)):
    return doc_view(conn, get_document_or_404(conn, s, doc_id), s.language)


@router.get("/documents/{doc_id}/image")
def get_image(doc_id: str, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    d = get_document_or_404(conn, s, doc_id)
    blob = repo.get_payload(conn, ctx.vault, doc_id, "images") if d["image_kept"] else None
    if blob is None:
        raise ApiError(404, "not_found")  # the photo was not kept
    return Response(blob, media_type=d["progress"].get("mime", "image/png"))


@router.post("/documents/{doc_id}/retry", status_code=202)
def retry(doc_id: str, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Only possible when the photo was kept (it is stored encrypted); otherwise the user must upload again."""
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "failed" or not d["image_kept"]:
        raise ApiError(409, "retry_unavailable")
    if not ctx.worker.has_room():
        raise ApiError(429, "queue_full", {"Retry-After": "60"})
    repo.update_document(conn, doc_id, state="queued", error_code=None, progress={"mime": d["progress"].get("mime", "image/png")})
    ctx.worker.submit_extraction(doc_id)
    return doc_view(conn, repo.get_document(conn, s.id, doc_id), s.language)


@router.post("/documents/{doc_id}/languages", status_code=202)
def add_language(doc_id: str, body: LanguageIn, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "awaiting_confirmation":
        raise ApiError(409, "not_ready")
    ctx.pipeline.request_language(conn, doc_id, body.language)
    return doc_view(conn, repo.get_document(conn, s.id, doc_id), s.language)
