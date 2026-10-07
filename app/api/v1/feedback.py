"""API endpoints for feedback."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.core.logging import get_logger
from app.db.engine import get_db_session
from app.models.feedback import Feedback

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback_in: FeedbackCreate,
    session: AsyncSession = Depends(get_db_session),
) -> Feedback:
    """Submit user feedback for a suggested route."""
    logger.info("Received feedback for route %s: %s stars", feedback_in.route_suggestion_id, feedback_in.rating)
    
    try:
        feedback = Feedback(
            id=str(uuid.uuid4()),
            route_suggestion_id=feedback_in.route_suggestion_id,
            rating=feedback_in.rating,
            comment=feedback_in.comment,
            difficulties_faced=feedback_in.difficulties_faced,
            created_at=datetime.now(timezone.utc),
        )
        
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        
        return feedback
    except Exception as e:
        logger.error("Failed to save feedback: %s", e)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not save feedback")
