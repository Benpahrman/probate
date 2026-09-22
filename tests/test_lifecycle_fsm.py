import uuid
from unittest.mock import MagicMock
import pytest
from app.models.enums import LifecycleStage, AuthorityTier, PriorityTier
from app.models.intelligence import Opportunity
from app.services.fsm import OpportunityLifecycleFSM, InvalidStateTransitionError
from app.services.gatekeeper import QualityControlGatekeeper, GatekeeperEvaluationContext
from app.services.exceptions import TaskExceptionRouter, ExceptionPriority, QuarantineTicketPayload
from app.services.lifecycle import LifecycleCoordinatorService
from app.engines.pas import ParcelAttributionResult, PASCategory
from app.engines.equity import EquityWaterfallResult, EquityTier
from app.engines.scoring import OpportunityScoringResult


# =====================================================================
# 1. 14-STAGE FSM TRANSITION TESTS
# =====================================================================

def test_fsm_valid_linear_progression():
    """Verify standard forward progression through the lifecycle."""
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.DISCOVERED, LifecycleStage.PROPERTY_IDENTIFIED
    )
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.PROPERTY_IDENTIFIED, LifecycleStage.OWNERSHIP_RESOLVED
    )
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.OWNERSHIP_RESOLVED, LifecycleStage.CONTROL_MAPPED
    )
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.CONTROL_MAPPED, LifecycleStage.AUTHORITY_RESOLVED
    )
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.AUTHORITY_RESOLVED, LifecycleStage.SCORED
    )
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.SCORED, LifecycleStage.QC_CERTIFIED
    )
    # Reaching DELIVERED requires is_qc_certified=True
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.QC_CERTIFIED, LifecycleStage.DELIVERED, is_qc_certified=True
    )


def test_fsm_illegal_skipping_transition():
    """Verify that jumping stages (e.g. DISCOVERED -> DELIVERED) is strictly rejected."""
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        OpportunityLifecycleFSM.validate_transition(
            LifecycleStage.DISCOVERED, LifecycleStage.DELIVERED
        )
    assert "Illegal state transition" in str(exc_info.value)


def test_fsm_uncertified_delivery_block():
    """Verify that transitioning to DELIVERED without is_qc_certified=True fails."""
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        OpportunityLifecycleFSM.validate_transition(
            LifecycleStage.QC_CERTIFIED, LifecycleStage.DELIVERED, is_qc_certified=False
        )
    assert "Cannot transition to DELIVERED without passing Quality Control Gate certification" in str(exc_info.value)


def test_fsm_terminal_and_same_stage():
    """Verify same-stage no-op and terminal state checks."""
    OpportunityLifecycleFSM.validate_transition(
        LifecycleStage.DISCOVERED, LifecycleStage.DISCOVERED
    )
    assert OpportunityLifecycleFSM.is_terminal(LifecycleStage.ARCHIVED) is True
    assert OpportunityLifecycleFSM.is_terminal(LifecycleStage.SCORED) is False


# =====================================================================
# 2. DETERMINISTIC QUALITY GATES TESTS
# =====================================================================

def test_gate_1_docket_integrity_success():
    """Confirm valid docket number and SHA-256 pass Gate 1."""
    res = QualityControlGatekeeper.verify_gate_1_docket_integrity(
        case_number="2026-PR-009182",
        filing_date_valid=True,
        petition_pdf_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert res.passed is True
    assert res.gate_number == 1


def test_gate_1_docket_integrity_invalid_sha():
    """Confirm invalid/missing SHA-256 fails Gate 1."""
    res = QualityControlGatekeeper.verify_gate_1_docket_integrity(
        case_number="2026-PR-009182",
        filing_date_valid=True,
        petition_pdf_sha256="corrupt_hash"
    )
    assert res.passed is False
    assert res.failure_reason is not None
    assert "Missing or corrupt court petition PDF" in res.failure_reason


def test_gate_1_docket_integrity_invalid_case_and_date():
    """Confirm invalid regex case number and outdated filing dates fail Gate 1."""
    res_bad_case = QualityControlGatekeeper.verify_gate_1_docket_integrity(
        case_number="!!",
        filing_date_valid=True,
        petition_pdf_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert res_bad_case.passed is False
    assert res_bad_case.failure_reason is not None
    assert "violates county docket regex formatting" in res_bad_case.failure_reason

    res_bad_date = QualityControlGatekeeper.verify_gate_1_docket_integrity(
        case_number="2026-PR-009182",
        filing_date_valid=False,
        petition_pdf_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert res_bad_date.passed is False
    assert res_bad_date.failure_reason is not None
    assert "Filing date falls outside the valid municipal intake lookback window" in res_bad_date.failure_reason


def test_gate_2_pas_threshold():
    """Confirm PAS >= 70 passes and < 70 fails Gate 2."""
    pass_input = ParcelAttributionResult(
        pas_score=75.5, category=PASCategory.PROBABLE_MATCH, gate_2_passed=True, requires_manual_triage=False
    )
    fail_input = ParcelAttributionResult(
        pas_score=52.0, category=PASCategory.MANUAL_REVIEW, gate_2_passed=False, requires_manual_triage=True
    )
    assert QualityControlGatekeeper.verify_gate_2_parcel_attribution(pass_input).passed is True
    assert QualityControlGatekeeper.verify_gate_2_parcel_attribution(fail_input).passed is False


def test_gate_3_equity_enforcement():
    """Confirm Net Equity >= $50k and >= 30% passes Gate 3."""
    pass_equity = EquityWaterfallResult(
        gross_market_value=300000.0,
        total_encumbrances=90000.0,
        net_actionable_equity=210000.0,
        equity_percentage=0.70,
        tier=EquityTier.EXCEPTIONAL,
        gate_3_passed=True,
        is_disqualified=False
    )
    fail_equity = EquityWaterfallResult(
        gross_market_value=100000.0,
        total_encumbrances=75000.0,
        net_actionable_equity=25000.0,  # Below $50,000 threshold
        equity_percentage=0.25,         # Below 30.0% threshold
        tier=EquityTier.LOW_OR_UNDERWATER,
        gate_3_passed=False,
        is_disqualified=True,
        disqualification_reason="Net equity $25,000.00 is below the $50,000 statutory minimum threshold."
    )
    assert QualityControlGatekeeper.verify_gate_3_encumbrance_equity(pass_equity).passed is True
    assert QualityControlGatekeeper.verify_gate_3_encumbrance_equity(fail_equity).passed is False


def test_gate_4_authority_caveat_quarantine():
    """Confirm that active caveats or Tier 4 Unresolved fail Gate 4."""
    res_clean = QualityControlGatekeeper.verify_gate_4_fiduciary_authority(
        authority_tier=AuthorityTier.TIER_1_CONFIRMED, has_contested_caveats=False
    )
    res_contested = QualityControlGatekeeper.verify_gate_4_fiduciary_authority(
        authority_tier=AuthorityTier.TIER_1_CONFIRMED, has_contested_caveats=True
    )
    assert res_clean.passed is True
    assert res_contested.passed is False
    assert res_contested.failure_reason is not None
    assert "active caveats" in res_contested.failure_reason


def test_gate_5_attorney_quarantine():
    """Confirm unquarantined attorney gatekeeper fails Gate 5."""
    res_quarantined = QualityControlGatekeeper.verify_gate_5_contact_scrubbing(
        primary_phone_active=True, dnc_filtered=True, is_attorney_quarantined=True
    )
    res_unquarantined = QualityControlGatekeeper.verify_gate_5_contact_scrubbing(
        primary_phone_active=True, dnc_filtered=True, is_attorney_quarantined=False
    )
    assert res_quarantined.passed is True
    assert res_unquarantined.passed is False
    assert res_unquarantined.failure_reason is not None
    assert "attorney gatekeeper has not been quarantined" in res_unquarantined.failure_reason


def test_gate_5_phone_and_dnc_checks():
    """Confirm disconnected phone or unscrubbed DNC fails Gate 5."""
    res_bad_phone = QualityControlGatekeeper.verify_gate_5_contact_scrubbing(
        primary_phone_active=False, dnc_filtered=True, is_attorney_quarantined=True
    )
    assert res_bad_phone.passed is False
    assert res_bad_phone.failure_reason is not None
    assert "disconnected or failed carrier HLR dip" in res_bad_phone.failure_reason

    res_bad_dnc = QualityControlGatekeeper.verify_gate_5_contact_scrubbing(
        primary_phone_active=True, dnc_filtered=False, is_attorney_quarantined=True
    )
    assert res_bad_dnc.passed is False
    assert res_bad_dnc.failure_reason is not None
    assert "National Do-Not-Call (DNC)" in res_bad_dnc.failure_reason


def test_gate_6_predelivery_certification():
    """Confirm buybox, viability score threshold, and evidence records requirements."""
    scoring_high = OpportunityScoringResult(
        composite_viability_score=85,
        gross_upside_score=90.0,
        deal_friction_score=5,
        priority_tier=PriorityTier.PRIORITY_A,
        dispatch_sla="FLASH_ALERT_4_HOUR",
        is_deliverable=True,
        summary="High viability opportunity"
    )
    scoring_low = OpportunityScoringResult(
        composite_viability_score=45,
        gross_upside_score=55.0,
        deal_friction_score=10,
        priority_tier=PriorityTier.PRIORITY_C,
        dispatch_sla="DOCKET_MONITOR",
        is_deliverable=False,
        summary="Below threshold score"
    )

    # Valid scenario
    res_valid = QualityControlGatekeeper.verify_gate_6_predelivery_certification(
        scoring_result=scoring_high, evidence_records_count=2, is_in_partner_buybox=True
    )
    assert res_valid.passed is True

    # Outside partner buybox
    res_buybox_fail = QualityControlGatekeeper.verify_gate_6_predelivery_certification(
        scoring_result=scoring_high, evidence_records_count=2, is_in_partner_buybox=False
    )
    assert res_buybox_fail.passed is False
    assert res_buybox_fail.failure_reason is not None
    assert "partner buy-box" in res_buybox_fail.failure_reason

    # Low score
    res_score_fail = QualityControlGatekeeper.verify_gate_6_predelivery_certification(
        scoring_result=scoring_low, evidence_records_count=2, is_in_partner_buybox=True
    )
    assert res_score_fail.passed is False
    assert res_score_fail.failure_reason is not None
    assert "below standard delivery threshold" in res_score_fail.failure_reason

    # Insufficient evidence records
    res_evidence_fail = QualityControlGatekeeper.verify_gate_6_predelivery_certification(
        scoring_result=scoring_high, evidence_records_count=1, is_in_partner_buybox=True
    )
    assert res_evidence_fail.passed is False
    assert res_evidence_fail.failure_reason is not None
    assert "Insufficient cryptographic evidence records" in res_evidence_fail.failure_reason


def test_evaluate_all_gates_sequential_execution():
    """Verify evaluate_all_gates succeeds when all 6 pass, and halts on earlier failure."""
    valid_pas = ParcelAttributionResult(
        pas_score=85.0, category=PASCategory.PROBABLE_MATCH, gate_2_passed=True, requires_manual_triage=False
    )
    valid_equity = EquityWaterfallResult(
        gross_market_value=350000.0,
        total_encumbrances=70000.0,
        net_actionable_equity=280000.0,
        equity_percentage=0.80,
        tier=EquityTier.EXCEPTIONAL,
        gate_3_passed=True,
        is_disqualified=False
    )
    valid_scoring = OpportunityScoringResult(
        composite_viability_score=88,
        gross_upside_score=92.0,
        deal_friction_score=4,
        priority_tier=PriorityTier.PRIORITY_A,
        dispatch_sla="FLASH_ALERT_4_HOUR",
        is_deliverable=True,
        summary="Certified viable file"
    )

    # All pass
    ctx_pass = GatekeeperEvaluationContext(
        case_number="2026-PR-009182",
        filing_date_valid=True,
        petition_pdf_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        pas_result=valid_pas,
        equity_result=valid_equity,
        authority_tier=AuthorityTier.TIER_1_CONFIRMED,
        has_contested_caveats=False,
        primary_phone_active=True,
        dnc_filtered=True,
        is_attorney_quarantined=True,
        scoring_result=valid_scoring,
        evidence_records_count=3,
        is_in_partner_buybox=True
    )
    summary = QualityControlGatekeeper.evaluate_all_gates(context=ctx_pass)
    assert summary.is_fully_certified is True
    assert summary.failed_gate is None
    assert len(summary.gate_results) == 6

    # Gate 2 failure stops pipeline before Gate 3
    fail_pas = ParcelAttributionResult(
        pas_score=45.0, category=PASCategory.MANUAL_REVIEW, gate_2_passed=False, requires_manual_triage=True
    )
    ctx_fail = GatekeeperEvaluationContext(
        case_number="2026-PR-009182",
        filing_date_valid=True,
        petition_pdf_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        pas_result=fail_pas,
        equity_result=valid_equity,
        authority_tier=AuthorityTier.TIER_1_CONFIRMED,
        has_contested_caveats=False,
        primary_phone_active=True,
        dnc_filtered=True,
        is_attorney_quarantined=True,
        scoring_result=valid_scoring,
        evidence_records_count=3,
        is_in_partner_buybox=True
    )
    summary_fail = QualityControlGatekeeper.evaluate_all_gates(context=ctx_fail)
    assert summary_fail.is_fully_certified is False
    assert summary_fail.failed_gate == 2
    assert len(summary_fail.gate_results) == 2


# =====================================================================
# 3. TASKS & EXCEPTIONS PRIORITY SLA TESTS
# =====================================================================

def test_exception_priority_calculation():
    """Confirm SLA priority assignment based on net equity tiers."""
    assert TaskExceptionRouter.calculate_priority(250000.0) == ExceptionPriority.CRITICAL  # > $200k
    assert TaskExceptionRouter.calculate_priority(150000.0) == ExceptionPriority.HIGH      # $100k-$200k
    assert TaskExceptionRouter.calculate_priority(45000.0) == ExceptionPriority.NORMAL     # < $100k


def test_create_quarantine_ticket():
    """Verify quarantine ticket persistence and SLA notes generation."""
    db_mock = MagicMock()
    case_id = uuid.uuid4()

    ticket = TaskExceptionRouter.create_quarantine_ticket(
        db=db_mock,
        payload=QuarantineTicketPayload(
            case_id=case_id,
            failed_gate=3,
            exception_type="Gate 3 Failure",
            net_equity=250000.0,
            resolution_notes="Encumbrance exceeds threshold",
            assigned_to="Triage Specialist"
        )
    )
    assert ticket.case_id == case_id
    assert ticket.priority == ExceptionPriority.CRITICAL
    assert ticket.resolution_notes is not None
    assert "SLA Target: 4 Hours" in ticket.resolution_notes
    assert db_mock.add.called
    assert db_mock.commit.called
    assert db_mock.refresh.called


# =====================================================================
# 4. LIFECYCLE COORDINATOR TESTS
# =====================================================================

def _create_mock_opportunity(
    stage: LifecycleStage = LifecycleStage.SCORED,
    is_qc_certified: bool = False
) -> Opportunity:
    return Opportunity(
        case_id=uuid.uuid4(),
        property_id=uuid.uuid4(),
        lifecycle_stage=stage,
        is_qc_certified=is_qc_certified
    )


def test_lifecycle_coordinator_transition_stage():
    """Verify Opportunity lifecycle stage transitions with validation."""
    db_mock = MagicMock()
    opp = _create_mock_opportunity(LifecycleStage.DISCOVERED, False)
    updated_opp = LifecycleCoordinatorService.transition_stage(
        db=db_mock,
        opportunity=opp,
        target_stage=LifecycleStage.PROPERTY_IDENTIFIED
    )
    assert updated_opp.lifecycle_stage == LifecycleStage.PROPERTY_IDENTIFIED
    assert db_mock.commit.called
    assert db_mock.refresh.called


def _build_test_qc_dataset():
    equity = EquityWaterfallResult(
        gross_market_value=350000.0,
        total_encumbrances=70000.0,
        net_actionable_equity=280000.0,
        equity_percentage=0.80,
        tier=EquityTier.EXCEPTIONAL,
        gate_3_passed=True,
        is_disqualified=False
    )
    scoring = OpportunityScoringResult(
        composite_viability_score=85,
        gross_upside_score=90.0,
        deal_friction_score=5,
        priority_tier=PriorityTier.PRIORITY_A,
        dispatch_sla="FLASH_ALERT_4_HOUR",
        is_deliverable=True,
        summary="Viable"
    )
    return equity, scoring


def _run_test_qc_audit(db_mock: MagicMock, opp: Opportunity, pas_result: ParcelAttributionResult):
    equity, scoring = _build_test_qc_dataset()
    context = GatekeeperEvaluationContext(
        case_number="2026-PR-009182",
        filing_date_valid=True,
        petition_pdf_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        pas_result=pas_result,
        equity_result=equity,
        authority_tier=AuthorityTier.TIER_1_CONFIRMED,
        has_contested_caveats=False,
        primary_phone_active=True,
        dnc_filtered=True,
        is_attorney_quarantined=True,
        scoring_result=scoring,
        evidence_records_count=2,
        is_in_partner_buybox=True
    )
    return LifecycleCoordinatorService.execute_qc_audit_and_transition(
        db=db_mock,
        opportunity=opp,
        context=context
    )


def test_lifecycle_coordinator_qc_audit_success():
    """Verify QC audit passing advances opportunity to QC_CERTIFIED."""
    db_mock = MagicMock()
    opp = _create_mock_opportunity(LifecycleStage.SCORED, False)
    valid_pas = ParcelAttributionResult(
        pas_score=85.0, category=PASCategory.PROBABLE_MATCH, gate_2_passed=True, requires_manual_triage=False
    )
    summary = _run_test_qc_audit(db_mock, opp, valid_pas)
    assert summary.is_fully_certified is True
    assert opp.is_qc_certified is True
    assert opp.lifecycle_stage == LifecycleStage.QC_CERTIFIED
    assert opp.composite_viability_score == 85
    assert opp.priority_tier == PriorityTier.PRIORITY_A
    assert db_mock.commit.called


def test_lifecycle_coordinator_qc_audit_failure_quarantine():
    """Verify QC audit failure creates quarantine ticket and does not advance stage."""
    db_mock = MagicMock()
    opp = _create_mock_opportunity(LifecycleStage.SCORED, False)
    fail_pas = ParcelAttributionResult(
        pas_score=50.0, category=PASCategory.MANUAL_REVIEW, gate_2_passed=False, requires_manual_triage=True
    )
    summary = _run_test_qc_audit(db_mock, opp, fail_pas)
    assert summary.is_fully_certified is False
    assert summary.failed_gate == 2
    assert opp.is_qc_certified is False
    assert opp.lifecycle_stage == LifecycleStage.SCORED  # Unchanged
    assert db_mock.add.called  # Quarantine ticket added
    assert db_mock.commit.called
