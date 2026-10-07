"""State definitions for the LangGraph workflow."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict):
    """The state dictionary passed between nodes in the graph."""
    # Inputs
    origin_query: str
    destination_query: str
    mode: str
    
    # Resolved locations (from Places API)
    origin_resolved: dict[str, Any] | None
    destination_resolved: dict[str, Any] | None
    
    # Base routes (from OpenRouteService)
    base_routes: list[dict[str, Any]]
    
    # Processed and scored routes
    # Using Annotated with operator.add to append if needed, but for simple overwrites
    # we can just use a regular list. We'll stick to a simple list.
    scored_routes: list[dict[str, Any]]
    
    # Any errors encountered during execution
    errors: list[str]
