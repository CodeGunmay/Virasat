"""Sites routes for Virasat.

Handles heritage site discovery, exploration, and detailed site pages.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from engine.safe_planner import hours_state

# Import from db via sys.path setup in main.py
from db.base import get_db
from db.models import Site, SiteSchedule, SiteSource

router = APIRouter(tags=["sites"])


@router.get("", tags=["sites"])
async def list_sites(
    category: Optional[str] = Query(None, description="Filter by site category"),
    hidden_tier: Optional[bool] = Query(
        None, description="Filter by hidden/heritage tier"
    ),
    open_now: Optional[bool] = Query(
        None, description="Filter sites open at current time"
    ),
    city_id: Optional[int] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
) -> dict:
    """List heritage sites with optional filters."""
    query = select(Site).where(Site.status == "approved")

    if hidden_tier is not None:
        query = query.where(Site.hidden_tier == hidden_tier)

    if city_id:
        query = query.where(Site.city_id == city_id)

    # Execute query
    result = db.execute(query.order_by(Site.name))
    sites = result.scalars().all()
    if category:
        sites = [site for site in sites if category in (site.categories or [])]
    if open_now is not None:
        now = datetime.now(ZoneInfo('Asia/Kolkata'))
        # Unknown hours do not count as definitely open or definitely closed.
        known_status = []
        for site in sites:
            allowed, verified = hours_state(db, site.id, now, now + timedelta(minutes=1))
            if verified and allowed == open_now:
                known_status.append(site)
        sites = known_status

    # Build response
    site_summaries = []
    for site in sites:
        site_summaries.append(
            {
                "id": site.id,
                "name": site.name,
                "categories": site.categories,
                "hidden_tier": site.hidden_tier,
                "visit_minutes": site.visit_minutes,
                "city_id": site.city_id,
                "lat": site.lat,
                "lng": site.lng,
                "summary": site.summary,
                "confidence": site.confidence,
                "hours_verified": bool(db.query(SiteSchedule.id).filter(SiteSchedule.site_id == site.id).first()),
            }
        )

    total = len(sites)

    return {"items": site_summaries, "total": total, "page": 1, "page_size": total}


@router.get("/{site_id}", tags=["sites"])
async def get_site_detail(
    site_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Get detailed information about a heritage site."""
    query = select(Site).where(Site.id == site_id, Site.status == 'approved')
    result = db.execute(query)
    site = result.scalar_one_or_none()

    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    # Get schedules
    sched_query = select(SiteSchedule).where(SiteSchedule.site_id == site_id)
    sched_result = db.execute(sched_query)
    schedules = sched_result.scalars().all()

    # Get sources
    src_query = select(SiteSource).where(SiteSource.site_id == site_id)
    src_result = db.execute(src_query)
    sources = src_result.scalars().all()

    # Format schedules
    schedule_list = []
    for s in schedules:
        schedule_list.append(
            {
                "weekday": s.weekday,
                "open": s.open,
                "close": s.close,
            }
        )

    # Format sources
    source_list = []
    for s in sources:
        source_list.append({"url": s.url, "title": s.title, "accessed_on": None})

    return {
        "id": site.id,
        "name": site.name,
        "categories": site.categories,
        "hidden_tier": site.hidden_tier,
        "visit_minutes": site.visit_minutes,
        "summary": site.summary,
        "why_it_matters": site.why_it_matters,
        "dress_notes": site.dress_notes,
        "location": {"lat": site.lat, "lng": site.lng},
        "status": site.status,
        "confidence": site.confidence,
        "last_verified_on": None,  # site.last_verified_on.isoformat() if site.last_verified_on else None,
        "schedules": schedule_list,
        "sources": source_list,
        "city_id": site.city_id,
    }
