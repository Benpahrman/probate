"""
Gieni OS AI Investigator API Router
Orchestrates domain intelligence, narrative synthesis, statutory legal analysis,
and concrete recommendations via the Gieni LLM Gateway (supporting Azure OpenAI,
Ollama, and verified Washington State RCW Title 11 deterministic rule engine fallback).
"""

import dataclasses
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from gieni_os.database.connection import get_db
from gieni_os.database.models import OpportunityModel
from gieni_os.api.routes.opportunities import build_pof_for_opportunity
from gieni_os.llm.gateway import default_llm_gateway
from gieni_os.llm.models import LLMProviderType

router = APIRouter(prefix="/ai", tags=["AI Investigator"])


class InvestigateRequest(BaseModel):
    opportunity_id: str
    query: Optional[str] = None
    question: Optional[str] = None
    forced_provider: Optional[LLMProviderType] = None


class Citation(BaseModel):
    source: str
    citation_id: str
    details: str


class InvestigateResponse(BaseModel):
    query: str
    opportunity_id: str
    narrative: str
    citations: List[Citation]
    recommendations: List[str]
    confidence_score: float
    connected_agents: List[str]
    provider_used: str
    model_name: str
    latency_ms: float


@router.post("/investigate", response_model=InvestigateResponse)
def investigate_opportunity(req: InvestigateRequest, db: Session = Depends(get_db)):
    opp = db.query(OpportunityModel).filter(OpportunityModel.id == req.opportunity_id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")

    pof = build_pof_for_opportunity(opp)
    if dataclasses.is_dataclass(pof):
        pof_dict = dataclasses.asdict(pof)
    elif hasattr(pof, "model_dump"):
        pof_dict = pof.model_dump()
    elif hasattr(pof, "dict"):
        pof_dict = pof.dict()
    else:
        pof_dict = getattr(pof, "__dict__", {})

    raw_query = req.query or req.question or "Provide probate and title intelligence evaluation."

    from gieni_os.intelligence.context import IntelligenceContext
    intel = IntelligenceContext(db=db)
    county_name = opp.county.name if opp.county else "Pierce"
    forced = req.forced_provider.value if req.forced_provider else None

    reasoning_resp = intel.evaluate_opportunity(
        opportunity_id=opp.id,
        inquiry=raw_query,
        opportunity_context=pof_dict,
        county_name=county_name,
        forced_provider=forced,
    )

    api_citations = [
        Citation(
            source=c.get("source", "Intelligence Context"),
            citation_id=c.get("citation_id", "ARE-STATUTORY"),
            details=c.get("details", ""),
        )
        for c in reasoning_resp.citations
    ]

    agents = ["IntelligenceContext", "ReasoningService", "MemoryService", "KnowledgeService"]
    q_lower = raw_query.lower()
    if "authority" in q_lower or "statut" in q_lower or "rcw" in q_lower or "path" in q_lower:
        agents.append("AuthorityAgent")
    if "control" in q_lower or "decision" in q_lower or "who" in q_lower:
        agents.append("ControlAgent")
    if "equity" in q_lower or "vesting" in q_lower or "title" in q_lower or "priority" in q_lower:
        agents.append("OwnershipAgent")
    if "score" in q_lower or "priority" in q_lower:
        agents.append("ScoringAgent")
    if "missing" in q_lower or "gap" in q_lower or "qc" in q_lower:
        agents.append("QCAgent")

    # If general inquiry, include core domain triad
    if len(agents) <= 4:
        agents.extend(["AuthorityAgent", "ControlAgent", "OwnershipAgent"])

    return InvestigateResponse(
        query=raw_query,
        opportunity_id=opp.id,
        narrative=reasoning_resp.narrative,
        citations=api_citations,
        recommendations=reasoning_resp.recommendations,
        confidence_score=reasoning_resp.confidence,
        connected_agents=agents,
        provider_used=reasoning_resp.provider_used,
        model_name=reasoning_resp.provider_used,
        latency_ms=reasoning_resp.latency_ms,
    )
