import threading

import pytest

from app.safety import interactions as I
from app.services import result as R
from apihelpers import Env, FakeOllama, fake_narrate, gt_output
from test_api_review import garbled_output

STORE = {"glimepiride|metformin": {"severity": "moderate"}, "atorvastatin|metformin": {"severity": "minor"}}
SELECT = {"index": 0, "action": "select_formulary_drug", "formulary_id": "metformin", "strength_choice": "500 mg"}


@pytest.fixture(autouse=True)
def synthetic_store(monkeypatch):
    monkeypatch.setattr(R, "safety_data", lambda: I.Data(STORE))


def sec(res, sid):
    return next((s for s in res["explanation"]["sections"] if s["id"] == sid), {"lines": []})["lines"]


def get(env, did, lang=None):
    r = env.client.get(f"/api/v1/documents/{did}/result" + (f"?lang={lang}" if lang else ""))
    assert r.status_code == 200, r.text
    return r.json()


def safety_texts(res):
    return [ln["text"][res["language"]]["text"] for ln in sec(res, "safety")]


def test_before_and_after_confirmation(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        before = get(e, did)
        rep = before["explanation"]["safety"]
        assert before["confirm_first"] and not before["confirmed"] and rep["overall_state"] == "confirm_first"
        pairs = {(p["a"], p["b"]): p for p in rep["pair_results"]}
        assert all(p["status"] == "not_checked_unconfirmed" for (a, b), p in pairs.items() if 0 in (a, b))  # the garbled medicine is never looked up
        assert not [ln for ln in sec(before, "safety") if ln["line_id"].startswith("safety-pair")]
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [SELECT]})
        after = get(e, did)
        assert after["confirmed"] and not after["confirm_first"] and after["explanation"]["safety"]["overall_state"] == "review_interactions"
        found = [p for p in after["explanation"]["safety"]["pair_results"] if p["status"] == "interaction_found"]
        assert {(p["generic_a"], p["generic_b"], p["level"]) for p in found} == {("Metformin", "Glimepiride", "moderate"), ("Metformin", "Atorvastatin", "minor")}
        texts = safety_texts(after)
        assert any("Metformin" in t or "Netfornin" in t or "may interact" in t.lower() for t in texts) and not any("safe" in t.lower() and "not" not in t.lower() for t in texts)
        meta = {m["ref"]: m for m in after["medicines_meta"]}
        assert meta["m0"]["resolution"] == "selected" and meta["m0"]["labels"][0] == {"template_id": "confirm.you_selected", "text": "You chose this medicine from the list."}
        assert meta["m1"]["resolution"] == "unchanged" and meta["m1"]["labels"] == []


def test_user_selecting_a_different_drug_gets_that_drugs_results(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "safety_data", lambda: I.Data({"glimepiride|omeprazole": {"severity": "major"}, **STORE}))
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{**SELECT, "formulary_id": "omeprazole", "strength_choice": "20 mg"}]})
        res = get(e, did)
        found = {(p["generic_a"], p["generic_b"], p["level"]) for p in res["explanation"]["safety"]["pair_results"] if p["status"] == "interaction_found"}
        assert found == {("Omeprazole", "Glimepiride", "major")}


def test_removed_and_not_in_list_medicines(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": 0, "action": "not_in_list"}, {"index": 3, "action": "remove"}]})
        res = get(e, did)
        meds = sec(res, "medicines")
        assert len(meds) == 3 and res["removed"] == [3] and res["confirm_first"]  # the not-in-list medicine keeps the banner
        m0 = res["medicines_meta"][0]
        assert m0["not_checked_reason"] == "user_not_in_list" and m0["labels"][0]["template_id"] == "confirm.flag.user_not_in_list" and not meds[0]["settled"]
        assert all(p["status"] != "interaction_found" for p in res["explanation"]["safety"]["pair_results"] if 0 in (p["a"], p["b"]))


def test_narrative_pending_then_ready(tmp_path):
    gate, started = threading.Event(), threading.Event()

    def slow(items, nar, lang, prov):
        started.set()
        gate.wait(10)
        return fake_narrate(items, nar, lang, prov)

    with Env(tmp_path, narrate=slow) as e:
        e.start("en")
        r = e.upload()
        did = r.json()["id"]
        started.wait(10)
        # the document is awaiting confirmation while the narrative is still running
        for _ in range(100):
            if e.client.get(f"/api/v1/documents/{did}").json()["state"] == "awaiting_confirmation":
                break
            threading.Event().wait(0.05)
        res = get(e, did)
        assert res["narrative_status"]["en"] in ("pending", "running")
        free = [ln for s in ("follow_ups", "advice", "warnings") for ln in sec(res, s) if ln["provenance"] != "phrase_library"]
        assert free and all(ln["narrative_pending"] and ln["text"]["en"]["text"] == "Still preparing this explanation. Please check again in a moment." for ln in free)
        assert all(not ln["notices"] for ln in free)  # not the fallback notice: nothing is guessed, nothing is claimed
        gate.set()
        e.wait()
        res = get(e, did)
        assert res["narrative_status"]["en"] == "ready"
        free = [ln for s in ("follow_ups", "advice", "warnings") for ln in sec(res, s) if ln["provenance"] != "phrase_library"]
        assert free and all(not ln["narrative_pending"] and ln["text"]["en"]["status"] == "verified" and ln["text"]["en"]["provenance"] == "model_checked" for ln in free)


def test_narrative_failure_falls_back_to_the_original_english(tmp_path):
    def boom(items, nar, lang, prov):
        raise RuntimeError("x")

    with Env(tmp_path, narrate=boom) as e:
        e.start()
        did = e.upload_ready()
        res = get(e, did)
        assert res["narrative_status"]["en"] == "failed"
        free = [ln for s in ("follow_ups", "advice", "warnings") for ln in sec(res, s) if ln["provenance"] != "phrase_library"]
        assert free
        for ln in free:
            t = ln["text"]["en"]
            assert not ln["narrative_pending"] and t["display_mode"] == "original_with_notice" and t["text"] == ln["source_text"] and t["provenance"] == "original_only"
            assert ln["notices"] and ln["notices"][0]["code"] == "fallback"


def test_second_language_flow_and_requested_language_only(tmp_path):
    with Env(tmp_path) as e:
        e.start("en")
        did = e.upload_ready()
        res = get(e, did, "hi")
        assert res["language"] == "hi" and res["narrative_status"] == {"en": "ready", "ta": "not_started", "hi": "not_started"}
        for s in res["explanation"]["sections"]:
            assert list(s["heading"]) == ["hi"]
            for ln in s["lines"]:
                assert list(ln["text"]) == ["hi"]
        free = [ln for s in ("advice",) for ln in sec(res, s) if ln["provenance"] != "phrase_library"]
        assert all(ln["text"]["hi"]["display_mode"] == "original_with_notice" for ln in free)  # never requested: the original text, with the notice
        e.client.post(f"/api/v1/documents/{did}/languages", json={"language": "hi"})
        e.wait()
        res = get(e, did, "hi")
        assert res["narrative_status"]["hi"] == "ready"
        assert all(any("ऀ" <= ch <= "ॿ" for ch in ln["text"]["hi"]["text"]) for ln in sec(res, "advice") if ln["provenance"] != "phrase_library")
        assert any("ऀ" <= ch <= "ॿ" for ch in sec(res, "medicines")[0]["text"]["hi"]["text"])
        assert e.client.get(f"/api/v1/documents/{did}/result?lang=fr").status_code == 422


def test_warning_count_invariant_in_every_state(tmp_path):
    out = gt_output("ds_025")
    assert len(out.red_flags) >= 3
    with Env(tmp_path, provider=FakeOllama(output=out)) as e:
        e.start()
        did = e.upload_ready()
        assert len(sec(get(e, did), "warnings")) == len(out.red_flags)
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": 0, "action": "remove"}]})
        assert len(sec(get(e, did), "warnings")) == len(out.red_flags)  # confirmation never touches warnings
        assert len(sec(get(e, did, "ta"), "warnings")) == len(out.red_flags)


def test_must_confirm_banner_invariant(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        for body in ({}, {"decisions": [{"index": 0, "action": "confirm_as_extracted"}]}, {"decisions": [SELECT]}):
            if body:
                e.client.post(f"/api/v1/documents/{did}/confirmations", json=body)
            res = get(e, did)
            for ln in sec(res, "medicines"):
                if ln["review_level"] == "must_confirm":
                    assert "must_confirm" in [n["code"] for n in ln["notices"]] and not ln["settled"]
                else:
                    assert "must_confirm" not in [n["code"] for n in ln["notices"]]
        assert sec(res, "medicines")[0]["review_level"] == "none" and sec(res, "medicines")[0]["settled"]  # resolved by the user's selection
        # a medicine that is not schedule_ready is never settled, even when nothing is flagged
        for ln in sec(res, "medicines"):
            assert ln["settled"] == (ln["review_level"] != "must_confirm" and next(m for m in res["medicines_meta"] if m["line_id"] == ln["line_id"])["schedule_ready"])


def test_result_requires_a_finished_extraction(tmp_path):
    with Env(tmp_path, provider=FakeOllama(error="timeout")) as e:
        e.start()
        did = e.upload_ready()
        assert e.client.get(f"/api/v1/documents/{did}/result").status_code == 409


def test_guardrail_runs_on_assembled_english_and_fails_closed(monkeypatch):
    events = []
    assert R.checked("confirm.you_confirmed", "en", events) == "You confirmed this." and events == []
    monkeypatch.setattr(R, "scan", lambda text, tid=None, source=None: [("reassurance", "x")])
    assert R.checked("confirm.you_confirmed", "ta", events) != "You confirmed this." and len(events) == 1  # the fallback notice, in the user's language
    assert R.checked("confirm.you_confirmed", "en", events) == R.T.render("fallback.notice", "en")


def test_response_is_json_data_only(tmp_path):
    with Env(tmp_path) as e:
        e.start()
        did = e.upload_ready()
        r = e.client.get(f"/api/v1/documents/{did}/result")
        assert r.headers["content-type"].startswith("application/json")
        assert r.headers["cache-control"] == "no-store"
