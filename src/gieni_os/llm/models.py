"""
Gieni OS LLM Data Models
Contracts for LLM requests, responses, citations, and provider status.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMProviderType(str, Enum):
    AZURE_OPENAI = "AZURE_OPENAI"
    OLLAMA = "OLLAMA"
    DETERMINISTIC_STATUTORY_ARE = "DETERMINISTIC_STATUTORY_ARE"


class LLMCitation(BaseModel):
    source: str = Field(..., description="Engine, court docket, or statutory code reference")
    citation_id: str = Field(..., description="Unique code or docket identifier, e.g. RCW-11.68.011")
    details: str = Field(..., description="Specific evidentiary summary or quote")


class LLMRequest(BaseModel):
    query: str = Field(..., description="User query or operator inquiry")
    system_instruction: Optional[str] = Field(None, description="System persona and instructions")
    opportunity_context: Optional[Dict[str, Any]] = Field(None, description="Serialized Packet of Facts (POF) context")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="Sampling temperature")
    max_tokens: int = Field(1500, description="Max token response length")
    forced_provider: Optional[LLMProviderType] = Field(None, description="Optionally bypass auto-selection")


class LLMResponse(BaseModel):
    narrative: str = Field(..., description="Structured legal/probate narrative analysis")
    citations: List[LLMCitation] = Field(default_factory=list, description="Grounding legal and factual citations")
    recommendations: List[str] = Field(default_factory=list, description="Concrete operational and disposition next steps")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model or engine confidence score")
    connected_agents: List[str] = Field(default_factory=list, description="Associated Gieni domain agents")
    provider_used: LLMProviderType = Field(..., description="The actual provider that executed the inference")
    model_name: str = Field(..., description="Model identifier or engine name")
    latency_ms: float = Field(..., description="Execution latency in milliseconds")


class LLMProviderInfo(BaseModel):
    provider: LLMProviderType
    is_available: bool
    details: str
    model: str
    endpoint: Optional[str] = None


class LLMStatusResponse(BaseModel):
    active_provider: LLMProviderType
    active_model: str
    providers: Dict[str, LLMProviderInfo]
    fallback_available: bool = True
