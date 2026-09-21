"""
Workflow Engine API Routes
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from gieni_os.database.connection import get_db
from gieni_os.database.models import WorkflowAuditLogModel
from gieni_os.workflow.engine import (
    WorkflowEngine,
    WorkflowStage,
    InvalidWorkflowTransitionError
)
from gieni_os.api.deps import get_current_user
from gieni_os.api.routes.opportunities import OpportunityResponse

router = APIRouter(prefix="/workflow", tags=["Workflow Engine"])

class TransitionRequest(BaseModel):
    opportunity_id: str
    to_stage: str
    notes: Optional[str] = None

class AuditLogResponse(BaseModel):
    id: str
    opportunity_id: str
    from_stage: str
    to_stage: str
    transitioned_by: str
    timestamp: datetime
    notes: Optional[str]

    model_config = ConfigDict(from_attributes=True)

@router.post("/transition", response_model=OpportunityResponse)
def transition_workflow(
    req: TransitionRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    try:
        opp = WorkflowEngine.transition(
            db=db,
            opportunity_id=req.opportunity_id,
            to_stage=req.to_stage,
            transitioned_by=user.get("username", "System"),
            notes=req.notes
        )
        return opp
    except InvalidWorkflowTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/allowed-transitions/{stage}")
def get_allowed_transitions(stage: str):
    try:
        st = WorkflowStage(stage)
        allowed = WorkflowEngine.ALLOWED_TRANSITIONS.get(st, set())
        return {"current_stage": stage, "allowed_transitions": [s.value for s in allowed]}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown workflow stage: {stage}")

@router.get("/audit-logs/{opportunity_id}", response_model=List[AuditLogResponse])
def get_audit_logs(opportunity_id: str, db: Session = Depends(get_db)):
    return (
        db.query(WorkflowAuditLogModel)
        .filter(WorkflowAuditLogModel.opportunity_id == opportunity_id)
        .order_by(WorkflowAuditLogModel.timestamp.asc())
        .all()
    )
