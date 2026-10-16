"""Shared helpers for API tests: app/client factory, fake (mocked) provider and narrative, tiny test images. Synthetic data only, no model calls."""
import io
import json
import re
from pathlib import Path

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.llm.base import LLMError, LLMResponse
from app.main import create_app
from app.schemas.extraction import ExtractedDocument
from app.schemas.extraction_output import ExtractionOutput, from_ground_truth
from app.services import narrative as N
from app.services.guards import REPO

H = {"X-CareBridge-Request": "1"}
ALL_PURPOSES = ["process_photo", "store_results_for_session", "keep_photo_for_session"]
REQUIRED = ["process_photo", "store_results_for_session"]


def gt_output(doc_id: str = "ds_037") -> ExtractionOutput:
    return from_ground_truth(ExtractedDocument.model_validate_json((REPO / "data" / "ground_truth" / f"{doc_id}.json").read_text(encoding="utf-8")))


class FakeOllama:
    """Mocked provider: answers every extraction call with the given output. `name == "ollama"` so the origin guard accepts it."""
    name = "ollama"
    model = "fake"

    def __init__(self, output: ExtractionOutput | None = None, error: str | None = None, hook=None):
        self.output, self.error, self.calls, self.hook = output or gt_output(), error, [], hook

    def cache_tag(self) -> str:
        return "fake"

    def generate(self, system, parts, schema, temperature=0.0):
        self.calls.append([p.kind for p in parts])
        if self.hook:
            self.hook(parts)
        if self.error:
            raise LLMError(self.error)
        return LLMResponse(text=self.output.model_dump_json(), usage={"prompt_tokens": 2000, "output_tokens": 100, "total_tokens": 2100})


class FakeGemini(FakeOllama):
    name = "gemini"


def fake_narrate(items, nar, lang, provider, calls=None):
    """Deterministic stand-in for narrate_lang: English echoes the source (judged supported); ta/hi produce a short target-script sentence."""
    if calls is not None:
        calls.append(lang)
    src = {i.id: i.text for i in items}
    if lang == "en":
        n = N.Narrative(items, N.Stage(N.Call("simplify", "en"), values=dict(src)))
        n.judged["en"] = N.Stage(N.Call("judge", "en"), values={i: ("supported", "ok") for i in src})
        return n
    word = {"ta": "இது ஒரு சோதனை உரை", "hi": "यह एक परीक्षण पाठ है"}[lang]
    n = nar
    n.translated[lang] = N.Stage(N.Call("translate", lang), values={i: (word + " " + " ".join(re.findall(r"\d+", t))).strip() for i, t in src.items()})
    n.back[lang] = N.Stage(N.Call("back", lang), values=dict(src))
    n.judged[lang] = N.Stage(N.Call("judge", lang), values={i: ("supported", "ok") for i in src})
    return n


def make_cfg(tmp_path: Path, **kw) -> Settings:
    base = dict(carebridge_data_key=Fernet.generate_key().decode(), db_path=str(tmp_path / "app" / "t.db"), job_timeout_seconds=30, ollama_base_url="http://localhost:11434")
    return Settings(_env_file=None, **{**base, **kw})


def png_bytes(size=(120, 80), color="white", exif=None) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def jpeg_with_gps() -> bytes:
    img = Image.new("RGB", (60, 40), "white")
    exif = Image.Exif()
    exif[0x010F] = "CanaryMake"  # Make
    gps = exif.get_ifd(0x8825)
    gps[1], gps[2], gps[3], gps[4] = "N", (12.0, 34.0, 56.0), "E", (77.0, 1.0, 2.0)
    buf = io.BytesIO()
    img.save(buf, "JPEG", exif=exif)
    return buf.getvalue()


class Env:
    """An app + client + handles. Use as a context manager (it runs the lifespan: database, worker)."""

    def __init__(self, tmp_path, provider=None, narrate=None, **cfg):
        self.cfg = make_cfg(tmp_path, **cfg)
        self.provider = provider or FakeOllama()
        self.narrate_calls: list = []
        nar = narrate or (lambda items, nar, lang, prov: fake_narrate(items, nar, lang, prov, self.narrate_calls))
        self.app = create_app(self.cfg, provider_factory=lambda: self.provider, narrate=nar, sweep_every_s=3600)
        self.client = TestClient(self.app, headers=dict(H))

    def __enter__(self):
        self.client.__enter__()
        return self

    def __exit__(self, *a):
        self.client.__exit__(*a)

    @property
    def ctx(self):
        return self.app.state.cb

    def wait(self):
        self.ctx.worker.join()

    def start(self, lang="en", purposes=REQUIRED, client=None):
        c = client or self.client
        assert c.post("/api/v1/sessions", json={"language": lang}).status_code in (200, 201)
        assert c.post("/api/v1/consent", json={"notice_version": "1", "purposes": purposes}).status_code == 200
        return c

    def upload(self, data=None, ctype="image/png", client=None):
        return (client or self.client).post("/api/v1/documents", content=data if data is not None else png_bytes(), headers={"Content-Type": ctype})

    def upload_ready(self, client=None, data=None):
        r = self.upload(data, client=client)
        assert r.status_code == 202, r.text
        self.wait()
        return r.json()["id"]

    def new_client(self):
        return TestClient(self.app, headers=dict(H))
