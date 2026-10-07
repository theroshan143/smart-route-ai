"""RouteSuggestion ORM model — persists route suggestion results."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RouteSuggestion(Base):
    """A saved route suggestion with full result payload."""

    __tablename__ = "route_suggestions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    origin: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="driving")
    preference: Mapped[str] = mapped_column(String(20), nullable=False, default="balanced")
    # Full JSON result blob (routes, scores, explanation)
    routes_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<RouteSuggestion {self.id[:8]}… {self.origin} → {self.destination}>"
