"""Phase 6d: builds the pre-recorded API responses of the sample (demo) mode into frontend/src/demo/fixtures/*.json.   python scripts/build_demo_data.py [--check]

Nothing here calls a model. The REAL FastAPI app runs in-process on a throw-away database (random in-memory key, temp folder) and is driven through its real
endpoints; its two model hooks are replaced by cache replays:
  * extraction: the cached output of the DEV document below (run dev-ollama-v1, cache key = rendered image bytes), served as if the model had answered;
  * narrative: the real narrative stages with the on-disk cache (data/cache/narrative) and a provider that RAISES on any cache miss.
A missing cache entry, a missing interaction store or a non-synthetic origin therefore stops the build with an error; there is no fallback.
Scripted user decisions follow docs/CONFIRMATION.md (name reasons are resolved by picking the formulary drug, every other reason by acknowledging it).
Output is deterministic: random ids and timestamps are replaced by fixed values. Every fixture carries a header (source document, condition, synthetic, version, date).
--check builds into memory and compares with the committed files (used by the staleness test)."""
import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.llm.base import LLMResponse  # noqa: E402
from app.llm.ollama import OllamaProvider  # noqa: E402
from app.main import create_app  # noqa: E402
from app.prompts import PROMPT_VERSION  # noqa: E402
from app.schemas.extraction_output import ExtractionOutput  # noqa: E402
from app.services import consent as C  # noqa: E402
from app.services import narrative as N  # noqa: E402
from app.services.extraction import cache_key  # noqa: E402

SCRIPT_VERSION = "1"
BUILT_ON = "2026-10-18"  # bumped by hand when the fixtures are rebuilt on purpose; keeps the output deterministic
DOC_ID, CONDITION = "ds_037", "poor"  # a dev-split document (checked below); the 40-document test split is never touched
OUT = REPO / "frontend" / "src" / "demo" / "fixtures"
IMAGE = REPO / "data" / "rendered" / CONDITION / f"{DOC_ID}.png"
LANGS = ("en", "ta", "hi")
SCRIPTED = {  # medicine index -> formulary id picked in the sample (the garbled "Netfornin" is read as Metformin; the duplicate-name row is Atorvastatin)
    "Netfornin": "metformin",
}
QUERIES = ["metf", "gli", "atorva"]  # picker searches recorded for the sample
H = {"X-CareBridge-Request": "1"}


class MissingCache(RuntimeError):
    pass


class ReplayExtraction:
    """Answers the extraction call with the cached model output of the chosen dev document. Looks like the local adapter; never calls anything."""
    name, model = "ollama", "replay-from-cache"

    def __init__(self, output: ExtractionOutput):
        self.output = output

    def cache_tag(self) -> str:
        return "replay"

    def generate(self, system, parts, schema, temperature=0.0):
        assert [p.kind for p in parts][0] == "image"
        return LLMResponse(text=self.output.model_dump_json(), usage={})


class CacheOnly(OllamaProvider):
    """Same cache tag as the real adapter (so the cached narrative is found) but any attempt to call the model stops the build."""
    def generate(self, *a, **k):
        raise MissingCache("narrative cache entry missing: the demo builder never calls a model; run the Phase 3 narrative run first")


def cached_extraction() -> ExtractionOutput:
    manifest = {d["id"]: d for d in json.loads((REPO / "data" / "manifest.json").read_text(encoding="utf-8"))["documents"]}
    assert manifest[DOC_ID]["split"] == "dev", "the demo document must come from the DEV split"
    f = REPO / "data" / "cache" / f"{cache_key(IMAGE.read_bytes(), OllamaProvider().cache_tag(), PROMPT_VERSION)}.json"
    if not f.exists():
        raise MissingCache(f"extraction cache entry for {DOC_ID}/{CONDITION} is missing ({f.name}); this script never calls a model")
    return ExtractionOutput.model_validate(json.loads(f.read_text(encoding="utf-8"))["output"])


def cached_narrate(items, nar, lang, provider):
    """narrate_lang with the real on-disk cache instead of NO_CACHE (same stages, same order)."""
    p, src = CacheOnly(), {i.id: i.text for i in items}
    if lang == "en":
        nar = N.Narrative(items, N.simplify(items, p))
        plain = {i: t for i, t in nar.simplified.values.items() if isinstance(t, str) and t.strip()}
        nar.judged["en"] = N.judge({i: (src[i], t) for i, t in plain.items()}, "en", p)
        return nar
    plain = {i: t for i, t in nar.simplified.values.items() if isinstance(t, str) and t.strip()}
    nar.translated[lang] = N.translate(plain, lang, p)
    tr = {i: t for i, t in nar.translated[lang].values.items() if isinstance(t, str) and t.strip()}
    nar.back[lang] = N.back_translate(tr, lang, p)
    bt = {i: t for i, t in nar.back[lang].values.items() if isinstance(t, str) and t.strip()}
    nar.judged[lang] = N.judge({i: (src[i], t) for i, t in bt.items()}, lang, p)
    return nar


# --- deterministic output ------------------------------------------------------------------------------------------------------------------
ISO = re.compile(r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d")
FIXED_TIME = "2026-01-01T00:00:00+00:00"
VOLATILE = {"timings", "narrative_done_at", "latency_s", "usage"}


def scrub(x, doc_id: str):
    if isinstance(x, dict):
        return {k: ({} if k in VOLATILE else scrub(v, doc_id)) for k, v in x.items()}
    if isinstance(x, list):
        return [scrub(v, doc_id) for v in x]
    if isinstance(x, str):
        if ISO.match(x):
            return FIXED_TIME
        return x.replace(doc_id, "demo")
    return x


def header(name: str) -> dict:
    return {"fixture": name, "synthetic": True, "source_document": DOC_ID, "condition": CONDITION, "split": "dev", "script": "scripts/build_demo_data.py",
            "script_version": SCRIPT_VERSION, "built_on": BUILT_ON,
            "note": "Pre-recorded response of the real API for a synthetic development document, replayed from cached model outputs. No model was called."}


def build() -> dict[str, dict]:
    out_img = cached_extraction()
    files: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        cfg = Settings(_env_file=None, carebridge_data_key=Fernet.generate_key().decode(), db_path=str(Path(tmp) / "demo.db"), job_timeout_seconds=60,
                       ollama_base_url="http://localhost:11434")
        app = create_app(cfg, provider_factory=lambda: ReplayExtraction(out_img), narrate=cached_narrate, sweep_every_s=3600)
        with TestClient(app, headers=dict(H)) as c:
            def get(path, **kw):
                r = c.get(path, **kw)
                assert r.status_code == 200, (path, r.status_code, r.text[:200])
                return r.json()

            for lang in LANGS:  # backend-owned fixed text per language
                files[f"strings_{lang}"] = get(f"/api/v1/strings?lang={lang}&prefix=")
            assert c.post("/api/v1/sessions", json={"language": "ta"}).status_code in (200, 201)
            notice = get("/api/v1/consent-notice?lang=en")
            assert c.post("/api/v1/consent", json={"notice_version": C.NOTICE_VERSION, "purposes": ["process_photo", "store_results_for_session"]}).status_code == 200
            up = c.post("/api/v1/documents", content=IMAGE.read_bytes(), headers={"Content-Type": "image/png"})
            assert up.status_code == 202, up.text
            did = up.json()["id"]
            app.state.cb.worker.join()
            assert c.post(f"/api/v1/documents/{did}/languages", json={"language": "hi"}).status_code in (200, 202)
            app.state.cb.worker.join()
            doc = get(f"/api/v1/documents/{did}")
            assert doc["state"] == "awaiting_confirmation" and all(doc["narrative"].get(lang) == "ready" for lang in LANGS), doc
            files["session"] = get("/api/v1/session")
            files["document"] = doc
            files["documents"] = get("/api/v1/documents")
            files["consent_notice_en"] = notice
            before = get(f"/api/v1/documents/{did}/medicines")
            files["medicines_before"] = before
            for lang in LANGS:
                files[f"result_before_{lang}"] = get(f"/api/v1/documents/{did}/result?lang={lang}")
            # scripted decisions (docs/CONFIRMATION.md)
            decisions, entries = [], {}
            for m in before["medicines"]:
                name = (m["as_written"].get("brand") or m["as_written"].get("generic") or "").strip()
                name_reasons = [r["id"] for r in m["reasons"] if r["kind"] == "name"]
                ack = [r["id"] for r in m["reasons"] if r["kind"] == "acknowledge"]
                if name_reasons:
                    fid = SCRIPTED.get(name) or (m["as_written"].get("generic") or "").lower()
                    e = get(f"/api/v1/formulary/{fid}")
                    entries[fid] = e
                    strength = m["strength"] if m["strength"] in e["available_strengths"] else "as_on_my_label"
                    decisions.append({"index": m["index"], "action": "select_formulary_drug", "formulary_id": fid, "strength_choice": strength, **({"acknowledged_flags": ack} if ack else {})})
                else:
                    decisions.append({"index": m["index"], "action": "confirm_as_extracted", **({"acknowledged_flags": ack} if ack else {})})
            files["scripted_decisions"] = {"decisions": decisions, "added_medicines": []}
            r = c.post(f"/api/v1/documents/{did}/confirmations", json=files["scripted_decisions"])
            assert r.status_code == 200, r.text
            files["confirm_response"] = r.json()
            files["medicines_after"] = get(f"/api/v1/documents/{did}/medicines")
            for lang in LANGS:
                files[f"result_after_{lang}"] = get(f"/api/v1/documents/{did}/result?lang={lang}")
            files["schedule"] = get(f"/api/v1/documents/{did}/schedule")
            files["doctor_summary"] = get(f"/api/v1/documents/{did}/doctor-summary")
            # formulary: entries of every drug involved (read, written as extracted, picked) plus the recorded picker searches
            for m in before["medicines"]:
                for key in (m["as_written"].get("generic"), m.get("resolved_generic")):
                    if key and (fid := key.lower()) not in entries and c.get(f"/api/v1/formulary/{fid}").status_code == 200:
                        entries[fid] = get(f"/api/v1/formulary/{fid}")
            searches = {q: get(f"/api/v1/formulary/search?q={q}&limit=20") for q in QUERIES}
            for s in searches.values():
                for e in s["results"]:
                    entries.setdefault(e["id"], {**e, "formulary_status": s["formulary_status"]})
            files["formulary"] = {"entries": entries, "searches": searches, "formulary_status": next(iter(searches.values()))["formulary_status"]}
    return {k: {"_meta": header(k), "data": scrub(v, did)} for k, v in files.items()}


def render(files: dict[str, dict]) -> dict[str, str]:
    return {f"{k}.json": json.dumps(v, ensure_ascii=False, indent=1, sort_keys=True) + "\n" for k, v in files.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    built = render(build())
    if a.check:
        stale = [n for n, t in built.items() if not (OUT / n).exists() or (OUT / n).read_text(encoding="utf-8") != t]
        print("fixtures are up to date" if not stale else f"stale fixtures: {stale}")
        return 1 if stale else 0
    OUT.mkdir(parents=True, exist_ok=True)
    for n, t in built.items():
        (OUT / n).write_text(t, encoding="utf-8", newline="\n")
    print(f"wrote {len(built)} fixture files to {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
