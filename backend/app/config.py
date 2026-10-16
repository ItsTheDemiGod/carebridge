from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")  # same .env whatever the cwd

    app_name: str = "CareBridge"
    version: str = "0.1.0"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_max_requests_per_minute: int = 5  # conservative: the docs do not publish free-tier numbers
    gemini_max_retries: int = 5
    llm_provider: str = "ollama"  # ollama (local, default) or gemini (optional, quota-limited)
    ollama_base_url: str = "http://localhost:11434"  # adapter refuses non-local hosts
    ollama_model: str = "qwen3-vl:8b-instruct"  # non-thinking tag; plain qwen3-vl:8b ignores think:false
    ollama_num_ctx: int = 6144
    ollama_num_predict: int = 3000  # room for the full JSON of a long document
    ollama_timeout_seconds: float = 600  # first request loads the model
    ollama_keep_alive: str = "30m"
    ollama_max_image_side: int = 1280
    ollama_max_retries: int = 2
    ollama_min_image_prompt_tokens: int = 1500  # text-only prompt measured at 1168 tokens; real image calls 2200+
    cors_origin: str = "http://localhost:5173"

    # Phase 5 (API, session database). The key is a secret: only ever read from the environment / .env, never logged.
    carebridge_data_key: str | None = None
    session_ttl_hours: int = 24
    max_upload_bytes: int = 10 * 1024 * 1024
    max_image_pixels: int = 40_000_000
    max_docs_per_session: int = 10
    job_queue_max: int = 3
    job_timeout_seconds: float = 900
    db_path: str = "data/app/carebridge.db"  # relative paths resolve against the repo root
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cookie_secure: bool = False  # must be true behind HTTPS

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def db_file(self) -> Path:
        p = Path(self.db_path)
        return p if p.is_absolute() else Path(__file__).resolve().parents[2] / p


settings = Settings()
