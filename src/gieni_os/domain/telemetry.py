"""
Domain Models for Closed-Loop Telemetry Ingestion & RL Recalibration
"""

from enum import Enum
from typing import Dict, Any, Optional
import time
from pydantic import BaseModel, Field, ConfigDict

class DispositionStage(str, Enum):
    FIRST_TOUCH = "FIRST_TOUCH"
    WALKTHROUGH_BOOKED = "WALKTHROUGH_BOOKED"
    OFFER_PRESENTED = "OFFER_PRESENTED"
    CONTRACT_EXECUTED = "CONTRACT_EXECUTED"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"

class DispositionRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    opportunity_id: str
    client_id: str
    disposition_stage: DispositionStage
    contact_latency_hours: float = 1.5
    offer_amount: float = 0.0
    assignment_fee_realized: float = 0.0
    decision_maker_accurate: bool = True
    disposition_notes: Optional[str] = None
    recorded_at: float = Field(default_factory=time.time)

class CountyCalibrationProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    county_fips: str
    sample_size: int
    closed_won_count: int
    win_rate: float
    calibrated_friction_coefficient: float
    updated_feature_weights: Dict[str, float]
    quarterly_predictive_accuracy_gain_pct: float
