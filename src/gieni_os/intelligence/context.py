"""
Gieni OS Intelligence Context (The Brain)
Centralizes Memory, Reasoning, Retrieval, Knowledge, Learning,
Recommendations, Prompt Registry, and Vector Embeddings.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from gieni_os.database.connection import get_db
from gieni_os.intelligence.models import (
    MemoryScope,
    ObservationSource,
    StakeholderRole,
    ReasoningResponseDTO,
)
from gieni_os.intelligence.memory.service import MemoryService
from gieni_os.intelligence.knowledge.service import KnowledgeService
from gieni_os.intelligence.learning.service import LearningService
from gieni_os.intelligence.recommendations.service import RecommendationService
from gieni_os.intelligence.embeddings.vector_service import VectorService
from gieni_os.intelligence.retrieval.service import RetrievalService
from gieni_os.intelligence.reasoning.service import ReasoningService
from gieni_os.intelligence.prompts.registry import PromptRegistry, default_prompt_registry


class IntelligenceContext:
    """The central unified intelligence brain of Gieni OS."""

    def __init__(self, db: Session):
        self.db = db
        self.prompts = default_prompt_registry
        self.memory = MemoryService(db=db)
        self.knowledge = KnowledgeService(db=db)
        self.learning = LearningService(db=db)
        self.recommendations = RecommendationService()
        self.vector = VectorService(db=db)
        self.retrieval = RetrievalService(
            db=db,
            memory_service=self.memory,
            knowledge_service=self.knowledge,
            vector_service=self.vector,
        )
        self.reasoning = ReasoningService(prompt_registry=self.prompts)

    def evaluate_opportunity(
        self,
        opportunity_id: str,
        inquiry: str = "Provide probate and title intelligence evaluation.",
        opportunity_context: Optional[Dict[str, Any]] = None,
        county_name: Optional[str] = None,
        forced_provider: Optional[str] = None,
    ) -> ReasoningResponseDTO:
        """
        Unified Cognitive Flow:
        1. Retrieve Memory
        2. Retrieve Knowledge & County Patterns
        3. Retrieve Similar Cases
        4. Reason through ReasoningService
        5. Store Decisions & Observations to Memory
        """
        ctx = opportunity_context or {}

        # 1. Retrieve historical opportunity memory
        opp_memory = self.memory.retrieve(scope=MemoryScope.OPPORTUNITY, entity_id=opportunity_id)
        memory_obs = [o.observation for o in opp_memory.observations] if opp_memory else []

        # 2. Retrieve county rules & institutional knowledge
        target_county = county_name or ctx.get("property_profile", {}).get("county", "Pierce")
        county_info = self.retrieval.retrieve_county_patterns(target_county)
        knowledge_texts = [r.get("content", "") for r in county_info.get("rules", [])]

        # 3. Retrieve similar opportunities
        similar_cases = self.retrieval.retrieve_similar_opportunities(opportunity_id, top_k=3)
        if similar_cases:
            ctx["comparable_cases"] = similar_cases

        # 4. Reason using the reasoning core
        decision = self.reasoning.reason(
            inquiry=inquiry,
            context=ctx,
            retrieved_memory=memory_obs,
            retrieved_knowledge=knowledge_texts,
            forced_provider=forced_provider,
        )

        # 5. Store decision observation in memory for persistent learning
        self.memory.merge(
            scope=MemoryScope.OPPORTUNITY,
            entity_id=opportunity_id,
            new_observations=[f"Reasoning: {decision.summary}"],
            summary_update=f"Evaluated with confidence {decision.confidence:.2f} ({decision.risk_assessment} risk)",
            confidence_delta=0.01,
            source=ObservationSource.ENGINE,
        )

        # 6. Index embedding for semantic retrieval
        self.vector.store(
            entity_type="OPPORTUNITY",
            entity_id=opportunity_id,
            text=f"{opportunity_id} {decision.narrative}",
            metadata={"risk": decision.risk_assessment, "confidence": decision.confidence},
        )

        return decision

    def get_status(self) -> Dict[str, Any]:
        """Diagnostic overview of the Intelligence Context."""
        return {
            "subsystems": {
                "memory_service": "ONLINE",
                "reasoning_service": "ONLINE",
                "retrieval_service": "ONLINE",
                "knowledge_service": "ONLINE",
                "learning_service": "ONLINE",
                "recommendation_service": "ONLINE",
                "prompt_registry": "ONLINE",
                "vector_embedding_layer": "ONLINE",
            },
            "active_prompt_templates": len(self.prompts._templates),
            "registered_knowledge_articles": len(self.knowledge.list_articles()),
            "status": "OPERATIONAL",
        }


def get_intelligence_context(db: Session = None) -> IntelligenceContext:
    """Dependency helper to instantiate or inject IntelligenceContext."""
    if db is not None:
        return IntelligenceContext(db=db)
    # Default standalone session if called outside FastAPI dependency
    from gieni_os.database.connection import SessionLocal
    standalone_db = SessionLocal()
    return IntelligenceContext(db=standalone_db)
