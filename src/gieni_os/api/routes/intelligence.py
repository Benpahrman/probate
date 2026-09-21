"""
Gieni OS Intelligence Context API Router
Exposes the central cognitive brain: Memory, Reasoning, Retrieval,
Knowledge, Learning, Recommendations, and Embeddings.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from gieni_os.database.connection import get_db
from gieni_os.api.deps import require_operator_role
from gieni_os.intelligence.models import (
    MemoryScope,
    ObservationSource,
    StakeholderRole,
    MemoryEntryDTO,
    KnowledgeArticleDTO,
    LearningOutcomeType,
    LearningEventDTO,
    RecommendationActionDTO,
    ReasoningRequestDTO,
    ReasoningResponseDTO,
)
from gieni_os.intelligence.context import IntelligenceContext

router = APIRouter(prefix="/intelligence", tags=["Intelligence Context"])


class StoreMemoryRequest(BaseModel):
    scope: MemoryScope
    entity_id: str
    summary: str
    observations: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.90


class RecommendationRequest(BaseModel):
    context: Dict[str, Any] = Field(default_factory=dict)
    role: StakeholderRole = StakeholderRole.RESEARCHER


class LearnOutcomeRequest(BaseModel):
    opportunity_id: str
    county_id: str
    event_type: LearningOutcomeType
    realized_margin: Optional[float] = None
    notes: Optional[str] = None


@router.get("/status")
def get_intelligence_status(db: Session = Depends(get_db)):
    """Returns the operational status of the 8 Intelligence Context subsystems."""
    intel = IntelligenceContext(db=db)
    return intel.get_status()


@router.post("/reason", response_model=ReasoningResponseDTO)
def execute_reasoning(
    req: ReasoningRequestDTO,
    db: Session = Depends(get_db),
    operator: dict = Depends(require_operator_role),
):
    """
    Executes centralized domain reasoning using retrieved memory,
    institutional knowledge, and LLM inference.
    """
    intel = IntelligenceContext(db=db)
    if req.opportunity_id:
        return intel.evaluate_opportunity(
            opportunity_id=req.opportunity_id,
            inquiry=req.inquiry,
            opportunity_context=req.context,
            county_name=req.county_name,
            forced_provider=req.forced_provider,
        )

    return intel.reasoning.reason(
        inquiry=req.inquiry,
        context=req.context,
        forced_provider=req.forced_provider,
    )


@router.get("/memory/{scope}/{entity_id}", response_model=MemoryEntryDTO)
def get_memory(
    scope: MemoryScope,
    entity_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve consolidated episodic memory for an entity."""
    intel = IntelligenceContext(db=db)
    mem = intel.memory.retrieve(scope=scope, entity_id=entity_id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory entry not found.")
    return mem


@router.post("/memory", response_model=MemoryEntryDTO)
def store_memory(
    req: StoreMemoryRequest,
    db: Session = Depends(get_db),
    operator: dict = Depends(require_operator_role),
):
    """Store or update an episodic memory entry."""
    intel = IntelligenceContext(db=db)
    return intel.memory.store(
        scope=req.scope,
        entity_id=req.entity_id,
        summary=req.summary,
        observations=req.observations,
        attributes=req.attributes,
        confidence=req.confidence,
    )


@router.get("/knowledge", response_model=List[KnowledgeArticleDTO])
def list_knowledge(
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: Session = Depends(get_db),
):
    """List verified institutional knowledge articles (SOPs, County Rules, Title Patterns)."""
    intel = IntelligenceContext(db=db)
    return intel.knowledge.list_articles(category=category)


@router.post("/recommendations", response_model=List[RecommendationActionDTO])
def get_recommendations(
    req: RecommendationRequest,
    db: Session = Depends(get_db),
):
    """Generate prescriptive next actions based on context and stakeholder role."""
    intel = IntelligenceContext(db=db)
    return intel.recommendations.next_action(context=req.context, role=req.role)


@router.post("/learn", response_model=LearningEventDTO)
def log_learning_outcome(
    req: LearnOutcomeRequest,
    db: Session = Depends(get_db),
    operator: dict = Depends(require_operator_role),
):
    """Log an outcome to trigger automated score and county friction recalibration."""
    intel = IntelligenceContext(db=db)
    return intel.learning.record_outcome(
        opportunity_id=req.opportunity_id,
        county_id=req.county_id,
        event_type=req.event_type,
        realized_margin=req.realized_margin,
        notes=req.notes,
    )
