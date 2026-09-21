"""
Exceptions & Tasks API Routes
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from gieni_os.database.connection import get_db
from gieni_os.database.models import ExceptionModel, OpportunityModel
from gieni_os.api.deps import get_current_user

router = APIRouter(prefix="/exceptions", tags=["Exceptions & Tasks"])

class ExceptionCreate(BaseModel):
    id: Optional[str] = None
    opportunity_id: str
    type: str
    severity: str = "MEDIUM"
    status: str = "OPEN"
    assignee: Optional[str] = None
    notes: Optional[str] = None

class ExceptionUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    assignee: Optional[str] = None
    notes: Optional[str] = None

class ExceptionResponse(BaseModel):
    id: str
    opportunity_id: str
    type: str
    severity: str
    status: str
    assignee: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[ExceptionResponse])
def list_exceptions(
    status: Optional[str] = None,
    type: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ExceptionModel)
    if status:
        query = query.filter(ExceptionModel.status == status)
    if type:
        query = query.filter(ExceptionModel.type == type)
    if opportunity_id:
        query = query.filter(ExceptionModel.opportunity_id == opportunity_id)
    return query.all()

@router.post("", response_model=ExceptionResponse, status_code=status.HTTP_201_CREATED)
def create_exception(
    exc_in: ExceptionCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == exc_in.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail=f"Opportunity '{exc_in.opportunity_id}' not found.")

    exc = ExceptionModel(
        id=exc_in.id,
        opportunity_id=exc_in.opportunity_id,
        type=exc_in.type,
        severity=exc_in.severity,
        status=exc_in.status,
        assignee=exc_in.assignee,
        notes=exc_in.notes
    )
    db.add(exc)
    db.commit()
    db.refresh(exc)
    return exc

@router.put("/{exception_id}", response_model=ExceptionResponse)
def update_exception(
    exception_id: str,
    exc_in: ExceptionUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    exc = db.query(ExceptionModel).filter(ExceptionModel.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found.")

    if exc_in.status is not None:
        exc.status = exc_in.status
    if exc_in.severity is not None:
        exc.severity = exc_in.severity
    if exc_in.assignee is not None:
        exc.assignee = exc_in.assignee
    if exc_in.notes is not None:
        exc.notes = exc_in.notes

    db.commit()
    db.refresh(exc)
    return exc
