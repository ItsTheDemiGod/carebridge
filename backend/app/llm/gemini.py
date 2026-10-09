"""Gemini adapter (optional provider; free tier is quota-limited)."""

import random
import time
from collections import deque

from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.config import settings
from app.llm.base import LLMError, LLMResponse, Part

_sleep = time.sleep  # patched in tests
_clock = time.monotonic
_calls: deque = deque()


def _throttle():
    """Sliding one-minute window."""
    limit = settings.gemini_max_requests_per_minute
    while True:
        now = _clock()
        while _calls and now - _calls[0] >= 60:
            _calls.popleft()
        if len(_calls) < limit:
            _calls.append(now)
            return
        _sleep(60 - (now - _calls[0]) + 0.1)


def _retry_delay(e: errors.APIError, attempt: int) -> float:
    backoff = min(2**attempt + random.uniform(0, 1), 60)
    hint = 0.0
    try:
        for d in e.details["error"]["details"]:  # Google RetryInfo, e.g. {"retryDelay": "34s"}
            if d.get("@type", "").endswith("RetryInfo"):
                hint = float(d["retryDelay"].rstrip("s"))
    except (TypeError, KeyError, ValueError, AttributeError):
        pass
    return max(backoff, hint)


def _daily_quota(e: errors.APIError) -> bool:
    return e.code == 429 and "PerDay" in str(e)


class GeminiProvider:
    name = "gemini"

    def __init__(self, client=None):
        self._client = client  # keep a reference: a temporary client is closed on garbage collection

    @property
    def model(self) -> str:
        return settings.gemini_model

    def cache_tag(self) -> str:
        return f"gemini|{self.model}"

    def _get_client(self):
        if self._client is None:
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY is not set (put it in backend/.env)")
            self._client = genai.Client(api_key=settings.gemini_api_key)
        return self._client

    def generate(self, system: str, parts: list[Part], schema: type[BaseModel], temperature: float = 0.0) -> LLMResponse:
        client = self._get_client()
        contents = [p.data if p.kind == "text" else types.Part.from_bytes(data=p.data, mime_type=p.mime) for p in parts]
        cfg = types.GenerateContentConfig(temperature=temperature, system_instruction=system, response_mime_type="application/json", response_schema=schema)
        retries, start = settings.gemini_max_retries, time.perf_counter()
        for attempt in range(retries + 1):
            _throttle()
            try:
                resp = client.models.generate_content(model=self.model, contents=contents, config=cfg)
                break
            except errors.APIError as e:
                transient = e.code == 429 or (e.code or 0) >= 500
                if not transient or attempt == retries or _daily_quota(e):  # daily quota: waiting will not help
                    raise LLMError(f"api_error {e.code}", quota=_daily_quota(e), calls=attempt + 1)
                _sleep(_retry_delay(e, attempt))
        um = getattr(resp, "usage_metadata", None)
        p, o = (getattr(um, "prompt_token_count", 0) or 0), (getattr(um, "candidates_token_count", 0) or 0)
        return LLMResponse(text=resp.text or "", usage={"prompt_tokens": p, "output_tokens": o, "total_tokens": p + o}, latency_s=time.perf_counter() - start, calls=attempt + 1)
