import json
from types import SimpleNamespace

import pytest
from google.genai import errors

from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import from_ground_truth
from app.services import extraction as ex
from app.services.guards import REPO, NotSyntheticError, assert_synthetic, check_split

DOC = REPO / "data" / "synthetic" / "rx_001.txt"
GOOD = from_ground_truth(ExtractedDocument.model_validate_json((REPO / "data/ground_truth/rx_001.json").read_text(encoding="utf-8"))).model_dump_json()
sleeps: list = []


class FakeClient:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), 0
        self.models = SimpleNamespace(generate_content=self._gen)

    def _gen(self, **kw):
        self.calls += 1
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(text=r, usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=5, total_token_count=15))


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(ex, "_sleep", lambda s: sleeps.append(s))
    ex._calls.clear()
    sleeps.clear()


def run(client, tmp_path, **kw):
    return ex.extract_document(DOC, client=client, cache_dir=tmp_path, **kw)


def err(code, retry=None, message="x"):
    details = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": f"{retry}s"}] if retry else []
    return errors.APIError(code, {"error": {"code": code, "message": message, "status": "S", "details": details}})


def test_success_records_usage(tmp_path):
    r = run(FakeClient(GOOD), tmp_path)
    assert r.ok and r.usage["total_token_count"] == 15 and r.api_calls == 1 and r.latency_s >= 0


def test_validation_failure_retries_once_then_fails(tmp_path):
    c = FakeClient("{bad", GOOD)
    assert run(c, tmp_path).ok and c.calls == 2
    c = FakeClient("{bad", "{bad")
    r = run(c, tmp_path, use_cache=False)
    assert not r.ok and r.error == "validation_failed" and c.calls == 2


def test_rate_limit_backoff_honours_hint(tmp_path):
    c = FakeClient(err(429, retry=30), err(503), GOOD)
    r = run(c, tmp_path)
    assert r.ok and c.calls == 3 and sleeps[0] >= 30 and sleeps[1] >= 2


def test_gives_up_after_max_retries(tmp_path, monkeypatch):
    monkeypatch.setattr(ex.settings, "gemini_max_retries", 2)
    c = FakeClient(err(503), err(503), err(503))
    r = run(c, tmp_path)
    assert not r.ok and c.calls == 3 and "503" in r.error


def test_daily_quota_not_retried(tmp_path):
    c = FakeClient(err(429, message="GenerateRequestsPerDay exceeded"))
    r = run(c, tmp_path)
    assert r.quota_exhausted and c.calls == 1


def test_cache_hit_costs_no_calls(tmp_path):
    run(FakeClient(GOOD), tmp_path)
    c = FakeClient()
    r = run(c, tmp_path)
    assert r.ok and r.cached and c.calls == 0


def test_throttle_waits_when_over_limit(monkeypatch):
    monkeypatch.setattr(ex.settings, "gemini_max_requests_per_minute", 2)
    t = [0.0]
    monkeypatch.setattr(ex, "_clock", lambda: t[0])
    monkeypatch.setattr(ex, "_sleep", lambda s: t.__setitem__(0, t[0] + s))
    for _ in range(3):
        ex._throttle()
    assert t[0] >= 60


def test_guard_refuses_non_synthetic(tmp_path):
    f = tmp_path / "real.txt"
    f.write_text("patient")
    with pytest.raises(NotSyntheticError):
        assert_synthetic(f)
    with pytest.raises(NotSyntheticError):
        ex.extract_document(f, client=FakeClient())
    with pytest.raises(NotSyntheticError):
        assert_synthetic(REPO / "data" / "synthetic" / ".." / ".." / "README.md")
    assert assert_synthetic(DOC) == DOC


def test_test_split_guard(tmp_path):
    log = tmp_path / "t.log"
    check_split("dev", False, "x", log=log)
    with pytest.raises(SystemExit):
        check_split("test", False, "x", log=log)
    assert not log.exists()
    check_split("test", True, "x", log=log)
    assert json.loads(log.read_text())["split"] == "test"


@pytest.mark.live
def test_live_text_extraction(tmp_path):
    r = ex.extract_document(DOC, cache_dir=tmp_path)
    assert r.ok and r.output.medications
