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
    ollama_min_image_prompt_tokens: int = 1200  # below this an image call is treated as image_not_received (calibrated in Phase 2 step 4)
    cors_origin: str = "http://localhost:5173"


settings = Settings()
