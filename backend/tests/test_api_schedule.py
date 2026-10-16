import itertools
from datetime import date, datetime, timedelta

import pytest

from app.api import routes_schedule as RS
from app.safety import interactions as I
from app.schemas.confirmation import ConfirmedMedicine
from app.schemas.extraction import TimingLabel
from app.services import result as R
from app.services import schedule as S
from apihelpers import Env, FakeOllama, gt_output
from medfactory import med
from test_api_review import garbled_output

STORE = {"glimepiride|metformin": {"severity": "moderate"}}


@pytest.fixture(autouse=True)
def synthetic_store(monkeypatch):
    monkeypatch.setattr(R, "safety_data", lambda: I.Data(STORE))


def cm(**kw) -> ConfirmedMedicine:
    unresolved = kw.pop("unresolved", [])
    return ConfirmedMedicine(ref="m0", source_index=0, resolution="unchanged", med=med(**kw), unresolved=unresolved)


def test_expected_slots_for_the_documented_combinations():
    t = lambda **kw: S.suggest(cm(**kw)).times  # noqa: E731
    assert t(times=1, timing="after_meals") == ["08:30"] and t(times=1, timing="before_meals") == ["07:30"] and t(times=1, timing="with_meals") == ["08:00"]
    assert t(times=2, timing="after_meals") == ["08:30", "20:30"] and t(times=2, timing="before_meals") == ["07:30", "19:30"] and t(times=2, timing="with_meals") == ["08:00", "20:00"]
    assert t(times=3, timing="after_meals") == ["08:30", "13:30", "20:30"] and t(times=3, timing="before_meals") == ["07:30", "12:30", "19:30"]
    assert t(times=4, timing="with_meals") == ["08:00", "13:00", "20:00", "22:00"] and t(times=4, timing="after_meals") == ["08:30", "13:30", "20:30", "22:00"]  # bedtime has no meal offset
    assert [t(times=1, timing=x) for x in ("morning", "afternoon", "evening", "night", "bedtime")] == [["08:00"], ["14:00"], ["18:00"], ["21:00"], ["22:00"]]
    assert t(times=1, timing="unspecified") == ["08:00"] and t(times=2, timing="unspecified") == ["08:00", "22:00"] and t(times=3, timing="unspecified") == ["08:00", "15:00", "22:00"]
    assert S.suggest(cm(times=2, timing="unspecified")).no_meal_timing and not S.suggest(cm(times=2, timing="after_meals")).no_meal_timing
    assert S.suggest(cm(times=2, timing="morning")).no_meal_timing  # a time-of-day label with several doses: no meal timing, evenly spaced
    for n in (5, 6, 8):
        sg = S.suggest(cm(times=n, timing="after_meals"))
        assert sg.times == [] and sg.reason == "too_many_doses" and sg.settable


def test_every_times_per_day_and_timing_label_combination():
    for n, timing, prn, sched in itertools.product([None, 0, 1, 2, 3, 4, 5, 6, 7, 12, "x", True], [x.value for x in TimingLabel] + [None, "bogus"], (False, True), (True, False)):
        sg = S.suggest(cm(times=n, timing=timing, prn=prn, sched=sched))
        assert sg.times == [] or (isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= 4 and len(sg.times) == n and all(S.HHMM.match(x) for x in sg.times) and sg.times == sorted(sg.times))
        if sg.times:
            assert sched and not prn and timing in S.KNOWN_TIMING
        assert (sg.times != []) == (sg.reason is None)
        if sg.reason:
            assert sg.reason in S.NOT_SCHEDULED
        if prn or timing == "as_needed":
            assert sg.times == []
    assert S.suggest(cm()).times == ["08:30", "20:30"]


def test_never_scheduled_cases():
    assert S.suggest(cm(flags=["non_daily_frequency"], level="none")).reason == "non_daily"
    assert S.suggest(cm(prn=True, times=None, timing="as_needed", sched=False)).reason == "as_needed"
    assert S.suggest(cm(timing="as_needed", sched=False)).reason == "as_needed"
    assert S.suggest(cm(level="must_confirm", sched=False)).reason == "not_confirmed"
    assert S.suggest(cm(unresolved=["unusual_strength"])).reason == "not_confirmed"
    assert S.suggest(cm(resolved=None)).reason == "no_identity"
    assert S.suggest(cm(times=None, sched=False)).reason == "not_confirmed" and S.suggest(cm(timing="other", sched=False)).reason == "not_confirmed"
    assert S.suggest(cm(sched=False)).reason == "not_confirmed"


def test_valid_times_and_even_spacing():
    assert S.valid_times(["08:00", "20:30"]) and not S.valid_times(["24:00"]) and not S.valid_times(["8:00"]) and not S.valid_times([]) and not S.valid_times(["08:00"] * 2)
    assert not S.valid_times([f"0{h}:00" for h in range(7)]) and S.valid_times([f"0{h}:00" for h in range(6)]) and not S.valid_times(["08:60"]) and not S.valid_times([8])


def weekly_output():
    o = gt_output("ds_037")
    o.medications[1].source_quote = "Tab Amaryl (Glimepiride) 1 mg - 1 tablet once weekly"
    o.medications[2].source_quote = "Tab Telma (Telmisartan) 40 mg - 1 tablet SOS"
    return o


def sched(e, did):
    r = e.client.get(f"/api/v1/documents/{did}/schedule")
    assert r.status_code == 200, r.text
    return r.json()


def test_schedule_endpoint_unconfirmed_never_scheduled_and_reasons(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        j = sched(e, did)
        assert j["notice"] == {"template_id": "schedule.notice", "text": "Suggested times only; adjust them to match your doctor's instructions."}
        assert [m["ref"] for m in j["medicines"]] == ["m1", "m2", "m3"] and {x["ref"]: x["reason"] for x in j["not_scheduled"]} == {"m0": "not_confirmed"}
        assert j["not_scheduled"][0]["text"].startswith("Not scheduled: please confirm") and [s["time"] for s in j["slots"]] == sorted(s["time"] for s in j["slots"])
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": 0, "action": "select_formulary_drug", "formulary_id": "metformin", "strength_choice": "500 mg"}]})
        j = sched(e, did)
        assert [m["ref"] for m in j["medicines"]] == ["m0", "m1", "m2", "m3"] and j["not_scheduled"] == []
        m0 = j["medicines"][0]
        assert m0["times"] == ["08:30", "20:30"] and m0["source"] == "suggested" and m0["strength"] == "500 mg" and m0["duration_text"] is None or m0["duration_days"] is None or m0["duration_text"].startswith("About")


def test_non_daily_and_as_needed_are_never_scheduled_even_after_confirmation(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=weekly_output())) as e:
        e.start()
        did = e.upload_ready()
        med1 = e.client.get(f"/api/v1/documents/{did}/medicines").json()["medicines"]
        acks = {i: [r["id"] for r in m["reasons"] if r["kind"] == "acknowledge"] for i, m in enumerate(med1)}
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": i, "action": "confirm_as_extracted", "acknowledged_flags": acks[i]} for i in (1, 2)]})
        j = sched(e, did)
        reasons = {x["ref"]: x["reason"] for x in j["not_scheduled"]}
        assert reasons == {"m1": "non_daily", "m2": "as_needed"} and {m["ref"] for m in j["medicines"]} == {"m0", "m3"}
        r = e.client.put(f"/api/v1/documents/{did}/schedule-overrides", json={"overrides": {"m1": ["09:00"]}})
        assert r.status_code == 422  # a non-daily medicine accepts no times either


def test_too_many_doses_the_user_sets_the_times(tmp_path):
    o = gt_output("ds_037")
    o.medications[0].source_quote = "Tab Metformin 500 mg - 1 tablet 5 times a day after meals"
    with Env(tmp_path, provider=FakeOllama(output=o)) as e:
        e.start()
        did = e.upload_ready()
        j = sched(e, did)
        x = next(n for n in j["not_scheduled"] if n["ref"] == "m0")
        assert x["reason"] == "too_many_doses" and x["user_can_set_times"] and "set your own times" in x["text"]
        r = e.client.put(f"/api/v1/documents/{did}/schedule-overrides", json={"overrides": {"m0": ["22:00", "06:00", "10:00", "14:00", "18:00"]}})
        assert r.status_code == 200
        m0 = next(m for m in r.json()["medicines"] if m["ref"] == "m0")
        assert m0["times"] == ["06:00", "10:00", "14:00", "18:00", "22:00"] and m0["source"] == "user" and not any(n["ref"] == "m0" for n in r.json()["not_scheduled"])


def test_override_validation_and_replace_semantics(tmp_path):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        url = f"/api/v1/documents/{did}/schedule-overrides"
        for bad in ({"m1": ["25:00"]}, {"m1": ["8:00"]}, {"m1": ["08:00", "08:00"]}, {"m1": []}, {"m1": [f"0{h}:00" for h in range(7)]}, {"m9": ["08:00"]}, {"m0": ["08:00"]},  # m0 is unconfirmed
                    {"zz": ["08:00"]}, {"m1": "08:00"}, {"m1": [800]}):
            assert e.client.put(url, json={"overrides": bad}).status_code == 422, bad
        assert e.client.put(url, json={"overrides": {"m1": ["09:15"]}, "x": 1}).status_code == 422
        r = e.client.put(url, json={"overrides": {"m1": ["20:15", "09:15"], "m2": ["07:00"]}})
        assert r.status_code == 200 and {m["ref"]: m["times"] for m in r.json()["medicines"] if m["source"] == "user"} == {"m1": ["09:15", "20:15"], "m2": ["07:00"]}
        r = e.client.put(url, json={"overrides": {"m2": ["07:30"]}})  # replaces the previous set
        assert {m["ref"]: m["source"] for m in r.json()["medicines"]}["m1"] == "suggested" and {m["ref"]: m["times"] for m in r.json()["medicines"]}["m2"] == ["07:30"]
        assert e.client.put(url, json={"overrides": {}}).status_code == 200


def test_unspecified_timing_notice(tmp_path):
    o = gt_output("ds_037")
    o.medications[2].source_quote = "Tab Telma (Telmisartan) 40 mg - 1 tablet twice daily"
    with Env(tmp_path, provider=FakeOllama(output=o)) as e:
        e.start()
        did = e.upload_ready()
        j = sched(e, did)
        assert j["extra_notices"] == [{"template_id": "schedule.no_meal_timing", "text": "No meal timing was found in the document, so these times are spread through the day."}]
        assert next(m for m in j["medicines"] if m["ref"] == "m2")["times"] == ["08:00", "22:00"]


# --- adherence ------------------------------------------------------------------------------------------------------------------------------
TODAY = date(2026, 10, 16)


@pytest.fixture
def clock(monkeypatch):
    state = {"now": datetime(2026, 10, 16, 21, 0)}
    monkeypatch.setattr(RS, "local_now", lambda: state["now"])
    return state


def ev(did, ref="m0", t="08:30", d="2026-10-16", status="taken"):
    return {"document_id": did, "med_ref": ref, "scheduled_time": t, "date": d, "status": status}


def test_adherence_validation_upsert_list_delete(tmp_path, clock):
    with Env(tmp_path) as e:
        e.start()
        did = e.upload_ready()
        post = lambda **kw: e.client.post("/api/v1/adherence", json={**ev(did), **kw})  # noqa: E731
        ok = post()
        assert ok.status_code == 201 and ok.json()["status"] == "taken"
        for bad in ({"status": "maybe"}, {"date": "2026-13-01"}, {"date": "16-10-2026"}, {"date": "2026-1-1"}, {"med_ref": "m99"}, {"med_ref": "x1"}, {"scheduled_time": "09:99"},
                    {"scheduled_time": "09:00"}, {"date": "2020-01-01"}, {"document_id": "nope"}, {"note": "free text"}):
            r = post(**bad)
            assert r.status_code in (404, 422), bad
            assert r.status_code == (404 if "document_id" in bad else 422)
        assert post(status="skipped").json()["id"] == ok.json()["id"]  # logging the same slot again changes the status
        e.client.post("/api/v1/adherence", json=ev(did, t="20:30"))
        lst = e.client.get(f"/api/v1/adherence?document_id={did}").json()["events"]
        assert [(x["scheduled_time"], x["status"]) for x in lst] == [("08:30", "skipped"), ("20:30", "taken")] and set(lst[0]) == {"id", "document_id", "med_ref", "scheduled_time", "date", "status"}
        assert e.client.get(f"/api/v1/adherence?document_id={did}&from=2026-10-17").json()["events"] == []
        assert e.client.get(f"/api/v1/adherence?document_id={did}&from=2026-10-16&to=2026-10-16").json()["events"] != []
        assert e.client.get(f"/api/v1/adherence?document_id={did}&from=garbage").status_code == 422
        assert e.client.get("/api/v1/adherence").status_code == 422 and e.client.get("/api/v1/adherence?document_id=nope").status_code == 404
        assert e.client.delete(f"/api/v1/adherence/{ok.json()['id']}").status_code == 204
        assert e.client.delete(f"/api/v1/adherence/{ok.json()['id']}").status_code == 404
        assert len(e.client.get(f"/api/v1/adherence?document_id={did}").json()["events"]) == 1


def test_adherence_only_for_scheduled_slots_and_follows_overrides(tmp_path, clock):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        assert e.client.post("/api/v1/adherence", json=ev(did, ref="m0", t="08:30")).status_code == 422  # unconfirmed: nothing to log
        assert e.client.post("/api/v1/adherence", json=ev(did, ref="m1", t="07:30")).status_code == 201  # Amaryl, once daily before meals
        e.client.put(f"/api/v1/documents/{did}/schedule-overrides", json={"overrides": {"m1": ["11:11"]}})
        assert e.client.post("/api/v1/adherence", json=ev(did, ref="m1", t="07:30", d="2026-10-15")).status_code == 422
        assert e.client.post("/api/v1/adherence", json=ev(did, ref="m1", t="11:11")).status_code == 201


def test_adherence_is_isolated_between_sessions(tmp_path, clock):
    with Env(tmp_path) as e:
        e.start()
        did = e.upload_ready()
        eid = e.client.post("/api/v1/adherence", json=ev(did)).json()["id"]
        other = e.new_client()
        e.start(client=other)
        assert other.post("/api/v1/adherence", json=ev(did)).status_code == 404
        assert other.get(f"/api/v1/adherence?document_id={did}").status_code == 404
        assert other.delete(f"/api/v1/adherence/{eid}").status_code == 404
        assert e.client.get(f"/api/v1/adherence?document_id={did}").json()["events"][0]["id"] == eid  # untouched


def test_doctor_summary_counts_lists_and_disclaimer(tmp_path, clock):
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        e.start()
        did = e.upload_ready()
        e.client.post(f"/api/v1/documents/{did}/confirmations", json={"decisions": [{"index": 0, "action": "select_formulary_drug", "formulary_id": "metformin", "strength_choice": "500 mg"},
                                                                                   {"index": 2, "action": "not_in_list"}]})
        post = lambda d, t, st, ref="m0": e.client.post("/api/v1/adherence", json=ev(did, ref=ref, t=t, d=d, status=st))  # noqa: E731
        assert post("2026-10-15", "08:30", "taken").status_code == 201
        post("2026-10-15", "20:30", "skipped")
        post("2026-10-16", "08:30", "taken")
        j = e.client.get(f"/api/v1/documents/{did}/doctor-summary?from=2026-10-15&to=2026-10-16").json()
        m0 = next(m for m in j["medicines"] if m["ref"] == "m0")
        # four slots in the period (08:30 and 20:30 on two days); 20:30 today (clock is 21:00) is already past: missed
        assert (m0["taken"], m0["skipped"], m0["missed"]) == (2, 1, 1) and m0["strength"] == "500 mg" and m0["times"] == ["08:30", "20:30"]
        assert [u["ref"] for u in j["unconfirmed"]] == ["m2"] and j["unconfirmed"][0]["reasons"][0]["id"] == "user_not_in_list" and "m2" not in [m["ref"] for m in j["medicines"]]
        assert j["not_scheduled"][0]["ref"] == "m2" and j["period"] == {"from": "2026-10-15", "to": "2026-10-16"}
        assert j["disclaimer"].startswith("This summary lists what was read from your document") and "not medical advice" in j["disclaimer"] and j["title"] == "Summary to show your doctor"
        assert set(j["labels"].values()) == {"Taken", "Skipped", "Missed"} and j["guardrail_events"] == []
        assert any("may interact" in ln for ln in j["interactions"]["lines"]) and j["interactions"]["found"][0]["level"] == "moderate"
        assert "percent" not in str(j).lower() and "%" not in str(j)  # counts only, no scores
        clock["now"] = datetime(2026, 10, 16, 9, 0)  # before today's evening slot: it is not missed yet
        j = e.client.get(f"/api/v1/documents/{did}/doctor-summary?from=2026-10-15&to=2026-10-16").json()
        assert next(m for m in j["medicines"] if m["ref"] == "m0")["missed"] == 0
        j = e.client.get(f"/api/v1/documents/{did}/doctor-summary").json()  # default period = the span of the logged events
        assert j["period"] == {"from": "2026-10-15", "to": "2026-10-16"}
        for q in ("from=2026-10-20&to=2026-10-01", "from=2026-01-01&to=2026-10-16", "from=nope"):
            assert e.client.get(f"/api/v1/documents/{did}/doctor-summary?{q}").status_code == 422


def test_doctor_summary_with_no_events_and_future_period(tmp_path, clock):
    with Env(tmp_path) as e:
        e.start()
        did = e.upload_ready()
        j = e.client.get(f"/api/v1/documents/{did}/doctor-summary").json()
        assert j["period"] == {"from": "2026-10-16", "to": "2026-10-16"} and all(m["taken"] == m["skipped"] == 0 for m in j["medicines"])
        j = e.client.get(f"/api/v1/documents/{did}/doctor-summary?from=2026-10-20&to=2026-10-22").json()
        assert all(m["missed"] == 0 for m in j["medicines"])  # the future is never "missed"
