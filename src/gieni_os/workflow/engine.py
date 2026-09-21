"""
Gieni OS Workflow State Machine & Transition Validator
Enforces deterministic progression across the 9 core workflow states.
"""

from enum import Enum
from typing import Dict, Set, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from gieni_os.database.models import OpportunityModel, WorkflowAuditLogModel

class WorkflowStage(str, Enum):
    INGESTED = "INGESTED"
    NEW = "NEW"
    PROPERTY_MATCH = "PROPERTY_MATCH"
    OWNERSHIP = "OWNERSHIP"
    AUTHORITY = "AUTHORITY"
    ENRICHMENT = "ENRICHMENT"
    SCORING = "SCORING"
    QC = "QC"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"
    EXCEPTION = "EXCEPTION"

class InvalidWorkflowTransitionError(Exception):
    def __init__(self, from_stage: str, to_stage: str, message: str = ""):
        self.from_stage = from_stage
        self.to_stage = to_stage
        super().__init__(message or f"Invalid workflow transition from '{from_stage}' to '{to_stage}'.")

class WorkflowEngine:
    # Deterministic Transition Rules
    ALLOWED_TRANSITIONS: Dict[WorkflowStage, Set[WorkflowStage]] = {
        WorkflowStage.INGESTED: {WorkflowStage.NEW, WorkflowStage.EXCEPTION},
        WorkflowStage.NEW: {WorkflowStage.PROPERTY_MATCH, WorkflowStage.QC, WorkflowStage.EXCEPTION, WorkflowStage.CLOSED_LOST},
        WorkflowStage.PROPERTY_MATCH: {WorkflowStage.OWNERSHIP, WorkflowStage.QC, WorkflowStage.EXCEPTION, WorkflowStage.CLOSED_LOST},
        WorkflowStage.OWNERSHIP: {WorkflowStage.AUTHORITY, WorkflowStage.QC, WorkflowStage.EXCEPTION, WorkflowStage.CLOSED_LOST},
        WorkflowStage.AUTHORITY: {WorkflowStage.ENRICHMENT, WorkflowStage.QC, WorkflowStage.EXCEPTION, WorkflowStage.CLOSED_LOST},
        WorkflowStage.ENRICHMENT: {WorkflowStage.SCORING, WorkflowStage.QC, WorkflowStage.EXCEPTION, WorkflowStage.CLOSED_LOST},
        WorkflowStage.SCORING: {WorkflowStage.QC, WorkflowStage.EXCEPTION, WorkflowStage.CLOSED_LOST},
        WorkflowStage.QC: {
            WorkflowStage.READY,          # Approved
            WorkflowStage.DELIVERED,      # Direct delivery
            WorkflowStage.OWNERSHIP,      # Rework title
            WorkflowStage.AUTHORITY,      # Rework fiduciary
            WorkflowStage.SCORING,        # Rework score
            WorkflowStage.EXCEPTION,      # Gate failed
            WorkflowStage.CLOSED_LOST
        },
        WorkflowStage.READY: {
            WorkflowStage.DELIVERED,
            WorkflowStage.QC,
            WorkflowStage.OWNERSHIP,
            WorkflowStage.AUTHORITY,
            WorkflowStage.EXCEPTION,
            WorkflowStage.CLOSED_LOST
        },
        WorkflowStage.DELIVERED: {WorkflowStage.CLOSED_WON, WorkflowStage.CLOSED_LOST, WorkflowStage.EXCEPTION},
        WorkflowStage.EXCEPTION: {
            WorkflowStage.NEW,
            WorkflowStage.OWNERSHIP,
            WorkflowStage.AUTHORITY,
            WorkflowStage.QC,
            WorkflowStage.READY,
            WorkflowStage.CLOSED_LOST
        },
        WorkflowStage.CLOSED_WON: set(),
        WorkflowStage.CLOSED_LOST: set()
    }

    @classmethod
    def can_transition(cls, from_stage: str, to_stage: str) -> bool:
        try:
            curr = WorkflowStage(from_stage)
            target = WorkflowStage(to_stage)
            return target in cls.ALLOWED_TRANSITIONS.get(curr, set())
        except ValueError:
            return False

    @classmethod
    def transition(
        cls,
        db: Session,
        opportunity_id: str,
        to_stage: str,
        transitioned_by: str = "System",
        notes: Optional[str] = None
    ) -> OpportunityModel:
        opp = db.query(OpportunityModel).filter(OpportunityModel.id == opportunity_id).first()
        if not opp:
            raise ValueError(f"Opportunity with ID '{opportunity_id}' not found.")

        from_stage = opp.workflow_stage

        # Validate transition
        if not cls.can_transition(from_stage, to_stage):
            raise InvalidWorkflowTransitionError(from_stage, to_stage)

        # Apply transition
        opp.workflow_stage = to_stage
        opp.updated_at = datetime.now(timezone.utc)

        # Record Audit Log
        audit_log = WorkflowAuditLogModel(
            opportunity_id=opp.id,
            from_stage=from_stage,
            to_stage=to_stage,
            transitioned_by=transitioned_by,
            notes=notes
        )
        db.add(audit_log)
        db.commit()
        db.refresh(opp)

        return opp
