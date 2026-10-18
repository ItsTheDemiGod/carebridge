"""Phase 6d investigation: DELETE /session while a background narrative job of the same session is still running (mocked slow narrative).
Measures how long the delete takes and what remains afterwards. Synthetic data, no model."""
import threading
import time

from tests.apihelpers import Env, fake_narrate


def _slow(gate: threading.Event, started: threading.Event):
    def narrate(items, nar, lang, prov):
        if lang != "en":
            started.set()
            assert gate.wait(30), "gate never opened"  # a Tamil/Hindi narrative that is still running
        return fake_narrate(items, nar, lang, prov)
    return narrate


def test_delete_while_a_language_job_is_running_is_fast_and_leaves_nothing(tmp_path):
    gate, started = threading.Event(), threading.Event()
    with Env(tmp_path, narrate=_slow(gate, started)) as env:
        c = env.start(lang="ta")  # english + tamil jobs start with the extraction
        r = env.upload(client=c)
        assert r.status_code == 202
        did = r.json()["id"]
        assert started.wait(20), "the Tamil job never started"
        # the Tamil job is blocked inside the narrative; delete now
        t0 = time.perf_counter()
        d = c.delete("/api/v1/session")
        took = time.perf_counter() - t0
        assert d.status_code == 200, d.text
        assert took < 2.0, f"delete took {took:.2f}s while a narrative job was running"
        with env.ctx.db.session() as conn:
            for table in ("sessions", "documents", "payloads", "consents", "adherence_events"):
                assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
        gate.set()  # the job finishes after the deletion
        env.wait()
        with env.ctx.db.session() as conn:  # it must not recreate anything
            for table in ("sessions", "documents", "payloads"):
                assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, f"{table} re-created after deletion"
        assert c.get(f"/api/v1/documents/{did}").status_code in (401, 403, 404)
