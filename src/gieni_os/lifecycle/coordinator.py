"""
Gieni OS Lifecycle Coordinator Service
Orchestrates lifecycle stage transitions, QC gate evaluation, and
exception ticket creation in a single transactional unit.

Transplanted from backend/app/services/lifecycle.py.
Imports rewritten: app.* → gieni_os.*
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from gieni_os.models.orm import Opportunity
from gieni_os.domain.enums import LifecycleStage, AuthorityTier
from gieni_os.lifecycle.fsm import OpportunityLifecycleFSM
from gieni_os.validation.gatekeeper import QualityControlGatekeeper, QualityControlAuditSummary
from gieni_os.workflow.exceptions import TaskExceptionRouter
from gieni_os.engines.pas import ParcelAttributionResult
from gieni_os.engines.equity import EquityWaterfallResult
from gieni_os.engines.scoring import OpportunityScoringResult


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
        case_number: str,
        filing_date_valid: bool,
        petition_pdf_sha256: Optional[str],
        pas_result: ParcelAttributionResult,
        equity_result: EquityWaterfallResult,
        authority_tier: AuthorityTier,
        has_contested_caveats: bool,
        primary_phone_active: bool,
        dnc_filtered: bool,
        is_attorney_quarantined: bool,
        scoring_result: OpportunityScoringResult,
        evidence_records_count: int,
        is_in_partner_buybox: bool = True
    ) -> QualityControlAuditSummary:
        """Executes full QC audit. If passed, toggles is_qc_certified=True and advances stage.
        If any gate fails, creates a quarantine ticket in Tasks & Exceptions.
        """
        audit_summary = QualityControlGatekeeper.evaluate_all_gates(
            case_number=case_number,
            filing_date_valid=filing_date_valid,
            petition_pdf_sha256=petition_pdf_sha256,
            pas_result=pas_result,
            equity_result=equity_result,
            authority_tier=authority_tier,
            has_contested_caveats=has_contested_caveats,
            primary_phone_active=primary_phone_active,
            dnc_filtered=dnc_filtered,
            is_attorney_quarantined=is_attorney_quarantined,
            scoring_result=scoring_result,
            evidence_records_count=evidence_records_count,
            is_in_partner_buybox=is_in_partner_buybox
        )

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
                net_equity=equity_result.net_actionable_equity,
                resolution_notes=audit_summary.disqualification_reason or "Unknown gate failure"
            )
            db.commit()

        return audit_summary
