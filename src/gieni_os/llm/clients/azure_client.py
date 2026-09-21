"""
Azure OpenAI Client
Communicates with enterprise Azure OpenAI deployments using the official OpenAI SDK.
"""

import time
import json
import logging
from typing import Optional
from openai import AzureOpenAI

from gieni_os import config
from gieni_os.llm.clients.base import BaseLLMClient
from gieni_os.llm.models import (
    LLMRequest,
    LLMResponse,
    LLMCitation,
    LLMProviderType,
    LLMProviderInfo,
)

logger = logging.getLogger(__name__)


class AzureOpenAIClient(BaseLLMClient):
    """Production client for Azure OpenAI deployments."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        super().__init__(provider_type=LLMProviderType.AZURE_OPENAI)
        self.endpoint = endpoint if endpoint is not None else config.AZURE_OPENAI_ENDPOINT
        self.api_key = api_key if api_key is not None else config.AZURE_OPENAI_API_KEY
        self.deployment_name = (
            deployment_name if deployment_name is not None else config.AZURE_OPENAI_DEPLOYMENT_NAME
        )
        self.api_version = (
            api_version if api_version is not None else config.AZURE_OPENAI_API_VERSION
        )

    def check_availability(self) -> LLMProviderInfo:
        if not self.endpoint or not self.api_key:
            return LLMProviderInfo(
                provider=self.provider_type,
                is_available=False,
                details="Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY in environment.",
                model=self.deployment_name or "unset",
                endpoint=self.endpoint or "unset",
            )
        return LLMProviderInfo(
            provider=self.provider_type,
            is_available=True,
            details=f"Configured for deployment '{self.deployment_name}' via {self.endpoint}",
            model=self.deployment_name,
            endpoint=self.endpoint,
        )

    def generate(self, req: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()
        info = self.check_availability()
        if not info.is_available:
            raise RuntimeError(f"Azure OpenAI client unavailable: {info.details}")

        client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )

        system_instruction = req.system_instruction or self.build_system_prompt(req.opportunity_context)

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": req.query},
        ]

        try:
            completion = client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                response_format={"type": "json_object"},
            )

            raw_content = completion.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)

            citations = [
                LLMCitation(
                    source=c.get("source", "Azure OpenAI Intelligence"),
                    citation_id=c.get("citation_id", "GEN-AZURE"),
                    details=c.get("details", ""),
                )
                for c in parsed.get("citations", [])
            ]

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return LLMResponse(
                narrative=parsed.get("narrative", raw_content),
                citations=citations,
                recommendations=parsed.get("recommendations", []),
                confidence_score=float(parsed.get("confidence_score", 0.95)),
                connected_agents=parsed.get("connected_agents", ["AuthorityAgent", "OwnershipAgent"]),
                provider_used=self.provider_type,
                model_name=f"azure:{self.deployment_name}",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            logger.error("Azure OpenAI completion failed: %s", e)
            raise
