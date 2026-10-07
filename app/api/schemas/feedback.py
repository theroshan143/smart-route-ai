"""Pydantic schemas for the feedback endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """Request model for submitting route feedback."""

    route_suggestion_id: str = Field(..., description="The ID of the suggested route taken")
    rating: int = Field(..., ge=1, le=5, description="User rating from 1 to 5")
    comment: str | None = Field(None, description="Optional user comments on the route")
    difficulties_faced: list[str] = Field(default_factory=list, description="Difficulties faced during the route")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""

    id: str
    route_suggestion_id: str
    rating: int
    comment: str | None = None
    difficulties_faced: list[str]
    created_at: Any
