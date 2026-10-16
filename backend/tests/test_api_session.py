import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import repo
from app.main import create_app
from app.services import consent as C
from apihelpers import ALL_PURPOSES, REQUIRED, Env, make_cfg

# Pin: the English notice hash for each version. Changing the text without bumping NOTICE_VERSION fails this test.
PINNED = {"1": "c0fb8081d5922137130490e4d3a630a8f859c3c610d7be43d9392db84da0090d"}


def test_app_refuses_to_start_without_key(tmp_path):
    cfg = Settings(_env_file=None, carebridge_data_key=None, db_path=str(tmp_path / "x.db"))
    with pytest.raises(RuntimeError, match="generate_data_key"):
        with TestClient(create_app(cfg)):
            pass
    with pytest.raises(RuntimeError, match="not a valid key"):
        with TestClient(create_app(make_cfg(tmp_path, carebridge_data_key="nope"))):
            pass


def test_notice_all_languages_and_version(tmp_path):
    with Env(tmp_path) as e:
        for lang in ("en", "ta", "hi"):
            n = e.client.get(f"/api/v1/consent-notice?lang={lang}").json()
            assert n["version"] == C.NOTICE_VERSION and len(n["sha256"]) == 64 and len(n["items"]) == 8
            assert {p["id"]: p["required"] for p in n["purposes"]} == {"process_photo": True, "store_results_for_session": True, "keep_photo_for_session": False}
            assert n["review_status"] == ("not_required" if lang == "en" else "draft_unreviewed")
        assert e.client.get("/api/v1/consent-notice?lang=fr").status_code == 422


def test_notice_hash_is_pinned_to_the_version():
    assert PINNED[C.NOTICE_VERSION] == C.notice("en")["sha256"], "notice text changed: bump NOTICE_VERSION and pin the new hash"


def test_consent_gate_blocks_every_data_endpoint(tmp_path):
    with Env(tmp_path) as e:
        e.client.post("/api/v1/sessions", json={"language": "en"})
        for method, path in (("get", "/api/v1/documents"), ("post", "/api/v1/documents"), ("get", "/api/v1/documents/abc")):
            r = e.client.request(method, path, content=b"x", headers={"Content-Type": "image/png"})
            assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required", path


def test_itemised_purposes_and_version(tmp_path):
    with Env(tmp_path) as e:
        e.client.post("/api/v1/sessions", json={"language": "en"})
        post = lambda **b: e.client.post("/api/v1/consent", json=b)  # noqa: E731
        assert post(notice_version="1", purposes=["process_photo"]).status_code == 400  # a required purpose is missing
        assert post(notice_version="1", purposes=["store_results_for_session"]).status_code == 400
        assert post(notice_version="0", purposes=REQUIRED).status_code == 400  # not the current version
        assert post(notice_version="1", purposes=REQUIRED + ["sell_data"]).status_code == 400  # unknown purpose
        r = post(notice_version="1", purposes=REQUIRED)
        assert r.status_code == 200 and r.json()["consent"] == {"granted": True, "current_version": "1", "purposes": sorted(REQUIRED)}
        assert e.client.get("/api/v1/documents").status_code == 200
        r = post(notice_version="1", purposes=ALL_PURPOSES)  # optional purpose can be added later
        assert "keep_photo_for_session" in r.json()["consent"]["purposes"]


def test_consent_record_stores_version_hash_language_purposes(tmp_path):
    with Env(tmp_path) as e:
        e.start("ta")
        with e.ctx.db.session() as c:
            row = c.execute("SELECT * FROM consents").fetchone()
        assert row["notice_version"] == "1" and row["language"] == "ta" and row["notice_sha256"] == C.notice("ta")["sha256"]


def test_cookie_flags_and_token_secrecy(tmp_path):
    with Env(tmp_path) as e:
        r = e.client.post("/api/v1/sessions", json={"language": "hi"})
        sc = r.headers["set-cookie"].lower()
        assert "httponly" in sc and "samesite=lax" in sc and "; secure" not in sc and "path=/api" in sc
        assert "cb_session=" in sc and "max-age=86400" in sc
        token = e.client.cookies.get("cb_session")
        assert len(token) >= 43 and token not in r.text
    with Env(tmp_path / "s", cookie_secure=True) as e:
        assert "; secure" in e.client.post("/api/v1/sessions", json={"language": "en"}).headers["set-cookie"].lower()


def test_session_is_reused_not_orphaned(tmp_path):
    with Env(tmp_path) as e:
        assert e.client.post("/api/v1/sessions", json={"language": "en"}).status_code == 201
        assert e.client.post("/api/v1/sessions", json={"language": "ta"}).status_code == 200
        assert e.client.get("/api/v1/session").json()["language"] == "ta"
        with e.ctx.db.session() as c:
            assert c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


def test_missing_csrf_header_and_bad_origin_rejected(tmp_path):
    with Env(tmp_path) as e:
        no_hdr = e.new_client()
        no_hdr.headers.pop("X-CareBridge-Request")
        r = no_hdr.post("/api/v1/sessions", json={"language": "en"})
        assert r.status_code == 403 and r.json()["error"]["code"] == "request_blocked"
        assert e.client.post("/api/v1/sessions", json={"language": "en"}, headers={"Origin": "https://evil.example"}).status_code == 403
        assert e.client.post("/api/v1/sessions", json={"language": "en"}, headers={"Origin": "null"}).status_code == 403
        assert e.client.post("/api/v1/sessions", json={"language": "en"}, headers={"Origin": "http://localhost:5173"}).status_code == 201
        assert e.client.post("/api/v1/sessions", json={"language": "en"}).status_code in (200, 201)  # no Origin + header: non-browser client
        # every state-changing verb is covered, not only POST
        assert no_hdr.delete("/api/v1/session").status_code == 403 and no_hdr.put("/api/v1/documents/x/schedule-overrides", json={}).status_code == 403
        assert no_hdr.get("/api/v1/consent-notice").status_code == 200  # reads need no header


def test_cors_allows_only_configured_origins_with_credentials(tmp_path):
    with Env(tmp_path) as e:
        ok = e.client.options("/api/v1/sessions", headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-carebridge-request,content-type"})
        assert ok.headers["access-control-allow-origin"] == "http://127.0.0.1:5173" and ok.headers["access-control-allow-credentials"] == "true"
        bad = e.client.options("/api/v1/sessions", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
        assert "access-control-allow-origin" not in bad.headers


def test_security_headers_on_every_response(tmp_path):
    with Env(tmp_path) as e:
        for r in (e.client.get("/api/v1/consent-notice"), e.client.get("/api/v1/session"), e.client.get("/nope"), e.client.get("/api/health")):
            assert r.headers["cache-control"] == "no-store" and r.headers["x-content-type-options"] == "nosniff"
            assert r.headers["referrer-policy"] == "no-referrer" and "default-src 'none'" in r.headers["content-security-policy"]


def test_expired_session_returns_401_and_data_is_removed(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        with e.ctx.db.session() as c:
            c.execute("UPDATE sessions SET expires_at=?", (repo.now() - 1,))
        r = e.client.get("/api/v1/documents")
        assert r.status_code == 401 and r.json()["error"]["code"] == "session_expired"
        with e.ctx.db.session() as c:
            assert c.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0 and c.execute("SELECT COUNT(*) FROM consents").fetchone()[0] == 0
        assert e.client.get("/api/v1/documents").status_code == 401  # now simply no session


def test_error_format_never_echoes_input_or_traces(tmp_path):
    with Env(tmp_path) as e:
        e.client.post("/api/v1/sessions", json={"language": "en"})
        for r in (e.client.post("/api/v1/consent", json={"notice_version": 5, "purposes": "SECRET-INPUT"}), e.client.get("/api/v1/nothing"), e.client.get("/api/v1/documents/SECRET-ID"),
                  e.client.post("/api/v1/sessions", content=b"{SECRET-BODY", headers={"Content-Type": "application/json"})):
            j = r.json()
            assert list(j) == ["error"] and set(j["error"]) == {"code", "message"}
            assert "SECRET" not in r.text and "Traceback" not in r.text
        assert e.client.get("/api/v1/session").status_code == 200


def test_unhandled_exception_is_a_generic_500(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        e.app.add_api_route("/api/v1/boom", lambda: 1 / 0)
        c = TestClient(e.app, headers=dict(e.client.headers), raise_server_exceptions=False)
        c.cookies = e.client.cookies
        r = c.get("/api/v1/boom")
        assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error" and "division" not in r.text


def test_strings_endpoint_serves_static_template_text(tmp_path):
    with Env(tmp_path) as e:
        j = e.client.get("/api/v1/strings?lang=ta&prefix=error.").json()
        assert j["draft_unreviewed"] and "error.consent_required" in j["strings"] and all(k.startswith("error.") for k in j["strings"])
        assert e.client.get("/api/v1/strings?lang=en&prefix=med.").json()["strings"] == {}  # only whitelisted prefixes


def test_delete_session_is_one_call_and_idempotent(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        r = e.client.delete("/api/v1/session")
        assert r.status_code == 200 and r.json()["deleted"]["sessions"] == 1 and "deleted_at" in r.json() and "deleted" in r.json()["message"].lower()
        assert "cb_session" in r.headers["set-cookie"] and 'max-age=0' in r.headers["set-cookie"].lower()
        assert e.client.delete("/api/v1/session").status_code == 204  # nothing left: no error
        assert e.client.get("/api/v1/session").status_code == 401
