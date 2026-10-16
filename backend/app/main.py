"""CareBridge API. All endpoints live under /api/v1 (plus the legacy /api/health). The app refuses to start without CAREBRIDGE_DATA_KEY."""
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import logging_config
from app.api import errors, security
from app.api.deps import Ctx
from app.config import Settings, settings as default_settings
from app.db.crypto import CryptoError, Vault
from app.db.database import Database
from app.llm import get_provider
from app.services.erasure import sweep_expired
from app.services.pipeline import Pipeline, narrate_lang
from app.services.worker import Worker

log = logging.getLogger("carebridge")
SWEEP_EVERY_S = 300
KEY_HELP = ("CAREBRIDGE_DATA_KEY is not set. Create it once with:  python scripts/generate_data_key.py   (it writes the key to backend/.env and never prints it). "
            "Then start the API again.")


def create_app(cfg: Settings | None = None, provider_factory=None, narrate=None, sweep_every_s: float = SWEEP_EVERY_S) -> FastAPI:
    cfg = cfg or default_settings

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if not cfg.carebridge_data_key:
            raise RuntimeError(KEY_HELP)
        try:
            vault = Vault(cfg.carebridge_data_key)
        except CryptoError:
            raise RuntimeError("CAREBRIDGE_DATA_KEY is not a valid key. " + KEY_HELP)
        logging_config.setup()
        db = Database(cfg.db_file)
        pipeline = Pipeline(db, vault, provider_factory or get_provider, narrate or narrate_lang)
        worker = Worker(pipeline, cfg.job_timeout_seconds, cfg.job_queue_max)
        ctx = Ctx(cfg, db, vault, pipeline, worker)
        pipeline.recover()
        sweep_expired(ctx)
        worker.start()
        stop = threading.Event()

        def sweeper():
            while not stop.wait(sweep_every_s):
                try:
                    sweep_expired(ctx)
                except Exception as e:  # type only
                    log.error("sweep failed type=%s", type(e).__name__)

        threading.Thread(target=sweeper, name="carebridge-sweeper", daemon=True).start()
        app.state.cb = ctx
        log.info("started")
        yield
        stop.set()
        worker.stop()

    app = FastAPI(title=cfg.app_name, version=cfg.version, lifespan=lifespan, docs_url=None, redoc_url=None)
    errors.install(app)
    security.install(app, cfg.origins)
    app.add_middleware(CORSMiddleware, allow_origins=cfg.origins, allow_credentials=True, allow_methods=["GET", "POST", "PUT", "DELETE"],
                       allow_headers=["Content-Type", "X-CareBridge-Request"])

    from app.api import routes_documents, routes_session

    app.include_router(routes_session.router)
    app.include_router(routes_documents.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "app": cfg.app_name, "version": cfg.version}

    return app


app = create_app()
