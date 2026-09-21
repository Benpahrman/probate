"""
Domain Models for Automated 14-Day County Expansion & Feasibility Scoring
"""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class ExpansionStatus(str, Enum):
    LAUNCH_IMMEDIATE = "LAUNCH_IMMEDIATE"  # Score >= 80
    PILOT_CANDIDATE = "PILOT_CANDIDATE"    # Score 65-79
    MONITORING = "MONITORING"              # Score 50-64
    INELIGIBLE = "INELIGIBLE"              # Score < 50

class CountyFeasibility(BaseModel):
    model_config = ConfigDict(extra="ignore")

    county_id: str
    county_name: str
    population: int
    population_score: float = Field(ge=0.0, le=100.0)
    court_portal_score: float = Field(ge=0.0, le=100.0)
    market_liquidity_score: float = Field(ge=0.0, le=100.0)
    statutory_clarity_score: float = Field(ge=0.0, le=100.0)
    partner_anchor_score: float = Field(ge=0.0, le=100.0)
    composite_feasibility: float = Field(ge=0.0, le=100.0)
    status: ExpansionStatus
    playbook_milestones: List[str] = Field(default_factory=list)
