import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.evidence import TaskException
from app.models.enums import ExceptionPriority
from app.services.exceptions import TaskExceptionRouter

router = APIRouter(prefix="/exceptions", tags=["Tasks & Exceptions"])


class ExceptionResponse(BaseModel):
    exception_id: uuid.UUID
    case_id: uuid.UUID
    case_number: str
    failed_gate: int
    exception_type: str
    priority: ExceptionPriority
    status: str
    resolution_notes: str


@router.get("", response_model=List[ExceptionResponse])
def list_open_exceptions(db: Session = Depends(get_db)):
    """Retrieves all quarantined pipeline exceptions ordered by priority (Critical first)."""
    exceptions = db.query(TaskException).filter(TaskException.status == "OPEN").all()
    return [
        ExceptionResponse(
            exception_id=e.exception_id,
            case_id=e.case_id,
            case_number=e.case.case_number,
            failed_gate=e.failed_gate,
            exception_type=e.exception_type,
            priority=e.priority,
            status=e.status,
            resolution_notes=e.resolution_notes or ""
        ) for e in exceptions
    ]




@router.post("/{exception_id}/resolve")
def resolve_exception(
    exception_id: uuid.UUID,
    resolution_text: str = "",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Resolves an exception ticket and triggers an immediate 6-gate re-audit of the opportunity."""
    result = TaskExceptionRouter.resolve_and_reaudit(
        db=db,
        exception_id=exception_id,
        resolution_text=resolution_text
    )
    if result.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=result.get("message", "Exception ticket not found."))

    return result

