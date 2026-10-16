"""Generic access-control tests over EVERY route of the app. A new route that is not classified here fails the coverage test."""
import pytest
from fastapi.routing import APIRoute

from apihelpers import Env, png_bytes

PUBLIC = {("GET", "/api/health"), ("GET", "/api/v1/consent-notice"), ("GET", "/api/v1/strings"), ("POST", "/api/v1/sessions"), ("DELETE", "/api/v1/session")}
SESSION_ONLY = {("GET", "/api/v1/session"), ("POST", "/api/v1/consent"), ("GET", "/api/v1/formulary/search"), ("GET", "/api/v1/formulary/{fid}")}

SELECT = {"index": 0, "action": "confirm_as_extracted"}
DOC_ROUTES = {  # (method, path template) -> request kwargs for a foreign document / event id
    ("GET", "/api/v1/documents/{doc_id}"): {},
    ("GET", "/api/v1/documents/{doc_id}/image"): {},
    ("POST", "/api/v1/documents/{doc_id}/retry"): {},
    ("POST", "/api/v1/documents/{doc_id}/languages"): {"json": {"language": "hi"}},
    ("GET", "/api/v1/documents/{doc_id}/medicines"): {},
    ("POST", "/api/v1/documents/{doc_id}/confirmations"): {"json": {"decisions": [SELECT]}},
    ("GET", "/api/v1/documents/{doc_id}/result"): {},
    ("GET", "/api/v1/documents/{doc_id}/schedule"): {},
    ("PUT", "/api/v1/documents/{doc_id}/schedule-overrides"): {"json": {"overrides": {}}},
    ("GET", "/api/v1/documents/{doc_id}/doctor-summary"): {},
    ("POST", "/api/v1/adherence"): {"json": {"document_id": "{doc_id}", "med_ref": "m0", "scheduled_time": "08:30", "date": "2026-10-16", "status": "taken"}},
    ("GET", "/api/v1/adherence"): {"params": {"document_id": "{doc_id}"}},
    ("DELETE", "/api/v1/adherence/{event_id}"): {},
}
CONSENT_ONLY_LIST = {("GET", "/api/v1/documents"), ("POST", "/api/v1/documents")}


def api_routes(app):
    for r in app.routes:  # this FastAPI version wraps included routers lazily
        yield from ([r] if isinstance(r, APIRoute) else getattr(getattr(r, "original_router", None), "routes", []))


def routes(app):
    return {(m, r.path) for r in api_routes(app) if isinstance(r, APIRoute) for m in r.methods if m not in ("HEAD", "OPTIONS")}


def fill(obj, **ids):
    if isinstance(obj, str):
        return obj.format(**ids) if obj.startswith("{") and obj.endswith("}") else obj
    if isinstance(obj, dict):
        return {k: fill(v, **ids) for k, v in obj.items()}
    return obj


def test_every_route_is_classified(tmp_path):
    with Env(tmp_path) as e:
        classified = PUBLIC | SESSION_ONLY | set(DOC_ROUTES) | CONSENT_ONLY_LIST
        assert routes(e.app) - classified == set(), "new routes must be added to the IDOR/consent tables in this file"
        assert not [r for r in classified - routes(e.app) if r[1] != "/openapi.json"], "stale entries in the table"


def test_every_document_route_returns_404_for_another_sessions_ids(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        did = e.upload_ready()
        eid = e.client.post("/api/v1/adherence", json={"document_id": did, "med_ref": "m0", "scheduled_time": "08:30", "date": "2026-10-16", "status": "taken"}).json()["id"]
        mine = e.client.get(f"/api/v1/documents/{did}").json()
        other = e.new_client()
        e.start(client=other)
        for (method, tpl), kw in DOC_ROUTES.items():
            path = tpl.format(doc_id=did, event_id=eid)
            kw = fill(kw, doc_id=did)
            r = other.request(method, path, **kw)
            assert r.status_code == 404 and r.json()["error"]["code"] == "not_found", (method, tpl, r.status_code, r.text[:100])
            missing = other.request(method, tpl.format(doc_id="doesnotexist", event_id="doesnotexist"), **fill(kw, doc_id="doesnotexist"))
            assert missing.status_code == 404 and missing.json() == r.json(), (method, tpl)  # a foreign id looks exactly like a missing one
        assert other.get("/api/v1/documents").json() == {"documents": []}
        assert e.client.get(f"/api/v1/documents/{did}").json() == mine  # the owner's data is untouched
        assert e.client.get(f"/api/v1/adherence?document_id={did}").json()["events"][0]["id"] == eid


def test_ids_are_random_and_long(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        ids = {e.upload_ready() for _ in range(5)}
        assert len(ids) == 5 and all(len(i) >= 22 for i in ids)
        with e.ctx.db.session() as c:
            assert len(c.execute("SELECT id FROM sessions").fetchone()[0]) >= 22


def test_every_route_needs_a_session_and_consent_unless_public(tmp_path):
    with Env(tmp_path) as e:
        anon = e.new_client()
        for method, tpl in sorted(routes(e.app) - PUBLIC):
            kw = fill(DOC_ROUTES.get((method, tpl), {}), doc_id="x")
            if (method, tpl) == ("POST", "/api/v1/documents"):
                kw = {"content": png_bytes(), "headers": {"Content-Type": "image/png"}}
            if (method, tpl) == ("POST", "/api/v1/consent"):
                kw = {"json": {"notice_version": "1", "purposes": []}}
            r = anon.request(method, tpl.format(doc_id="x", event_id="x", fid="x"), **kw)
            assert r.status_code == 401 and r.json()["error"]["code"] == "no_session", (method, tpl, r.status_code)
        # a session without consent: 403 on every data route, 200/other on session-only routes
        sess = e.new_client()
        sess.post("/api/v1/sessions", json={"language": "en"})
        for method, tpl in sorted(set(DOC_ROUTES) | CONSENT_ONLY_LIST):
            kw = fill(DOC_ROUTES.get((method, tpl), {}), doc_id="x")
            if (method, tpl) == ("POST", "/api/v1/documents"):
                kw = {"content": png_bytes(), "headers": {"Content-Type": "image/png"}}
            r = sess.request(method, tpl.format(doc_id="x", event_id="x"), **kw)
            assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required", (method, tpl, r.status_code)
        assert sess.get("/api/v1/session").status_code == 200 and sess.get("/api/v1/formulary/search?q=a").status_code == 200


def test_consent_for_an_old_notice_version_does_not_pass_the_gate(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        with e.ctx.db.session() as c:
            c.execute("UPDATE consents SET notice_version='0'")  # as if the notice was updated after the user consented
        r = e.client.get("/api/v1/documents")
        assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required"


def test_a_stolen_cookie_value_of_the_wrong_kind_gets_nothing(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        did = e.upload_ready()
        other = e.new_client()
        other.cookies.set("cb_session", "A" * 43, path="/api")
        assert other.get(f"/api/v1/documents/{did}").status_code == 401
        with e.ctx.db.session() as c:
            h = c.execute("SELECT token_hash FROM sessions").fetchone()[0]
        other.cookies.set("cb_session", h, path="/api")  # the stored hash is not a usable credential
        assert other.get(f"/api/v1/documents/{did}").status_code == 401
