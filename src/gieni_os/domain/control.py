"""
Domain Model: Control Archetypes & Decision-Maker Dynamics
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

class ControlArchetype(str, Enum):
    MODEL_1_UNIFIED = "Model 1: Unified Fiduciary Control"       # Fiduciary is sole heir, lives locally
    MODEL_2_BIFURCATED = "Model 2: Bifurcated Control"           # Fiduciary out-of-state, relative on-site
    MODEL_3_COMMITTEE = "Model 3: Committee / Multi-Heir Gridlock"# 3+ heirs with divided goals
    MODEL_4_CARETAKER = "Model 4: Caretaker / Adverse Resident"  # Non-owner resident/squatter refusing to vacate
    MODEL_5_INSTITUTIONAL = "Model 5: Institutional / Attorney Dominated"# Public admin or aggressive law firm gatekeeping

class OccupancyStatus(str, Enum):
    VACANT = "VACANT"
    OWNER_OCCUPIED = "OWNER_OCCUPIED"
    HEIR_RESIDENT = "HEIR_RESIDENT"
    ADVERSE_RESIDENT = "ADVERSE_RESIDENT"
    TENANT_OCCUPIED = "TENANT_OCCUPIED"
    UNKNOWN = "UNKNOWN"

@dataclass
class DecisionMaker:
    name: str
    relationship: str                    # e.g. "Son & Personal Representative", "Tenant"
    is_fiduciary: bool
    is_on_site: bool
    phone: Optional[str] = None
    email: Optional[str] = None
    mailing_address: Optional[str] = None
    influence_weight: float = 1.0        # 0.0 to 1.0

@dataclass
class ControlProfile:
    archetype: ControlArchetype
    primary_decision_maker: DecisionMaker
    occupancy_status: OccupancyStatus
    friction_rating: int                 # 1 (lowest friction) to 10 (highest friction)
    property_id: Optional[str] = None
    on_site_resident: Optional[DecisionMaker] = None
    attorney_gatekeeper_name: Optional[str] = None
    attorney_bypass_strategy: Optional[str] = None
    all_parties: List[DecisionMaker] = field(default_factory=list)
