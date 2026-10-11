"""Model-written free-text lines (advice, follow-ups, warnings): simplify (A), translate (B), back-translate (C), judge (D).

Text-only calls through the existing provider layer (no image bytes), batched per document per language, structured output
(a list of {id, ...}), temperature 0, fixed seed (adapter), thinking off (instruct tag), context-truncation guard (adapter).
Results are cached on disk; the key includes prompt version, prompt text, provider tag (model, ctx, seed) and the input.
"""

import hashlib
import json
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMError, Part
from app.services.guards import REPO

PROMPT_VERSION = "v1"
PROMPT_ROOT = Path(__file__).resolve().parents[1] / "prompts"
CACHE_DIR = REPO / "data" / "cache" / "narrative"  # gitignored (data/cache/)
LANG_NAME = {"ta": "Tamil", "hi": "Hindi"}
PROMPT_FILE = {"simplify": "A_simplify.txt", "translate": "B_translate.txt", "back": "C_backtranslate.txt", "judge": "D_judge.txt"}
Verdict = Literal["supported", "adds_information", "omits_information", "contradicts", "unclear"]


class Item(BaseModel):
    id: str
    kind: Literal["advice", "follow_up", "warning"]
    text: str


class _Plain(BaseModel):
    id: str
    plain_english: str


class _Text(BaseModel):
    id: str
    text: str


class _English(BaseModel):
    id: str
    english: str


class _Judged(BaseModel):
    id: str
    verdict: Verdict
    reason: str


class SimplifyOut(BaseModel):
    items: list[_Plain]


class TranslateOut(BaseModel):
    items: list[_Text]


class BackOut(BaseModel):
    items: list[_English]


class JudgeOut(BaseModel):
    items: list[_Judged]


@dataclass
class Call:
    stage: str  # simplify | translate | back | judge
    lang: str
    cached: bool = False
    latency_s: float = 0.0
    api_calls: int = 0
    usage: dict = field(default_factory=dict)
    error: str | None = None
    raw: str | None = None


@dataclass
class Stage:
    """One batch call, reconciled with its input ids."""

    call: Call
    values: dict[str, object] = field(default_factory=dict)  # id -> text (or (verdict, reason) for the judge); only ids with exactly one output
    id_problems: dict[str, str] = field(default_factory=dict)  # id -> id_missing | id_duplicate
    batch_problems: list[str] = field(default_factory=list)  # extra_ids / order_changed / call failure: these fail every line of the batch

    @property
    def ok(self) -> bool:
        return self.call.error is None and not self.batch_problems


def load_prompt(stage: str, version: str = PROMPT_VERSION) -> str:
    return (PROMPT_ROOT / f"narrative_{version}" / PROMPT_FILE[stage]).read_text(encoding="utf-8")


def reconcile(input_ids: list[str], out_ids: list[str]) -> tuple[set[str], dict[str, str], list[str]]:
    """(ids with exactly one output, per-id problems, batch problems). Extra ids and a changed order are batch problems."""
    n, known = Counter(out_ids), set(input_ids)
    problems = {i: "id_missing" if n[i] == 0 else "id_duplicate" for i in input_ids if n[i] != 1}
    batch = []
    if extra := sorted(set(out_ids) - known):
        batch.append(f"extra_ids: {extra}")
    if [i for i in out_ids if i in known and n[i] == 1] != [i for i in input_ids if n[i] == 1]:
        batch.append("order_changed")
    return {i for i in input_ids if n[i] == 1}, problems, batch


def _key(provider, stage: str, version: str, system: str, user: str) -> str:
    h = hashlib.sha256(f"{provider.cache_tag()}|{stage}|{version}|{system}|{user}".encode()).hexdigest()
    return h


def _generate(provider, system: str, user: str, schema, cache_dir, version: str, call: Call):
    """Returns the validated model output or None (call.error set). One retry on invalid JSON."""
    cdir = Path(cache_dir or CACHE_DIR)
    f = cdir / f"{_key(provider, call.stage, version, system, user)}.json"
    if f.exists():
        c = json.loads(f.read_text(encoding="utf-8"))
        call.cached, call.latency_s, call.usage, call.raw = True, c["latency_s"], c["usage"], c["raw"]
        return schema.model_validate_json(c["raw"])
    parts, start = [Part("text", user)], time.perf_counter()
    for _ in range(2):
        try:
            resp = provider.generate(system, parts, schema)
        except LLMError as e:
            call.error, call.raw = e.reason, e.raw
            call.api_calls += e.calls
            call.latency_s = time.perf_counter() - start
            return None
        call.api_calls += resp.calls
        for k, v in resp.usage.items():
            call.usage[k] = call.usage.get(k, 0) + v
        call.raw = resp.text
        try:
            out = schema.model_validate_json(resp.text)
            break
        except ValidationError as e:
            parts = [Part("text", user), Part("text", f"Your previous JSON was invalid: {str(e)[:800]}\nReturn corrected JSON that follows the schema exactly.")]
    else:
        call.error = "validation_failed"
        call.latency_s = time.perf_counter() - start
        return None
    call.latency_s = time.perf_counter() - start
    cdir.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps({"raw": call.raw, "usage": call.usage, "latency_s": call.latency_s}), encoding="utf-8")
    return out


def _run(provider, stage: str, lang: str, payload: dict, schema, ids: list[str], pick, cache_dir, version: str) -> Stage:
    call = Call(stage, lang)
    if not ids:
        return Stage(call)
    out = _generate(provider, load_prompt(stage, version), json.dumps(payload, ensure_ascii=False), schema, cache_dir, version, call)
    if out is None:
        return Stage(call, batch_problems=[f"call_failed: {call.error}"])
    one, problems, batch = reconcile(ids, [x.id for x in out.items])
    return Stage(call, values={x.id: pick(x) for x in out.items if x.id in one}, id_problems=problems, batch_problems=batch)


def simplify(items: list[Item], provider, cache_dir=None, version=PROMPT_VERSION) -> Stage:
    return _run(provider, "simplify", "en", {"items": [i.model_dump() for i in items]}, SimplifyOut, [i.id for i in items], lambda x: x.plain_english, cache_dir, version)


def translate(plain: dict[str, str], lang: str, provider, cache_dir=None, version=PROMPT_VERSION) -> Stage:
    return _run(provider, "translate", lang, {"language": LANG_NAME[lang], "items": [{"id": i, "text": t} for i, t in plain.items()]}, TranslateOut, list(plain), lambda x: x.text, cache_dir, version)


def back_translate(texts: dict[str, str], lang: str, provider, cache_dir=None, version=PROMPT_VERSION) -> Stage:
    return _run(provider, "back", lang, {"language": LANG_NAME[lang], "items": [{"id": i, "text": t} for i, t in texts.items()]}, BackOut, list(texts), lambda x: x.english, cache_dir, version)


def judge(pairs: dict[str, tuple[str, str]], lang: str, provider, cache_dir=None, version=PROMPT_VERSION) -> Stage:
    """pairs: id -> (original English, candidate English). lang only labels the call (en: plain English, ta/hi: back-translation)."""
    return _run(provider, "judge", lang, {"items": [{"id": i, "original": o, "candidate": c} for i, (o, c) in pairs.items()]}, JudgeOut, list(pairs),
                lambda x: (x.verdict, x.reason), cache_dir, version)


@dataclass
class Narrative:
    """Everything the model produced for one document, per stage and language."""

    items: list[Item]
    simplified: Stage
    translated: dict[str, Stage] = field(default_factory=dict)
    back: dict[str, Stage] = field(default_factory=dict)
    judged: dict[str, Stage] = field(default_factory=dict)

    def calls(self) -> list[Call]:
        stages = [self.simplified, *self.translated.values(), *self.back.values(), *self.judged.values()]
        return [s.call for s in stages if s.call.api_calls or s.call.cached]


def narrate_document(items: list[Item], provider, cache_dir=None, version=PROMPT_VERSION, langs=("ta", "hi")) -> Narrative:
    """A (en) -> B and C (ta, hi) -> D (en, ta, hi): 8 calls for a document with free-text lines. No items, no calls."""
    src = {i.id: i.text for i in items}
    nar = Narrative(items, simplify(items, provider, cache_dir, version))
    plain = {i: t for i, t in nar.simplified.values.items() if isinstance(t, str) and t.strip()}
    nar.judged["en"] = judge({i: (src[i], t) for i, t in plain.items()}, "en", provider, cache_dir, version)
    for lang in langs:
        nar.translated[lang] = translate(plain, lang, provider, cache_dir, version)
        tr = {i: t for i, t in nar.translated[lang].values.items() if isinstance(t, str) and t.strip()}
        nar.back[lang] = back_translate(tr, lang, provider, cache_dir, version)
        bt = {i: t for i, t in nar.back[lang].values.items() if isinstance(t, str) and t.strip()}
        nar.judged[lang] = judge({i: (src[i], t) for i, t in bt.items()}, lang, provider, cache_dir, version)
    return nar
