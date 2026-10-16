import sqlite3

import pytest
from cryptography.fernet import Fernet

from app.db import repo
from app.db.crypto import CryptoError, Vault
from app.db.database import Database

SECRET = "CANARY-Metformin-500mg-secret"


@pytest.fixture
def vault():
    return Vault(Fernet.generate_key())


@pytest.fixture
def db(tmp_path):
    return Database(tmp_path / "t.db")


def _doc(c):
    sid, tok = repo.create_session(c, "en", 24)
    return sid, tok, repo.create_document(c, sid, False)


def test_round_trip_json_and_bytes(vault):
    assert vault.open("d1", "normalised", vault.seal("d1", "normalised", {"a": [1, "x"]})) == {"a": [1, "x"]}
    assert vault.open("d1", "images", vault.seal("d1", "images", b"\x89PNG\x00\xff")) == b"\x89PNG\x00\xff"


def test_tampering_detected(vault):
    blob = bytearray(vault.seal("d1", "normalised", {"a": 1}))
    blob[-5] ^= 1
    with pytest.raises(CryptoError):
        vault.open("d1", "normalised", bytes(blob))


def test_blob_moved_to_other_document_or_kind_rejected(vault):
    blob = vault.seal("d1", "normalised", {"a": 1})
    with pytest.raises(CryptoError):
        vault.open("d2", "normalised", blob)
    with pytest.raises(CryptoError):
        vault.open("d1", "narrative", blob)


def test_wrong_key_and_bad_key():
    blob = Vault(Fernet.generate_key()).seal("d1", "k", {"a": 1})
    with pytest.raises(CryptoError):
        Vault(Fernet.generate_key()).open("d1", "k", blob)
    with pytest.raises(CryptoError):
        Vault("not a key")


def test_blob_moved_between_rows_in_the_database(db, vault):
    with db.session() as c:
        _, _, d1 = _doc(c)
        _, _, d2 = _doc(c)
        repo.put_payload(c, vault, d1, "normalised", {"x": SECRET})
        c.execute("INSERT INTO payloads SELECT ?, kind, blob, created_at FROM payloads WHERE document_id=?", (d2, d1))
        with pytest.raises(CryptoError):
            repo.get_payload(c, vault, d2, "normalised")


def test_database_file_has_no_plaintext_and_token_not_stored(db, vault):
    with db.session() as c:
        sid, tok, d = _doc(c)
        repo.put_payload(c, vault, d, "normalised", {"x": SECRET})
        repo.put_payload(c, vault, d, "images", SECRET.encode())
    raw = db.path.read_bytes()
    assert SECRET.encode() not in raw
    assert tok.encode() not in raw
    with db.session() as c:
        assert c.execute("SELECT token_hash FROM sessions").fetchone()[0] == repo.token_hash(tok) != tok
        assert repo.session_by_token(c, tok)["id"] == sid and repo.session_by_token(c, tok + "x") is None


def test_pragmas_and_no_wal(db):
    with db.session() as c:
        assert c.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert c.execute("PRAGMA secure_delete").fetchone()[0] == 1
        assert c.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert c.execute("PRAGMA user_version").fetchone()[0] == 1
    assert not list(db.path.parent.glob("*-wal")) and not list(db.path.parent.glob("*-shm"))


def test_cascade_delete_and_counts(db, vault):
    with db.session() as c:
        sid, _, d = _doc(c)
        sid2, _, d2 = _doc(c)
        repo.put_consent(c, sid, "1", "h", "en", ["process_photo"])
        repo.put_payload(c, vault, d, "normalised", {"x": 1})
        repo.put_payload(c, vault, d, "images", b"img")
        repo.put_adherence(c, sid, d, "m0", "08:00", "2026-10-16", "taken")
        repo.put_payload(c, vault, d2, "normalised", {"x": 2})
        counts = repo.delete_session(c, sid)
        assert counts == {"consents": 1, "documents": 1, "adherence_events": 1, "payloads": 2, "images": 1, "sessions": 1}
        assert repo.delete_session(c, sid)["sessions"] == 0  # idempotent
        assert c.execute("SELECT COUNT(*) FROM payloads").fetchone()[0] == 1  # the other session is untouched
        repo.vacuum(c)


def test_adherence_upsert_and_status_check(db):
    with db.session() as c:
        sid, _, d = _doc(c)
        a = repo.put_adherence(c, sid, d, "m0", "08:00", "2026-10-16", "taken")
        assert repo.put_adherence(c, sid, d, "m0", "08:00", "2026-10-16", "skipped") == a
        assert [e["status"] for e in repo.list_adherence(c, sid, d)] == ["skipped"]
        with pytest.raises(sqlite3.IntegrityError):
            c.execute("INSERT INTO adherence_events VALUES ('x',?,?,'m0','09:00','2026-10-16','maybe',0)", (sid, d))


def test_documents_are_filtered_by_session(db):
    with db.session() as c:
        s1, _, d1 = _doc(c)
        s2, _, _ = _doc(c)
        assert repo.get_document(c, s1, d1)["id"] == d1 and repo.get_document(c, s2, d1) is None
