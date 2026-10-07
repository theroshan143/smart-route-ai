"""Shared test fixtures and configuration."""

from __future__ import annotations

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force test configuration BEFORE any app imports
os.environ["MOCK_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["LOG_LEVEL"] = "WARNING"

from app.core.config import Settings, get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache() -> None:
    """Clear the cached settings so test env vars take effect."""
    get_settings.cache_clear()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client for the FastAPI app."""
    # Clear cache for each test to ensure fresh settings
    get_settings.cache_clear()

    app = create_app()

    from app.db.engine import create_tables
    await create_tables()

    # Run lifespan (startup/shutdown)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    # Clean up test database
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            pass
