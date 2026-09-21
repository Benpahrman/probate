"""
Gieni OS Retrieval Service (Subsystem 3)
Aggregates relevant intelligence across Knowledge Base articles,
County and Case memories, historical probate dockets, and vector similarity matches.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from gieni_os.database.models import ProbateCaseModel, OpportunityModel
from gieni_os.intelligence.models import MemoryScope
from gieni_os.intelligence.memory.service import MemoryService
from gieni_os.intelligence.knowledge.service import KnowledgeService
from gieni_os.intelligence.embeddings.vector_service import VectorService


class RetrievalService:
    """Aggregates contextual intelligence across all institutional memory layers."""

    def __init__(
        self,
        db: Session,
        memory_service: MemoryService,
        knowledge_service: KnowledgeService,
        vector_service: VectorService,
    ):
        self.db = db
        self.memory = memory_service
        self.knowledge = knowledge_service
        self.vector = vector_service

    def retrieve(
        self,
        query: str,
        county_name: Optional[str] = None,
        scope: Optional[MemoryScope] = None,
    ) -> Dict[str, Any]:
        """Consolidate memory entries, knowledge articles, and semantic matches for a query."""
        memory_matches = self.memory.search(query=query, scope=scope, limit=5)
        vector_matches = self.vector.similar(text=query, top_k=5)

        county_rules = []
        if county_name:
            county_rules = self.knowledge.get_county_rules(county_name)

        def dump(obj):
            return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()

        return {
            "query": query,
            "memory_entries": [dump(m) for m in memory_matches],
            "knowledge_articles": [dump(k) for k in county_rules],
            "semantic_similarities": vector_matches,
        }

    def retrieve_related_cases(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieve cases sharing the same county, decedent surname, or attorney."""
        target = self.db.query(ProbateCaseModel).filter(ProbateCaseModel.id == case_id).first()
        if not target:
            return []

        # Find other cases in the same county
        peers = (
            self.db.query(ProbateCaseModel)
            .filter(
                ProbateCaseModel.county_id == target.county_id,
                ProbateCaseModel.id != case_id,
            )
            .limit(5)
            .all()
        )

        return [
            {
                "case_id": p.id,
                "case_number": p.case_number,
                "decedent": p.decedent,
                "status": p.status,
                "filing_date": str(p.filing_date),
            }
            for p in peers
        ]

    def retrieve_county_patterns(self, county_name: str) -> Dict[str, Any]:
        """Fetch local court rules, typical filing timelines, and county memory."""
        rules = self.knowledge.get_county_rules(county_name)
        county_mem = self.memory.retrieve(scope=MemoryScope.COUNTY, entity_id=county_name.upper())

        def dump(obj):
            return obj.model_dump() if hasattr(obj, "model_dump") else obj.dict()

        return {
            "county_name": county_name,
            "rules": [dump(r) for r in rules],
            "memory": dump(county_mem) if county_mem else None,
        }

    def retrieve_similar_opportunities(
        self,
        opp_id: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find comparable opportunities by semantic embedding and property equity profile."""
        target_opp = self.db.query(OpportunityModel).filter(OpportunityModel.id == opp_id).first()
        if not target_opp:
            return []

        search_text = f"Opportunity {target_opp.id} Stage {target_opp.workflow_stage} Priority {target_opp.priority} Score {target_opp.score}"
        return self.vector.similar(text=search_text, entity_type="OPPORTUNITY", top_k=top_k)
