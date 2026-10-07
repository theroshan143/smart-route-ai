"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.engine import check_db_connection

logger = get_logger(__name__)

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check() -> dict:
    """Return service health status including database and Qdrant connectivity.

    Returns:
        Health status with mock_mode flag and service connection states.
    """
    settings = get_settings()
    db_connected = await check_db_connection()

    # Qdrant check — best-effort
    qdrant_connected = False
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.qdrant_url}/healthz")
            qdrant_connected = resp.status_code == 200
    except Exception:
        qdrant_connected = False

    overall = "ok" if db_connected else "degraded"

    return {
        "status": overall,
        "mock_mode": settings.is_mock_mode,
        "services": {
            "db": "connected" if db_connected else "disconnected",
            "qdrant": "connected" if qdrant_connected else "disconnected",
        },
    }
