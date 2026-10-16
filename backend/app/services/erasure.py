"""Erase a session and everything linked to it: one transaction, then VACUUM. Used by DELETE /session, lazy expiry and the sweep."""
import logging

from app.db import repo

log = logging.getLogger("carebridge")


def erase_session(ctx, sid: str) -> dict:
    with ctx.db.session() as c:
        doc_ids = [d["id"] for d in repo.list_documents(c, sid)]
        counts = repo.delete_session(c, sid)
        repo.vacuum(c)
    if ctx.pipeline is not None:
        ctx.pipeline.forget(doc_ids)  # in-memory photos of queued/running jobs
    log.info("session erased id=%s documents=%s", sid, counts["documents"])
    return counts


def sweep_expired(ctx) -> int:
    with ctx.db.session() as c:
        ids = repo.expired_session_ids(c)
    for sid in ids:
        erase_session(ctx, sid)
    return len(ids)
