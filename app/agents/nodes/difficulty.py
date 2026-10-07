"""Difficulty scoring logic using LangChain and LLMs."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm() -> Any:
    """Initialize the LLM based on configuration."""
    settings = get_settings()

    # Use a dummy mock model if mock_mode is active and no key is provided
    if settings.mock_mode and not settings.llm_api_key:
        return _MockLLM()

    if settings.llm_provider == "google":
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            temperature=0.0,
        )
    # Default to OpenAI
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        temperature=0.0,
    )


class _MockLLM:
    """A mock LLM for testing when MOCK_MODE is enabled without keys."""
    def invoke(self, messages: list[Any]) -> Any:
        class MockMessage:
            content = '{"score": 7.5, "reasoning": "Mocked: High traffic and rain.", "detected_tags": ["traffic", "weather"]}'
        return MockMessage()


def calculate_difficulty_score(route: dict[str, Any], past_trips: list[dict[str, Any]]) -> dict[str, Any]:
    """Examine base routes vs past trips to determine a difficulty score.

    Args:
        route: A single route dictionary (e.g. from OpenRouteService).
        past_trips: A list of semantically similar past trips from Qdrant.

    Returns:
        A dictionary containing:
        - score: Float (0-10) where 10 is very difficult.
        - reasoning: String explanation.
        - detected_tags: List of strings (e.g. "traffic", "weather").
    """
    settings = get_settings()
    llm = get_llm()

    # If there are no past trips, default to a moderate score based solely on distance/duration
    if not past_trips:
        return {
            "score": 3.0,
            "reasoning": "No historical context available. Standard route assumed.",
            "detected_tags": [],
        }

    # Aggregate historical difficulties
    historical_notes = []
    avg_delay = 0.0
    for trip in past_trips:
        avg_delay += trip.get("delay_minutes", 0)
        notes = trip.get("notes")
        if notes:
            historical_notes.append(f"- {notes} (similarity: {trip.get('similarity', 0.0):.2f})")
    
    avg_delay = avg_delay / len(past_trips) if past_trips else 0.0

    prompt = f"""You are a smart travel routing assistant. Your task is to calculate a difficulty score (0-10) for a proposed route based on historical trip experiences on similar routes.

Proposed Route:
- Distance: {route.get('distance_m', 0) / 1000:.1f} km
- Expected Duration: {route.get('duration_s', 0) / 60:.1f} mins
- Route type: {", ".join(route.get('road_types', []))}

Historical Experiences on Similar Routes (Avg Delay: {avg_delay:.1f} mins):
{chr(10).join(historical_notes) if historical_notes else "No specific notes."}

Analyze the historical notes and delays. Return a JSON object with:
1. "score": a number from 0 to 10 (10 being extremely difficult/delayed).
2. "reasoning": a concise string explaining the score.
3. "detected_tags": a list of string tags (e.g., "traffic", "weather", "construction", "crowds") based on the historical notes.

Output exactly valid JSON and nothing else.
"""

    messages = [
        SystemMessage(content="You return only JSON without markdown formatting blocks."),
        HumanMessage(content=prompt),
    ]

    try:
        response = llm.invoke(messages)
        # Parse the JSON response
        # Handle cases where the LLM might wrap the output in markdown code blocks
        raw_content = response.content.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
            
        result = json.loads(raw_content.strip())
        
        # Ensure schema
        return {
            "score": float(result.get("score", 5.0)),
            "reasoning": result.get("reasoning", "No reasoning provided."),
            "detected_tags": result.get("detected_tags", []),
        }
    except Exception as e:
        logger.error("Error calling LLM for difficulty score: %s", e)
        # Fallback heuristic if LLM fails
        return {
            "score": min(10.0, 3.0 + (avg_delay / 15.0)),
            "reasoning": "Fallback calculation due to LLM error. Based on average historical delay.",
            "detected_tags": ["error"],
        }
