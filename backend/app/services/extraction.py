"""Extract structured data from a synthetic document (text, PNG, JPG or PDF) through an LLM provider."""

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from app.llm import get_provider
from app.llm.base import LLMError, Part
from app.prompts import PROMPT_VERSION, load_prompt
from app.schemas.extraction_output import SCHEMA_VERSION, ExtractionOutput
from app.services.guards import REPO, assert_origin_allowed, assert_synthetic

CACHE_DIR = REPO / "data" / "cache"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".pdf": "application/pdf"}


@dataclass
class ExtractionResult:
    ok: bool
    output: ExtractionOutput | None = None
    error: str | None = None
    cached: bool = False
    quota_exhausted: bool = False
    skipped: bool = False  # provider/model failure (not a scored parse failure); evaluator reports these separately
    latency_s: float = 0.0
    usage: dict = field(default_factory=dict)
    api_calls: int = 0
    raw_text: str | None = None


def cache_key(data: bytes, provider_tag: str, prompt_version: str = PROMPT_VERSION) -> str:
    """Provider, model, generation settings, prompt and schema versions all change the key, so results never mix."""
    return hashlib.sha256(data + f"|{provider_tag}|{prompt_version}|{SCHEMA_VERSION}".encode()).hexdigest()


def _part(p: Path, data: bytes) -> Part | None:
    if p.suffix.lower() == ".txt":
        return Part("text", data.decode("utf-8"))
    kind = "pdf" if p.suffix.lower() == ".pdf" else "image"
    return Part(kind, data, MIME[p.suffix.lower()]) if p.suffix.lower() in MIME else None


def extract_document(path, provider=None, use_cache=True, prompt_version=PROMPT_VERSION, cache_dir=None) -> ExtractionResult:
    p = assert_synthetic(path)
    data = p.read_bytes()
    provider = provider or get_provider()
    cache_file = Path(cache_dir or CACHE_DIR) / f"{cache_key(data, provider.cache_tag(), prompt_version)}.json"
    if use_cache and cache_file.exists():
        c = json.loads(cache_file.read_text(encoding="utf-8"))
        return ExtractionResult(ok=True, output=ExtractionOutput.model_validate(c["output"]), cached=True, usage=c["usage"], latency_s=c["latency_s"], raw_text=c["output_raw"])

    doc = _part(p, data)
    if doc is None:
        return ExtractionResult(ok=False, error=f"unsupported_input: file type {p.suffix}", skipped=True)

    res = _call_model(doc, provider, prompt_version)
    if res.ok and use_cache:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"output": res.output.model_dump(mode="json"), "output_raw": res.raw_text, "usage": res.usage, "latency_s": res.latency_s}), encoding="utf-8")
    return res


def extract_bytes(data: bytes, mime: str, provider, origin: str = "user_upload", prompt_version=PROMPT_VERSION) -> ExtractionResult:
    """Extraction for a user upload (image bytes in memory). Never reads or writes the disk cache; only the local Ollama adapter may be used."""
    assert_origin_allowed(origin, provider)
    return _call_model(Part("image", data, mime), provider, prompt_version)


def _call_model(doc: Part, provider, prompt_version) -> ExtractionResult:
    system = load_prompt(prompt_version)
    parts = [doc]
    start, calls, usage, raw = time.perf_counter(), 0, {}, None
    for _ in range(2):  # second pass = the single retry, with the validation error appended
        try:
            resp = provider.generate(system, parts, ExtractionOutput)
        except LLMError as e:
            return ExtractionResult(ok=False, error=e.reason, skipped=True, quota_exhausted=e.quota, api_calls=calls + e.calls, usage=e.usage or usage, raw_text=e.raw, latency_s=time.perf_counter() - start)
        calls += resp.calls
        raw = resp.text
        for k, v in resp.usage.items():
            usage[k] = usage.get(k, 0) + v
        try:
            out = ExtractionOutput.model_validate_json(raw)
            break
        except ValidationError as e:
            parts = [doc, Part("text", f"Your previous JSON was invalid: {str(e)[:1500]}\nReturn corrected JSON that follows the schema exactly.")]
    else:
        return ExtractionResult(ok=False, error="validation_failed", api_calls=calls, usage=usage, raw_text=raw, latency_s=time.perf_counter() - start)

    latency = time.perf_counter() - start
    return ExtractionResult(ok=True, output=out, api_calls=calls, usage=usage, latency_s=latency, raw_text=raw)
