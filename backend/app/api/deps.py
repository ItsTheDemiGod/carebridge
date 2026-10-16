"""Request context: app services, database connection, the session from the cookie, and the consent gate."""
from dataclasses import dataclass
from typing import Any, NamedTuple

from fastapi import Depends, Request

from app.api.errors import ApiError
from app.db import repo
from app.db.crypto import Vault
from app.db.database import Database
from app.services import consent as C

COOKIE = "cb_session"


@dataclass
class Ctx:
    settings: Any
    db: Database
    vault: Vault
    pipeline: Any = None
    worker: Any = None


class Sess(NamedTuple):
    id: str
    language: str
    expires_at: float


def get_ctx(request: Request) -> Ctx:
    return request.app.state.cb


def db_conn(ctx: Ctx = Depends(get_ctx)):
    with ctx.db.session() as conn:
        yield conn


def require_session(request: Request, ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)) -> Sess:
    token = request.cookies.get(COOKIE)
    row = repo.session_by_token(conn, token) if token else None
    if row is None:
        raise ApiError(401, "no_session")
    if row["expires_at"] <= repo.now():
        from app.services.erasure import erase_session

        erase_session(ctx, row["id"])  # retention is enforced here too, not only by the periodic sweep
        raise ApiError(401, "session_expired")
    repo.touch(conn, row["id"])
    return Sess(row["id"], row["language"], row["expires_at"])


def require_consent(s: Sess = Depends(require_session), conn=Depends(db_conn)) -> Sess:
    if repo.get_consent(conn, s.id, C.NOTICE_VERSION) is None:
        raise ApiError(403, "consent_required")
    return s


def get_document_or_404(conn, s: Sess, doc_id: str) -> dict:
    d = repo.get_document(conn, s.id, doc_id)
    if d is None:
        raise ApiError(404, "not_found")  # a foreign id looks exactly like a missing one
    return d
