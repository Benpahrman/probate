from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import PriorityTier, AuthorityTier, PowerScope, ControlArchetype


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


def _calculate_equity_pillar(equity_percentage: float, net_equity_amount: float) -> float:
    pct_score = min(50.0, (equity_percentage / 0.70) * 50.0)
    dollar_score = min(50.0, (net_equity_amount / 200000.0) * 50.0)
    return pct_score + dollar_score


AUTHORITY_PILLAR_SCORES: dict[AuthorityTier, float] = {
    AuthorityTier.TIER_1_CONFIRMED: 100.0,
    AuthorityTier.TIER_2_LIKELY: 75.0,
    AuthorityTier.TIER_3_STAKEHOLDER_CONSENSUS: 45.0,
    AuthorityTier.TIER_4_UNRESOLVED: 15.0,
}


def _calculate_distress_pillar(inputs: OpportunityScoringInputs) -> float:
    points = 0.0
    if inputs.is_vacant:
        points += 35.0
    if inputs.has_notice_of_default_or_lis_pendens:
        points += 30.0
    if inputs.has_tax_delinquency:
        points += 20.0
    if inputs.has_code_violations:
        points += 15.0
    return min(100.0, points)


CONTROL_FRICTION_PENALTIES: dict[ControlArchetype, int] = {
    ControlArchetype.CONTESTED_FACTIONS: 20,
    ControlArchetype.PROXY_CONTROLLER: 8,
    ControlArchetype.INFORMAL_FAMILY_LEADER: 5,
}


def _calculate_deal_friction(inputs: OpportunityScoringInputs) -> int:
    friction = 0
    if inputs.power_scope == PowerScope.DEPENDENT_COURT_SUPERVISED:
        friction += 15
    friction += CONTROL_FRICTION_PENALTIES.get(inputs.control_archetype, 0)
    if inputs.has_contested_caveat_or_will_dispute:
        friction += 20
    if inputs.has_unprobated_title_gap:
        friction += 15
    if inputs.ownership_complexity_score > 50:
        friction += int((inputs.ownership_complexity_score - 50) * 0.25)
    return min(35, max(0, friction))


def _is_priority_a(composite_score: int, net_equity: float, authority_tier: AuthorityTier) -> bool:
    if composite_score < 80:
        return False
    if net_equity < 150000.0:
        return False
    return authority_tier in (
        AuthorityTier.TIER_1_CONFIRMED,
        AuthorityTier.TIER_2_LIKELY
    )


def _classify_priority(
    composite_score: int,
    net_equity: float,
    authority_tier: AuthorityTier
) -> tuple[PriorityTier, str, bool, str]:
    if _is_priority_a(composite_score, net_equity, authority_tier):
        return (
            PriorityTier.PRIORITY_A,
            "FLASH_ALERT_4_HOUR",
            True,
            "Exceptional equity and confirmed authority. Priority A instant dispatch SLA."
        )
    if composite_score >= 60:
        return (
            PriorityTier.PRIORITY_B,
            "STANDARD_BATCH_MONDAY_8AM",
            True,
            "Core production queue. Deliverable in standard weekly partner batch."
        )
    if composite_score >= 40:
        return (
            PriorityTier.PRIORITY_C,
            "MILESTONE_WATCH",
            False,
            "High friction file. Quarantined on docket milestone watch until Letters issue."
        )
    return (
        PriorityTier.DISQUALIFIED,
        "SUPPRESSED",
        False,
        "Disqualified. Inadequate equity spread or fatal legal dispute."
    )


def compute_opportunity_viability(inputs: OpportunityScoringInputs) -> OpportunityScoringResult:
    """Computes the 0-100 Composite Viability Score balancing Gross Upside against DFS:

    Gross Upside = (P1_Equity * 0.35) + (P2_Authority * 0.30) + (P3_Distress * 0.20) + (P4_Liquidity * 0.15)
    Composite Score = max(0, min(100, round(Gross Upside - Deal Friction Score)))
    """
    p1_equity = _calculate_equity_pillar(inputs.equity_percentage, inputs.net_equity_amount)
    p2_authority = AUTHORITY_PILLAR_SCORES.get(inputs.authority_tier, 15.0)
    p3_distress = _calculate_distress_pillar(inputs)
    base_liquidity = 85.0 if inputs.is_single_family_residence else 60.0
    p4_liquidity = min(100.0, base_liquidity * inputs.county_liquidity_multiplier)

    gross_upside = (
        (p1_equity * 0.35) +
        (p2_authority * 0.30) +
        (p3_distress * 0.20) +
        (p4_liquidity * 0.15)
    )

    dfs = _calculate_deal_friction(inputs)
    composite_score = round(max(0.0, min(100.0, gross_upside - float(dfs))))
    tier, sla, is_deliverable, summary = _classify_priority(
        composite_score,
        inputs.net_equity_amount,
        inputs.authority_tier
    )

    return OpportunityScoringResult(
        composite_viability_score=composite_score,
        gross_upside_score=round(gross_upside, 2),
        deal_friction_score=dfs,
        priority_tier=tier,
        dispatch_sla=sla,
        is_deliverable=is_deliverable,
        summary=summary
    )
