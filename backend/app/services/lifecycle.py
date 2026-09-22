import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.intelligence import Opportunity
from app.models.enums import LifecycleStage, AuthorityTier
from app.services.fsm import OpportunityLifecycleFSM
from app.services.gatekeeper import QualityControlGatekeeper, QualityControlAuditSummary, GatekeeperEvaluationContext
from app.services.exceptions import TaskExceptionRouter
from app.engines.pas import ParcelAttributionResult
from app.engines.equity import EquityWaterfallResult
from app.engines.scoring import OpportunityScoringResult


class LifecycleCoordinatorService:
    """Coordinates lifecycle transitions, gate verification, and exception interception."""

    @staticmethod
    def transition_stage(
        db: Session,
        opportunity: Opportunity,
        target_stage: LifecycleStage
    ) -> Opportunity:
        """Validates structural legality and transitions the opportunity stage."""
        OpportunityLifecycleFSM.validate_transition(
            current_stage=opportunity.lifecycle_stage,
            target_stage=target_stage,
            is_qc_certified=opportunity.is_qc_certified
        )

        opportunity.lifecycle_stage = target_stage
        db.commit()
        db.refresh(opportunity)
        return opportunity

    @staticmethod
    def execute_qc_audit_and_transition(
        db: Session,
        opportunity: Opportunity,
        context: Optional[GatekeeperEvaluationContext] = None,
        **kwargs
    ) -> QualityControlAuditSummary:
        """Executes full QC audit. If passed, toggles is_qc_certified=True and advances stage.
        If any gate fails, creates a quarantine ticket in Tasks & Exceptions.
        Supports both GatekeeperEvaluationContext and legacy keyword arguments.
        """
        if context is None:
            context = GatekeeperEvaluationContext(
                case_number=kwargs["case_number"],
                filing_date_valid=kwargs["filing_date_valid"],
                petition_pdf_sha256=kwargs.get("petition_pdf_sha256"),
                pas_result=kwargs["pas_result"],
                equity_result=kwargs["equity_result"],
                authority_tier=kwargs["authority_tier"],
                has_contested_caveats=kwargs["has_contested_caveats"],
                primary_phone_active=kwargs["primary_phone_active"],
                dnc_filtered=kwargs["dnc_filtered"],
                is_attorney_quarantined=kwargs["is_attorney_quarantined"],
                scoring_result=kwargs["scoring_result"],
                evidence_records_count=kwargs["evidence_records_count"],
                is_in_partner_buybox=kwargs.get("is_in_partner_buybox", True)
            )

        audit_summary = QualityControlGatekeeper.evaluate_all_gates(context=context)

        scoring_result = context.scoring_result
        if audit_summary.is_fully_certified:
            opportunity.is_qc_certified = True
            opportunity.composite_viability_score = scoring_result.composite_viability_score
            opportunity.deal_friction_score = scoring_result.deal_friction_score
            opportunity.priority_tier = scoring_result.priority_tier
            opportunity.dispatch_sla = scoring_result.dispatch_sla

            # Transition to QC_CERTIFIED stage
            OpportunityLifecycleFSM.validate_transition(
                current_stage=opportunity.lifecycle_stage,
                target_stage=LifecycleStage.QC_CERTIFIED,
                is_qc_certified=True
            )
            opportunity.lifecycle_stage = LifecycleStage.QC_CERTIFIED
            db.commit()
            db.refresh(opportunity)
        else:
            # Route to Tasks & Exceptions queue
            opportunity.is_qc_certified = False
            TaskExceptionRouter.create_quarantine_ticket(
                db=db,
                case_id=opportunity.case_id,
                failed_gate=audit_summary.failed_gate or 1,
                exception_type=f"Gate {audit_summary.failed_gate} Failure",
                net_equity=context.equity_result.net_actionable_equity,
                resolution_notes=audit_summary.disqualification_reason or "Unknown gate failure"
            )
            db.commit()

        return audit_summary
