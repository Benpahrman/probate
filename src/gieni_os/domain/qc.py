"""
Domain Models for Automated 6-Gate Quality Control Pass (QCA) and HITL Exceptions.
"""

from typing import List, Optional
import time
from pydantic import BaseModel, Field, ConfigDict

class GateResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    gate_number: int = Field(ge=1, le=6)
    gate_name: str
    passed: bool
    score: float
    threshold: float
    rationale: str

class QCValidationReport(BaseModel):
    """
    Automated 6-Gate Quality Control Pass Certification Report.
    """
    model_config = ConfigDict(extra="ignore")

    opportunity_id: str
    gates: List[GateResult]
    all_passed: bool
    certification_stamp: Optional[str] = None
    certification_timestamp: float = Field(default_factory=time.time)
    requires_hitl: bool = False
    hitl_reasons: List[str] = Field(default_factory=list)
    analyst_override: bool = False
    analyst_notes: Optional[str] = None
