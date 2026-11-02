"""Moderation routes for Virasat.

Handles the moderation queue, submission approval/rejection, and problem report management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from db.base import get_db
from db.models import Submission, ProblemReport, Site, SiteSource
from core.security import check_role

router = APIRouter(tags=["moderation"])

class DecisionIn(BaseModel):
    decision: str = Field(pattern='^(approve|reject|changes_requested)$')
    moderator_note: str = Field(min_length=5, max_length=2000)


@router.get("/queue", tags=["moderation"], dependencies=[Depends(check_role("moderator"))])
async def get_moderation_queue(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
) -> dict:
    """Get the moderation queue.

    Shows pending submissions and problem reports awaiting review.
    Sorted by creation date (oldest first).
    """
    submissions = db.query(Submission).filter(Submission.status == (status or "pending")).order_by(Submission.created_at).limit(50).all()
    reports = db.query(ProblemReport).filter(ProblemReport.status == "pending").limit(10).all()
    return {
        "submissions": [{"id": s.id, "status": s.status, "name": s.proposed_data.get('name'), "source_url": s.proposed_data.get('source_url')} for s in submissions],
        "reports": [{"id": r.id, "status": r.status, "site_id": r.site_id} for r in reports],
        "message": "Pending reviews",
    }


@router.post("/{submission_id}/decision", tags=["moderation"], dependencies=[Depends(check_role("moderator"))])
async def decide_submission(
    submission_id: int,
    data: DecisionIn,
    db: Session = Depends(get_db),
) -> dict:
    """Make a decision on a submission.

    Approve, reject, or request changes for a submitted heritage site.
    Records who, when, and a note for each state change.
    """
    # Get the submission
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    if submission.status != 'pending':
        raise HTTPException(status_code=409, detail="Submission is no longer pending")

    # Update status
    submission.status = 'approved' if data.decision == 'approve' else ('rejected' if data.decision == 'reject' else 'changes_requested')
    submission.moderator_note = data.moderator_note
    from datetime import datetime
    submission.resolved_at = datetime.now()

    # If approved, create a Site entry
    if data.decision == "approve":
        # Create a new Site entry from the proposed data
        from db.models import Site as SiteModel
        new_site = SiteModel(
            name=submission.proposed_data.get("name", "Unknown"),
            city_id=1,
            lat=submission.proposed_data['lat'],
            lng=submission.proposed_data['lng'],
            categories=[submission.proposed_data['category']],
            hidden_tier=False,
            visit_minutes=submission.proposed_data.get("visit_minutes", 30),
            summary=submission.proposed_data['description'],
            status="approved",
            confidence="low",
        )
        db.add(new_site)
        db.flush()
        db.add(SiteSource(site_id=new_site.id, url=submission.proposed_data['source_url']))
        submission.site_id = new_site.id

    db.commit()
    return {"id": submission.id, "new_status": submission.status, "site_id": submission.site_id}


@router.get("/reports", tags=["moderation"], dependencies=[Depends(check_role("moderator"))])
async def get_problem_reports(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    site_id: Optional[int] = None,
) -> dict:
    """Get problem reports.

    Shows reports about heritage site issues (closed, wrong timings, etc.).
    """
    # Placeholder implementation
    query = db.query(ProblemReport)
    if status:
        query = query.filter(ProblemReport.status == status)
    if site_id:
        query = query.filter(ProblemReport.site_id == site_id)
    reports = query.limit(10).all()
    return {"reports": [{"id": r.id, "status": r.status, "site_id": r.site_id, "type": r.report_type} for r in reports],
            "message": "Problem reports (placeholder)"}
