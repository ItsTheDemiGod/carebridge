"""SQLite (standard library) with versioned migrations. One short-lived connection per use; no connection is shared between threads.

PRAGMAs: foreign_keys (cascade deletes), secure_delete (freed pages are overwritten), journal_mode=DELETE (no -wal/-shm residue), busy_timeout."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS = [
    """
    CREATE TABLE sessions (
        id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE, language TEXT NOT NULL,
        created_at REAL NOT NULL, last_seen REAL NOT NULL, expires_at REAL NOT NULL);
    CREATE TABLE consents (
        session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, notice_version TEXT NOT NULL, notice_sha256 TEXT NOT NULL,
        language TEXT NOT NULL, purposes TEXT NOT NULL, granted_at REAL NOT NULL, PRIMARY KEY (session_id, notice_version));
    CREATE TABLE documents (
        id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, state TEXT NOT NULL, error_code TEXT,
        progress TEXT NOT NULL DEFAULT '{}', created_at REAL NOT NULL, updated_at REAL NOT NULL, image_kept INTEGER NOT NULL DEFAULT 0);
    CREATE INDEX documents_session ON documents(session_id);
    CREATE TABLE payloads (
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, kind TEXT NOT NULL, blob BLOB NOT NULL, created_at REAL NOT NULL,
        PRIMARY KEY (document_id, kind));
    CREATE TABLE adherence_events (
        id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, med_ref TEXT NOT NULL, scheduled_time TEXT NOT NULL,
        date TEXT NOT NULL, status TEXT NOT NULL CHECK (status IN ('taken','skipped')), logged_at REAL NOT NULL,
        UNIQUE (document_id, med_ref, scheduled_time, date));
    CREATE INDEX adherence_doc ON adherence_events(document_id);
    """,
]
KINDS = ("normalised", "narrative", "explanation", "confirmations", "decisions", "images", "schedule_overrides")


def connect(path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, timeout=10, isolation_level=None)  # autocommit; transactions are explicit (tx)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA secure_delete=ON")
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def migrate(conn: sqlite3.Connection) -> int:
    v = conn.execute("PRAGMA user_version").fetchone()[0]
    for n, sql in enumerate(MIGRATIONS[v:], start=v + 1):
        conn.execute("BEGIN IMMEDIATE")
        try:
            for stmt in filter(str.strip, sql.split(";")):
                conn.execute(stmt)
            conn.execute(f"PRAGMA user_version={n}")
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return len(MIGRATIONS)


@contextmanager
def tx(conn: sqlite3.Connection):
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


class Database:
    def __init__(self, path):
        self.path = Path(path)
        with self.session() as c:
            migrate(c)

    @contextmanager
    def session(self):
        c = connect(self.path)
        try:
            yield c
        finally:
            c.close()
