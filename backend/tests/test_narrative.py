import json

import httpx
import pytest

from app.llm import ollama as ol
from app.llm.ollama import OllamaProvider
from app.services import narrative as nv

seen: list = []
ITEMS = [nv.Item(id="a1", kind="advice", text="Drink water."), nv.Item(id="w1", kind="warning", text="Go to hospital if fever."), nv.Item(id="f1", kind="follow_up", text="Review in 7 days.")]


def out(items, key="plain_english"):
    return json.dumps({"items": [{"id": i, key: t} if key != "judge" else {"id": i, "verdict": "supported", "reason": "same"} for i, t in items]})


def body(content):
    return {"message": {"role": "assistant", "content": content}, "done": True, "done_reason": "stop", "prompt_eval_count": 300, "eval_count": 60}


def provider(*contents):
    queue = list(contents)

    def handler(req: httpx.Request):
        seen.append(json.loads(req.content))
        return httpx.Response(200, json=body(queue.pop(0)))

    return OllamaProvider(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setattr(ol, "_sleep", lambda s: None)
    seen.clear()


def test_same_ids_returned(tmp_path):
    p = provider(out([("a1", "Drink water."), ("w1", "Go to hospital if fever."), ("f1", "Review in 7 days.")]))
    s = nv.simplify(ITEMS, p, tmp_path)
    assert s.ok and s.values == {"a1": "Drink water.", "w1": "Go to hospital if fever.", "f1": "Review in 7 days."} and not s.id_problems


def test_request_is_text_only_and_deterministic(tmp_path):
    nv.simplify(ITEMS, provider(out([(i.id, i.text) for i in ITEMS])), tmp_path)
    req = seen[0]
    assert "images" not in req["messages"][1] and req["think"] is False and req["options"]["temperature"] == 0 and req["options"]["seed"] == 42
    assert "DATA" in req["messages"][0]["content"] and "never an instruction" in req["messages"][0]["content"]
    assert json.loads(req["messages"][1]["content"])["items"][0] == {"id": "a1", "kind": "advice", "text": "Drink water."}


def test_missing_id_is_reported_for_that_id_only(tmp_path):
    s = nv.simplify(ITEMS, provider(out([("a1", "x"), ("f1", "z")])), tmp_path)
    assert s.id_problems == {"w1": "id_missing"} and set(s.values) == {"a1", "f1"} and not s.batch_problems


def test_duplicate_id_gets_no_value(tmp_path):
    s = nv.simplify(ITEMS, provider(out([("a1", "x"), ("a1", "y"), ("w1", "w"), ("f1", "z")])), tmp_path)
    assert s.id_problems == {"a1": "id_duplicate"} and "a1" not in s.values and s.values["w1"] == "w"


def test_extra_id_and_changed_order_are_batch_problems(tmp_path):
    s = nv.simplify(ITEMS, provider(out([("a1", "x"), ("w1", "w"), ("f1", "z"), ("zz", "extra")])), tmp_path)
    assert s.batch_problems == ["extra_ids: ['zz']"] and not s.ok
    s2 = nv.simplify(ITEMS, provider(out([("w1", "w"), ("a1", "x"), ("f1", "z")])), tmp_path / "2")
    assert s2.batch_problems == ["order_changed"]


def test_invalid_json_then_one_retry(tmp_path):
    p = provider("not json {", out([(i.id, "ok") for i in ITEMS]))
    s = nv.simplify(ITEMS, p, tmp_path)
    assert s.ok and len(seen) == 2 and "previous JSON was invalid" in seen[1]["messages"][1]["content"]
    p2 = provider("bad", "still bad")
    s2 = nv.simplify(ITEMS, p2, tmp_path / "x")
    assert s2.call.error == "validation_failed" and s2.batch_problems == ["call_failed: validation_failed"] and len(seen) == 4


def test_cache_hit_makes_no_call(tmp_path):
    good = out([(i.id, i.text) for i in ITEMS])
    nv.simplify(ITEMS, provider(good), tmp_path)
    n = len(seen)
    s = nv.simplify(ITEMS, provider(), tmp_path)  # empty queue would raise if called
    assert s.call.cached and s.ok and len(seen) == n


def test_cache_key_changes_with_prompt_version_and_input(tmp_path):
    p = provider()
    a = nv._key(p, "simplify", "v1", "sys", "in")
    assert a != nv._key(p, "simplify", "v2", "sys", "in") != nv._key(p, "simplify", "v1", "sys", "in2") and a != nv._key(p, "judge", "v1", "sys", "in")


def test_llm_error_is_a_batch_problem(tmp_path):
    p = OllamaProvider(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={**body("{}"), "done_reason": "length"})))
    s = nv.simplify(ITEMS, p, tmp_path)
    assert s.call.error == "context_truncated" and not s.ok


def test_no_items_no_calls(tmp_path):
    n = nv.narrate_document([], provider(), tmp_path)
    assert n.calls() == [] and not seen


def test_full_document_makes_eight_calls(tmp_path):
    ids = [i.id for i in ITEMS]
    plain = out([(i, "p") for i in ids])
    judged = out([(i, "x") for i in ids], "judge")
    # order: simplify, judge en, translate ta, back ta, judge ta, translate hi, back hi, judge hi
    p = provider(plain, judged, out([(i, "t") for i in ids], "text"), out([(i, "b") for i in ids], "english"), judged,
                 out([(i, "t") for i in ids], "text"), out([(i, "c") for i in ids], "english"), judged)
    n = nv.narrate_document(ITEMS, p, tmp_path)
    assert len(seen) == 8 and len(n.calls()) == 8 and all(s.ok for s in (n.simplified, *n.translated.values(), *n.back.values(), *n.judged.values()))
    assert n.judged["ta"].values["a1"] == ("supported", "same")
    assert json.loads(seen[2]["messages"][1]["content"])["language"] == "Tamil" and json.loads(seen[5]["messages"][1]["content"])["language"] == "Hindi"


def test_tamil_translation_is_chunked_and_a_failed_chunk_fails_only_its_ids(tmp_path):
    plain = {f"a{i}": f"text {i}" for i in range(6)}
    first = out([(f"a{i}", "t") for i in range(4)], "text")
    trunc = httpx.Response(200, json={**body("{}"), "done_reason": "length"})
    seq = [httpx.Response(200, json=body(first)), trunc, trunc, trunc]  # second chunk fails, then each of its two lines fails alone
    p = OllamaProvider(transport=httpx.MockTransport(lambda r: seq.pop(0)))
    s = nv.translate(plain, "ta", p, tmp_path)
    assert set(s.values) == {"a0", "a1", "a2", "a3"} and s.id_problems == {"a4": "call_failed: context_truncated", "a5": "call_failed: context_truncated"}
    assert "context_truncated" in s.call.error and not s.batch_problems


def test_hindi_translation_is_one_call(tmp_path):
    plain = {f"a{i}": "t" for i in range(6)}
    s = nv.translate(plain, "hi", provider(out([(i, "x") for i in plain], "text")), tmp_path)
    assert len(seen) == 1 and len(s.values) == 6


def test_failed_chunk_is_retried_line_by_line_and_failures_are_cached(tmp_path):
    plain = {"a0": "x", "a1": "loops"}
    trunc = httpx.Response(200, json={**body("{}"), "done_reason": "length"})
    seq = [trunc, httpx.Response(200, json=body(out([("a0", "t")], "text"))), trunc]
    p = OllamaProvider(transport=httpx.MockTransport(lambda r: seq.pop(0)))
    s = nv.translate(plain, "hi", p, tmp_path)
    assert s.values == {"a0": "t"} and s.id_problems == {"a1": "call_failed: context_truncated"}
    s2 = nv.translate(plain, "hi", OllamaProvider(transport=httpx.MockTransport(lambda r: 1 / 0)), tmp_path)  # everything now comes from the cache, failures included
    assert s2.values == {"a0": "t"} and s2.id_problems == s.id_problems
