"""Consent notice, anonymous session, itemised consent, delete-my-data, static UI strings."""
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel

from app.api.deps import COOKIE, Ctx, Sess, db_conn, get_ctx, require_session
from app.api.errors import ApiError
from app.db import repo
from app.services import consent as C
from app.services import templates as T
from app.services.erasure import erase_session

router = APIRouter(prefix="/api/v1")
Lang = Literal["en", "ta", "hi"]
STRING_PREFIXES = ("error.", "job.", "status.", "confirm.", "picker.", "schedule.", "summary.", "consent.", "delete.", "label.", "heading.", "timing.", "banner.", "notice.")


class SessionIn(BaseModel):
    language: Lang = "en"


class ConsentIn(BaseModel):
    notice_version: str
    purposes: list[str]


def _cookie_args(ctx: Ctx) -> dict:
    return dict(httponly=True, samesite="lax", secure=ctx.settings.cookie_secure, path="/api")


@router.get("/consent-notice")
def consent_notice(lang: Lang = "en"):
    return C.notice(lang)


@router.get("/strings")
def strings(lang: Lang = "en", prefix: str = Query("", max_length=40)):
    """Static template text (no user data) so the UI can show errors, labels and notices in the user's language."""
    S = T.load()["strings"]
    return {"language": lang, "strings": {t: v[lang]["text"] for t, v in S.items() if t.startswith(STRING_PREFIXES) and t.startswith(prefix)},  # {placeholders} are filled by the UI
            "draft_unreviewed": lang != "en"}


def _state(ctx: Ctx, conn, s: Sess) -> dict:
    cons = repo.get_consent(conn, s.id, C.NOTICE_VERSION)
    return {"language": s.language, "expires_at": datetime.fromtimestamp(s.expires_at, timezone.utc).isoformat(),
            "consent": {"granted": cons is not None, "current_version": C.NOTICE_VERSION, "purposes": cons["purposes"] if cons else []},
            "documents": repo.count_documents(conn, s.id),
            "limits": {"max_documents": ctx.settings.max_docs_per_session, "max_upload_bytes": ctx.settings.max_upload_bytes}}


@router.post("/sessions", status_code=201)
def create_session(body: SessionIn, request: Request, response: Response, ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Start (or resume) the anonymous session. A valid cookie is reused, so a page reload does not orphan data."""
    token = request.cookies.get(COOKIE)
    row = repo.session_by_token(conn, token) if token else None
    if row is not None and row["expires_at"] > repo.now():
        repo.set_language(conn, row["id"], body.language)
        sess = Sess(row["id"], body.language, row["expires_at"])
        response.status_code = 200
    else:
        sid, token = repo.create_session(conn, body.language, ctx.settings.session_ttl_hours)
        sess = Sess(sid, body.language, repo.now() + ctx.settings.session_ttl_hours * 3600)
        response.set_cookie(COOKIE, token, max_age=int(ctx.settings.session_ttl_hours * 3600), **_cookie_args(ctx))
    return _state(ctx, conn, sess)


@router.get("/session")
def get_session(s: Sess = Depends(require_session), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    return _state(ctx, conn, s)


@router.post("/consent")
def give_consent(body: ConsentIn, s: Sess = Depends(require_session), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    if body.notice_version != C.NOTICE_VERSION or not C.valid_purposes(body.purposes):
        raise ApiError(400, "consent_invalid")
    n = C.notice(s.language)
    repo.put_consent(conn, s.id, n["version"], n["sha256"], s.language, sorted(set(body.purposes)))
    return _state(ctx, conn, s)


@router.delete("/session")
def delete_session(request: Request, ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Delete-my-data and withdraw consent: one call. Idempotent: no session (already deleted) gives 204."""
    token = request.cookies.get(COOKIE)
    row = repo.session_by_token(conn, token) if token else None
    resp = Response(status_code=204)
    resp.delete_cookie(COOKIE, **_cookie_args(ctx))
    if row is None:
        return resp
    lang, counts = row["language"], erase_session(ctx, row["id"])
    deleted_at = datetime.now(timezone.utc).isoformat()
    resp = Response(json.dumps({"deleted": counts, "deleted_at": deleted_at, "message": T.render("delete.done", lang),
                                "receipt": T.render("delete.receipt", lang, documents=counts["documents"], payloads=counts["payloads"], images=counts["images"])}, ensure_ascii=False),
                    media_type="application/json")
    resp.delete_cookie(COOKIE, **_cookie_args(ctx))
    return resp
