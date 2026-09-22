import pytest
from app.engines.pas import calculate_pas, calculate_jaro_winkler, ParcelAttributionInputs, PASCategory
from app.engines.equity import compute_net_actionable_equity, EncumbranceWaterfallInputs, EquityTier
from app.engines.complexity import compute_ownership_complexity, OwnershipComplexityInputs
from app.engines.scoring import compute_opportunity_viability, OpportunityScoringInputs
from app.models.enums import VestingType, AuthorityTier, PowerScope, ControlArchetype, PriorityTier


# =====================================================================
# 1. PARCEL ATTRIBUTION SCORE (PAS) TESTS
# =====================================================================

def test_jaro_winkler_similarity():
    """Verify string distance calculation on legal identity names."""
    assert calculate_jaro_winkler("ROBERT JOHNSON", "ROBERT JOHNSON") == 1.0
    assert calculate_jaro_winkler("ROBERT JOHNSON", "ROBERT E JOHNSON") > 0.90
    assert calculate_jaro_winkler("JOHN SMITH", "MARY WILLIAMS") < 0.50
    assert calculate_jaro_winkler("", "JOHN") == 0.0


def test_pas_calculation_verified_tier():
    """Confirm PAS >= 90.0 triggers Verified Parcel Match and passes Gate 2."""
    inputs = ParcelAttributionInputs(
        source_agreement=0.95,      # 0.95 * 30 = 28.5
        name_similarity=0.98,       # 0.98 * 25 = 24.5
        address_correlation=1.00,   # 1.00 * 20 = 20.0
        title_continuity=1.00,      # 1.00 * 15 = 15.0
        tax_alignment=1.00          # 1.00 * 10 = 10.0 => Total = 98.0
    )
    res = calculate_pas(inputs)
    assert res.pas_score == 98.0
    assert res.category == PASCategory.VERIFIED_MATCH
    assert res.gate_2_passed is True
    assert res.requires_manual_triage is False


def test_pas_calculation_failure_quarantine():
    """Confirm PAS < 70.0 fails Gate 2 and routes to Tasks & Exceptions."""
    inputs = ParcelAttributionInputs(
        source_agreement=0.40,      # 12.0
        name_similarity=0.50,       # 12.5
        address_correlation=0.60,   # 12.0
        title_continuity=0.50,      # 7.5
        tax_alignment=0.40          # 4.0 => Total = 48.0
    )
    res = calculate_pas(inputs)
    assert res.pas_score == 48.0
    assert res.category == PASCategory.MANUAL_REVIEW
    assert res.gate_2_passed is False
    assert res.requires_manual_triage is True


# =====================================================================
# 2. NET ACTIONABLE EQUITY WATERFALL TESTS
# =====================================================================

def test_equity_waterfall_exceptional_tier():
    """Verify clean equity calculation with > 70% equity spread."""
    inputs = EncumbranceWaterfallInputs(
        gross_market_value=350000.0,
        open_mortgage_balance=60000.0,
        delinquent_real_property_taxes=4500.0,
        municipal_and_mechanics_liens=1500.0,
        estimated_probate_statutory_fees=4000.0
    )
    res = compute_net_actionable_equity(inputs)
    assert res.total_encumbrances == 70000.0
    assert res.net_actionable_equity == 280000.0
    assert res.equity_percentage == 0.8000
    assert res.tier == EquityTier.EXCEPTIONAL
    assert res.gate_3_passed is True
    assert res.is_disqualified is False


def test_equity_waterfall_merp_disqualification():
    """Verify Gate 3 disqualification when MERP liens exhaust equity."""
    inputs = EncumbranceWaterfallInputs(
        gross_market_value=200000.0,
        open_mortgage_balance=80000.0,
        delinquent_real_property_taxes=5000.0,
        merp_statutory_claim=95000.0  # Leaves only $20,000 net equity
    )
    res = compute_net_actionable_equity(inputs)
    assert res.total_encumbrances == 180000.0
    assert res.net_actionable_equity == 200000.0 - 180000.0
    assert res.equity_percentage == 0.1000
    assert res.tier == EquityTier.LOW_OR_UNDERWATER
    assert res.gate_3_passed is False
    assert res.is_disqualified is True
    assert res.disqualification_reason is not None
    assert "below the $50,000 statutory minimum threshold" in res.disqualification_reason


# =====================================================================
# 3. OWNERSHIP COMPLEXITY TESTS
# =====================================================================

def test_complexity_sole_fee_simple():
    """Confirm base complexity of 10 for uncontested sole fee simple."""
    inputs = OwnershipComplexityInputs(vesting_type=VestingType.SOLE_FEE_SIMPLE)
    res = compute_ownership_complexity(inputs)
    assert res.complexity_score == 10
    assert res.base_score == 10
    assert res.penalties_applied == 0


def test_complexity_multi_generational_heir_property():
    """Confirm compounding penalties for 8 heirs and 2 unprobated ancestor links."""
    inputs = OwnershipComplexityInputs(
        vesting_type=VestingType.HEIR_PROPERTY,     # Base 85
        heir_count=8,                               # (8-4)*4 = +16 pts
        ancestor_probates_unresolved=2,             # 2*15 = +30 pts
        has_title_cloud_or_wild_deed=True           # +15 pts => Total capped at 100
    )
    res = compute_ownership_complexity(inputs)
    assert res.complexity_score == 100
    assert res.base_score == 85
    assert res.penalties_applied == 61


# =====================================================================
# 4. DEAL FRICTION & VIABILITY SCORING TESTS
# =====================================================================

def test_opportunity_scoring_priority_a():
    """Confirm high-equity, low-friction file achieves Priority A and 4-hour SLA."""
    inputs = OpportunityScoringInputs(
        net_equity_amount=250000.0,
        equity_percentage=0.85,
        authority_tier=AuthorityTier.TIER_1_CONFIRMED,
        power_scope=PowerScope.FULL_INDEPENDENT_ADMINISTRATION,
        is_vacant=True,
        has_tax_delinquency=True,
        ownership_complexity_score=10,
        control_archetype=ControlArchetype.UNIFIED_FIDUCIARY
    )
    res = compute_opportunity_viability(inputs)
    assert res.composite_viability_score >= 80
    assert res.deal_friction_score == 0
    assert res.priority_tier == PriorityTier.PRIORITY_A
    assert res.dispatch_sla == "FLASH_ALERT_4_HOUR"
    assert res.is_deliverable is True


def test_opportunity_scoring_court_oversight_friction_penalty():
    """Confirm Dependent Court Supervision imposes a 15-point DFS deduction."""
    inputs = OpportunityScoringInputs(
        net_equity_amount=160000.0,
        equity_percentage=0.65,
        authority_tier=AuthorityTier.TIER_2_LIKELY,
        power_scope=PowerScope.DEPENDENT_COURT_SUPERVISED,  # -15 pts penalty
        ownership_complexity_score=65,
        control_archetype=ControlArchetype.PROXY_CONTROLLER   # -8 pts penalty
    )
    res = compute_opportunity_viability(inputs)
    assert res.deal_friction_score >= 23
    assert res.priority_tier in [PriorityTier.PRIORITY_B, PriorityTier.PRIORITY_C]
