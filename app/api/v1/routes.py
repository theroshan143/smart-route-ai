"""API endpoints for routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.graph import create_agent_graph
from app.agents.state import AgentState
from app.api.schemas.routes import RouteSuggestRequest, RouteSuggestResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()
_agent_graph = create_agent_graph()


@router.post("/suggest", response_model=RouteSuggestResponse)
async def suggest_routes(request: RouteSuggestRequest) -> RouteSuggestResponse:
    """Get smart route suggestions for a given origin, destination, and mode.
    
    This endpoint uses an AI agent to resolve the locations, fetch potential
    routes, and score them against semantic trip history to find the easiest paths.
    """
    logger.info("Suggesting routes: %s -> %s (%s)", request.origin, request.destination, request.mode)
    
    initial_state: AgentState = {
        "origin_query": request.origin,
        "destination_query": request.destination,
        "mode": request.mode,
        "origin_resolved": None,
        "destination_resolved": None,
        "base_routes": [],
        "scored_routes": [],
        "errors": [],
    }
    
    try:
        # Run the LangGraph workflow
        final_state = await _agent_graph.ainvoke(initial_state)
    except Exception as e:
        logger.error("Agent graph execution failed: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error during route calculation")
        
    errors = final_state.get("errors")
    if not final_state.get("scored_routes"):
        err_msg = errors[0] if errors else "Could not resolve locations or find any routes."
        raise HTTPException(status_code=400, detail=f"Failed to suggest route: {err_msg}")

    return RouteSuggestResponse(
        origin_resolved=final_state.get("origin_resolved"),
        destination_resolved=final_state.get("destination_resolved"),
        routes=final_state.get("scored_routes", []),
        errors=errors if errors else None,
    )
