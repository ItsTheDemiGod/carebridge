"""Local Ollama adapter. Documents never leave this machine: only localhost / 127.0.0.1 is accepted."""

import base64
import io
import time
from urllib.parse import urlparse

import httpx
from PIL import Image
from pydantic import BaseModel

from app.config import settings
from app.llm.base import LLMError, LLMResponse, Part

LOCAL_HOSTS = {"localhost", "127.0.0.1"}
SEED = 42
_sleep = time.sleep


def assert_local(url: str) -> str:
    if urlparse(url).hostname not in LOCAL_HOSTS:
        raise ValueError(f"Refusing OLLAMA_BASE_URL {url!r}: only localhost or 127.0.0.1 is allowed, so documents cannot leave this machine")
    return url.rstrip("/")


def downscale(data: bytes, max_side: int) -> bytes:
    """Shrink (never enlarge) so the longest side is at most max_side; keeps aspect ratio."""
    img = Image.open(io.BytesIO(data))
    if max(img.size) <= max_side:
        return data
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


class OllamaProvider:
    name = "ollama"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.base_url = assert_local(settings.ollama_base_url)
        self._transport = transport

    @property
    def model(self) -> str:
        return settings.ollama_model

    def cache_tag(self) -> str:
        s = settings
        return f"ollama|{s.ollama_model}|ctx{s.ollama_num_ctx}|side{s.ollama_max_image_side}|seed{SEED}"

    def _payload(self, system, parts, schema, temperature):
        text = "\n\n".join(p.data for p in parts if p.kind == "text")
        images = [base64.b64encode(downscale(p.data, settings.ollama_max_image_side)).decode() for p in parts if p.kind == "image"]
        user = {"role": "user", "content": text or "Extract the data from the attached document image.", **({"images": images} if images else {})}
        return {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, user],
            "stream": False,
            "think": False,  # reasoning output off; only message.content is parsed
            "format": schema.model_json_schema(),
            "keep_alive": settings.ollama_keep_alive,
            "options": {"temperature": temperature, "seed": SEED, "num_ctx": settings.ollama_num_ctx, "num_predict": settings.ollama_num_predict},
        }, bool(images)

    def _post(self, payload) -> tuple[dict, int]:
        """POST with a few retries on 5xx. Returns (json, calls)."""
        retries = settings.ollama_max_retries
        for attempt in range(retries + 1):
            try:
                with httpx.Client(transport=self._transport, timeout=settings.ollama_timeout_seconds) as c:
                    r = c.post(f"{self.base_url}/api/chat", json=payload)
            except httpx.TimeoutException:
                raise LLMError("timeout", calls=attempt + 1)
            except httpx.TransportError as e:
                raise LLMError(f"ollama_unreachable ({type(e).__name__})", calls=attempt + 1)
            if r.status_code < 500:
                break
            if attempt == retries:
                raise LLMError(f"api_error {r.status_code}", calls=attempt + 1)
            _sleep(2**attempt)
        if r.status_code != 200:
            raise LLMError(f"api_error {r.status_code}: {r.text[:200]}", calls=attempt + 1)
        return r.json(), attempt + 1

    def generate(self, system: str, parts: list[Part], schema: type[BaseModel], temperature: float = 0.0) -> LLMResponse:
        if any(p.kind == "pdf" for p in parts):
            raise LLMError("unsupported_input: PDF (Ollama takes images, not PDFs)", calls=0)
        payload, has_image = self._payload(system, parts, schema, temperature)
        start = time.perf_counter()
        body, calls = self._post(payload)
        # prompt_eval_cached_count: tokens served from Ollama's prompt cache; they still occupy the context
        prompt = (body.get("prompt_eval_count") or 0) + (body.get("prompt_eval_cached_count") or 0)
        out = body.get("eval_count") or 0
        usage = {"prompt_tokens": prompt, "output_tokens": out, "total_tokens": prompt + out}
        content = (body.get("message") or {}).get("content") or ""
        fail = lambda reason: LLMError(reason, calls=calls, usage=usage, raw=content)  # noqa: E731
        if body.get("done_reason") == "length" or prompt + out >= settings.ollama_num_ctx:
            raise fail("context_truncated")
        if has_image and prompt < settings.ollama_min_image_prompt_tokens:
            raise fail("image_not_received")
        return LLMResponse(text=content, usage=usage, latency_s=time.perf_counter() - start, calls=calls)
