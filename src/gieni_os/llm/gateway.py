"""
Gieni OS LLM Gateway
Central orchestrator for AI model inference supporting:
1. Azure OpenAI (Enterprise cloud deployments)
2. Ollama (Local and private open weights)
3. Deterministic Statutory Rule Engine (Internal RCW Title 11 engine fallback)
"""

import os
import logging
from typing import Dict, Optional, Any

from gieni_os import config
from gieni_os.llm.models import (
    LLMRequest,
    LLMResponse,
    LLMStatusResponse,
    LLMProviderInfo,
    LLMProviderType,
)
from gieni_os.llm.clients.base import BaseLLMClient
from gieni_os.llm.clients.azure_client import AzureOpenAIClient
from gieni_os.llm.clients.ollama_client import OllamaClient
from gieni_os.llm.clients.deterministic_client import DeterministicStatutoryClient

logger = logging.getLogger(__name__)


class LLMGateway:
    """Intelligent inference gateway managing provider selection, health, and fallback."""

    def __init__(
        self,
        azure_client: Optional[AzureOpenAIClient] = None,
        ollama_client: Optional[OllamaClient] = None,
        deterministic_client: Optional[DeterministicStatutoryClient] = None,
    ):
        self.azure_client = azure_client or AzureOpenAIClient()
        self.ollama_client = ollama_client or OllamaClient()
        self.deterministic_client = deterministic_client or DeterministicStatutoryClient()

    def get_provider_clients(self) -> Dict[LLMProviderType, BaseLLMClient]:
        return {
            LLMProviderType.AZURE_OPENAI: self.azure_client,
            LLMProviderType.OLLAMA: self.ollama_client,
            LLMProviderType.DETERMINISTIC_STATUTORY_ARE: self.deterministic_client,
        }

    def get_status(self) -> LLMStatusResponse:
        """Query availability across all configured providers."""
        providers_info: Dict[str, LLMProviderInfo] = {}

        azure_info = self.azure_client.check_availability()
        providers_info[LLMProviderType.AZURE_OPENAI.value] = azure_info

        ollama_info = self.ollama_client.check_availability()
        providers_info[LLMProviderType.OLLAMA.value] = ollama_info

        deterministic_info = self.deterministic_client.check_availability()
        providers_info[LLMProviderType.DETERMINISTIC_STATUTORY_ARE.value] = deterministic_info

        # Determine active provider by priority and override
        active_client = self.resolve_active_client(providers_info)
        active_info = providers_info[active_client.provider_type.value]

        return LLMStatusResponse(
            active_provider=active_client.provider_type,
            active_model=active_info.model,
            providers=providers_info,
            fallback_available=True,
        )

    def resolve_active_client(
        self,
        prefetched_info: Optional[Dict[str, LLMProviderInfo]] = None,
        forced_provider: Optional[LLMProviderType] = None,
    ) -> BaseLLMClient:
        """Resolve which provider should service requests based on preference, health, and overrides."""
        clients = self.get_provider_clients()

        # 1. Check runtime forced provider
        if forced_provider and forced_provider in clients:
            return clients[forced_provider]

        # 2. Check config environment override (e.g. LLM_PROVIDER_OVERRIDE=AZURE_OPENAI or OLLAMA)
        # Read from environment dynamically so unit test environment patches and live runtime updates apply
        env_override = os.getenv("LLM_PROVIDER_OVERRIDE", config.LLM_PROVIDER_OVERRIDE).strip().upper()
        if env_override:
            for p_type, client in clients.items():
                if p_type.value == env_override:
                    if client.check_availability().is_available:
                        return client

        # 3. Check Azure OpenAI availability
        if prefetched_info:
            azure_avail = prefetched_info.get(LLMProviderType.AZURE_OPENAI.value, {}).is_available
        else:
            azure_avail = self.azure_client.check_availability().is_available

        if azure_avail:
            return self.azure_client

        # 4. Check Ollama availability
        if prefetched_info:
            ollama_avail = prefetched_info.get(LLMProviderType.OLLAMA.value, {}).is_available
        else:
            ollama_avail = self.ollama_client.check_availability().is_available

        if ollama_avail:
            return self.ollama_client

        # 5. Default verified fallback
        return self.deterministic_client

    def investigate(
        self,
        query: str,
        opportunity_context: Optional[Dict[str, Any]] = None,
        forced_provider: Optional[LLMProviderType] = None,
    ) -> LLMResponse:
        """
        Execute an investigation inquiry through the primary available LLM,
        transparently falling back to deterministic statutory rule engine on failure.
        """
        primary_client = self.resolve_active_client(forced_provider=forced_provider)
        req = LLMRequest(
            query=query,
            opportunity_context=opportunity_context,
            forced_provider=forced_provider,
        )

        try:
            return primary_client.generate(req)
        except Exception as err:
            logger.warning(
                "Primary LLM provider %s failed (%s). Falling back to deterministic statutory engine.",
                primary_client.provider_type.value,
                err,
            )
            # If the primary wasn't already the deterministic client, execute fallback
            if primary_client.provider_type != LLMProviderType.DETERMINISTIC_STATUTORY_ARE:
                return self.deterministic_client.generate(req)
            raise

    def test_prompt(
        self,
        prompt: str,
        forced_provider: Optional[LLMProviderType] = None,
    ) -> LLMResponse:
        """Diagnostic prompt execution testing live connectivity."""
        return self.investigate(
            query=prompt,
            opportunity_context={"test_mode": True},
            forced_provider=forced_provider,
        )


# Lazy singleton implementation for platform-wide injection
_default_llm_gateway: Optional[LLMGateway] = None

def get_default_llm_gateway() -> LLMGateway:
    global _default_llm_gateway
    if _default_llm_gateway is None:
        _default_llm_gateway = LLMGateway()
    return _default_llm_gateway

class _LazyGatewayProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_default_llm_gateway(), name)

default_llm_gateway: LLMGateway = _LazyGatewayProxy()  # type: ignore
