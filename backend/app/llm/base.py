"""Provider interface: system instruction + input parts + output schema -> raw JSON text."""

from dataclasses import dataclass, field
from typing import Protocol

from pydantic import BaseModel


@dataclass
class Part:
    kind: str  # "text" | "image" | "pdf"
    data: bytes | str
    mime: str | None = None


@dataclass
class LLMResponse:
    text: str
    usage: dict = field(default_factory=dict)  # prompt_tokens, output_tokens, total_tokens
    latency_s: float = 0.0
    calls: int = 1


class LLMError(Exception):
    """Structured failure. `reason` examples: api_error 503, timeout, context_truncated, image_not_received, unsupported_input."""

    def __init__(self, reason: str, *, quota: bool = False, calls: int = 1, usage: dict | None = None, raw: str | None = None):
        super().__init__(reason)
        self.reason, self.quota, self.calls, self.usage, self.raw = reason, quota, calls, usage or {}, raw


class Provider(Protocol):
    name: str
    model: str

    def cache_tag(self) -> str:
        """Everything about this provider that changes output (name, model, relevant settings)."""

    def generate(self, system: str, parts: list[Part], schema: type[BaseModel], temperature: float = 0.0) -> LLMResponse: ...
