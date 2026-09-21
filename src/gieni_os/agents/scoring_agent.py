"""
Scoring Agent
Calculates Master Opportunity Viability Formula, Deal Friction Score, Priority Tier, and Strategy.
"""

from typing import Dict, Any
from gieni_os.agents.base import BaseAgent
from gieni_os.engines.scoring_engine import ScoringEngine
from gieni_os.domain.authority import AuthorityTier
from gieni_os.domain.control import ControlArchetype, OccupancyStatus
from gieni_os.domain.ownership import VestingType

class ScoringAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="agt_scoring",
            agent_name="Opportunity Scoring Agent",
            version="2.0.0"
        )
        self.engine = ScoringEngine()

    def validate(self, payload: Dict[str, Any]) -> bool:
        return bool(payload.get("opportunity_id"))

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate(payload):
            raise ValueError("Invalid scoring payload: opportunity_id is required.")

        opp_id = payload["opportunity_id"]
        est_val = float(payload.get("estimated_value", 500000.0))
        net_eq = float(payload.get("net_equity", 250000.0))

        # Parse enums safely
        raw_auth = payload.get("authority_tier", AuthorityTier.TIER_1_CERTIFIED.value)
        try:
            auth_tier = AuthorityTier(raw_auth)
        except ValueError:
            auth_tier = AuthorityTier.TIER_1_CERTIFIED

        raw_arch = payload.get("control_archetype", ControlArchetype.MODEL_1_UNIFIED.value)
        try:
            archetype = ControlArchetype(raw_arch)
        except ValueError:
            archetype = ControlArchetype.MODEL_1_UNIFIED

        raw_occ = payload.get("occupancy_status", OccupancyStatus.OWNER_OCCUPIED.value)
        try:
            occ_status = OccupancyStatus(raw_occ)
        except ValueError:
            occ_status = OccupancyStatus.OWNER_OCCUPIED

        raw_vest = payload.get("vesting_type", VestingType.FEE_SIMPLE_SOLE.value)
        try:
            vesting = VestingType(raw_vest)
        except ValueError:
            vesting = VestingType.FEE_SIMPLE_SOLE

        title_complexity = int(payload.get("title_complexity_score", 0))
        court_oversight = bool(payload.get("court_oversight_required", False))
        has_distress = bool(payload.get("has_distress_flags", True))
        is_sfr = bool(payload.get("is_single_family", True))

        score_result = self.engine.calculate_score(
            opportunity_id=opp_id,
            estimated_value=est_val,
            net_equity=net_eq,
            authority_tier=auth_tier,
            archetype=archetype,
            occupancy_status=occ_status,
            vesting_type=vesting,
            title_complexity_score=title_complexity,
            court_oversight_required=court_oversight,
            has_distress_flags=has_distress,
            is_single_family=is_sfr
        )

        return {
            "status": "SCORED",
            "opportunity_id": opp_id,
            "opportunity_score": score_result,
            "composite_score": score_result.composite_score,
            "gross_upside": score_result.gross_upside,
            "deal_friction_score": score_result.deal_friction.total_dfs,
            "priority_tier": score_result.priority_tier.value,
            "recommended_strategy": score_result.recommended_strategy.value,
            "scoring_notes": score_result.scoring_notes
        }

    def return_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        return result
