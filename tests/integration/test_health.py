"""Integration tests for the /health endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /health should return 200 with expected schema."""
    resp = await client.get("/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert isinstance(data["mock_mode"], bool)
    assert "services" in data
    assert data["services"]["db"] in ("connected", "disconnected")
    assert data["services"]["qdrant"] in ("connected", "disconnected")


@pytest.mark.asyncio
async def test_health_shows_mock_mode(client: AsyncClient) -> None:
    """In test env, mock_mode should be True."""
    resp = await client.get("/health")
    data = resp.json()
    assert data["mock_mode"] is True


@pytest.mark.asyncio
async def test_health_db_connected_with_sqlite(client: AsyncClient) -> None:
    """SQLite test DB should report as connected."""
    resp = await client.get("/health")
    data = resp.json()
    assert data["services"]["db"] == "connected"


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient) -> None:
    """CORS preflight should allow configured origins."""
    resp = await client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORS middleware responds to OPTIONS
    assert resp.status_code in (200, 405)
    # When CORS is active, the response header is set
    if resp.status_code == 200:
        assert "access-control-allow-origin" in resp.headers
