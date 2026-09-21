"""
Gieni OS Intelligence Context Data Models
Data contracts for Memory, Observations, Knowledge, Learning, and Reasoning.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class MemoryScope(str, Enum):
    CASE = "CASE"
    OPPORTUNITY = "OPPORTUNITY"
    COUNTY = "COUNTY"
    ORGANIZATION = "ORGANIZATION"
    PLATFORM = "PLATFORM"


class ObservationSource(str, Enum):
    ENGINE = "ENGINE"
    AGENT = "AGENT"
    OPERATOR = "OPERATOR"
    COURT_RECORD = "COURT_RECORD"
    TITLE_REPORT = "TITLE_REPORT"


class MemoryObservationDTO(BaseModel):
    id: Optional[str] = None
    observation: str
    source: ObservationSource = ObservationSource.ENGINE
    confidence: float = Field(0.90, ge=0.0, le=1.0)
    created_at: Optional[datetime] = None


class MemoryEntryDTO(BaseModel):
    id: Optional[str] = None
    scope: MemoryScope
    entity_id: str
    summary: str
    confidence: float = Field(0.90, ge=0.0, le=1.0)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    observations: List[MemoryObservationDTO] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class KnowledgeArticleDTO(BaseModel):
    id: Optional[str] = None
    category: str
    title: str
    content: str
    county_id: Optional[str] = None
    statutory_reference: Optional[str] = None
    version: str = "1.0.0"


class LearningOutcomeType(str, Enum):
    OFFER = "OFFER"
    CONTRACT = "CONTRACT"
    DEAD_DEAL = "DEAD_DEAL"
    NO_RESPONSE = "NO_RESPONSE"
    CLOSING = "CLOSING"


class LearningEventDTO(BaseModel):
    id: Optional[str] = None
    opportunity_id: str
    county_id: str
    event_type: LearningOutcomeType
    realized_margin: Optional[float] = None
    delta_score: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class StakeholderRole(str, Enum):
    RESEARCHER = "RESEARCHER"
    QC_ANALYST = "QC_ANALYST"
    CLIENT_INVESTOR = "CLIENT_INVESTOR"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class RecommendationActionDTO(BaseModel):
    action_type: str
    title: str
    instructions: str
    urgency: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    target_role: StakeholderRole
    statutory_citations: List[str] = Field(default_factory=list)


class ReasoningRequestDTO(BaseModel):
    inquiry: str
    context: Dict[str, Any] = Field(default_factory=dict)
    case_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    county_name: Optional[str] = None
    forced_provider: Optional[str] = None


class ReasoningResponseDTO(BaseModel):
    summary: str
    narrative: str
    risk_assessment: str
    confidence: float
    citations: List[Dict[str, str]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    memory_referenced: List[str] = Field(default_factory=list)
    knowledge_referenced: List[str] = Field(default_factory=list)
    provider_used: str
    latency_ms: float
