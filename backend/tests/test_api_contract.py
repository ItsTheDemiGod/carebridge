"""Contract tests: the response shapes the frontend builds against, plus the committed OpenAPI file and the Phase 5 template set."""
import csv
import json
from datetime import date
import re
import sys

from app.api.errors import message
from app.api.routes_documents import ERROR_CODES
from app.safety import interactions as I
from app.services import confirmation as CF
from app.services import result as R
from app.services import templates as T
from app.services.guards import REPO
from apihelpers import Env, FakeOllama
from test_api_review import garbled_output

sys.path.insert(0, str(REPO / "scripts"))
import add_phase5_templates as P5  # noqa: E402
import export_openapi as EO  # noqa: E402

LINE_KEYS = {"line_id", "source_ref", "kind", "text", "source_text", "provenance", "status", "display_mode", "review_level", "flags", "notices", "settled", "narrative_pending"}
LANGTEXT_KEYS = {"text", "status", "display_mode", "review_status", "verification", "provenance", "label", "label_key"}


def test_openapi_file_is_up_to_date():
    committed = (REPO / "docs" / "openapi.json").read_text(encoding="utf-8")
    assert committed == EO.build(), "docs/openapi.json is out of date: run  python scripts/export_openapi.py  and commit it"


def test_openapi_describes_every_endpoint_and_the_raw_upload():
    o = json.loads((REPO / "docs" / "openapi.json").read_text(encoding="utf-8"))
    assert len(o["paths"]) == 21 and set(o["paths"]["/api/v1/documents"]["post"]["requestBody"]["content"]) == {"image/png", "image/jpeg"}
    assert "multipart/form-data" not in json.dumps(o)
    assert "x" != json.dumps(o)  # the schema never carries configuration
    assert "CAREBRIDGE_DATA_KEY" not in json.dumps(o)


def test_main_response_shapes(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "safety_data", lambda: I.Data({"glimepiride|metformin": {"severity": "moderate"}}))
    with Env(tmp_path, provider=FakeOllama(output=garbled_output())) as e:
        c = e.client
        n = c.get("/api/v1/consent-notice?lang=en").json()
        assert set(n) == {"version", "language", "sha256", "title", "items", "purposes", "review_status"} and set(n["items"][0]) == {"id", "text"} and set(n["purposes"][0]) == {"id", "label", "required", "default"}
        s = c.post("/api/v1/sessions", json={"language": "en"}).json()
        assert set(s) == {"language", "expires_at", "consent", "documents", "limits"} and set(s["consent"]) == {"granted", "current_version", "purposes"} and set(s["limits"]) == {"max_documents", "max_upload_bytes"}
        e.start()
        d = e.upload().json()
        assert set(d) == {"id", "state", "error_code", "error_message", "created_at", "updated_at", "image_kept", "narrative", "timings", "retry_possible", "confirmed"}
        e.wait()
        did = d["id"]
        sel = {"decisions": [{"index": 0, "action": "select_formulary_drug", "formulary_id": "metformin", "strength_choice": "500 mg"}]}
        conf = c.post(f"/api/v1/documents/{did}/confirmations", json=sel).json()
        assert set(conf) == {"confirmed", "medicines", "removed"} and set(conf["medicines"][0]) == {"ref", "resolution", "interaction_ready", "schedule_ready", "review_level", "unresolved", "not_checked_reason"}
        r = c.get(f"/api/v1/documents/{did}/result?lang=en").json()
        assert set(r) == {"document_id", "language", "confirmed", "confirm_first", "narrative_status", "explanation", "medicines_meta", "removed", "guardrail_events"}
        ex = r["explanation"]
        assert [s_["id"] for s_ in ex["sections"]] == ["disclaimer", "medicines", "safety", "follow_ups", "advice", "warnings"]
        assert set(ex) >= {"document_id", "document_type", "sections", "templates_version", "prompt_version", "model", "safety", "guardrail_events"}
        for sec in ex["sections"]:
            assert set(sec) == {"id", "heading", "lines"}
            for ln in sec["lines"]:
                assert set(ln) == LINE_KEYS and set(ln["text"]) == {"en"} and set(ln["text"]["en"]) == LANGTEXT_KEYS
        assert set(ex["safety"]) == {"pair_results", "duplicate_notices", "counts", "overall_state", "schedule_reminder", "supplement_reviewed", "supplement_ignored"}
        assert set(ex["safety"]["pair_results"][0]) == {"a", "b", "generic_a", "generic_b", "status", "level", "source", "same_medicine"}
        assert set(r["medicines_meta"][0]) == {"line_id", "ref", "source_index", "resolution", "provenance", "unresolved", "not_checked_reason", "interaction_ready", "schedule_ready", "labels"}
        sc = c.get(f"/api/v1/documents/{did}/schedule").json()
        assert set(sc) == {"document_id", "language", "notice", "extra_notices", "slots", "medicines", "not_scheduled", "guardrail_events"} and set(sc["slots"][0]) == {"med_ref", "name", "time", "source"}
        assert set(sc["medicines"][0]) == {"ref", "name", "strength", "dose", "times_per_day", "timing_label", "times", "source", "duration_days", "duration_text"}
        ev = c.post("/api/v1/adherence", json={"document_id": did, "med_ref": sc["slots"][0]["med_ref"], "scheduled_time": sc["slots"][0]["time"], "date": date.today().isoformat(), "status": "taken"})
        assert ev.status_code == 201 and set(ev.json()) == {"id", "document_id", "med_ref", "scheduled_time", "date", "status"}
        sm = c.get(f"/api/v1/documents/{did}/doctor-summary").json()
        assert set(sm) == {"document_id", "language", "title", "period", "headings", "labels", "medicines", "unconfirmed", "not_scheduled", "interactions", "schedule_notice", "disclaimer", "guardrail_events"}
        assert set(sm["medicines"][0]) == {"ref", "name", "strength", "dose", "times_per_day", "timing_label", "times", "duration_days", "duration_text", "taken", "skipped", "missed"}
        assert set(sm["interactions"]) == {"lines", "found"}
        f = c.get("/api/v1/formulary/search?q=metf").json()
        assert set(f) == {"results", "formulary_status"}
        err = c.get("/api/v1/documents/nope").json()
        assert err == {"error": {"code": "not_found", "message": "We could not find that."}}
        rc = c.delete("/api/v1/session").json()
        assert set(rc) == {"deleted", "deleted_at", "message", "receipt"} and set(rc["deleted"]) == {"consents", "documents", "adherence_events", "payloads", "images", "sessions"}


def test_every_error_code_the_code_can_raise_has_a_template():
    import app.api as api_pkg
    from pathlib import Path

    src = "".join(p.read_text(encoding="utf-8") for p in Path(api_pkg.__file__).parent.glob("*.py")) + (REPO / "backend/app/services/uploads.py").read_text(encoding="utf-8")
    codes = set(re.findall(r'ApiError\(\d+, "(\w+)"', src)) | set(re.findall(r'UploadError\(\d+, "(\w+)"', src))
    assert {"consent_required", "not_found", "queue_full", "pdf_not_supported", "invalid_confirmation"} <= codes
    for code in codes:
        assert f"error.{code}" in T.load()["strings"], code
        assert message(code) == T.render(f"error.{code}", "en")
    for code in ERROR_CODES:
        assert f"job.failed.{code}" in T.load()["strings"], code


def test_every_reason_id_has_a_user_facing_sentence():
    reasons = set(CF.NAME_REASONS) | {"incomplete_quote", "unusual_strength", "non_daily_frequency", "ambiguous_OD", "conflicting_frequency", "conflicting_meal_relation", "conflicting_duration",
                                      "low_confidence", "quote_not_in_document", "user_not_in_list", "not_identifiable"}
    for r in reasons:
        assert f"confirm.flag.{r}" in T.load()["strings"], r
    from app.services.schedule import NOT_SCHEDULED

    assert all(f"schedule.not.{x}" in T.load()["strings"] for x in NOT_SCHEDULED)


def test_phase5_review_sheet_contains_exactly_the_new_ids():
    path = REPO / "data" / "templates" / "review_sheet_phase5_new.csv"
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # UTF-8 with BOM, for Excel
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    assert list(rows[0]) == ["template_id", "language", "english", "translation", "placeholders", "status", "reviewer_verdict", "reviewer_correction", "reviewer_comment"]
    assert {(r["template_id"], r["language"]) for r in rows} == {(t, lang) for t in P5.NEW for lang in ("ta", "hi")}
    assert all(r["status"] == "draft_unreviewed" and not r["reviewer_verdict"] for r in rows)
    first = list(csv.DictReader((REPO / "data" / "templates" / "review_sheet.csv").read_bytes().decode("utf-8-sig").splitlines()))
    assert list(first[0]) == list(rows[0])  # same columns as the earlier sheet
    for t in P5.NEW:  # the script and the committed templates agree
        assert T.load()["strings"][t]["en"]["text"] == P5.NEW[t][0]
