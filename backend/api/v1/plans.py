"""Planning routes for Virasat.

Handles heritage walk planning and mid-walk re-optimization.

Routes:
  POST /plans            - Create a new heritage walk plan
  POST /plans/replan     - Re-plan mid-walk with current state
  GET  /plans/{plan_id}  - Get a saved plan (placeholder)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, root_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from db.base import get_db
from db.models import Site, User, Route
from engine.safe_planner import make_plan


router = APIRouter(tags=["plans"])


# ─── Pydantic models for request/response ───────────────────────────────────


class InterestWeights(BaseModel):
    """Weights for different heritage interest categories.

    Users select which types of heritage sites interest them.
    Weights are applied during route planning.
    """

    sultanate: float = 1.0
    temples_jain: float = 1.0
    pols_living: float = 1.0
    markets_food: float = 1.0
    colonial_industrial: float = 1.0
    hidden: float = 0.5  # bonus for lesser-known sites

    class Config:
        extra = "allow"


class PlanRequest(BaseModel):
    """Request body for creating a new walk plan.

    Accepts constraints and returns an optimized itinerary with
    arrival/departure times, reasons for each stop, and route geometry.
    """

    start_lat: float = Field(..., description="Starting latitude")
    start_lng: float = Field(..., description="Starting longitude")
    start_time: datetime = Field(
        ..., description="Start datetime (Asia/Kolkata TZ)"
    )
    end_time: Optional[datetime] = Field(
        None, description="End/return datetime (optional, Asia/Kolkata TZ)"
    )
    duration_minutes: Optional[int] = Field(
        None,
        description="Optional duration in minutes if no fixed end time",
        gt=0,
    )
    weekday: Optional[str] = Field(
        None, description="Weekday name (e.g. Monday, Tuesday), defaults to current"
    )
    interests: Optional[Dict[str, float]] = Field(
        None,
        description="Interest weights per category; defaults to balanced weights",
    )
    pace: str = Field(
        "normal", description="Walking pace: normal or gentle"
    )
    hidden_preference: float = Field(
        0.5,
        description="Hidden heritage preference scaling (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    leg_cap_minutes: Optional[int] = Field(
        None, gt=0,
        description="Maximum walking leg in minutes (optional)",
    )
    rest_minutes: Optional[int] = Field(
        None, ge=0, le=120, description="Rest minutes between stops (optional)"
    )

    @root_validator(skip_on_failure=True)
    def require_time_budget(cls, values):
        if values.get("duration_minutes") is None and values.get("end_time") is None:
            raise ValueError("Provide duration_minutes or end_time")
        return values


class ReplanRequest(BaseModel):
    """Request body for mid-walk re-planning.

    Accepts current state and returns a new plan with a diff.
    """

    current_lat: float = Field(..., description="Current latitude")
    current_lng: float = Field(..., description="Current longitude")
    current_time: datetime = Field(
        ..., description="Current time (Asia/Kolkata TZ)"
    )
    visited_ids: List[int] = Field(
        default_factory=list,
        description="IDs of already-visited stops (must not be re-added)",
    )
    skipped_ids: List[int] = Field(
        default_factory=list,
        description="IDs of stops the user wants to skip",
    )
    locked_ids: List[int] = Field(
        default_factory=list,
        description="IDs of must-include stops that must be preserved",
    )
    new_end_time: Optional[datetime] = Field(
        None, description="Updated end time, or None to keep original"
    )
    new_duration: Optional[int] = Field(
        None, description="Updated duration in minutes, or None"
    )
    previous_stop_ids: List[int] = Field(default_factory=list)
    interests: Dict[str, float] = Field(default_factory=dict)
    pace: str = "normal"
    hidden_preference: float = Field(0.5, ge=0, le=1)


class PlanStop(BaseModel):
    """Individual stop in a planned walk."""

    site_id: int = Field(..., description="Heritage site ID")
    visit_minutes: int = Field(30, description=" planned visit duration")
    walking_minutes: float = Field(
        ..., description="Walking time from previous stop (or start)"
    )
    reason: str = Field("interest_match", description="Why this stop was included")
    reason_codes: List[str] = Field(
        default_factory=lambda: ["interest_match"], description="Machine-readable reason codes"
    )
    lat: float = Field(..., description="Site latitude")
    lng: float = Field(..., description="Site longitude")


class PlanResponse(BaseModel):
    """Response body for a planned walk.

    Contains the ordered stops, timeline, totals, and explanation codes.
    """

    stops: List[PlanStop]
    total_duration_minutes: float
    finish_time: datetime
    predicted_completion: datetime
    walking_minutes: float
    visiting_minutes: float
    reasons: List[Dict[str, Any]]
    route_geometry: Optional[List[Dict[str, Any]]] = None
    engine_notes: str = ""
    diff: Optional[Dict[str, Any]] = None


# ─── API Routes ────────────────────────────────────────────────────────-----


@router.post("", response_model=PlanResponse, tags=["plans"])
async def create_plan(
    request: PlanRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Create a new heritage walk plan.

    Accepts constraints and returns an optimized itinerary with
    arrival/departure times, reasons for each stop, and route geometry.
    """
    # Build interest weights
    weights = InterestWeights(**(request.interests or {}))

    # Get candidate sites from the database
    # For now, use a basic query; in production, this would be more sophisticated
    stmt = db.query(Site).filter(Site.status == "approved")
    candidate_sites = stmt.all()

    # Run the route optimizer
    plan_result = make_plan(
        db,
        start_lat=request.start_lat,
        start_lng=request.start_lng,
        start_time=request.start_time,
        duration_minutes=request.duration_minutes or int((request.end_time-request.start_time).total_seconds()/60),
        interests={
            "sultanate": weights.sultanate,
            "temples_jain": weights.temples_jain,
            "pols_living": weights.pols_living,
            "markets_food": weights.markets_food,
            "colonial_industrial": weights.colonial_industrial,
            "hidden": weights.hidden,
        },
        pace=request.pace,
        hidden_preference=request.hidden_preference,
        leg_cap_minutes=request.leg_cap_minutes,
        rest_minutes=request.rest_minutes or 0,
    )

    # Format response into PlanStop objects
    stops = []
    for i, stop in enumerate(plan_result["stops"]):
        stops.append(
            {
                "site_id": stop["site_id"],
                "visit_minutes": stop.get("visit_minutes", 30),
                "walking_minutes": stop.get("walking_minutes", 0),
                "reason": stop.get("reason", "interest_match"),
                "reason_codes": stop.get("reason_codes", ["interest_match"]),
                "lat": stop.get("lat", 0.0),
                "lng": stop.get("lng", 0.0),
            }
        )

    # Build reasons list
    reasons = plan_result.get("reasons", [])

    # Format finish time
    finish_dt = plan_result["finish_time"]
    pred_comp_dt = plan_result["predicted_completion"]

    return {
        "stops": stops,
        "total_duration_minutes": plan_result["total_minutes"],
        "finish_time": finish_dt,
        "predicted_completion": pred_comp_dt,
        "walking_minutes": plan_result.get("walking_minutes", 0),
        "visiting_minutes": plan_result.get("visiting_minutes", 0),
        "reasons": reasons,
        "route_geometry": plan_result.get("geometry"),
        "engine_notes": plan_result.get("engine_notes", ""),
    }


@router.post("/replan", response_model=PlanResponse, tags=["plans", "replan"])
async def replan_walk(
    request: ReplanRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Re-optimize a walk mid-way based on current state.

    Accepts current position, current time, visited/skipped/locked stops,
    and a new end time or duration. Returns a new plan plus a diff
    against the previous plan.

    Key behaviors:
    - Visited stops are never re-added
    - Skipped stops are never added
    - Locked stops are always included or the response says which other
      stops it would drop to make room
    - The response includes a before/after diff with reasons
    """
    # Run the re-planner
    budget = request.new_duration
    if budget is None and request.new_end_time is not None:
        budget = int((request.new_end_time-request.current_time).total_seconds()/60)
    if budget is None or budget <= 0:
        raise HTTPException(status_code=422, detail="Provide a positive remaining duration or future end time")
    result = make_plan(db, start_lat=request.current_lat, start_lng=request.current_lng,
                       start_time=request.current_time, duration_minutes=budget,
                       interests=request.interests, pace=request.pace,
                       hidden_preference=request.hidden_preference,
                       visited=request.visited_ids, skipped=request.skipped_ids,
                       locked=request.locked_ids)

    # Format response
    stops = []
    for stop in result["stops"]:
        stops.append(
            {
                "site_id": stop["site_id"],
                "visit_minutes": stop.get("visit_minutes", 30),
                "walking_minutes": stop.get("walking_minutes", 0),
                "reason": stop.get("reason", "interest_match"),
                "reason_codes": stop.get("reason_codes", ["interest_match"]),
                "lat": stop.get("lat", 0.0),
                "lng": stop.get("lng", 0.0),
            }
        )

    # Build reasons
    reasons = result["reasons"]
    old = request.previous_stop_ids
    new = [s["site_id"] for s in stops]
    diff = {"added": [x for x in new if x not in old],
            "removed": [x for x in old if x not in new and x not in request.visited_ids],
            "reordered": [x for x in new if x in old and old.index(x) != new.index(x)]}

    return {
        "stops": stops,
        "total_duration_minutes": result["total_minutes"],
        "finish_time": result["finish_time"],
        "predicted_completion": result["predicted_completion"],
        "walking_minutes": result["walking_minutes"],
        "visiting_minutes": result["visiting_minutes"],
        "reasons": reasons,
        "route_geometry": result.get("geometry"),
        "engine_notes": result.get("engine_notes", ""),
        "diff": diff,
    }
