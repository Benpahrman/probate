"""
Ollama Client
Communicates with local or private Ollama instances using native HTTP REST API.
"""

import time
import json
import logging
from typing import Optional
import httpx

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


class OllamaClient(BaseLLMClient):
    """Production client for local and self-hosted Ollama model instances with circuit breaker."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 15.0,
    ):
        super().__init__(provider_type=LLMProviderType.OLLAMA)
        self.host = (host if host is not None else config.OLLAMA_HOST).rstrip("/")
        self.model = model if model is not None else config.OLLAMA_MODEL
        self.timeout = timeout
        self._consecutive_failures: int = 0
        self._circuit_tripped_until: float = 0.0
        self._max_failures_before_trip: int = 2
        self._circuit_cooldown_seconds: float = 30.0

    def check_availability(self) -> LLMProviderInfo:
        """Ping Ollama's tags endpoint to verify the service is running and model exists."""
        now = time.perf_counter()
        if now < self._circuit_tripped_until:
            return LLMProviderInfo(
                provider=self.provider_type,
                is_available=False,
                details=f"Ollama circuit breaker OPEN (cooling down for {self._circuit_tripped_until - now:.1f}s).",
                model=self.model,
                endpoint=self.host,
            )

        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.host}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Auto-resolve model if default is missing but models are installed
                    active_model = self.model
                    if self.model and any(self.model in m or m.startswith(self.model) for m in models):
                        has_model = True
                    elif models:
                        # Prioritize quality local models if available
                        preferred_candidates = ["qwen2.5:7b", "hermes3:8b", "llama3:latest", "phi4-mini:latest", "qwen2.5:3b"]
                        matched = next((c for c in preferred_candidates if any(c in m for m in models)), models[0])
                        active_model = matched
                        has_model = True
                    else:
                        has_model = False

                    detail = f"Ollama operational. Active model: '{active_model}'. ({len(models)} local models installed)"
                    return LLMProviderInfo(
                        provider=self.provider_type,
                        is_available=has_model,
                        details=detail,
                        model=active_model or self.model or "unset",
                        endpoint=self.host,
                    )
        except Exception as e:
            return LLMProviderInfo(
                provider=self.provider_type,
                is_available=False,
                details=f"Ollama server not reachable at {self.host} ({e.__class__.__name__}).",
                model=self.model,
                endpoint=self.host,
            )

        return LLMProviderInfo(
            provider=self.provider_type,
            is_available=False,
            details=f"Ollama server returned unexpected status at {self.host}.",
            model=self.model,
            endpoint=self.host,
        )

    def generate(self, req: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()
        info = self.check_availability()
        target_model = info.model if info.is_available and info.model != "unset" else self.model
        system_instruction = req.system_instruction or self.build_system_prompt(req.opportunity_context)

        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": req.query},
            ],
            "format": "json",
            "stream": False,
            "options": {
                "temperature": req.temperature,
                "num_predict": req.max_tokens,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(f"{self.host}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()

            raw_content = data.get("message", {}).get("content", "{}")
            parsed = json.loads(raw_content)

            citations = [
                LLMCitation(
                    source=c.get("source", "Ollama Local Engine"),
                    citation_id=c.get("citation_id", "GEN-OLLAMA"),
                    details=c.get("details", ""),
                )
                for c in parsed.get("citations", [])
            ]

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            self._consecutive_failures = 0
            return LLMResponse(
                narrative=parsed.get("narrative", raw_content),
                citations=citations,
                recommendations=parsed.get("recommendations", []),
                confidence_score=float(parsed.get("confidence_score", 0.92)),
                connected_agents=parsed.get("connected_agents", ["AuthorityAgent", "OwnershipAgent"]),
                provider_used=self.provider_type,
                model_name=f"ollama:{target_model}",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as e:
            self._consecutive_failures += 1
            if self._consecutive_failures >= self._max_failures_before_trip:
                self._circuit_tripped_until = time.perf_counter() + self._circuit_cooldown_seconds
                logger.warning(
                    "Ollama circuit breaker tripped for %.1fs after %d failures (%s).",
                    self._circuit_cooldown_seconds,
                    self._consecutive_failures,
                    e,
                )
            logger.error("Ollama completion failed: %s", e)
            raise
