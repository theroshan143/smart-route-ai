"""Seed script to generate synthetic trip data for the database and vector store."""

import asyncio
import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.engine import create_tables, engine
from app.models.trip import Trip
from app.services.pattern_store import PatternStore

setup_logging("INFO")
logger = get_logger("seed_data")

CITY_PAIRS = [
    ("Times Square", 40.7580, -73.9855, "JFK Airport", 40.6413, -73.7781),
    ("Central Park", 40.7812, -73.9665, "Empire State Building", 40.7484, -73.9857),
    ("Brooklyn Bridge", 40.7061, -73.9969, "Statue of Liberty", 40.6892, -74.0445),
    ("Wall Street", 40.7074, -74.0113, "Grand Central", 40.7527, -73.9772),
]

MODES = ["driving", "walking", "cycling"]

DIFFICULTIES = ["traffic", "bad_roads", "crowds", "weather", "construction"]


def generate_synthetic_trip() -> Trip:
    """Generate a random trip record."""
    origin_name, origin_lat, origin_lng, dest_name, dest_lat, dest_lng = random.choice(CITY_PAIRS)
    mode = random.choice(MODES)

    # Base duration
    expected = random.randint(600, 3600)
    delay = random.choice([0, 0, 0, 5, 10, 15, 30, 45, 60])
    actual = expected + (delay * 60)

    # Random tags
    tags = []
    if delay > 15:
        tags.append(random.choice(["traffic", "weather"]))
    if random.random() > 0.7:
        tags.append(random.choice(DIFFICULTIES))
    tags = list(set(tags))

    # Notes based on tags
    notes = ""
    if "traffic" in tags:
        notes += "Heavy traffic. "
    if "weather" in tags:
        notes += "Raining heavily. "
    if "construction" in tags:
        notes += "Road works blocked two lanes. "

    trip = Trip(
        id=str(uuid.uuid4()),
        origin=origin_name,
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination=dest_name,
        destination_lat=dest_lat,
        destination_lng=dest_lng,
        mode=mode,
        departure_time=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        actual_duration_s=actual,
        expected_duration_s=expected,
        delay_minutes=delay,
        notes=notes.strip() if notes else None,
    )
    trip.difficulty_tags = tags
    return trip


async def main() -> None:
    settings = get_settings()
    if settings.mock_mode:
        logger.warning("MOCK_MODE is true, script will only write to local dev.db")

    await create_tables()

    store = PatternStore()
    await store.initialize()

    logger.info("Generating 50 synthetic trips...")
    trips = [generate_synthetic_trip() for _ in range(50)]

    # 1. Insert into DB
    session_factory = __import__("app.db.engine", fromlist=["async_session_factory"]).async_session_factory
    async with session_factory() as session:
        # Clear existing
        await session.execute(text("DELETE FROM trips"))
        
        # Insert new
        session.add_all(trips)
        await session.commit()
    logger.info("Saved 50 trips to database.")

    # 2. Embed into Qdrant
    if not settings.mock_mode:
        logger.info("Embedding trips into Qdrant (this may take a minute)...")
        for i, trip in enumerate(trips):
            if i > 0 and i % 10 == 0:
                logger.info("  embedded %d/50", i)
            
            trip_dict = {
                "id": trip.id,
                "origin": trip.origin,
                "destination": trip.destination,
                "mode": trip.mode,
                "delay_minutes": trip.delay_minutes,
                "difficulty_tags": trip.difficulty_tags,
                "notes": trip.notes,
            }
            await store.store_trip(trip_dict)
        logger.info("Finished embedding trips.")
    else:
        logger.info("Skipped Qdrant embedding due to MOCK_MODE=true.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
