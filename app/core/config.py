"""Application configuration via pydantic-settings.

All settings are loaded from environment variables or a .env file.
Defaults are safe for local development with MOCK_MODE=true.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Smart Route AI backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────
    mock_mode: bool = Field(
        default=True,
        description="Use fixture data instead of real external APIs",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
    )

    # ── Database ────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        description="Async SQLAlchemy connection URL",
    )

    # ── Qdrant ──────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "trip_patterns"

    # ── Google Places API ───────────────────────────
    google_places_api_key: str = ""

    # ── OpenRouteService ────────────────────────────
    ors_api_key: str = ""

    # ── LLM ─────────────────────────────────────────
    llm_provider: Literal["openai", "google"] = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # ── Rate Limiting ───────────────────────────────
    rate_limit_suggest: str = "30/minute"
    rate_limit_default: str = "60/minute"

    # ── Embedding ───────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Accept comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_mock_mode(self) -> bool:
        """True if mock mode is enabled or critical API keys are missing."""
        return self.mock_mode or not self.google_places_api_key or not self.ors_api_key

    @property
    def is_sqlite(self) -> bool:
        """True if using SQLite backend."""
        return "sqlite" in self.database_url


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()
