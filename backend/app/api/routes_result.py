"""The assembled result for one document."""
from typing import Literal

from fastapi import APIRouter, Depends

from app.api.deps import Ctx, Sess, db_conn, get_ctx, get_document_or_404, require_consent
from app.api.errors import ApiError
from app.services import result as R

router = APIRouter(prefix="/api/v1")


@router.get("/documents/{doc_id}/result")
def get_result(doc_id: str, lang: Literal["en", "ta", "hi"] | None = None, s: Sess = Depends(require_consent), ctx: Ctx = Depends(get_ctx), conn=Depends(db_conn)):
    """Before confirmation: the unconfirmed normalised document (names that are not interaction_ready are `not_checked_unconfirmed`).
    After confirmation: the overlay. A narrative that is not ready is marked `narrative_pending`, never guessed."""
    d = get_document_or_404(conn, s, doc_id)
    if d["state"] != "awaiting_confirmation":
        raise ApiError(409, "not_ready")
    return R.assemble(ctx, conn, d, lang or s.language)
