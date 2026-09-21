"""
Domain Models for Phase 7 Market Validation
Tracks the 3 Business Validation Challenges:
1. 100 Probate Case Challenge
2. Decision Maker Challenge (Ownership != Control)
3. Acquisition Conversation Challenge (Pilot Partner Conversion)
And the Friday Weekly Operating Rhythm Scorecard.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
import time
from pydantic import BaseModel, Field, ConfigDict

class FailureCategory(str, Enum):
    MISSING_PROPERTY = "MISSING_PROPERTY"
    BAD_ADDRESS = "BAD_ADDRESS"
    MULTIPLE_APNS = "MULTIPLE_APNS"
    TRUST_OWNERSHIP = "TRUST_OWNERSHIP"
    BROKEN_TITLE = "BROKEN_TITLE"
    CONTESTED_PETITION = "CONTESTED_PETITION"
    DECEASED_FIDUCIARY = "DECEASED_FIDUCIARY"
    OTHER = "OTHER"

class CountyValidationReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    county_id: str
    county_name: str
    total_cases_entered: int = 100
    cases_parsed_successfully: int = 0
    intake_accuracy_pct: float = 0.0      # Target: >= 95.0%
    property_matches_found: int = 0
    pas_above_70_count: int = 0
    property_match_pct: float = 0.0       # Target: >= 80.0% (Ideal 90%)
    failure_breakdown: Dict[str, int] = Field(default_factory=dict)
    backlog_action_items: List[str] = Field(default_factory=list)
    generated_at: float = Field(default_factory=time.time)

class DecisionMakerAuditResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    case_number: str
    opportunity_id: str
    decedent_name: str
    system_decision_maker: str
    system_authority_tier: str
    system_control_archetype: str
    court_record_fiduciary: str
    court_letters_status: str
    court_attorney_name: Optional[str] = None
    is_authority_accurate: bool
    notes: Optional[str] = None

class DecisionMakerChallengeReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sample_size: int = 50
    correct_fiduciary_count: int = 0
    authority_accuracy_pct: float = 0.0   # Target: >= 80.0% (Ideal 90%)
    audit_results: List[DecisionMakerAuditResult] = Field(default_factory=list)
    failure_patterns: Dict[str, int] = Field(default_factory=dict)
    generated_at: float = Field(default_factory=time.time)

class PilotOpportunityStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    opportunity_id: str
    property_address: str
    net_equity: float
    composite_score: int
    priority_tier: str
    contacted: bool = False
    contact_channel: Optional[str] = None
    response_received: bool = False
    real_conversation: bool = False
    appointment_booked: bool = False
    offer_presented: bool = False
    offer_amount: float = 0.0
    contract_executed: bool = False
    wholesale_fee_realized: float = 0.0
    buyer_feedback_notes: Optional[str] = None

class PilotConversationTracker(BaseModel):
    model_config = ConfigDict(extra="ignore")

    partner_name: str
    territory_county: str
    trial_duration_days: int = 30
    total_delivered: int = 20            # Target: 20 Priority A Deals
    contacted_count: int = 0
    response_count: int = 0
    conversation_count: int = 0
    conversation_rate_pct: float = 0.0   # Target: >= 20.0%
    appointment_count: int = 0
    offer_count: int = 0
    contract_count: int = 0
    total_fees_realized: float = 0.0
    opportunities: List[PilotOpportunityStatus] = Field(default_factory=list)

class WeeklyHealthScorecard(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reporting_date: str
    county_name: str
    cases_processed: int
    property_match_pct: float
    authority_success_pct: float
    qc_pass_pct: float
    conversation_pct: float
    offer_pct: float
    contract_pct: float
    red_flag_triggers: List[str] = Field(default_factory=list)
    health_status: str = "HEALTHY"       # HEALTHY, WARNING, CRITICAL_SYSTEM_RECALIBRATION
    next_week_priorities: List[str] = Field(default_factory=list)
