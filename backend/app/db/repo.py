"""Data access. Every document query is filtered by the session id, so a foreign id behaves exactly like a missing one (404)."""
import hashlib
import json
import secrets
import sqlite3
import time

from app.db.crypto import Vault
from app.db.database import tx


def now() -> float:
    return time.time()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_id() -> str:
    return secrets.token_urlsafe(16)  # 128 bits


# --- sessions -------------------------------------------------------------------------------------------------------------------------
def create_session(c: sqlite3.Connection, language: str, ttl_hours: float) -> tuple[str, str]:
    sid, token, t = new_id(), secrets.token_urlsafe(32), now()
    c.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?)", (sid, token_hash(token), language, t, t, t + ttl_hours * 3600))
    return sid, token


def session_by_token(c, token: str):
    return c.execute("SELECT * FROM sessions WHERE token_hash=?", (token_hash(token),)).fetchone()


def touch(c, sid: str) -> None:
    c.execute("UPDATE sessions SET last_seen=? WHERE id=?", (now(), sid))


def set_language(c, sid: str, language: str) -> None:
    c.execute("UPDATE sessions SET language=? WHERE id=?", (language, sid))


def expired_session_ids(c) -> list[str]:
    return [r[0] for r in c.execute("SELECT id FROM sessions WHERE expires_at<=?", (now(),))]


COUNT_TABLES = (("consents", "session_id"), ("documents", "session_id"), ("adherence_events", "session_id"))


def delete_session(c, sid: str) -> dict:
    """Erase the session and everything linked to it in one transaction; returns counts (the receipt). VACUUM is the caller's next step."""
    with tx(c):
        counts = {t: c.execute(f"SELECT COUNT(*) FROM {t} WHERE {col}=?", (sid,)).fetchone()[0] for t, col in COUNT_TABLES}
        counts["payloads"] = c.execute("SELECT COUNT(*) FROM payloads WHERE document_id IN (SELECT id FROM documents WHERE session_id=?)", (sid,)).fetchone()[0]
        counts["images"] = c.execute("SELECT COUNT(*) FROM payloads WHERE kind='images' AND document_id IN (SELECT id FROM documents WHERE session_id=?)", (sid,)).fetchone()[0]
        counts["sessions"] = c.execute("DELETE FROM sessions WHERE id=?", (sid,)).rowcount  # cascades to every child table
    return counts


def vacuum(c) -> None:
    c.execute("VACUUM")  # rewrites the file so freed pages (deleted content) are not left behind


# --- consent ---------------------------------------------------------------------------------------------------------------------------
def put_consent(c, sid: str, version: str, sha: str, language: str, purposes: list[str]) -> None:
    c.execute("INSERT OR REPLACE INTO consents VALUES (?,?,?,?,?,?)", (sid, version, sha, language, json.dumps(sorted(purposes)), now()))


def get_consent(c, sid: str, version: str):
    r = c.execute("SELECT * FROM consents WHERE session_id=? AND notice_version=?", (sid, version)).fetchone()
    return None if r is None else {"notice_version": r["notice_version"], "notice_sha256": r["notice_sha256"], "language": r["language"],
                                   "purposes": json.loads(r["purposes"]), "granted_at": r["granted_at"]}


# --- documents -------------------------------------------------------------------------------------------------------------------------
def create_document(c, sid: str, image_kept: bool) -> str:
    did, t = new_id(), now()
    c.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)", (did, sid, "queued", None, "{}", t, t, int(image_kept)))
    return did


def _doc(r) -> dict:
    return {"id": r["id"], "session_id": r["session_id"], "state": r["state"], "error_code": r["error_code"], "progress": json.loads(r["progress"]),
            "created_at": r["created_at"], "updated_at": r["updated_at"], "image_kept": bool(r["image_kept"])}


def get_document(c, sid: str, did: str) -> dict | None:
    r = c.execute("SELECT * FROM documents WHERE id=? AND session_id=?", (did, sid)).fetchone()
    return _doc(r) if r else None


def get_document_any(c, did: str) -> dict | None:
    """Worker only (no session context): the worker holds ids it created itself."""
    r = c.execute("SELECT * FROM documents WHERE id=?", (did,)).fetchone()
    return _doc(r) if r else None


def list_documents(c, sid: str) -> list[dict]:
    return [_doc(r) for r in c.execute("SELECT * FROM documents WHERE session_id=? ORDER BY created_at", (sid,))]


def count_documents(c, sid: str) -> int:
    return c.execute("SELECT COUNT(*) FROM documents WHERE session_id=?", (sid,)).fetchone()[0]


def update_document(c, did: str, state: str | None = None, error_code: str | None = None, progress: dict | None = None, merge: dict | None = None) -> None:
    """state/error_code replace; `progress` replaces the progress json; `merge` shallow-merges into it."""
    r = c.execute("SELECT progress FROM documents WHERE id=?", (did,)).fetchone()
    if r is None:
        return
    prog = progress if progress is not None else json.loads(r[0])
    if merge:
        prog.update(merge)
    sets, args = ["updated_at=?", "progress=?"], [now(), json.dumps(prog)]
    if state is not None:
        sets += ["state=?", "error_code=?"]
        args += [state, error_code]
    c.execute(f"UPDATE documents SET {', '.join(sets)} WHERE id=?", (*args, did))


def all_documents(c) -> list[dict]:
    return [_doc(r) for r in c.execute("SELECT * FROM documents")]


# --- payloads (always encrypted) ---------------------------------------------------------------------------------------------------------
def put_payload(c, vault: Vault, did: str, kind: str, value) -> None:
    c.execute("INSERT OR REPLACE INTO payloads VALUES (?,?,?,?)", (did, kind, vault.seal(did, kind, value), now()))


def get_payload(c, vault: Vault, did: str, kind: str):
    r = c.execute("SELECT blob FROM payloads WHERE document_id=? AND kind=?", (did, kind)).fetchone()
    return None if r is None else vault.open(did, kind, r[0])


def has_payload(c, did: str, kind: str) -> bool:
    return c.execute("SELECT 1 FROM payloads WHERE document_id=? AND kind=?", (did, kind)).fetchone() is not None


def delete_payload(c, did: str, kind: str) -> None:
    c.execute("DELETE FROM payloads WHERE document_id=? AND kind=?", (did, kind))


# --- adherence ---------------------------------------------------------------------------------------------------------------------------
def put_adherence(c, sid: str, did: str, med_ref: str, scheduled_time: str, date: str, status: str) -> str:
    """One event per (document, medicine, time, date); logging again changes the status (idempotent for the user)."""
    old = c.execute("SELECT id FROM adherence_events WHERE document_id=? AND med_ref=? AND scheduled_time=? AND date=?", (did, med_ref, scheduled_time, date)).fetchone()
    if old:
        c.execute("UPDATE adherence_events SET status=?, logged_at=? WHERE id=?", (status, now(), old[0]))
        return old[0]
    eid = new_id()
    c.execute("INSERT INTO adherence_events VALUES (?,?,?,?,?,?,?,?)", (eid, sid, did, med_ref, scheduled_time, date, status, now()))
    return eid


def list_adherence(c, sid: str, did: str, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
    q, a = "SELECT * FROM adherence_events WHERE session_id=? AND document_id=?", [sid, did]
    if date_from:
        q, a = q + " AND date>=?", a + [date_from]
    if date_to:
        q, a = q + " AND date<=?", a + [date_to]
    return [{k: r[k] for k in ("id", "document_id", "med_ref", "scheduled_time", "date", "status")} for r in c.execute(q + " ORDER BY date, scheduled_time", a)]


def delete_adherence(c, sid: str, eid: str) -> bool:
    return c.execute("DELETE FROM adherence_events WHERE id=? AND session_id=?", (eid, sid)).rowcount > 0
