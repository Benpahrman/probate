"""
Deterministic Engine Tests
Verifies the mathematical correctness of the four core scoring engines:
1. Parcel Attribution Score (PAS) with Jaro-Winkler
2. Net Actionable Equity Waterfall
3. Ownership Complexity Score (OCS)
4. Composite Opportunity Viability Score

Transplanted from backend/app/tests/test_engines.py.
All imports rewritten from app.* to gieni_os.*
"""

import pytest
from gieni_os.engines.pas import calculate_pas, calculate_jaro_winkler, ParcelAttributionInputs, PASCategory
from gieni_os.engines.equity import compute_net_actionable_equity, EncumbranceWaterfallInputs, EquityTier
from gieni_os.engines.complexity import compute_ownership_complexity, OwnershipComplexityInputs
from gieni_os.engines.scoring import compute_opportunity_viability, OpportunityScoringInputs
from gieni_os.domain.enums import VestingType, AuthorityTier, PowerScope, ControlArchetype, PriorityTier


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


def test_pas_calculation_probable_tier():
    """Confirm PAS between 70 and 90 returns PROBABLE_MATCH."""
    inputs = ParcelAttributionInputs(
        source_agreement=0.80,      # 24.0
        name_similarity=0.75,       # 18.75
        address_correlation=0.80,   # 16.0
        title_continuity=0.70,      # 10.5
        tax_alignment=0.60          # 6.0 => Total = 75.25
    )
    res = calculate_pas(inputs)
    assert res.pas_score == 75.25
    assert res.category == PASCategory.PROBABLE_MATCH
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
    assert "below the $50,000 statutory minimum threshold" in res.disqualification_reason


def test_equity_waterfall_insufficient_percentage():
    """Verify Gate 3 failure when equity % < 30% even if dollar amount is high."""
    inputs = EncumbranceWaterfallInputs(
        gross_market_value=1000000.0,
        open_mortgage_balance=750000.0,
        estimated_probate_statutory_fees=10000.0
    )
    res = compute_net_actionable_equity(inputs)
    assert res.net_actionable_equity == 240000.0
    assert res.equity_percentage < 0.30
    assert res.gate_3_passed is False
    assert "30.0% viable minimum" in res.disqualification_reason


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


def test_complexity_jtwros_with_ancillary_jurisdiction():
    """Verify JTWROS base + ancillary jurisdiction penalty."""
    inputs = OwnershipComplexityInputs(
        vesting_type=VestingType.JTWROS,
        has_foreign_or_ancillary_jurisdiction=True  # +10 pts
    )
    res = compute_ownership_complexity(inputs)
    assert res.base_score == 35
    assert res.penalties_applied == 10
    assert res.complexity_score == 45


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


def test_opportunity_scoring_contested_factions_disqualification():
    """Confirm contested factions + low equity results in DISQUALIFIED."""
    inputs = OpportunityScoringInputs(
        net_equity_amount=55000.0,
        equity_percentage=0.32,
        authority_tier=AuthorityTier.TIER_4_UNRESOLVED,
        power_scope=PowerScope.UNAUTHORIZED,
        ownership_complexity_score=85,
        control_archetype=ControlArchetype.CONTESTED_FACTIONS,  # -20 pts
        has_contested_caveat_or_will_dispute=True                # -20 pts
    )
    res = compute_opportunity_viability(inputs)
    assert res.priority_tier == PriorityTier.DISQUALIFIED
    assert res.is_deliverable is False
