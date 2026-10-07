"""Async SQLAlchemy engine and session factory.

Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite) based on DATABASE_URL.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_settings()

# SQLite requires special connect_args for async usage
_connect_args: dict = {}
if _settings.is_sqlite:
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.log_level == "DEBUG",
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (for use as a FastAPI dependency)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_db_connection() -> bool:
    """Check if the database is reachable.

    Returns:
        True if connected, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)
        return False


async def create_tables() -> None:
    """Create all tables defined by ORM models (for dev/testing)."""
    from app.db.base import Base  # noqa: F811

    # Import all models so they register with Base.metadata
    import app.models.trip  # noqa: F401
    import app.models.route_suggestion  # noqa: F401
    import app.models.feedback  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
