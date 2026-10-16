"""Orchestrates one uploaded document: extraction (local Ollama, origin user_upload, no disk cache) -> normalisation -> background narrative.

States: queued -> extracting -> normalising -> awaiting_confirmation | failed(error_code). Narrative state per language: pending, running, ready, failed.
The photo lives only in memory (dropped after extraction) unless keep_photo_for_session was consented, in which case it is stored encrypted.
User-origin results are written ONLY to the encrypted session database; no disk cache is touched. Nothing here logs content."""
import logging
import threading
import time
from dataclasses import asdict

from app.db import repo
from app.db.database import Database
from app.db.crypto import CryptoError, Vault
from app.llm import get_provider
from app.schemas.normalised import NormalisedDocument
from app.services import explain as E
from app.services import narrative as N
from app.services.extraction import extract_bytes
from app.services.guards import NotSyntheticError, assert_origin_allowed
from app.services.normalisation import normalise_document

log = logging.getLogger("carebridge")
ORIGIN = "user_upload"
LANGS = ("en", "ta", "hi")


def map_error(error: str | None) -> str:
    e = error or ""
    for code in ("context_truncated", "image_not_received", "timeout"):
        if e.startswith(code):
            return code
    if e.startswith(("validation_failed", "unsupported_input")):
        return "image_unreadable"
    return "ollama_unavailable"  # unreachable server, api_error, anything else from the adapter


# --- narrative (de)serialisation: stages are plain data; the raw model text is dropped ---------------------------------------------------
def _stage_out(s: N.Stage) -> dict:
    c = asdict(s.call)
    c["raw"] = None
    return {"call": c, "values": {k: list(v) if isinstance(v, tuple) else v for k, v in s.values.items()}, "id_problems": s.id_problems, "batch_problems": s.batch_problems}


def _stage_in(d: dict) -> N.Stage:
    return N.Stage(N.Call(**d["call"]), {k: tuple(v) if isinstance(v, list) else v for k, v in d["values"].items()}, d["id_problems"], d["batch_problems"])


def narrative_to_json(nar: N.Narrative) -> dict:
    return {"items": [i.model_dump() for i in nar.items], "simplified": _stage_out(nar.simplified),
            **{k: {lang: _stage_out(s) for lang, s in getattr(nar, k).items()} for k in ("translated", "back", "judged")}}


def narrative_from_json(d: dict) -> N.Narrative:
    return N.Narrative([N.Item(**i) for i in d["items"]], _stage_in(d["simplified"]),
                       **{k: {lang: _stage_in(s) for lang, s in d[k].items()} for k in ("translated", "back", "judged")})


def narrate_lang(items: list[N.Item], nar: N.Narrative | None, lang: str, provider) -> N.Narrative:
    """One language of narrate_document, on top of what already exists. English: simplify + judge. ta/hi: translate, back-translate, judge.
    cache_dir=NO_CACHE: nothing is read from or written to the shared disk cache."""
    src = {i.id: i.text for i in items}
    if lang == "en":
        nar = N.Narrative(items, N.simplify(items, provider, N.NO_CACHE))
        plain = {i: t for i, t in nar.simplified.values.items() if isinstance(t, str) and t.strip()}
        nar.judged["en"] = N.judge({i: (src[i], t) for i, t in plain.items()}, "en", provider, N.NO_CACHE)
        return nar
    plain = {i: t for i, t in nar.simplified.values.items() if isinstance(t, str) and t.strip()}
    nar.translated[lang] = N.translate(plain, lang, provider, N.NO_CACHE)
    tr = {i: t for i, t in nar.translated[lang].values.items() if isinstance(t, str) and t.strip()}
    nar.back[lang] = N.back_translate(tr, lang, provider, N.NO_CACHE)
    bt = {i: t for i, t in nar.back[lang].values.items() if isinstance(t, str) and t.strip()}
    nar.judged[lang] = N.judge({i: (src[i], t) for i, t in bt.items()}, lang, provider, N.NO_CACHE)
    return nar


class Pipeline:
    def __init__(self, db: Database, vault: Vault, provider_factory=get_provider, narrate=narrate_lang):
        self.db, self.vault, self.provider_factory, self.narrate = db, vault, provider_factory, narrate
        self.worker = None  # set by the app: used to queue the background narrative
        self._images: dict[str, tuple[bytes, str]] = {}
        self._lock = threading.Lock()

    # --- photo bytes held in memory only -----------------------------------------------------------------------------------------------
    def hold(self, doc_id: str, data: bytes, mime: str) -> None:
        with self._lock:
            self._images[doc_id] = (data, mime)

    def forget(self, doc_ids) -> None:
        with self._lock:
            for d in doc_ids:
                self._images.pop(d, None)

    # --- helpers -----------------------------------------------------------------------------------------------------------------------
    def _alive(self, c, doc_id: str, cancel: threading.Event | None) -> dict | None:
        d = repo.get_document_any(c, doc_id)
        return None if d is None or (cancel is not None and cancel.is_set()) else d

    def fail(self, doc_id: str, code: str) -> None:
        with self.db.session() as c:
            if repo.get_document_any(c, doc_id):
                repo.update_document(c, doc_id, state="failed", error_code=code)
        log.info("doc=%s state=failed error=%s", doc_id, code)
        self.forget([doc_id])

    def _session_language(self, c, doc: dict) -> str:
        r = c.execute("SELECT language FROM sessions WHERE id=?", (doc["session_id"],)).fetchone()
        return r[0] if r else "en"

    # --- extraction job ------------------------------------------------------------------------------------------------------------------
    def run_extraction(self, doc_id: str, cancel: threading.Event | None = None) -> None:
        t_start = time.time()
        with self.db.session() as c:
            d = self._alive(c, doc_id, cancel)
            if d is None:
                return
            timings = {"queued_s": round(t_start - d["created_at"], 2)}
            repo.update_document(c, doc_id, state="extracting", merge={"timings": timings})
            image = self._images.get(doc_id)
            if image is None and d["image_kept"]:
                blob = repo.get_payload(c, self.vault, doc_id, "images")
                image = (blob, d["progress"].get("mime", "image/png")) if blob else None
        log.info("doc=%s state=extracting queued_s=%s", doc_id, timings["queued_s"])
        if image is None:
            return self.fail(doc_id, "interrupted")
        try:
            provider = self.provider_factory()
            assert_origin_allowed(ORIGIN, provider)
            res = extract_bytes(image[0], image[1], provider, ORIGIN)
        except NotSyntheticError:
            return self.fail(doc_id, "provider_not_allowed")
        except Exception as e:  # provider construction/adapter failures: the type only, never the message
            log.error("doc=%s extraction crashed type=%s", doc_id, type(e).__name__)
            return self.fail(doc_id, "ollama_unavailable")
        timings["extracting_s"] = round(time.time() - t_start, 2)
        if cancel is not None and cancel.is_set():
            return
        if not res.ok:
            return self.fail(doc_id, map_error(res.error))
        t_norm = time.time()
        with self.db.session() as c:
            if self._alive(c, doc_id, cancel) is None:
                return
            repo.update_document(c, doc_id, state="normalising", merge={"timings": timings})
            nd = normalise_document(res.output)  # rules only; document text is not available in the app
            timings["normalising_s"] = round(time.time() - t_norm, 2)
            langs = self._narrative_langs(c, repo.get_document_any(c, doc_id))
            repo.put_payload(c, self.vault, doc_id, "normalised", nd.model_dump(mode="json"))
            repo.update_document(c, doc_id, state="awaiting_confirmation", merge={"timings": timings, "narrative": {lang: "pending" for lang in langs}, "narrative_done_at": {}})
        self.forget([doc_id])  # the photo is dropped here unless it was stored (encrypted) because the user opted in
        log.info("doc=%s state=awaiting_confirmation medicines=%s", doc_id, len(nd.medications))
        if self.worker is not None:
            for lang in langs:
                self.worker.submit_narrative(doc_id, lang)

    def _narrative_langs(self, c, doc: dict) -> list[str]:
        lang = self._session_language(c, doc)
        return ["en"] + ([lang] if lang in ("ta", "hi") else [])

    # --- narrative job (runs while the user confirms the medicine list) ----------------------------------------------------------------------
    def request_language(self, c, doc_id: str, lang: str) -> str:
        """Start a narrative for one more language unless it is already pending/running/ready. Returns the resulting state."""
        d = repo.get_document_any(c, doc_id)
        cur = d["progress"].get("narrative", {}).get(lang)
        if cur in ("pending", "running", "ready"):
            return cur
        langs = ["en"] if lang != "en" and d["progress"].get("narrative", {}).get("en") not in ("pending", "running", "ready") else []
        for x in langs + [lang]:
            self._set_narrative(c, doc_id, x, "pending")
            if self.worker is not None:
                self.worker.submit_narrative(doc_id, x)
        return "pending"

    def _set_narrative(self, c, doc_id: str, lang: str, state: str, extra: dict | None = None) -> None:
        d = repo.get_document_any(c, doc_id)
        if d is None:
            return
        nar = dict(d["progress"].get("narrative", {}))
        nar[lang] = state
        merge = {"narrative": nar}
        if extra:
            merge.update({k: {**d["progress"].get(k, {}), **v} for k, v in extra.items()})
        repo.update_document(c, doc_id, merge=merge)

    def run_narrative(self, doc_id: str, lang: str, cancel: threading.Event | None = None) -> None:
        t0 = time.time()
        with self.db.session() as c:
            if self._alive(c, doc_id, cancel) is None:
                return
            self._set_narrative(c, doc_id, lang, "running")
            try:
                nd = NormalisedDocument.model_validate(repo.get_payload(c, self.vault, doc_id, "normalised"))
                stored = repo.get_payload(c, self.vault, doc_id, "narrative")
            except (CryptoError, TypeError, ValueError):
                return self._set_narrative(c, doc_id, lang, "failed")
        items = E.model_items(nd)  # lines the phrase library does not match exactly; matched lines never cost a model call
        try:
            nar = narrative_from_json(stored) if stored else None
            if items and lang != "en" and (nar is None or not nar.simplified.values):
                raise RuntimeError("english_unavailable")  # translation starts from the simplified English
            if items:
                nar = self.narrate(items, nar, lang, self.provider_factory())
            else:
                nar = N.Narrative([], N.Stage(N.Call("simplify", "en")))
            failed = bool(items) and not self._lang_ok(nar, lang)
        except Exception as e:
            log.error("doc=%s narrative crashed lang=%s type=%s", doc_id, lang, type(e).__name__)
            nar, failed = (narrative_from_json(stored) if stored else None), True
        with self.db.session() as c:
            if self._alive(c, doc_id, cancel) is None:
                return
            if nar is not None:
                repo.put_payload(c, self.vault, doc_id, "narrative", narrative_to_json(nar))
            self._set_narrative(c, doc_id, lang, "failed" if failed else "ready", {"narrative_done_at": {lang: round(time.time() - t0, 2)}})
        log.info("doc=%s narrative lang=%s state=%s s=%s", doc_id, lang, "failed" if failed else "ready", round(time.time() - t0, 2))

    @staticmethod
    def _lang_ok(nar: N.Narrative, lang: str) -> bool:
        """Ready means the stage for this language ran and produced at least one line; single lines may still fall back to the original text."""
        if lang == "en":
            return nar.simplified.ok and bool(nar.simplified.values)
        st = nar.translated.get(lang)
        return st is not None and bool(st.values)

    # --- startup recovery ------------------------------------------------------------------------------------------------------------------
    def recover(self) -> int:
        """Anything in flight when the process stopped cannot continue (the photo and the model call are gone): mark it failed/interrupted."""
        n = 0
        with self.db.session() as c:
            for d in repo.all_documents(c):
                if d["state"] in ("queued", "extracting", "normalising"):
                    repo.update_document(c, d["id"], state="failed", error_code="interrupted")
                    n += 1
                nar = d["progress"].get("narrative", {})
                if any(v in ("pending", "running") for v in nar.values()):
                    repo.update_document(c, d["id"], merge={"narrative": {k: "failed" if v in ("pending", "running") else v for k, v in nar.items()}})
                    n += 1
        return n
