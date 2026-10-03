from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CareBridge"
    version: str = "0.1.0"
    anthropic_api_key: str | None = None
    cors_origin: str = "http://localhost:5173"


settings = Settings()
