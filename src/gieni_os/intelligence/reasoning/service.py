"""
Gieni OS Reasoning Service (Subsystem 2)
Central cognitive engine replacing ad-hoc LLM calls across all agents.
Synthesizes domain context, retrieved memory, and institutional knowledge
through the Gieni LLM Gateway with deterministic fallback.
"""

import time
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

from gieni_os.llm.gateway import LLMGateway, default_llm_gateway
from gieni_os.llm.models import LLMProviderType
from gieni_os.intelligence.prompts.registry import PromptRegistry, default_prompt_registry
from gieni_os.intelligence.models import (
    ReasoningRequestDTO,
    ReasoningResponseDTO,
)


class ReasoningService:
    """The central intelligence core where all Gieni agents think."""

    def __init__(
        self,
        llm_gateway: Optional[LLMGateway] = None,
        prompt_registry: Optional[PromptRegistry] = None,
    ):
        self.gateway = llm_gateway or default_llm_gateway
        self.prompts = prompt_registry or default_prompt_registry

    def reason(
        self,
        inquiry: str,
        context: Optional[Dict[str, Any]] = None,
        retrieved_memory: Optional[List[str]] = None,
        retrieved_knowledge: Optional[List[str]] = None,
        forced_provider: Optional[str] = None,
    ) -> ReasoningResponseDTO:
        """
        Execute unified multi-factor domain reasoning against provided context,
        incorporating institutional knowledge and historical observations.
        """
        start_time = time.perf_counter()
        ctx = context or {}

        # Enrich context with retrieved memory and knowledge
        augmented_context = dict(ctx)
        if retrieved_memory:
            augmented_context["retrieved_observations"] = retrieved_memory
        if retrieved_knowledge:
            augmented_context["institutional_rules"] = retrieved_knowledge

        # Resolve provider override if supplied
        target_provider = None
        if forced_provider:
            try:
                target_provider = LLMProviderType(forced_provider)
            except Exception as e:
                logger.warning("Invalid forced_provider string '%s' supplied; ignoring override (%s).", forced_provider, e)

        # Dispatch inference to the LLM Gateway
        llm_response = self.gateway.investigate(
            query=inquiry,
            opportunity_context=augmented_context,
            forced_provider=target_provider,
        )

        # Risk assessment classification
        risk = "LOW"
        conf = llm_response.confidence_score
        if conf < 0.80 or "unresolved" in inquiry.lower() or "missing" in inquiry.lower():
            risk = "HIGH"
        elif conf < 0.90:
            risk = "MEDIUM"

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return ReasoningResponseDTO(
            summary=llm_response.narrative[:160] + "..." if len(llm_response.narrative) > 160 else llm_response.narrative,
            narrative=llm_response.narrative,
            risk_assessment=risk,
            confidence=llm_response.confidence_score,
            citations=[{"source": c.source, "citation_id": c.citation_id, "details": c.details} for c in llm_response.citations],
            recommendations=llm_response.recommendations,
            memory_referenced=retrieved_memory or [],
            knowledge_referenced=retrieved_knowledge or [],
            provider_used=llm_response.provider_used.value,
            latency_ms=round(latency_ms, 2),
        )

    def explain(
        self,
        decision_label: str,
        supporting_facts: Dict[str, Any],
    ) -> str:
        """Produce a plain-English, legally grounded explanation of a classification."""
        inquiry = f"Explain legal and title basis for '{decision_label}' with facts: {json.dumps(supporting_facts, default=str)}"
        res = self.reason(inquiry=inquiry, context=supporting_facts)
        return res.narrative

    def classify(
        self,
        attributes: Dict[str, Any],
        taxonomy: str,
    ) -> Dict[str, Any]:
        """
        Classify entity attributes against standard probate/title taxonomy
        (e.g., Authority Tiers, Control Archetypes, Vesting status).
        """
        inquiry = f"Classify the following attributes into {taxonomy}: {json.dumps(attributes, default=str)}"
        res = self.reason(inquiry=inquiry, context=attributes)
        return {
            "taxonomy": taxonomy,
            "classification": res.summary,
            "risk": res.risk_assessment,
            "confidence": res.confidence,
        }

    def compare(
        self,
        opportunity_a: Dict[str, Any],
        opportunity_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare two opportunities for equity cushion, friction, and authority certainty."""
        inquiry = "Compare Opportunity A vs Opportunity B. Which asset represents higher acquisition certainty and lower legal friction?"
        combined_ctx = {"opportunity_a": opportunity_a, "opportunity_b": opportunity_b}
        res = self.reason(inquiry=inquiry, context=combined_ctx)
        return {
            "comparison": res.narrative,
            "confidence": res.confidence,
            "recommendations": res.recommendations,
        }
