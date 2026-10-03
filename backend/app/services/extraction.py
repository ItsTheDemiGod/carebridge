"""Extract structured data from a synthetic document with Gemini (text, PNG, JPG or PDF)."""

import hashlib
import json
import random
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.config import settings
from app.prompts import PROMPT_VERSION, load_prompt
from app.schemas.extraction_output import SCHEMA_VERSION, ExtractionOutput
from app.services.guards import REPO, assert_synthetic

CACHE_DIR = REPO / "data" / "cache"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".pdf": "application/pdf"}
_sleep = time.sleep  # patched in tests
_clock = time.monotonic
_calls: deque = deque()
_client = None


@dataclass
class ExtractionResult:
    ok: bool
    output: ExtractionOutput | None = None
    error: str | None = None
    cached: bool = False
    quota_exhausted: bool = False
    latency_s: float = 0.0
    usage: dict = field(default_factory=dict)
    api_calls: int = 0
    raw_text: str | None = None


def get_client():
    global _client
    if _client is None:  # keep a reference: a temporary client is closed on garbage collection
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set (put it in backend/.env)")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


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


def _generate(client, contents, system, retries):
    """One model call with throttling and backoff on 429/5xx. Returns (response, n_calls)."""
    cfg = types.GenerateContentConfig(temperature=0, system_instruction=system, response_mime_type="application/json", response_schema=ExtractionOutput)
    for attempt in range(retries + 1):
        _throttle()
        try:
            return client.models.generate_content(model=settings.gemini_model, contents=contents, config=cfg), attempt + 1
        except errors.APIError as e:
            transient = e.code == 429 or (e.code or 0) >= 500
            if not transient or attempt == retries or _daily_quota(e):  # daily quota: waiting will not help
                raise
            _sleep(_retry_delay(e, attempt))


def cache_key(data: bytes, prompt_version: str = PROMPT_VERSION) -> str:
    return hashlib.sha256(data + f"|{settings.gemini_model}|{prompt_version}|{SCHEMA_VERSION}".encode()).hexdigest()


def extract_document(path, client=None, use_cache=True, prompt_version=PROMPT_VERSION, cache_dir=None) -> ExtractionResult:
    p = assert_synthetic(path)
    data = p.read_bytes()
    cache_file = Path(cache_dir or CACHE_DIR) / f"{cache_key(data, prompt_version)}.json"
    if use_cache and cache_file.exists():
        c = json.loads(cache_file.read_text(encoding="utf-8"))
        return ExtractionResult(ok=True, output=ExtractionOutput.model_validate(c["output"]), cached=True, usage=c["usage"], latency_s=c["latency_s"], raw_text=c["output_raw"])

    suffix = p.suffix.lower()
    if suffix == ".txt":
        doc = types.Part.from_text(text=data.decode("utf-8"))
    elif suffix in MIME:
        doc = types.Part.from_bytes(data=data, mime_type=MIME[suffix])
    else:
        return ExtractionResult(ok=False, error=f"unsupported file type {suffix}")

    client = client or get_client()
    system = load_prompt(prompt_version)
    contents: list = [doc]
    start, calls, usage, raw = time.perf_counter(), 0, {}, None
    for _ in range(2):  # second pass = the single retry, with the validation error appended
        try:
            resp, n = _generate(client, contents, system, settings.gemini_max_retries)
        except errors.APIError as e:
            return ExtractionResult(ok=False, error=f"api_error {e.code}", quota_exhausted=_daily_quota(e), api_calls=calls + 1, usage=usage, latency_s=time.perf_counter() - start)
        calls += n
        raw = resp.text
        um = getattr(resp, "usage_metadata", None)
        if um:
            for k in ("prompt_token_count", "candidates_token_count", "total_token_count"):
                usage[k] = (usage.get(k) or 0) + (getattr(um, k, None) or 0)
        try:
            out = ExtractionOutput.model_validate_json(raw or "")
            break
        except ValidationError as e:
            contents = [doc, f"Your previous JSON was invalid: {str(e)[:1500]}\nReturn corrected JSON that follows the schema exactly."]
    else:
        return ExtractionResult(ok=False, error="validation_failed", api_calls=calls, usage=usage, raw_text=raw, latency_s=time.perf_counter() - start)

    latency = time.perf_counter() - start
    if use_cache:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"output": out.model_dump(mode="json"), "output_raw": raw, "usage": usage, "latency_s": latency}), encoding="utf-8")
    return ExtractionResult(ok=True, output=out, api_calls=calls, usage=usage, latency_s=latency, raw_text=raw)
