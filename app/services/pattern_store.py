"""Qdrant integration for storing and querying semantic trip patterns.

Uses sentence-transformers to embed text. Falls back to mock data
if MOCK_MODE is enabled.
"""

from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mock data for when MOCK_MODE is true
_MOCK_SIMILAR_TRIPS = [
    {
        "id": "mock-trip-1",
        "origin": "Times Square",
        "destination": "Central Park",
        "mode": "driving",
        "delay_minutes": 15,
        "difficulty_tags": ["traffic", "crowds"],
        "notes": "Heavy traffic on 7th Ave.",
        "similarity": 0.89,
    },
    {
        "id": "mock-trip-2",
        "origin": "Times Square",
        "destination": "JFK Airport",
        "mode": "driving",
        "delay_minutes": 45,
        "difficulty_tags": ["traffic", "weather"],
        "notes": "Raining, Van Wyck Expressway was backed up.",
        "similarity": 0.75,
    },
]


class PatternStore:
    """Service to interact with Qdrant for trip pattern retrieval."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._qdrant: AsyncQdrantClient | None = None
        self._model: Any | None = None

    @property
    def qdrant(self) -> AsyncQdrantClient:
        """Lazy load Qdrant client."""
        if self._qdrant is None:
            self._qdrant = AsyncQdrantClient(url=self.settings.qdrant_url)
        return self._qdrant

    @property
    def model(self) -> Any:
        """Lazy load sentence-transformers model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embedding model %s", self.settings.embedding_model)
            # Use sentence-transformers
            self._model = SentenceTransformer(self.settings.embedding_model)
        return self._model

    async def initialize(self) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        if self.settings.mock_mode:
            return

        try:
            exists = await self.qdrant.collection_exists(self.settings.qdrant_collection)
            if not exists:
                logger.info("Creating Qdrant collection: %s", self.settings.qdrant_collection)
                await self.qdrant.create_collection(
                    collection_name=self.settings.qdrant_collection,
                    vectors_config=VectorParams(
                        size=self.settings.embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error("Failed to initialize Qdrant collection: %s", e)

    def _create_trip_document(self, trip_dict: dict[str, Any]) -> str:
        """Create a semantic text representation of a trip for embedding."""
        parts = [
            f"Trip from {trip_dict.get('origin', 'Unknown')} to {trip_dict.get('destination', 'Unknown')}",
            f"Mode: {trip_dict.get('mode', 'driving')}",
        ]
        
        delay = trip_dict.get('delay_minutes', 0)
        if delay > 0:
            parts.append(f"Experienced a delay of {delay} minutes.")
            
        tags = trip_dict.get('difficulty_tags', [])
        if tags:
            parts.append(f"Difficulties: {', '.join(tags)}.")
            
        notes = trip_dict.get('notes')
        if notes:
            parts.append(f"Notes: {notes}")
            
        return " ".join(parts)

    async def store_trip(self, trip_dict: dict[str, Any]) -> None:
        """Embed and store a trip record in Qdrant.

        Args:
            trip_dict: Dictionary containing trip data (needs id, origin, dest, mode, etc.)
        """
        if self.settings.mock_mode:
            logger.debug("MOCK_MODE: Skipping trip storage in Qdrant")
            return

        doc_text = self._create_trip_document(trip_dict)
        
        # sentence-transformers is synchronous, but we can run it here
        # For a truly async heavy-load we'd use run_in_executor
        vector = self.model.encode(doc_text).tolist()

        point = PointStruct(
            id=trip_dict["id"],
            vector=vector,
            payload={
                "origin": trip_dict.get("origin"),
                "destination": trip_dict.get("destination"),
                "mode": trip_dict.get("mode"),
                "delay_minutes": trip_dict.get("delay_minutes", 0),
                "difficulty_tags": trip_dict.get("difficulty_tags", []),
                "notes": trip_dict.get("notes", ""),
            },
        )

        try:
            await self.qdrant.upsert(
                collection_name=self.settings.qdrant_collection,
                points=[point],
            )
            logger.info("Stored trip %s in Qdrant", trip_dict["id"])
        except Exception as e:
            logger.error("Failed to store trip in Qdrant: %s", e)

    async def query_similar(
        self, origin: str, destination: str, mode: str, k: int = 5
    ) -> list[dict[str, Any]]:
        """Find past trips similar to the proposed route.

        Args:
            origin: Starting point name.
            destination: Ending point name.
            mode: Travel mode.
            k: Number of results to return.

        Returns:
            List of similar trip dictionaries with a 'similarity' score.
        """
        if self.settings.mock_mode:
            logger.info(
                "MOCK_MODE: returning fixture similar trips for %s → %s",
                origin,
                destination,
            )
            return _MOCK_SIMILAR_TRIPS[:k]

        query_text = f"Trip from {origin} to {destination} Mode: {mode}"
        vector = self.model.encode(query_text).tolist()

        try:
            results = await self.qdrant.search(
                collection_name=self.settings.qdrant_collection,
                query_vector=vector,
                limit=k,
            )
            
            parsed_results = []
            for r in results:
                payload = r.payload or {}
                # Score is cosine similarity if distance is COSINE
                parsed_results.append({
                    "id": str(r.id),
                    "origin": payload.get("origin", ""),
                    "destination": payload.get("destination", ""),
                    "mode": payload.get("mode", ""),
                    "delay_minutes": payload.get("delay_minutes", 0),
                    "difficulty_tags": payload.get("difficulty_tags", []),
                    "notes": payload.get("notes", ""),
                    "similarity": float(r.score),
                })
            return parsed_results
            
        except Exception as e:
            logger.error("Failed to query Qdrant: %s", e)
            return []
