"""Integration tests for the /feedback endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_feedback_success(client: AsyncClient) -> None:
    """Test submitting feedback successfully."""
    payload = {
        "route_suggestion_id": "test_route_123",
        "rating": 4,
        "comment": "Good route, minimal traffic.",
        "difficulties_faced": ["Traffic", "Steep hill"]
    }
    
    response = await client.post("/api/v1/feedback", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["route_suggestion_id"] == "test_route_123"
    assert data["rating"] == 4
    assert data["comment"] == "Good route, minimal traffic."
    assert "Traffic" in data["difficulties_faced"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_submit_feedback_invalid_rating(client: AsyncClient) -> None:
    """Test submitting feedback with invalid rating fails validation."""
    payload = {
        "route_suggestion_id": "test_route_123",
        "rating": 6,  # max is 5
    }
    
    response = await client.post("/api/v1/feedback", json=payload)
    
    assert response.status_code == 422
