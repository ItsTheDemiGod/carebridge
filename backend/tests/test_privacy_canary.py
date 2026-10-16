"""Privacy audit: a unique canary string travels through the whole flow (image, extraction output, narrative, confirmation note) and must never be readable
from disk, logs, caches or temp files, neither while the data exists (encrypted) nor after deletion."""
import io
import logging
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from app.api.deps import Ctx
from app.db import repo
from app.logging_config import PolicyFilter
from app.services.erasure import sweep_expired
from app.services.guards import REPO
from apihelpers import ALL_PURPOSES, Env, FakeOllama, fake_narrate, gt_output

CANARY = "CANARY-7f3a9c1e5b42"
DATA = REPO / "data"


def canary_image(text=CANARY) -> bytes:
    img = Image.new("RGB", (400, 120), "white")
    ImageDraw.Draw(img).text((10, 40), f"Rx {text}", fill="black")
    buf = io.BytesIO()
    img.save(buf, "PNG")  # in memory only: no source file is written anywhere
    return buf.getvalue()


def canary_output(tag=CANARY):
    o = gt_output("ds_037")
    o.medications[0].special_instructions = f"take as told {tag}"
    o.medications[0].source_quote += f" {tag}"
    o.diet_activity_advice.append(f"Drink plenty of water {tag}")
    o.follow_ups[0].description += f" {tag}"
    o.red_flags[0].text += f" {tag}"
    return o


def files_with(root: Path, needle: bytes, skip=()) -> list[str]:
    hits = []
    for p in root.rglob("*"):
        if p.is_file() and not any(p.is_relative_to(s) for s in skip):
            try:
                if needle in p.read_bytes():
                    hits.append(str(p))
            except OSError:
                pass
    return hits


def side_files(db_path: Path) -> list[Path]:
    return [p for p in db_path.parent.iterdir() if p.is_file() and p.name.startswith(db_path.name) and p != db_path]  # -journal, -wal, -shm


def run_flow(e, lang="ta", tag=CANARY, client=None):
    c = e.start(lang, ALL_PURPOSES, client=client)
    r = e.upload(canary_image(tag), client=c)
    assert r.status_code == 202
    e.wait()
    did = r.json()["id"]
    assert c.get(f"/api/v1/documents/{did}").json()["state"] == "awaiting_confirmation"
    r = c.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": 0, "action": "confirm_as_extracted", "note": tag}]})
    assert r.status_code == 200
    return c, did


def test_canary_is_encrypted_at_rest_and_gone_after_deletion(tmp_path, tmp_path_factory, caplog):
    caplog.set_level(logging.DEBUG)
    tmp_before = {p.name: p.stat().st_mtime_ns for p in Path(tempfile.gettempdir()).iterdir() if p.is_file()}
    cache_before = sorted((str(p), p.stat().st_mtime_ns) for p in (DATA / "cache").rglob("*") if p.is_file())
    with Env(tmp_path, provider=FakeOllama(output=canary_output())) as e:
        c, did = run_flow(e)
        other = e.new_client()
        e.provider.output = canary_output("OTHERSESSION-9d8c7b6a5f40")
        oc, odid = run_flow(e, "en", "OTHERSESSION-9d8c7b6a5f40", client=other)
        # the data really carries the canary: it is visible through the API (so the checks below are meaningful)
        res = c.get(f"/api/v1/documents/{did}/result?lang=en").text
        assert CANARY in res and CANARY in c.get(f"/api/v1/documents/{did}/medicines").text
        assert c.get(f"/api/v1/documents/{did}/image").status_code == 200  # the photo was kept (encrypted)
        # --- BEFORE deletion: encrypted, so no plaintext in the database file or its side files -------------------------------------------------
        db = e.ctx.db.path
        assert CANARY.encode() not in db.read_bytes() and b"OTHERSESSION" not in db.read_bytes()
        assert all(CANARY.encode() not in p.read_bytes() for p in side_files(db))
        with e.ctx.db.session() as conn:
            blobs = [bytes(r[0]) for r in conn.execute("SELECT blob FROM payloads WHERE document_id=?", (did,))]
            token_hash = conn.execute("SELECT token_hash FROM sessions WHERE id=(SELECT session_id FROM documents WHERE id=?)", (did,)).fetchone()[0]
        assert blobs and all(b[:60] in db.read_bytes() for b in blobs)  # the ciphertext IS in the file...
        # --- delete ---------------------------------------------------------------------------------------------------------------------------
        r = c.delete("/api/v1/session")
        assert r.status_code == 200 and r.json()["deleted"]["images"] == 1 and r.json()["deleted"]["documents"] == 1
        assert c.delete("/api/v1/session").status_code == 204  # idempotent
        raw = db.read_bytes()
        assert CANARY.encode() not in raw and all(b[:60] not in raw for b in blobs) and token_hash.encode() not in raw  # ...and is overwritten after VACUUM
        assert all(CANARY.encode() not in p.read_bytes() for p in side_files(db))
        assert not [p for p in db.parent.iterdir() if p.name.endswith(("-wal", "-shm", "-journal"))]
        # other sessions' data is untouched and still readable
        assert OTHER_OK(oc, odid)
        # --- everywhere else ------------------------------------------------------------------------------------------------------------------
        assert files_with(DATA, CANARY.encode(), skip=[DATA / "synthetic"]) == []
        assert files_with(tmp_path_factory.getbasetemp(), CANARY.encode()) == []  # pytest's temp folder: database, caches, anything the app wrote
        for p in Path(tempfile.gettempdir()).iterdir():  # the system temp folder: nothing new or changed contains the canary
            if p.is_file() and tmp_before.get(p.name) != p.stat().st_mtime_ns and p.stat().st_size < 20_000_000:
                try:
                    assert CANARY.encode() not in p.read_bytes()
                except OSError:
                    pass
        assert CANARY not in caplog.text and "OTHERSESSION" not in caplog.text
    cache_after = sorted((str(p), p.stat().st_mtime_ns) for p in (DATA / "cache").rglob("*") if p.is_file())
    assert cache_before == cache_after  # the shared caches never receive user content


def OTHER_OK(oc, odid):
    r = oc.get(f"/api/v1/documents/{odid}/result?lang=en")
    return r.status_code == 200 and "OTHERSESSION-9d8c7b6a5f40" in r.text


def test_logs_never_contain_content_even_when_jobs_crash(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)

    class Crashing(FakeOllama):
        def generate(self, *a, **k):
            raise RuntimeError(f"model exploded on {CANARY}")

    def narrate_crash(items, nar, lang, prov):
        raise RuntimeError(f"narrative exploded on {CANARY}")

    with Env(tmp_path, provider=Crashing(), narrate=narrate_crash) as e:
        e.start()
        e.upload_ready(data=canary_image())
        e.ctx.pipeline.provider_factory = lambda: FakeOllama(output=canary_output())
        e.upload_ready(data=canary_image())  # second document: extraction works, narrative crashes
        e.app.add_api_route("/api/v1/boom", lambda: (_ for _ in ()).throw(RuntimeError(f"route exploded on {CANARY}")))
        from fastapi.testclient import TestClient
        c = TestClient(e.app, headers=dict(e.client.headers), raise_server_exceptions=False)
        c.cookies = e.client.cookies
        assert c.get("/api/v1/boom").status_code == 500
    assert CANARY not in caplog.text
    assert any("type=RuntimeError" in r.getMessage() for r in caplog.records)  # the failure is logged, as a type only


def test_log_messages_are_limited_to_ids_states_timings_codes(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    with Env(tmp_path, provider=FakeOllama(output=canary_output())) as e:
        c, did = run_flow(e)
        c.get(f"/api/v1/formulary/search?q={CANARY}")
        c.delete("/api/v1/session")
    allowed = ("started", "session erased id=", "doc=")
    own = [r for r in caplog.records if r.name == "carebridge"]
    assert own and all(r.getMessage().startswith(allowed) for r in own), [r.getMessage() for r in own if not r.getMessage().startswith(allowed)]
    text = caplog.text
    for forbidden in (CANARY, "Metformin", "Glycomet", "Amaryl", "Tab ", "water"):
        assert forbidden not in text


def test_policy_filter_strips_exception_text_and_query_strings():
    f = PolicyFilter()
    try:
        raise ValueError(f"secret {CANARY}")
    except ValueError:
        import sys
        rec = logging.LogRecord("x", logging.ERROR, "f", 1, "job failed", None, sys.exc_info())
    assert f.filter(rec) and CANARY not in rec.getMessage() and "type=ValueError" in rec.getMessage() and rec.exc_info is None
    acc = logging.LogRecord("uvicorn.access", logging.INFO, "f", 1, '%s - "%s %s HTTP/%s" %d', ("127.0.0.1:1", "GET", f"/api/v1/formulary/search?q={CANARY}", "1.1", 200), None)
    f.filter(acc)
    assert CANARY not in acc.getMessage() and "/api/v1/formulary/search" in acc.getMessage()


def test_expiry_sweep_deletes_everything_and_spares_live_sessions(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=canary_output())) as e:
        c, did = run_flow(e)
        e.provider.output = canary_output("OTHERSESSION-9d8c7b6a5f40")
        oc, odid = run_flow(e, "en", "OTHERSESSION-9d8c7b6a5f40", client=e.new_client())
        with e.ctx.db.session() as conn:
            sid = conn.execute("SELECT session_id FROM documents WHERE id=?", (did,)).fetchone()[0]
            conn.execute("UPDATE sessions SET expires_at=? WHERE id=?", (repo.now() - 5, sid))
        assert sweep_expired(e.ctx) == 1 and sweep_expired(e.ctx) == 0
        with e.ctx.db.session() as conn:
            for t in ("sessions", "consents", "documents"):
                assert conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 1  # only the live session's rows remain
            assert conn.execute("SELECT COUNT(*) FROM payloads WHERE document_id!=?", (odid,)).fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM documents WHERE id=?", (did,)).fetchone()[0] == 0
        assert CANARY.encode() not in e.ctx.db.path.read_bytes()
        assert OTHER_OK(oc, odid)
        assert c.get(f"/api/v1/documents/{did}").status_code == 401  # the expired session is gone


def test_startup_sweep_and_periodic_sweeper_run(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        e.upload_ready()
        with e.ctx.db.session() as conn:
            conn.execute("UPDATE sessions SET expires_at=?", (repo.now() - 5,))
        cfg = e.cfg
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app(cfg, provider_factory=lambda: FakeOllama(), sweep_every_s=3600)) as c:  # restart: the startup sweep deletes it
        with c.app.state.cb.db.session() as conn:
            assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0 and conn.execute("SELECT COUNT(*) FROM payloads").fetchone()[0] == 0
    # the periodic sweeper thread: a very short interval removes a session that expires while the app runs
    with Env(tmp_path / "p") as e2:
        pass
    import time

    cfg2 = e2.cfg
    app2 = create_app(cfg2, provider_factory=lambda: FakeOllama(), sweep_every_s=0.1)
    with TestClient(app2, headers={"X-CareBridge-Request": "1"}) as c2:
        c2.post("/api/v1/sessions", json={"language": "en"})
        with app2.state.cb.db.session() as conn:
            conn.execute("UPDATE sessions SET expires_at=?", (repo.now() - 1,))
        for _ in range(50):
            time.sleep(0.1)
            with app2.state.cb.db.session() as conn:
                if conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0:
                    break
        with app2.state.cb.db.session() as conn:
            assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_deleting_a_session_with_a_running_job_does_not_resurrect_data(tmp_path):
    import threading

    gate, started = threading.Event(), threading.Event()
    with Env(tmp_path, provider=FakeOllama(output=canary_output(), hook=lambda parts: (started.set(), gate.wait(10)))) as e:
        c = e.start()
        assert e.upload(canary_image(), client=c).status_code == 202
        started.wait(5)
        assert c.delete("/api/v1/session").status_code == 200  # deleted while the model is still working
        gate.set()
        e.wait()
        with e.ctx.db.session() as conn:
            for t in ("sessions", "documents", "payloads", "consents"):
                assert conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0
        assert e.ctx.pipeline._images == {} and CANARY.encode() not in e.ctx.db.path.read_bytes()
