"""OpenRouteService integration for fetching directions and geometries.

Falls back to mock data if MOCK_MODE is enabled or API key is missing.
"""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mock data for when API keys aren't available
_MOCK_ROUTES = [
    {
        "distance_m": 4500.0,
        "duration_s": 1200.0,
        "geometry": {
            "type": "LineString",
            "coordinates": [[-73.9855, 40.7580], [-73.98, 40.76], [-73.9665, 40.7812]],
        },
        "steps": [
            {"instruction": "Head north", "distance_m": 2000.0, "duration_s": 600.0, "road_type": "street"},
            {"instruction": "Turn right", "distance_m": 2500.0, "duration_s": 600.0, "road_type": "avenue"},
        ],
        "road_types": ["street", "avenue"],
        "elevation_gain": 15.0,
    },
    {
        "distance_m": 4800.0,
        "duration_s": 1350.0,
        "geometry": {
            "type": "LineString",
            "coordinates": [[-73.9855, 40.7580], [-73.99, 40.75], [-73.9665, 40.7812]],
        },
        "steps": [
            {"instruction": "Head east", "distance_m": 4800.0, "duration_s": 1350.0, "road_type": "highway"},
        ],
        "road_types": ["highway"],
        "elevation_gain": 5.0,
    },
]


class RoutingService:
    """Service to interact with OpenRouteService (ORS) API."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = "https://api.openrouteservice.org/v2/directions"
        self.headers = {
            "Authorization": self.settings.ors_api_key,
            "Content-Type": "application/json",
            "Accept": "application/json, application/geo+json",
        }
        # Map our modes to ORS profiles
        self.mode_map = {
            "driving": "driving-car",
            "walking": "foot-walking",
            "cycling": "cycling-regular",
        }

    async def get_directions(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
        alternatives: int = 3,
    ) -> list[dict[str, Any]]:
        """Fetch directions between two points with alternatives.

        Args:
            origin_lat: Origin latitude.
            origin_lng: Origin longitude.
            dest_lat: Destination latitude.
            dest_lng: Destination longitude.
            mode: "driving", "walking", or "cycling".
            alternatives: Number of alternative routes to request.

        Returns:
            List of parsed route dictionaries containing distance, duration, geometry, and steps.
        """
        if self.settings.is_mock_mode:
            logger.info(
                "MOCK_MODE: returning fixture routes for %s → %s (%s)",
                (origin_lat, origin_lng),
                (dest_lat, dest_lng),
                mode,
            )
            return _MOCK_ROUTES[:alternatives]

        profile = self.mode_map.get(mode, "driving-car")
        url = f"{self.base_url}/{profile}/geojson"

        payload: dict[str, Any] = {
            "coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]],
            "alternatives": True,  # ORS boolean flag for alternatives
            "instructions": True,
            "geometry": True,
            "elevation": True,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
            except httpx.RequestError as exc:
                logger.error("ORS API request failed: %s", exc)
                raise ExternalServiceError("openrouteservice", f"Request failed: {exc}")
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "ORS API returned error %s: %s",
                    exc.response.status_code,
                    exc.response.text,
                )
                raise ExternalServiceError("openrouteservice", f"HTTP {exc.response.status_code}")

        data = response.json()
        features = data.get("features", [])

        parsed_routes = []
        for feature in features:
            try:
                geom = feature.get("geometry", {})
                props = feature.get("properties", {})
                summary = props.get("summary", {})
                segments = props.get("segments", [{}])
                steps_data = segments[0].get("steps", []) if segments else []

                steps = []
                for step in steps_data:
                    steps.append({
                        "instruction": step.get("instruction", ""),
                        "distance_m": step.get("distance", 0.0),
                        "duration_s": step.get("duration", 0.0),
                        "road_type": step.get("type", "unknown"), # simplified road type
                    })

                parsed = {
                    "distance_m": summary.get("distance", 0.0),
                    "duration_s": summary.get("duration", 0.0),
                    "geometry": geom,
                    "steps": steps,
                    # Simplified derived attributes
                    "road_types": list({s["road_type"] for s in steps}),
                    "elevation_gain": summary.get("ascent", 0.0),
                }
                parsed_routes.append(parsed)
            except Exception as e:
                logger.warning("Skipping route parsing due to error: %s", e)

        # Ensure we don't return more than requested alternatives (ORS might return fewer)
        return parsed_routes[:alternatives]
