from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://tasker:tasker_secret@localhost:5432/tasker"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Cache
    cache_ttl_seconds: int = 3600

    # Celery
    celery_concurrency: int = 4

    # LLM (Anthropic)
    anthropic_api_key: str = ""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
