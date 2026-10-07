"""Integration tests for the /routes endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_suggest_routes_success(client: AsyncClient) -> None:
    """Test the /suggest endpoint with valid data."""
    payload = {
        "origin": "Times Square",
        "destination": "JFK Airport",
        "mode": "driving"
    }
    
    response = await client.post("/api/v1/routes/suggest", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "origin_resolved" in data
    assert "destination_resolved" in data
    assert "routes" in data
    
    routes = data["routes"]
    assert len(routes) > 0
    assert "difficulty_score" in routes[0]
    assert "tags" in routes[0]


@pytest.mark.asyncio
async def test_suggest_routes_unresolvable(client: AsyncClient) -> None:
    """Test the /suggest endpoint when locations cannot be resolved."""
    payload = {
        "origin": "Unresolvablexyz",
        "destination": "AnotherUnresolvable",
        "mode": "driving"
    }
    
    response = await client.post("/api/v1/routes/suggest", json=payload)
    
    # The API throws a 400 if it couldn't resolve locations and get routes
    assert response.status_code == 400
    data = response.json()
    assert "Failed to suggest route" in data["detail"]
