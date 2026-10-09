import io
import json

import httpx
import pytest
from PIL import Image

from app.llm import gemini, get_provider, ollama as ol
from app.llm.base import LLMError, Part
from app.llm.ollama import OllamaProvider
from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth
from app.services import extraction as ex
from app.services.guards import REPO

TXT = REPO / "data" / "synthetic" / "rx_001.txt"
GOOD = from_ground_truth(ExtractedDocument.model_validate_json((REPO / "data/ground_truth/rx_001.json").read_text(encoding="utf-8"))).model_dump_json()
seen: list = []


def png(w=2000, h=1000) -> bytes:
    b = io.BytesIO()
    Image.new("RGB", (w, h), "white").save(b, "PNG")
    return b.getvalue()


def body(content=GOOD, prompt=2000, out=300, reason="stop", **kw):
    return {"message": {"role": "assistant", "content": content}, "done": True, "done_reason": reason, "prompt_eval_count": prompt, "eval_count": out, **kw}


def provider(*responses):
    """Mock Ollama: each response is a dict (200 JSON), an int status, or an exception."""
    queue = list(responses)

    def handler(req: httpx.Request):
        seen.append(json.loads(req.content))
        r = queue.pop(0)
        if isinstance(r, Exception):
            raise r
        return httpx.Response(r, text="err") if isinstance(r, int) else httpx.Response(200, json=r)

    return OllamaProvider(transport=httpx.MockTransport(handler))


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(ol, "_sleep", lambda s: None)
    seen.clear()


def gen(p, parts):
    return p.generate("sys", parts, ExtractionOutput)


def test_success_and_payload_options():
    r = gen(provider(body()), [Part("text", "doc")])
    assert r.text == GOOD and r.usage == {"prompt_tokens": 2000, "output_tokens": 300, "total_tokens": 2300}
    req = seen[0]
    assert req["think"] is False and req["stream"] is False  # thinking off
    assert req["options"]["temperature"] == 0 and req["options"]["seed"] == ol.SEED and req["options"]["num_ctx"] == ol.settings.ollama_num_ctx
    assert req["format"]["type"] == "object" and req["messages"][0]["role"] == "system" and "images" not in req["messages"][1]


def test_schema_sent_has_all_properties_required():
    gen(provider(body()), [Part("text", "d")])
    fmt = seen[0]["format"]
    assert set(fmt["required"]) == set(fmt["properties"]) and "medications" in fmt["required"]
    med = fmt["$defs"]["OutMedication"]
    assert set(med["required"]) == set(med["properties"])
    assert "medications" not in ExtractionOutput.model_json_schema()["required"]  # our own schema is untouched


def test_image_payload_is_base64_and_downscaled(monkeypatch):
    import base64

    monkeypatch.setattr(ol.settings, "ollama_max_image_side", 1000)
    gen(provider(body()), [Part("image", png(2000, 1000), "image/png")])
    (img,) = seen[0]["messages"][1]["images"]
    assert Image.open(io.BytesIO(base64.b64decode(img))).size == (1000, 500)  # aspect kept
    assert ol.downscale(png(300, 200), 1000) == png(300, 200)  # never upscaled


def test_non_local_url_refused(monkeypatch):
    for url in ("http://example.com:11434", "http://192.168.1.5:11434", "http://localhost.evil.com"):
        monkeypatch.setattr(ol.settings, "ollama_base_url", url)
        with pytest.raises(ValueError):
            OllamaProvider()
    monkeypatch.setattr(ol.settings, "ollama_base_url", "http://127.0.0.1:11434")
    OllamaProvider()


def test_pdf_unsupported(tmp_path):
    with pytest.raises(LLMError, match="unsupported_input"):
        gen(provider(), [Part("pdf", b"%PDF", "application/pdf")])
    f = REPO / "data" / "rendered" / "clean"
    pdfs = list(f.glob("*.pdf")) if f.exists() else []
    if pdfs:
        r = ex.extract_document(pdfs[0], provider=provider(), cache_dir=tmp_path)
        assert not r.ok and r.skipped and r.error.startswith("unsupported_input")


def test_timeout_and_unreachable():
    with pytest.raises(LLMError, match="timeout"):
        gen(provider(httpx.ReadTimeout("slow")), [Part("text", "d")])
    with pytest.raises(LLMError, match="ollama_unreachable"):
        gen(provider(httpx.ConnectError("down")), [Part("text", "d")])


def test_5xx_retried_then_ok():
    r = gen(provider(503, 500, body()), [Part("text", "d")])
    assert r.calls == 3 and len(seen) == 3


def test_context_truncated():
    for b in (body(reason="length"), body(prompt=5000, out=1200)):  # cut off, or prompt+output reached num_ctx (6144)
        with pytest.raises(LLMError) as e:
            gen(provider(b), [Part("text", "d")])
        assert e.value.reason == "context_truncated"


def test_image_not_received():
    with pytest.raises(LLMError) as e:
        gen(provider(body(prompt=1300)), [Part("image", png(), "image/png")])
    assert e.value.reason == "image_not_received"
    with pytest.raises(LLMError, match="image_not_received"):  # image bytes removed
        gen(provider(body()), [Part("image", b"", "image/png")])
    gen(provider(body(prompt=700)), [Part("text", "d")])  # a text-only call is not subject to the image check


def test_invalid_json_then_retry_through_service(tmp_path):
    p = provider(body(content="{bad"), body())
    r = ex.extract_document(TXT, provider=p, cache_dir=tmp_path)
    assert r.ok and r.api_calls == 2
    assert "previous JSON was invalid" in seen[1]["messages"][1]["content"]
    r = ex.extract_document(TXT, provider=provider(body(content="{bad"), body(content="{bad")), cache_dir=tmp_path, use_cache=False)
    assert not r.ok and r.error == "validation_failed" and not r.skipped


def test_service_reports_skip_reason(tmp_path):
    r = ex.extract_document(TXT, provider=provider(body(reason="length")), cache_dir=tmp_path)
    assert not r.ok and r.skipped and r.error == "context_truncated"


def test_cache_key_differs_by_provider_and_settings(monkeypatch):
    k = lambda tag: ex.cache_key(b"x", tag)  # noqa: E731
    o, g = OllamaProvider(), gemini.GeminiProvider(client=object())
    assert k(o.cache_tag()) != k(g.cache_tag())
    base = k(o.cache_tag())
    monkeypatch.setattr(ol.settings, "ollama_num_ctx", 8192)
    assert k(o.cache_tag()) != base
    monkeypatch.setattr(ol.settings, "ollama_num_ctx", 6144)
    monkeypatch.setattr(ol.settings, "ollama_max_image_side", 900)
    assert k(o.cache_tag()) != base
    monkeypatch.undo()
    monkeypatch.setattr(ol.settings, "ollama_model", "other:tag")
    assert k(o.cache_tag()) != base
    assert ex.cache_key(b"x", "t", "v1") != ex.cache_key(b"x", "t", "v2")


def test_get_provider_default_is_ollama():
    assert get_provider().name == "ollama"


@pytest.mark.live
def test_live_ollama_text(tmp_path):
    r = ex.extract_document(TXT, provider=OllamaProvider(), cache_dir=tmp_path)
    assert r.ok and r.output.medications
