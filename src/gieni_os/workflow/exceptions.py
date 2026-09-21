"""
Gieni OS Task Exception Router
Routes pipeline gate failures to the Tasks & Exceptions database with
SLA-tiered priority assignment.

Transplanted from backend/app/services/exceptions.py.
Imports rewritten: app.models.* → gieni_os.models.orm / gieni_os.domain.enums
"""

import uuid
from sqlalchemy.orm import Session
from gieni_os.models.orm import TaskException
from gieni_os.domain.enums import ExceptionPriority


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
        case_id: uuid.UUID,
        failed_gate: int,
        exception_type: str,
        net_equity: float,
        resolution_notes: str,
        assigned_to: str = "Triage Specialist"
    ) -> TaskException:
        """Persists a new quarantined exception entry to prevent bad data dispatch."""
        priority = cls.calculate_priority(net_equity)

        exception_ticket = TaskException(
            case_id=case_id,
            failed_gate=failed_gate,
            exception_type=exception_type,
            priority=priority,
            status="OPEN",
            assigned_to=assigned_to,
            resolution_notes=f"SLA Target: {'4 Hours' if priority == ExceptionPriority.CRITICAL else '24 Hours'}. Reason: {resolution_notes}"
        )

        db.add(exception_ticket)
        db.commit()
        db.refresh(exception_ticket)
        return exception_ticket
