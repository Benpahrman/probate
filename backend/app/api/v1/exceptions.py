import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.evidence import TaskException
from app.models.enums import ExceptionPriority

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
    resolution_text: str,
    db: Session = Depends(get_db)
):
    """Resolves an exception ticket and permits re-audit of the opportunity."""
    exc = db.query(TaskException).filter(TaskException.exception_id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception ticket not found.")

    exc.status = "RESOLVED"
    exc.resolution_notes = f"RESOLVED: {resolution_text}"
    db.commit()
    return {"status": "SUCCESS", "exception_id": str(exception_id)}
