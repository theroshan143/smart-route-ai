"""Aggregate v1 API router.

All v1 endpoints are mounted under /api/v1 by the main app.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router

v1_router = APIRouter()

# Health is mounted at root level (no /api/v1 prefix)
# Other endpoints will be added in later phases

# Placeholder routers for future phases
# from app.api.v1.routes import router as routes_router
# from app.api.v1.places import router as places_router
# from app.api.v1.feedback import router as feedback_router
