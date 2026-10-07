"""Google Places API integration for location search and resolution.

Falls back to mock data if MOCK_MODE is enabled or API key is missing.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mock data for when API keys aren't available
_MOCK_PLACES = [
    {
        "place_id": "mock_times_square",
        "name": "Times Square",
        "address": "Manhattan, NY 10036, USA",
        "lat": 40.7580,
        "lng": -73.9855,
        "types": ["tourist_attraction", "point_of_interest", "establishment"],
    },
    {
        "place_id": "mock_jfk",
        "name": "John F. Kennedy International Airport",
        "address": "Queens, NY 11430, USA",
        "lat": 40.6413,
        "lng": -73.7781,
        "types": ["airport", "point_of_interest", "establishment"],
    },
    {
        "place_id": "mock_central_park",
        "name": "Central Park",
        "address": "New York, NY, USA",
        "lat": 40.7812,
        "lng": -73.9665,
        "types": ["park", "tourist_attraction", "point_of_interest"],
    },
]


class PlacesService:
    """Service to interact with Google Places API (New)."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_url = "https://places.googleapis.com/v1/places:searchText"
        self.headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.settings.google_places_api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.types",
        }

    async def search(
        self, query: str, lat: float | None = None, lng: float | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Search for places by text query.

        Args:
            query: The search string (e.g. "Times Square").
            lat: Optional latitude for location bias.
            lng: Optional longitude for location bias.
            limit: Max number of results (1-20).

        Returns:
            List of parsed place dictionaries.
        """
        if self.settings.is_mock_mode:
            logger.info("MOCK_MODE: returning fixture places for query %r", query)
            q_lower = query.lower()
            results = [p for p in _MOCK_PLACES if q_lower in p["name"].lower() or (q_lower == "jfk airport" and "jfk" in p["place_id"])]
            return results[:limit]

        payload: dict[str, Any] = {
            "textQuery": query,
            "maxResultCount": max(1, min(limit, 20)),
        }

        if lat is not None and lng is not None:
            # Add a 50km location bias circle
            payload["locationBias"] = {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": 50000.0,
                }
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.RequestError as exc:
                logger.error("Places API request failed: %s", exc)
                raise ExternalServiceError("google_places", f"Request failed: {exc}")
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Places API returned error %s: %s",
                    exc.response.status_code,
                    exc.response.text,
                )
                raise ExternalServiceError("google_places", f"HTTP {exc.response.status_code}")

        data = response.json()
        places = data.get("places", [])

        # Parse into our standard schema
        parsed_places = []
        for p in places:
            try:
                parsed = {
                    "place_id": p["id"],
                    "name": p.get("displayName", {}).get("text", ""),
                    "address": p.get("formattedAddress", ""),
                    "lat": p.get("location", {}).get("latitude", 0.0),
                    "lng": p.get("location", {}).get("longitude", 0.0),
                    "types": p.get("types", []),
                }
                parsed_places.append(parsed)
            except KeyError as e:
                logger.warning("Skipping place due to missing field %s: %s", e, p)

        return parsed_places
