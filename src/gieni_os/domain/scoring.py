"""
Domain Models for Opportunity Scoring Engine (OSE) and Deal Friction Score (DFS).
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

class PriorityTier(str, Enum):
    PRIORITY_A = "PRIORITY_A"  # 85-100: Premier Deal / Flash Dispatch Candidate
    PRIORITY_B = "PRIORITY_B"  # 65-84: High Commercial Viability / Core Queue
    PRIORITY_C = "PRIORITY_C"  # 50-64: Moderate Viability / Requires Strategic Handling
    DISQUALIFIED = "DISQUALIFIED"  # <50: Excessive Friction or Inadequate Equity

class DealStrategy(str, Enum):
    WHOLESALE_CASH_ASSIGNMENT = "WHOLESALE_CASH_ASSIGNMENT"
    NOVATION_PARTNERSHIP = "NOVATION_PARTNERSHIP"
    WHOLETAIL_CLEANOUT = "WHOLETAIL_CLEANOUT"
    DISQUALIFIED_PASS = "DISQUALIFIED_PASS"

class DealFrictionScore(BaseModel):
    """
    Penalties deducted from Gross Upside (0-35 scale).
    """
    model_config = ConfigDict(extra="ignore")

    title_complexity_penalty: int = Field(default=0, ge=0, le=10, description="Title cloud or tenancy complexity")
    authority_friction_penalty: int = Field(default=0, ge=0, le=10, description="Full court supervision or missing nonintervention powers")
    occupancy_penalty: int = Field(default=0, ge=0, le=8, description="Adverse resident, tenant refusal, or estate clean-out burden")
    heir_gridlock_penalty: int = Field(default=0, ge=0, le=7, description="Multi-heir dispute or committee gridlock (Model 3)")
    total_dfs: int = Field(default=0, ge=0, le=35, description="Composite Deal Friction Score")

class OpportunityScore(BaseModel):
    """
    Master Opportunity Score Model.
    Gross Upside = (Equity * 0.35) + (Authority * 0.30) + (Distress * 0.20) + (Liquidity * 0.15)
    Composite Viability Score = max(0, min(100, round(Gross Upside - Total DFS)))
    """
    model_config = ConfigDict(extra="ignore")

    opportunity_id: str
    equity_score: float = Field(ge=0.0, le=100.0)
    authority_score: float = Field(ge=0.0, le=100.0)
    distress_score: float = Field(ge=0.0, le=100.0)
    liquidity_score: float = Field(ge=0.0, le=100.0)
    gross_upside: float = Field(ge=0.0, le=100.0)
    deal_friction: DealFrictionScore
    composite_score: int = Field(ge=0, le=100)
    priority_tier: PriorityTier
    recommended_strategy: DealStrategy
    scoring_notes: Optional[str] = None
