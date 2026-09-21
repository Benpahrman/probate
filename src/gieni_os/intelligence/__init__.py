"""
Gieni OS Intelligence Context Package (The Brain)
"""

from gieni_os.intelligence.models import (
    MemoryScope,
    ObservationSource,
    StakeholderRole,
    MemoryEntryDTO,
    MemoryObservationDTO,
    KnowledgeArticleDTO,
    LearningOutcomeType,
    LearningEventDTO,
    RecommendationActionDTO,
    ReasoningRequestDTO,
    ReasoningResponseDTO,
)
from gieni_os.intelligence.memory.service import MemoryService
from gieni_os.intelligence.knowledge.service import KnowledgeService
from gieni_os.intelligence.learning.service import LearningService
from gieni_os.intelligence.recommendations.service import RecommendationService
from gieni_os.intelligence.embeddings.vector_service import VectorService
from gieni_os.intelligence.retrieval.service import RetrievalService
from gieni_os.intelligence.reasoning.service import ReasoningService
from gieni_os.intelligence.prompts.registry import PromptRegistry, PromptTemplate, default_prompt_registry
from gieni_os.intelligence.context import IntelligenceContext, get_intelligence_context

__all__ = [
    "MemoryScope",
    "ObservationSource",
    "StakeholderRole",
    "MemoryEntryDTO",
    "MemoryObservationDTO",
    "KnowledgeArticleDTO",
    "LearningOutcomeType",
    "LearningEventDTO",
    "RecommendationActionDTO",
    "ReasoningRequestDTO",
    "ReasoningResponseDTO",
    "MemoryService",
    "KnowledgeService",
    "LearningService",
    "RecommendationService",
    "VectorService",
    "RetrievalService",
    "ReasoningService",
    "PromptRegistry",
    "PromptTemplate",
    "default_prompt_registry",
    "IntelligenceContext",
    "get_intelligence_context",
]
