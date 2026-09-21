"""
Composite Opportunity Viability Scoring Engine
Computes the 0-100 Composite Viability Score balancing four weighted pillars
(Net Equity, Signatory Authority, Distress Indicators, Market Liquidity) against
a Deal Friction Score (DFS) deduction.

Transplanted from backend/app/engines/scoring.py.
Imports rewritten: app.models.enums → gieni_os.domain.enums
"""

from pydantic import BaseModel, Field, ConfigDict
from gieni_os.domain.enums import PriorityTier, AuthorityTier, PowerScope, ControlArchetype


class OpportunityScoringInputs(BaseModel):
    # Pillar 1: Net Equity Factor (Weight: 35%)
    net_equity_amount: float = Field(..., ge=0.0)
    equity_percentage: float = Field(..., ge=0.0, le=1.0)

    # Pillar 2: Signatory Authority Factor (Weight: 30%)
    authority_tier: AuthorityTier
    power_scope: PowerScope

    # Pillar 3: Distress Indicators (Weight: 20%)
    is_vacant: bool = Field(default=False)
    has_tax_delinquency: bool = Field(default=False)
    has_notice_of_default_or_lis_pendens: bool = Field(default=False)
    has_code_violations: bool = Field(default=False)

    # Pillar 4: Real Estate Liquidity (Weight: 15%)
    is_single_family_residence: bool = Field(default=True)
    county_liquidity_multiplier: float = Field(default=1.0, ge=0.5, le=1.5)

    # Deal Friction Parameters (Deductions: 0 - 35 points)
    ownership_complexity_score: int = Field(..., ge=10, le=100)
    control_archetype: ControlArchetype
    has_unprobated_title_gap: bool = Field(default=False)
    has_contested_caveat_or_will_dispute: bool = Field(default=False)

    model_config = ConfigDict(extra="forbid")


class OpportunityScoringResult(BaseModel):
    composite_viability_score: int = Field(..., ge=0, le=100)
    gross_upside_score: float
    deal_friction_score: int = Field(..., ge=0, le=35)
    priority_tier: PriorityTier
    dispatch_sla: str
    is_deliverable: bool
    summary: str


def compute_opportunity_viability(inputs: OpportunityScoringInputs) -> OpportunityScoringResult:
    """Computes the 0-100 Composite Viability Score balancing Gross Upside against DFS:

    Gross Upside = (P1_Equity * 0.35) + (P2_Authority * 0.30) + (P3_Distress * 0.20) + (P4_Liquidity * 0.15)
    Composite Score = max(0, min(100, round(Gross Upside - Deal Friction Score)))
    """
    # -------------------------------------------------------------
    # 1. PILLAR 1: Equity Score (0 to 100)
    # -------------------------------------------------------------
    pct_score = min(50.0, (inputs.equity_percentage / 0.70) * 50.0)
    dollar_score = min(50.0, (inputs.net_equity_amount / 200000.0) * 50.0)
    p1_equity = pct_score + dollar_score

    # -------------------------------------------------------------
    # 2. PILLAR 2: Authority Score (0 to 100)
    # -------------------------------------------------------------
    if inputs.authority_tier == AuthorityTier.TIER_1_CONFIRMED:
        p2_authority = 100.0
    elif inputs.authority_tier == AuthorityTier.TIER_2_LIKELY:
        p2_authority = 75.0
    elif inputs.authority_tier == AuthorityTier.TIER_3_STAKEHOLDER_CONSENSUS:
        p2_authority = 45.0
    else:  # TIER_4_UNRESOLVED
        p2_authority = 15.0

    # -------------------------------------------------------------
    # 3. PILLAR 3: Distress Score (0 to 100)
    # -------------------------------------------------------------
    distress_points = 0.0
    if inputs.is_vacant:
        distress_points += 35.0
    if inputs.has_notice_of_default_or_lis_pendens:
        distress_points += 30.0
    if inputs.has_tax_delinquency:
        distress_points += 20.0
    if inputs.has_code_violations:
        distress_points += 15.0
    p3_distress = min(100.0, distress_points)

    # -------------------------------------------------------------
    # 4. PILLAR 4: Liquidity Score (0 to 100)
    # -------------------------------------------------------------
    base_liquidity = 85.0 if inputs.is_single_family_residence else 60.0
    p4_liquidity = min(100.0, base_liquidity * inputs.county_liquidity_multiplier)

    # -------------------------------------------------------------
    # GROSS UPSIDE CALCULATION
    # -------------------------------------------------------------
    gross_upside = (
        (p1_equity * 0.35) +
        (p2_authority * 0.30) +
        (p3_distress * 0.20) +
        (p4_liquidity * 0.15)
    )

    # -------------------------------------------------------------
    # DEAL FRICTION SCORE (DFS) DEDUCTION (0 to 35 points)
    # -------------------------------------------------------------
    friction = 0

    # A. Court Oversight Penalty
    if inputs.power_scope == PowerScope.DEPENDENT_COURT_SUPERVISED:
        friction += 15  # Mandatory Court Confirmation Penalty

    # B. Control Dynamics Penalty
    if inputs.control_archetype == ControlArchetype.CONTESTED_FACTIONS:
        friction += 20
    elif inputs.control_archetype == ControlArchetype.PROXY_CONTROLLER:
        friction += 8
    elif inputs.control_archetype == ControlArchetype.INFORMAL_FAMILY_LEADER:
        friction += 5

    # C. Title & Dispute Cloud Penalties
    if inputs.has_contested_caveat_or_will_dispute:
        friction += 20
    if inputs.has_unprobated_title_gap:
        friction += 15

    # D. Ownership Complexity Scaling (OCS > 50 yields deduction)
    if inputs.ownership_complexity_score > 50:
        friction += int((inputs.ownership_complexity_score - 50) * 0.25)

    # Cap DFS at 35 points max deduction
    dfs = min(35, max(0, friction))

    # -------------------------------------------------------------
    # COMPOSITE SCORE & PRIORITY TIER CLASSIFICATION
    # -------------------------------------------------------------
    composite_score = int(round(max(0.0, min(100.0, gross_upside - float(dfs)))))

    if composite_score >= 80 and inputs.net_equity_amount >= 150000.0 and inputs.authority_tier in [
        AuthorityTier.TIER_1_CONFIRMED, AuthorityTier.TIER_2_LIKELY
    ]:
        tier = PriorityTier.PRIORITY_A
        sla = "FLASH_ALERT_4_HOUR"
        is_deliverable = True
        summary = "Exceptional equity and confirmed authority. Priority A instant dispatch SLA."
    elif composite_score >= 60:
        tier = PriorityTier.PRIORITY_B
        sla = "STANDARD_BATCH_MONDAY_8AM"
        is_deliverable = True
        summary = "Core production queue. Deliverable in standard weekly partner batch."
    elif composite_score >= 40:
        tier = PriorityTier.PRIORITY_C
        sla = "MILESTONE_WATCH"
        is_deliverable = False
        summary = "High friction file. Quarantined on docket milestone watch until Letters issue."
    else:
        tier = PriorityTier.DISQUALIFIED
        sla = "SUPPRESSED"
        is_deliverable = False
        summary = "Disqualified. Inadequate equity spread or fatal legal dispute."

    return OpportunityScoringResult(
        composite_viability_score=composite_score,
        gross_upside_score=round(gross_upside, 2),
        deal_friction_score=dfs,
        priority_tier=tier,
        dispatch_sla=sla,
        is_deliverable=is_deliverable,
        summary=summary
    )
