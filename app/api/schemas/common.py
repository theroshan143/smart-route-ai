"""Common response schemas shared across API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Individual error detail."""

    code: str
    message: str
    details: Any = None


class ErrorResponse(BaseModel):
    """Consistent error response wrapper."""

    error: ErrorDetail
