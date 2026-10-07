"""Unit tests for external services."""

from __future__ import annotations

import pytest

from app.services.pattern_store import PatternStore
from app.services.places_service import PlacesService
from app.services.routing_service import RoutingService


@pytest.mark.asyncio
async def test_places_service_mock_search() -> None:
    """PlacesService should return mock data in MOCK_MODE."""
    service = PlacesService()
    results = await service.search("Times Square")
    assert len(results) >= 1
    assert results[0]["place_id"] == "mock_times_square"
    assert "lat" in results[0]


@pytest.mark.asyncio
async def test_routing_service_mock_directions() -> None:
    """RoutingService should return mock routes in MOCK_MODE."""
    service = RoutingService()
    routes = await service.get_directions(40.0, -73.0, 41.0, -74.0, alternatives=2)
    assert len(routes) == 2
    assert "distance_m" in routes[0]
    assert "geometry" in routes[0]
    assert "steps" in routes[0]


@pytest.mark.asyncio
async def test_pattern_store_mock_query() -> None:
    """PatternStore should return mock similar trips in MOCK_MODE."""
    store = PatternStore()
    results = await store.query_similar("Origin", "Dest", "driving", k=2)
    assert len(results) == 2
    assert results[0]["id"] == "mock-trip-1"
    assert "similarity" in results[0]


@pytest.mark.asyncio
async def test_pattern_store_create_document() -> None:
    """Test text document creation for embedding."""
    store = PatternStore()
    trip_dict = {
        "origin": "A",
        "destination": "B",
        "mode": "walking",
        "delay_minutes": 10,
        "difficulty_tags": ["rain"],
        "notes": "Wet",
    }
    doc = store._create_trip_document(trip_dict)
    assert "Trip from A to B" in doc
    assert "Mode: walking" in doc
    assert "delay of 10 minutes" in doc
    assert "rain" in doc
    assert "Notes: Wet" in doc
