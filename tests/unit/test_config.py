"""Unit tests for app.core.config."""

from __future__ import annotations

import os

import pytest

from app.core.config import Settings


class TestSettings:
    """Test configuration loading and defaults."""

    def test_default_mock_mode_is_true(self) -> None:
        """MOCK_MODE defaults to True."""
        settings = Settings(mock_mode=True)
        assert settings.mock_mode is True

    def test_is_mock_mode_when_keys_missing(self) -> None:
        """is_mock_mode returns True when API keys are empty."""
        settings = Settings(
            mock_mode=False,
            google_places_api_key="",
            ors_api_key="test-key",
        )
        assert settings.is_mock_mode is True

    def test_is_mock_mode_false_when_all_keys_present(self) -> None:
        """is_mock_mode returns False when all keys are provided and mock_mode=False."""
        settings = Settings(
            mock_mode=False,
            google_places_api_key="gp-key",
            ors_api_key="ors-key",
        )
        assert settings.is_mock_mode is False

    def test_cors_origins_from_comma_string(self) -> None:
        """CORS_ORIGINS can be a comma-separated string."""
        settings = Settings(cors_origins="http://a.com, http://b.com")
        assert settings.cors_origins == ["http://a.com", "http://b.com"]

    def test_cors_origins_from_list(self) -> None:
        """CORS_ORIGINS can be a list."""
        origins = ["http://a.com", "http://b.com"]
        settings = Settings(cors_origins=origins)
        assert settings.cors_origins == origins

    def test_is_sqlite_detection(self) -> None:
        """is_sqlite detects SQLite URLs."""
        settings = Settings(database_url="sqlite+aiosqlite:///./dev.db")
        assert settings.is_sqlite is True

        settings2 = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost/db"
        )
        assert settings2.is_sqlite is False

    def test_default_database_url(self) -> None:
        """Default DATABASE_URL is SQLite."""
        settings = Settings()
        assert "sqlite" in settings.database_url

    def test_default_qdrant_collection(self) -> None:
        """Default Qdrant collection name."""
        settings = Settings()
        assert settings.qdrant_collection == "trip_patterns"

    def test_llm_defaults(self) -> None:
        """Default LLM settings."""
        settings = Settings()
        assert settings.llm_provider == "openai"
        assert settings.llm_model == "gpt-4o-mini"
