import uuid
from dataclasses import dataclass
from typing import Optional
from sqlalchemy.orm import Session
from app.models.evidence import TaskException
from app.models.enums import ExceptionPriority


@dataclass
class QuarantineTicketPayload:
    case_id: uuid.UUID
    failed_gate: int
    exception_type: str
    net_equity: float
    resolution_notes: str
    assigned_to: str = "Triage Specialist"


class TaskExceptionRouter:
    """Routes pipeline exceptions to the Tasks & Exceptions database.
    SLA Assignment Standard:
    - Critical (Net Equity > $200k): 4-Hour Resolution SLA
    - High (Net Equity $100k-$200k): 24-Hour Resolution SLA
    - Normal (Net Equity < $100k): 24-Hour Resolution SLA
    """

    @staticmethod
    def calculate_priority(net_equity: float) -> ExceptionPriority:
        if net_equity > 200000.0:
            return ExceptionPriority.CRITICAL
        elif net_equity >= 100000.0:
            return ExceptionPriority.HIGH
        else:
            return ExceptionPriority.NORMAL

    @classmethod
    def create_quarantine_ticket(
        cls,
        db: Session,
        payload: QuarantineTicketPayload
    ) -> TaskException:
        """Persists a new quarantined exception entry to prevent bad data dispatch."""
        priority = cls.calculate_priority(payload.net_equity)
        sla_target = "4 Hours" if priority == ExceptionPriority.CRITICAL else "24 Hours"

        exception_ticket = TaskException(
            case_id=payload.case_id,
            failed_gate=payload.failed_gate,
            exception_type=payload.exception_type,
            priority=priority,
            status="OPEN",
            assigned_to=payload.assigned_to,
            resolution_notes=f"SLA Target: {sla_target}. Reason: {payload.resolution_notes}"
        )

        db.add(exception_ticket)
        db.commit()
        db.refresh(exception_ticket)
        return exception_ticket
