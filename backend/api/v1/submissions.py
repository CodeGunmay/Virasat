"""Source-backed community heritage contributions. Nothing goes public before review."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db.base import get_db
from db.models import Submission
from core.security import require_user

router = APIRouter(tags=['submissions'])

class SubmissionIn(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    category: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=20, max_length=3000)
    source_url: str = Field(pattern=r'^https?://', max_length=500)
    lat: float = Field(ge=-90,le=90)
    lng: float = Field(ge=-180,le=180)
    visit_minutes: int = Field(default=30,ge=5,le=240)

@router.post('', status_code=201)
def submit_site(data: SubmissionIn, db: Session=Depends(get_db), user: dict=Depends(require_user)):
    if user['role'] not in ('visitor','contributor','moderator'):
        raise HTTPException(403,'Account cannot submit contributions')
    record=Submission(user_id=user['id'], status='pending', proposed_data=data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {'id':record.id,'status':'pending'}

@router.get('/mine')
def mine(db: Session=Depends(get_db), user: dict=Depends(require_user)):
    records=db.query(Submission).filter(Submission.user_id==user['id']).order_by(Submission.created_at.desc()).all()
    return {'submissions':[{'id':s.id,'status':s.status,'name':s.proposed_data.get('name'),'moderator_note':s.moderator_note} for s in records]}

@router.get('/{submission_id}')
def detail(submission_id: int, db: Session=Depends(get_db), user: dict=Depends(require_user)):
    record=db.get(Submission,submission_id)
    if not record:
        raise HTTPException(404,'Submission not found')
    if user['role']!='moderator' and record.user_id!=user['id']:
        raise HTTPException(403,'Not permitted')
    return {'id':record.id,'status':record.status,'proposed_data':record.proposed_data,'moderator_note':record.moderator_note}
