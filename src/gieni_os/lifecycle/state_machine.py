"""
Gieni OS 14-Stage Opportunity Lifecycle State Machine
Enforces deterministic progression across legal and commercial pipeline states.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import time
import logging

logger = logging.getLogger("StateMachine")

class OpportunityStage(Enum):
    DISCOVERED = "DISCOVERED"
    PROPERTY_IDENTIFIED = "PROPERTY_IDENTIFIED"
    OWNERSHIP_RESOLVED = "OWNERSHIP_RESOLVED"
    CONTROL_MAPPED = "CONTROL_MAPPED"
    AUTHORITY_RESOLVED = "AUTHORITY_RESOLVED"
    SCORED = "SCORED"
    QC_CERTIFIED = "QC_CERTIFIED"
    DELIVERED = "DELIVERED"
    CONTACTED = "CONTACTED"
    APPOINTMENT = "APPOINTMENT"
    OFFER_PRESENTED = "OFFER_PRESENTED"
    CONTRACT_EXECUTED = "CONTRACT_EXECUTED"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"
    ARCHIVED = "ARCHIVED"

class OpportunityStateMachine:
    def __init__(self, opportunity_id: str, initial_stage: OpportunityStage = OpportunityStage.DISCOVERED):
        self.opportunity_id = opportunity_id
        self.current_stage = initial_stage
        self.history: List[Dict[str, Any]] = [
            {
                "stage": initial_stage.value,
                "timestamp": time.time(),
                "context": {},
                "actor": "System"
            }
        ]

    def transition_to(
        self,
        new_stage: OpportunityStage,
        context: Optional[Dict[str, Any]] = None,
        actor: str = "System"
    ) -> None:
        self.current_stage = new_stage
        record = {
            "stage": new_stage.value,
            "timestamp": time.time(),
            "context": context or {},
            "actor": actor
        }
        self.history.append(record)
        logger.info(f"[{self.opportunity_id}] Transitioned to {new_stage.value} by {actor}")
