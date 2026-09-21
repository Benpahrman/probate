"""
Domain Model: Ownership, Vesting & Equity Waterfall
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class VestingType(str, Enum):
    FEE_SIMPLE_SOLE = "Fee Simple Sole Ownership"
    JOINT_TENANCY_WROS = "Joint Tenancy with Right of Survivorship"
    COMMUNITY_PROPERTY = "Community Property with Right of Survivorship"
    TENANTS_IN_COMMON = "Tenants in Common"
    REVOCABLE_TRUST = "Revocable Living Trust"
    UNKNOWN = "Unknown / Title Ambiguity"

@dataclass
class EquityWaterfall:
    estimated_market_value: float
    total_senior_debt: float
    junior_liens: float
    estimated_repairs: float
    closing_and_probate_costs: float
    net_equity: float
    equity_spread_ratio: float

@dataclass
class OwnershipRecord:
    property_id: str
    vesting_type: VestingType
    title_complexity_score: int       # 0 (Clean) to 10 (Clouded / Curative Required)
    title_holders: List[str]
    waterfall: EquityWaterfall
    curative_required: bool = False
    curative_notes: Optional[str] = None

    @property
    def complexity_score(self) -> int:
        return self.title_complexity_score
