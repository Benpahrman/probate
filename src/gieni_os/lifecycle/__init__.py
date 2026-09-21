"""
Gieni OS Lifecycle Package
"""

# ── Canonical strict FSM (transplanted from backend/app/services/fsm.py) ──────
from gieni_os.lifecycle.fsm import OpportunityLifecycleFSM, InvalidStateTransitionError

# ── Legacy loose state machine (retained for backward compatibility) ───────────
from gieni_os.lifecycle.state_machine import OpportunityStateMachine, OpportunityStage

__all__ = [
    "OpportunityLifecycleFSM",
    "InvalidStateTransitionError",
    "OpportunityStateMachine",
    "OpportunityStage",
]
