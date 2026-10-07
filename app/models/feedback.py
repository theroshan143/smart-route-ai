"""Feedback ORM model — user feedback on route suggestions."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Feedback(Base):
    """User feedback on a specific route suggestion."""

    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    route_suggestion_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("route_suggestions.id"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    # Store difficulties as comma-separated for SQLite compat
    difficulties_faced_str: Mapped[str] = mapped_column(Text, default="")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    @property
    def difficulties_faced(self) -> list[str]:
        """Parse comma-separated difficulties into a list."""
        if not self.difficulties_faced_str:
            return []
        return [d.strip() for d in self.difficulties_faced_str.split(",") if d.strip()]

    @difficulties_faced.setter
    def difficulties_faced(self, difficulties: list[str]) -> None:
        """Store difficulties as comma-separated string."""
        self.difficulties_faced_str = ",".join(difficulties)

    def __repr__(self) -> str:
        return f"<Feedback {self.id[:8]}… rating={self.rating}>"
