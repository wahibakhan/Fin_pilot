from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FinPilot AI"
    environment: str = "local"

    database_url: str = "postgresql+asyncpg://finpilot:finpilot@localhost:5432/finpilot"
    # Postgres schema all tables live under. Defaults to "public" (normal
    # behavior for a dedicated database). Override only when sharing a
    # database with another, unrelated application, to guarantee zero
    # table-name collisions regardless of what's already in `public`.
    db_schema: str = "public"

    jwt_secret: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: list[str] = ["http://localhost:3000"]

    ai_provider: str = "openai"
    ai_model: str = "gpt-5"
    openai_api_key: str | None = None
    google_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
