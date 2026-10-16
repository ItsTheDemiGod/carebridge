import pytest

from app.db import repo
from app.services import formulary as F
from apihelpers import Env, FakeOllama, gt_output


def garbled_output():
    o = gt_output("ds_037")
    m = o.medications[0]
    m.brand_name, m.generic_name = "Netfornin", "Glibenclamide"
    m.source_quote = "Tab Netfornin 500 mg - 1 tablet twice daily after meals"
    return o


@pytest.fixture
def env(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        yield e


def test_formulary_search_behaviour(env):
    env.start()
    r = env.client.get("/api/v1/formulary/search?q=metf").json()
    assert r["formulary_status"] == "unverified_requires_pharmacist_review" and r["results"][0]["id"] == "metformin"
    e = r["results"][0]
    assert set(e) == {"id", "generic", "brand_names", "available_strengths", "form", "route", "strength_as_label_option"} and "500 mg" in e["available_strengths"]
    assert env.client.get("/api/v1/formulary/search?q=GLYCOMET").json()["results"][0]["id"] == "metformin"  # brand, case-insensitive
    assert env.client.get("/api/v1/formulary/search?q=formin").json()["results"][0]["id"] == "metformin"  # substring
    assert env.client.get("/api/v1/formulary/search?q=metfromin").json()["results"] == []  # no fuzzy matching
    assert env.client.get("/api/v1/formulary/search?q=").json()["results"] == []
    assert len(env.client.get("/api/v1/formulary/search?q=a&limit=20").json()["results"]) <= 20
    assert len(env.client.get("/api/v1/formulary/search?q=a&limit=3").json()["results"]) == 3
    assert env.client.get("/api/v1/formulary/search?q=a&limit=21").status_code == 422 and env.client.get("/api/v1/formulary/search?q=a&limit=0").status_code == 422
    assert env.client.get("/api/v1/formulary/search?q=" + "x" * 61).status_code == 422


def test_search_never_echoes_the_query(env):
    env.start()
    for q in ("<script>alert(1)</script>", "SECRET-QUERY", '"}{', "%00"):
        r = env.client.get("/api/v1/formulary/search", params={"q": q})
        assert r.status_code == 200 and r.json()["results"] == [] and q not in r.text
        assert r.headers["content-type"].startswith("application/json") and r.headers["x-content-type-options"] == "nosniff"


def test_prefix_matches_come_before_substring_matches():
    ids = [e["id"] for e in F.search("ol", 20)]
    first_non_prefix = next(i for i, x in enumerate(ids) if not any(n.lower().startswith("ol") or any(w.startswith("ol") for w in n.lower().split()) for n in [F.get(x)["generic"], *F.get(x)["brand_names"]]))
    assert all(any(n.lower().startswith("ol") or any(w.startswith("ol") for w in n.lower().split()) for n in [F.get(x)["generic"], *F.get(x)["brand_names"]]) for x in ids[:first_non_prefix])


def test_every_formulary_entry_is_reachable_by_its_id_and_names():
    for e in F.all_entries():
        assert F.get(e["id"]) == e and e["id"] in [x["id"] for x in F.search(e["generic"], 20)]
        for b in e["brand_names"]:
            assert e["id"] in [x["id"] for x in F.search(b, 20)]


def test_formulary_endpoints_need_a_session_but_not_consent(env):
    assert env.client.get("/api/v1/formulary/search?q=met").status_code == 401
    env.client.post("/api/v1/sessions", json={"language": "en"})
    assert env.client.get("/api/v1/formulary/search?q=met").status_code == 200  # reference data, no user data involved
    assert env.client.get("/api/v1/formulary/metformin").json()["generic"] == "Metformin"
    assert env.client.get("/api/v1/formulary/unknown").status_code == 404


def test_medicines_field_shapes_and_language_rendering(env):
    env.start("ta")
    did = env.upload_ready()
    j = env.client.get(f"/api/v1/documents/{did}/medicines").json()
    assert set(j) == {"medicines", "added_medicines", "dose_options", "strength_as_label_option", "formulary_status", "compare_note"} and len(j["medicines"]) == 4
    m0 = j["medicines"][0]
    assert set(m0) == {"index", "ref", "as_written", "printed", "resolved_generic", "name_match_type", "strength", "dose", "form", "route", "frequency", "duration_days", "duration_text",
                       "source_quote", "review_level", "flags", "reasons", "interaction_ready", "schedule_ready", "has_exact_identity", "allowed_actions", "current_decision"}
    assert m0["as_written"] == {"brand": "Netfornin", "generic": "Glibenclamide"} and m0["review_level"] == "must_confirm" and not m0["interaction_ready"] and m0["resolved_generic"] is None
    assert m0["allowed_actions"] == ["confirm_as_extracted", "select_formulary_drug", "not_in_list", "remove"] and m0["source_quote"].startswith("Tab Netfornin")
    r = {x["id"]: x for x in m0["reasons"]}
    assert r["unresolved_name"]["kind"] == "name" and r["unresolved_name"]["template_id"] == "confirm.flag.unresolved_name" and any("஀" <= ch <= "௿" for ch in r["unresolved_name"]["text"])
    assert j["medicines"][1]["review_level"] == "none" and j["medicines"][1]["reasons"] == [] and j["medicines"][1]["interaction_ready"]
    assert "Compare" not in j["compare_note"] and any("஀" <= ch <= "௿" for ch in j["compare_note"])  # Tamil (draft) rendering
    from app.services import templates as T
    assert T.render("confirm.flag.unresolved_name", "en").startswith("The name could not be found")


def test_medicines_not_ready_before_extraction_finishes(env):
    env.start()
    with env.ctx.db.session() as c:
        sid = c.execute("SELECT id FROM sessions").fetchone()[0]
        did = repo.create_document(c, sid, False)
    r = env.client.get(f"/api/v1/documents/{did}/medicines")
    assert r.status_code == 409 and r.json()["error"]["code"] == "not_ready"
    assert env.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": []}).status_code == 409


SELECT = {"index": 0, "action": "select_formulary_drug", "formulary_id": "metformin", "strength_choice": "500 mg"}


def test_confirmations_flow_replace_and_current_decision(env):
    env.start("en")
    did = env.upload_ready()
    url = f"/api/v1/documents/{did}/confirmations"
    r = env.client.post(url, json={"decisions": [SELECT]})
    assert r.status_code == 200 and r.json()["confirmed"] and r.json()["medicines"][0] == {"ref": "m0", "resolution": "selected", "interaction_ready": True, "schedule_ready": True,
                                                                                        "review_level": "none", "unresolved": [], "not_checked_reason": None}
    j = env.client.get(f"/api/v1/documents/{did}/medicines").json()
    assert j["medicines"][0]["current_decision"]["formulary_id"] == "metformin" and env.client.get(f"/api/v1/documents/{did}").json()["confirmed"]
    r = env.client.post(url, json={"decisions": [{"index": 0, "action": "not_in_list", "note": "x"}]})  # replaces the previous set
    assert r.json()["medicines"][0]["resolution"] == "not_in_list" and not r.json()["medicines"][0]["interaction_ready"]
    j = env.client.get(f"/api/v1/documents/{did}/medicines").json()
    assert j["medicines"][0]["current_decision"]["action"] == "not_in_list"
    r2 = env.client.post(url, json={"decisions": [{"index": 0, "action": "not_in_list", "note": "x"}]})
    assert r2.json() == r.json()  # idempotent
    r = env.client.post(url, json={"decisions": []})
    assert r.json()["medicines"][0]["resolution"] == "unchanged"  # an empty set clears the earlier decisions


def test_confirmation_validation_errors(env):
    env.start()
    did = env.upload_ready()
    url = f"/api/v1/documents/{did}/confirmations"
    for body, code in (({"decisions": [{"index": 9, "action": "remove"}]}, "invalid_confirmation"),
                       ({"decisions": [{**SELECT, "formulary_id": "nope"}]}, "invalid_confirmation"),
                       ({"decisions": [{"index": 0, "action": "confirm_as_extracted", "acknowledged_flags": ["bogus"]}]}, "invalid_confirmation"),
                       ({"decisions": [{"index": 0, "action": "confirm_as_extracted", "extra": 1}]}, "invalid_request"),
                       ({"decisions": [{"index": 0, "action": "not_in_list", "note": "x" * 81}]}, "invalid_request"),
                       ({"added_medicines": [{"formulary_id": "metformin", "strength_choice": "500 mg", "dose": "a lot", "schedule": {"times_per_day": 1, "timing_label": "morning"}}]}, "invalid_request")):
        r = env.client.post(url, json=body)
        assert r.status_code == 422 and r.json()["error"]["code"] == code, body
    assert env.client.get(f"/api/v1/documents/{did}").json()["confirmed"] is False  # nothing half-applied


def test_added_medicine_through_the_api(env):
    env.start()
    did = env.upload_ready()
    add = {"formulary_id": "omeprazole", "strength_choice": "20 mg", "dose": "1 capsule", "schedule": {"times_per_day": 1, "timing_label": "before_meals", "duration_days": 14}}
    r = env.client.post(f"/api/v1/documents/{did}/confirmations", json={"added_medicines": [add]})
    assert r.status_code == 200 and r.json()["medicines"][-1] == {"ref": "a0", "resolution": "added", "interaction_ready": True, "schedule_ready": True, "review_level": "none", "unresolved": [], "not_checked_reason": None}
    assert env.client.get(f"/api/v1/documents/{did}/medicines").json()["added_medicines"][0]["formulary_id"] == "omeprazole"


def test_decisions_audit_trail_and_note_is_encrypted(env):
    env.start()
    did = env.upload_ready()
    env.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": 0, "action": "not_in_list", "note": "NOTE-CANARY-123"}, {"index": 1, "action": "remove"}]})
    with env.ctx.db.session() as c:
        audit = repo.get_payload(c, env.ctx.vault, did, "decisions")
        assert [(a["index"], a["action"], a["has_note"]) for a in audit] == [(0, "not_in_list", True), (1, "remove", False)] and all("at" in a for a in audit)
        assert "NOTE-CANARY-123" not in str(audit)
        assert repo.get_payload(c, env.ctx.vault, did, "confirmations")["decisions"][0]["note"] == "NOTE-CANARY-123"  # stored (encrypted), never used
    assert b"NOTE-CANARY-123" not in env.ctx.db.path.read_bytes()
