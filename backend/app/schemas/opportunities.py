from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import LifecycleStage, PriorityTier


class OpportunityBase(BaseModel):
    case_id: UUID
    property_id: UUID
    lifecycle_stage: LifecycleStage = LifecycleStage.DISCOVERED
    composite_viability_score: int = Field(default=0, ge=0, le=100)
    deal_friction_score: int = Field(default=0, ge=0, le=100)
    priority_tier: PriorityTier = PriorityTier.DISQUALIFIED
    dispatch_sla: str = "STANDARD_BATCH"
    is_qc_certified: bool = False


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityResponse(OpportunityBase):
    opportunity_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
