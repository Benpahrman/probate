"""
Base LLM Client Abstract Class
Defines the standard contract for any LLM provider in Gieni OS.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from gieni_os.llm.models import LLMRequest, LLMResponse, LLMProviderInfo, LLMProviderType


class BaseLLMClient(ABC):
    """Abstract interface that all LLM clients must implement."""

    def __init__(self, provider_type: LLMProviderType):
        self.provider_type = provider_type

    @abstractmethod
    def check_availability(self) -> LLMProviderInfo:
        """Check if the provider is reachable and correctly configured."""
        pass

    @abstractmethod
    def generate(self, req: LLMRequest) -> LLMResponse:
        """Execute a prompt request and return a structured LLMResponse."""
        pass

    def build_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Standard Washington State Title 11 & Probate Intelligence prompt."""
        base_prompt = (
            "You are the Gieni OS Principal Probate Legal & Real Estate Title Intelligence Specialist. "
            "You analyze Washington State (RCW Title 11) probate dockets, deed vesting chains, nonintervention powers, "
            "heirship control structures, and equity waterfalls. "
            "You always provide objective, grounded legal and title risk analyses, referencing specific Washington statutes "
            "(e.g., RCW 11.68.011 for Nonintervention Powers, RCW 11.28 for Letters Testamentary, RCW 11.04 for Intestate Succession, "
            "RCW 11.96A for TEDRA Agreements). "
            "You must return your output strictly formatted as JSON matching this schema:\n"
            "{\n"
            '  "narrative": "Detailed technical analysis of the inquiry against the factual evidence and estate context.",\n'
            '  "citations": [\n'
            '    {"source": "Engine or Legal Code", "citation_id": "Identifier", "details": "Specific evidence quote"}\n'
            "  ],\n"
            '  "recommendations": ["Actionable next step 1", "Actionable next step 2"],\n'
            '  "confidence_score": 0.95,\n'
            '  "connected_agents": ["AuthorityAgent", "OwnershipAgent"]\n'
            "}\n"
        )
        if context:
            import json
            base_prompt += f"\nEVALUATION CONTEXT (Packet of Facts):\n{json.dumps(context, default=str, indent=2)}\n"
        return base_prompt
