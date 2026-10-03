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
    cors_origin: str = "http://localhost:5173"


settings = Settings()
