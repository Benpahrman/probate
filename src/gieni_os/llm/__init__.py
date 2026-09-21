"""
Gieni OS LLM Gateway Engine
Provides dual support for local Ollama instances and enterprise Azure OpenAI,
with automatic Washington State statutory rule engine fallback.
"""

from gieni_os.llm.models import (
    LLMProviderType,
    LLMCitation,
    LLMRequest,
    LLMResponse,
    LLMProviderInfo,
    LLMStatusResponse,
)
from gieni_os.llm.gateway import LLMGateway, default_llm_gateway

__all__ = [
    "LLMProviderType",
    "LLMCitation",
    "LLMRequest",
    "LLMResponse",
    "LLMProviderInfo",
    "LLMStatusResponse",
    "LLMGateway",
    "default_llm_gateway",
]
