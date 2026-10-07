"""Unit tests for the LangGraph agent workflow."""

from __future__ import annotations

import pytest

from app.agents.graph import create_agent_graph
from app.agents.state import AgentState


@pytest.mark.asyncio
async def test_agent_graph_full_success_mock() -> None:
    """Test the graph execution end-to-end using mock mode."""
    graph = create_agent_graph()
    
    initial_state: AgentState = {
        "origin_query": "Times Square",
        "destination_query": "JFK Airport",
        "mode": "driving",
        "origin_resolved": None,
        "destination_resolved": None,
        "base_routes": [],
        "scored_routes": [],
        "errors": [],
    }
    
    # Run the graph
    result = await graph.ainvoke(initial_state)
    
    # Assertions
    assert not result["errors"]
    assert result["origin_resolved"]["place_id"] == "mock_times_square"
    assert result["destination_resolved"]["place_id"] == "mock_jfk"
    assert len(result["base_routes"]) > 0
    assert len(result["scored_routes"]) > 0
    
    # Check that scoring worked
    scored = result["scored_routes"][0]
    assert "difficulty_score" in scored
    assert "reasoning" in scored


@pytest.mark.asyncio
async def test_agent_graph_resolve_failure() -> None:
    """Test the graph stops early if location resolution fails (mock bad inputs or missing logic)."""
    graph = create_agent_graph()
    
    initial_state: AgentState = {
        "origin_query": "Unresolvable Place xyz",
        "destination_query": "Another unresolvable place",
        "mode": "driving",
        "origin_resolved": None,
        "destination_resolved": None,
        "base_routes": [],
        "scored_routes": [],
        "errors": [],
    }
    
    # In mock mode, the simple substring match won't find these
    result = await graph.ainvoke(initial_state)
    
    assert result["origin_resolved"] is None or result["destination_resolved"] is None
    assert "base_routes" not in result or not result["base_routes"]
    assert "scored_routes" not in result or not result["scored_routes"]
