from typing import Dict, Set, Union
from app.models.enums import LifecycleStage


class InvalidStateTransitionError(Exception):
    """Raised when an opportunity attempts an illegal lifecycle transition."""
    def __init__(self, current_stage: Union[LifecycleStage, str], target_stage: Union[LifecycleStage, str], reason: str = ""):
        self.current_stage = current_stage
        self.target_stage = target_stage
        self.reason = reason
        c_val = current_stage.value if hasattr(current_stage, "value") else str(current_stage)
        t_val = target_stage.value if hasattr(target_stage, "value") else str(target_stage)
        super().__init__(
            f"Illegal state transition from {c_val} to {t_val}. {reason}"
        )


class OpportunityLifecycleFSM:
    """Canonical 14-stage state machine governance.
    Enforces forward-only transitions, gate certification requirements,
    and terminal archiving logic.
    """

    # Permitted state transitions according to Chapter 2 & 17
    VALID_TRANSITIONS: Dict[LifecycleStage, Set[LifecycleStage]] = {
        LifecycleStage.DISCOVERED: {
            LifecycleStage.PROPERTY_IDENTIFIED,
            LifecycleStage.ARCHIVED  # Instant disqualification (e.g. fatal docket defect)
        },
        LifecycleStage.PROPERTY_IDENTIFIED: {
            LifecycleStage.OWNERSHIP_RESOLVED,
            LifecycleStage.ARCHIVED  # No real estate or unmatchable APN
        },
        LifecycleStage.OWNERSHIP_RESOLVED: {
            LifecycleStage.CONTROL_MAPPED,
            LifecycleStage.ARCHIVED  # Underwater equity (<30% or <$50k)
        },
        LifecycleStage.CONTROL_MAPPED: {
            LifecycleStage.AUTHORITY_RESOLVED,
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.AUTHORITY_RESOLVED: {
            LifecycleStage.SCORED,
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.SCORED: {
            LifecycleStage.QC_CERTIFIED,
            LifecycleStage.ARCHIVED  # Composite score < 40
        },
        LifecycleStage.QC_CERTIFIED: {
            LifecycleStage.DELIVERED,
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.DELIVERED: {
            LifecycleStage.CONTACTED,
            LifecycleStage.ARCHIVED  # Timeout / client non-outreach cancellation
        },
        LifecycleStage.CONTACTED: {
            LifecycleStage.APPOINTMENT,
            LifecycleStage.CLOSED_LOST,
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.APPOINTMENT: {
            LifecycleStage.OFFER,
            LifecycleStage.CLOSED_LOST,
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.OFFER: {
            LifecycleStage.CONTRACT,
            LifecycleStage.CLOSED_LOST,
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.CONTRACT: {
            LifecycleStage.CLOSED_WON,
            LifecycleStage.CLOSED_LOST
        },
        LifecycleStage.CLOSED_WON: {
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.CLOSED_LOST: {
            LifecycleStage.ARCHIVED
        },
        LifecycleStage.ARCHIVED: set()  # Terminal state
    }

    @staticmethod
    def _normalize_stage(stage: Union[LifecycleStage, str]) -> LifecycleStage:
        return LifecycleStage(stage) if isinstance(stage, str) else stage

    @classmethod
    def _check_structural_transition(cls, curr_enum: LifecycleStage, target_enum: LifecycleStage) -> None:
        permitted_targets = cls.VALID_TRANSITIONS.get(curr_enum, set())
        if target_enum not in permitted_targets:
            raise InvalidStateTransitionError(
                current_stage=curr_enum,
                target_stage=target_enum,
                reason=f"Stage {curr_enum.value} can only transition to: {[s.value for s in permitted_targets]}."
            )

    @staticmethod
    def _check_qc_requirement(target_enum: LifecycleStage, is_qc_certified: bool) -> None:
        if target_enum == LifecycleStage.DELIVERED and not is_qc_certified:
            raise InvalidStateTransitionError(
                current_stage=target_enum,
                target_stage=target_enum,
                reason="Cannot transition to DELIVERED without passing Quality Control Gate certification."
            )

    @classmethod
    def validate_transition(
        cls,
        current_stage: Union[LifecycleStage, str],
        target_stage: Union[LifecycleStage, str],
        is_qc_certified: bool = False
    ) -> None:
        """Validates whether a transition between two lifecycle stages is structurally legal."""
        curr_enum = cls._normalize_stage(current_stage)
        target_enum = cls._normalize_stage(target_stage)

        if curr_enum == target_enum:
            return

        if target_enum == LifecycleStage.QC_CERTIFIED and is_qc_certified:
            return

        cls._check_structural_transition(curr_enum, target_enum)
        cls._check_qc_requirement(target_enum, is_qc_certified)

    @classmethod
    def is_terminal(cls, stage: Union[LifecycleStage, str]) -> bool:
        return cls._normalize_stage(stage) == LifecycleStage.ARCHIVED
