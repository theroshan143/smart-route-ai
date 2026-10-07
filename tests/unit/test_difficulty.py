"""Unit tests for the difficulty scoring node."""

from __future__ import annotations

from app.agents.nodes.difficulty import calculate_difficulty_score


def test_calculate_difficulty_score_no_past_trips() -> None:
    """If no past trips, should return a default moderate score."""
    route = {"distance_m": 5000, "duration_s": 1500, "road_types": ["street"]}
    result = calculate_difficulty_score(route, [])
    assert result["score"] == 3.0
    assert result["detected_tags"] == []
    assert "No historical context" in result["reasoning"]


def test_calculate_difficulty_score_mock_llm() -> None:
    """Test the difficulty scoring with a mock LLM (no API keys provided)."""
    route = {"distance_m": 5000, "duration_s": 1500, "road_types": ["street"]}
    past_trips = [
        {"delay_minutes": 15, "notes": "Heavy traffic", "similarity": 0.9},
        {"delay_minutes": 30, "notes": "Rain and traffic", "similarity": 0.8},
    ]
    
    # In MOCK_MODE, we return the mock response from `_MockLLM`.
    result = calculate_difficulty_score(route, past_trips)
    assert result["score"] == 7.5
    assert "Mocked" in result["reasoning"]
    assert "traffic" in result["detected_tags"]
    assert "weather" in result["detected_tags"]
