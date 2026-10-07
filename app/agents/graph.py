"""LangGraph workflow definition for the smart route agent."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.nodes.difficulty import calculate_difficulty_score
from app.agents.state import AgentState
from app.services.pattern_store import PatternStore
from app.services.places_service import PlacesService
from app.services.routing_service import RoutingService


async def resolve_locations(state: AgentState) -> dict[str, Any]:
    """Resolve origin and destination queries using Places API."""
    places = PlacesService()
    
    try:
        origins = await places.search(state["origin_query"], limit=1)
        destinations = await places.search(state["destination_query"], limit=1)
        
        return {
            "origin_resolved": origins[0] if origins else None,
            "destination_resolved": destinations[0] if destinations else None,
        }
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"Location resolution failed: {e}"]}


async def fetch_routes(state: AgentState) -> dict[str, Any]:
    """Fetch base routes using OpenRouteService."""
    if not state.get("origin_resolved") or not state.get("destination_resolved"):
        return {"errors": state.get("errors", []) + ["Missing resolved locations for routing."]}

    routing = RoutingService()
    try:
        routes = await routing.get_directions(
            origin_lat=state["origin_resolved"]["lat"],
            origin_lng=state["origin_resolved"]["lng"],
            dest_lat=state["destination_resolved"]["lat"],
            dest_lng=state["destination_resolved"]["lng"],
            mode=state["mode"],
            alternatives=3,
        )
        return {"base_routes": routes}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"Routing failed: {e}"]}


async def score_routes(state: AgentState) -> dict[str, Any]:
    """Analyze base routes and score them based on past semantic patterns."""
    if not state.get("base_routes"):
        return {"errors": state.get("errors", []) + ["No base routes to score."]}

    store = PatternStore()
    
    scored = []
    try:
        # Retrieve context once for the OD pair to save time,
        # or we could retrieve it for each route if they vastly differed.
        # Here we just fetch general past trips for this OD pair and mode.
        origin_name = state["origin_resolved"]["name"]
        dest_name = state["destination_resolved"]["name"]
        
        past_trips = await store.query_similar(
            origin=origin_name,
            destination=dest_name,
            mode=state["mode"],
            k=3
        )
        
        for route in state["base_routes"]:
            # Evaluate using LLM + historical data
            evaluation = calculate_difficulty_score(route, past_trips)
            
            # Combine the base route data with the evaluation
            scored_route = dict(route)
            scored_route["difficulty_score"] = evaluation["score"]
            scored_route["reasoning"] = evaluation["reasoning"]
            scored_route["tags"] = evaluation["detected_tags"]
            
            scored.append(scored_route)
            
        # Sort by difficulty score (lowest first)
        scored.sort(key=lambda r: r["difficulty_score"])
        
        return {"scored_routes": scored}
    except Exception as e:
        return {"errors": state.get("errors", []) + [f"Scoring failed: {e}"]}


def route_after_resolve(state: AgentState) -> str:
    """Conditional edge after resolution."""
    if state.get("errors"):
        return "end"
    if not state.get("origin_resolved") or not state.get("destination_resolved"):
        return "end"
    return "fetch_routes"


def route_after_fetch(state: AgentState) -> str:
    """Conditional edge after fetching routes."""
    if state.get("errors") or not state.get("base_routes"):
        return "end"
    return "score_routes"


def create_agent_graph() -> StateGraph:
    """Construct the state graph for the agent."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("resolve_locations", resolve_locations)
    workflow.add_node("fetch_routes", fetch_routes)
    workflow.add_node("score_routes", score_routes)
    
    # Define edges
    workflow.set_entry_point("resolve_locations")
    
    workflow.add_conditional_edges(
        "resolve_locations",
        route_after_resolve,
        {
            "fetch_routes": "fetch_routes",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "fetch_routes",
        route_after_fetch,
        {
            "score_routes": "score_routes",
            "end": END
        }
    )
    
    workflow.add_edge("score_routes", END)
    
    return workflow.compile()
