"""FastAPI application factory.

Creates and configures the main application with:
- CORS middleware
- Exception handlers
- Lifespan for startup/shutdown
- All API routers
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.db.engine import create_tables, engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown logic."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(
        "Starting Smart Route AI (mock_mode=%s, db=%s)",
        settings.is_mock_mode,
        "sqlite" if settings.is_sqlite else "postgresql",
    )

    # Create tables on startup (dev convenience)
    await create_tables()

    yield

    # Shutdown: dispose engine
    await engine.dispose()
    logger.info("Smart Route AI shut down")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Returns:
        Fully configured FastAPI instance.
    """
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="Travel Route Suggester API",
        description=(
            "AI-powered travel route suggestion backend. Suggests routes based on "
            "historical travel patterns, real-time difficulty scoring, and user preferences."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ───────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────
    # Health at root
    app.include_router(health_router)

    # v1 API routers will be added here in later phases
    # app.include_router(v1_router, prefix="/api/v1")

    logger.info("Application configured (CORS origins: %s)", settings.cors_origins)
    return app


# Module-level app instance for uvicorn
app = create_app()
