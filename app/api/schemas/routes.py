"""Pydantic schemas for the routing endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RouteSuggestRequest(BaseModel):
    """Request model for getting route suggestions."""

    origin: str = Field(..., min_length=2, max_length=200, description="Starting location name or address")
    destination: str = Field(..., min_length=2, max_length=200, description="Destination name or address")
    mode: str = Field("driving", description="Travel mode (driving, walking, cycling)")


class ScoredRoute(BaseModel):
    """A suggested route with difficulty score and details."""

    distance_m: float
    duration_s: float
    difficulty_score: float
    reasoning: str
    tags: list[str]
    geometry: dict[str, Any]
    steps: list[dict[str, Any]]


class RouteSuggestResponse(BaseModel):
    """Response model containing suggested routes."""

    origin_resolved: dict[str, Any] | None
    destination_resolved: dict[str, Any] | None
    routes: list[ScoredRoute]
    errors: list[str] | None = None
