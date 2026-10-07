"""Trip ORM model — records of past travel experiences."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trip(Base):
    """A recorded trip with timing and difficulty information."""

    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_lat: Mapped[float] = mapped_column(Float, nullable=False)
    destination_lng: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="driving")
    departure_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    actual_duration_s: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_duration_s: Mapped[int] = mapped_column(Integer, nullable=False)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    # Store difficulty tags as comma-separated for SQLite compat
    difficulty_tags_str: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @property
    def difficulty_tags(self) -> list[str]:
        """Parse comma-separated tags into a list."""
        if not self.difficulty_tags_str:
            return []
        return [t.strip() for t in self.difficulty_tags_str.split(",") if t.strip()]

    @difficulty_tags.setter
    def difficulty_tags(self, tags: list[str]) -> None:
        """Store tags as comma-separated string."""
        self.difficulty_tags_str = ",".join(tags)

    def __repr__(self) -> str:
        return f"<Trip {self.origin} → {self.destination} ({self.mode})>"
