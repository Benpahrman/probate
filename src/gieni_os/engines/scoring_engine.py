"""
Opportunity Scoring Engine (OSE)
Computes Master Viability Scoring Formula, Deal Friction Score (DFS) matrix,
Priority Tiers, and Exit Strategies.
"""

from typing import Dict, Any, Optional
import logging
from gieni_os.domain.scoring import (
    PriorityTier,
    DealStrategy,
    DealFrictionScore,
    OpportunityScore
)
from gieni_os.domain.authority import AuthorityTier
from gieni_os.domain.control import ControlArchetype, OccupancyStatus
from gieni_os.domain.ownership import VestingType

logger = logging.getLogger("ScoringEngine")

class ScoringEngine:
    """
    Deterministic implementation of GOS Master Viability Formula:
    Gross Upside = (Equity * 0.35) + (Authority * 0.30) + (Distress * 0.20) + (Liquidity * 0.15)
    Composite Score = max(0, min(100, round(Gross Upside - Deal Friction Score)))
    """

    def calculate_deal_friction(
        self,
        vesting_type: Optional[VestingType] = None,
        title_complexity_score: int = 0,
        authority_tier: Optional[AuthorityTier] = None,
        court_oversight_required: bool = False,
        archetype: Optional[ControlArchetype] = None,
        occupancy_status: Optional[OccupancyStatus] = None,
        dispute_detected: bool = False
    ) -> DealFrictionScore:
        # 1. Title Complexity Penalty (0-10)
        title_penalty = min(10, max(0, title_complexity_score))
        if vesting_type == VestingType.TENANTS_IN_COMMON and title_penalty < 5:
            title_penalty = 5

        # 2. Authority / Court Friction Penalty (0-10)
        auth_penalty = 0
        if court_oversight_required:
            auth_penalty += 6
        if authority_tier == AuthorityTier.TIER_4_UNCERTAIN:
            auth_penalty += 8
        elif authority_tier == AuthorityTier.TIER_3_NON_PROBATE:
            auth_penalty += 3
        elif authority_tier == AuthorityTier.TIER_2_PROBABLE:
            auth_penalty += 2
        elif authority_tier == AuthorityTier.TIER_1_CERTIFIED:
            auth_penalty += 0
        auth_penalty = min(10, auth_penalty)

        # 3. Occupancy Penalty (0-8)
        occ_penalty = 0
        if occupancy_status == OccupancyStatus.ADVERSE_RESIDENT:
            occ_penalty = 8
        elif occupancy_status in (OccupancyStatus.TENANT_OCCUPIED, "TENANT"):
            occ_penalty = 5
        elif occupancy_status == OccupancyStatus.HEIR_RESIDENT:
            occ_penalty = 3
        elif occupancy_status == OccupancyStatus.OWNER_OCCUPIED:
            occ_penalty = 2
        elif occupancy_status == OccupancyStatus.VACANT:
            occ_penalty = 0
        occ_penalty = min(8, occ_penalty)

        # 4. Heir Gridlock Penalty (0-7)
        heir_penalty = 0
        if archetype in (ControlArchetype.MODEL_3_COMMITTEE, "MODEL_3_COMMITTEE_GRIDLOCK") or dispute_detected:
            heir_penalty = 7
        elif archetype in (ControlArchetype.MODEL_4_CARETAKER, "MODEL_4_CARETAKER_ADVERSE"):
            heir_penalty = 4
        elif archetype == ControlArchetype.MODEL_2_BIFURCATED:
            heir_penalty = 3
        elif archetype == ControlArchetype.MODEL_5_INSTITUTIONAL:
            heir_penalty = 2
        elif archetype == ControlArchetype.MODEL_1_UNIFIED:
            heir_penalty = 0
        heir_penalty = min(7, heir_penalty)

        total_dfs = min(35, title_penalty + auth_penalty + occ_penalty + heir_penalty)

        return DealFrictionScore(
            title_complexity_penalty=title_penalty,
            authority_friction_penalty=auth_penalty,
            occupancy_penalty=occ_penalty,
            heir_gridlock_penalty=heir_penalty,
            total_dfs=total_dfs
        )

    def calculate_score(
        self,
        opportunity_id: str,
        estimated_value: float,
        net_equity: float,
        authority_tier: AuthorityTier,
        archetype: ControlArchetype,
        occupancy_status: OccupancyStatus,
        vesting_type: VestingType = VestingType.FEE_SIMPLE_SOLE,
        title_complexity_score: int = 0,
        court_oversight_required: bool = False,
        has_distress_flags: bool = True,
        is_single_family: bool = True,
        dispute_detected: bool = False
    ) -> OpportunityScore:
        # A. Equity Score (0-100)
        equity_ratio = (net_equity / estimated_value) if estimated_value > 0 else 0.0
        if net_equity <= 0:
            equity_score = 0.0
        elif equity_ratio >= 0.50 and net_equity >= 150000:
            equity_score = min(100.0, 85.0 + (equity_ratio * 25.0))
        elif equity_ratio >= 0.30:
            equity_score = min(84.0, 60.0 + (equity_ratio * 40.0))
        elif equity_ratio >= 0.15:
            equity_score = 50.0
        else:
            equity_score = 25.0

        # B. Authority Score (0-100)
        if authority_tier == AuthorityTier.TIER_1_CERTIFIED:
            authority_score = 98.0 if not court_oversight_required else 80.0
        elif authority_tier == AuthorityTier.TIER_2_PROBABLE:
            authority_score = 80.0
        elif authority_tier == AuthorityTier.TIER_3_NON_PROBATE:
            authority_score = 65.0
        else:
            authority_score = 25.0

        # C. Distress Score (0-100)
        distress_score = 75.0 if has_distress_flags else 50.0
        if occupancy_status in (OccupancyStatus.VACANT, OccupancyStatus.ADVERSE_RESIDENT):
            distress_score = min(100.0, distress_score + 15.0)

        # D. Liquidity Score (0-100)
        liquidity_score = 90.0 if is_single_family else 70.0

        # Master Formula:
        gross_upside = (
            (equity_score * 0.35) +
            (authority_score * 0.30) +
            (distress_score * 0.20) +
            (liquidity_score * 0.15)
        )
        gross_upside = max(0.0, min(100.0, gross_upside))

        # Deal Friction Score:
        deal_friction = self.calculate_deal_friction(
            vesting_type=vesting_type,
            title_complexity_score=title_complexity_score,
            authority_tier=authority_tier,
            court_oversight_required=court_oversight_required,
            archetype=archetype,
            occupancy_status=occupancy_status,
            dispute_detected=dispute_detected
        )

        composite_score = max(0, min(100, round(gross_upside - deal_friction.total_dfs)))

        # Priority Tiers:
        if composite_score >= 85:
            priority_tier = PriorityTier.PRIORITY_A
        elif composite_score >= 65:
            priority_tier = PriorityTier.PRIORITY_B
        elif composite_score >= 50:
            priority_tier = PriorityTier.PRIORITY_C
        else:
            priority_tier = PriorityTier.DISQUALIFIED

        # Exit Strategy:
        if priority_tier in (PriorityTier.PRIORITY_A, PriorityTier.PRIORITY_B) and equity_ratio >= 0.40:
            strategy = DealStrategy.WHOLESALE_CASH_ASSIGNMENT
        elif priority_tier in (PriorityTier.PRIORITY_B, PriorityTier.PRIORITY_C):
            strategy = DealStrategy.NOVATION_PARTNERSHIP
        elif priority_tier == PriorityTier.PRIORITY_C:
            strategy = DealStrategy.WHOLETAIL_CLEANOUT
        else:
            strategy = DealStrategy.DISQUALIFIED_PASS

        notes = (
            f"Gross: {gross_upside:.1f} | DFS: -{deal_friction.total_dfs} "
            f"(Title: {deal_friction.title_complexity_penalty}, Auth: {deal_friction.authority_friction_penalty}, "
            f"Occ: {deal_friction.occupancy_penalty}, Heir: {deal_friction.heir_gridlock_penalty}) "
            f"-> Composite: {composite_score} ({priority_tier.value})"
        )

        logger.info(f"[{opportunity_id}] Scored: {notes}")

        return OpportunityScore(
            opportunity_id=opportunity_id,
            equity_score=round(equity_score, 1),
            authority_score=round(authority_score, 1),
            distress_score=round(distress_score, 1),
            liquidity_score=round(liquidity_score, 1),
            gross_upside=round(gross_upside, 1),
            deal_friction=deal_friction,
            composite_score=composite_score,
            priority_tier=priority_tier,
            recommended_strategy=strategy,
            scoring_notes=notes
        )
