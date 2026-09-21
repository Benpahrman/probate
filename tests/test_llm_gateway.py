"""
Test Suite: Gieni OS LLM Gateway Engine
Validates Azure OpenAI client, Ollama client, Deterministic Statutory Rule Engine fallback,
gateway auto-resolution, error resilience, and HTTP API endpoints.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from gieni_os.api.main import app
from gieni_os.llm.models import (
    LLMProviderType,
    LLMRequest,
    LLMResponse,
    LLMCitation,
    LLMStatusResponse,
)
from gieni_os.llm.clients.base import BaseLLMClient
from gieni_os.llm.clients.azure_client import AzureOpenAIClient
from gieni_os.llm.clients.ollama_client import OllamaClient
from gieni_os.llm.clients.deterministic_client import DeterministicStatutoryClient
from gieni_os.llm.gateway import LLMGateway

client = TestClient(app)

OPP_CONTEXT = {
    "property_profile": {
        "situs_address": "4521 112th St Ct E, Tacoma, WA 98446",
        "avm_market_estimate": 450000.0,
        "total_assessed_value": 380000.0,
        "apn": "0319042045",
    },
    "ownership_profile": {
        "net_distributable_equity": 320000.0,
        "net_equity_pct": 0.71,
        "legal_title_vesting": "Estate of John Doe",
        "target_wholesale_mao": 290000.0,
    },
    "authority_profile": {
        "authority_tier": "TIER_1_UNCONTESTED_NONINTERVENTION",
        "statutory_basis": "RCW 11.68.011 (Nonintervention Powers)",
    },
    "control_profile": {
        "primary_decision_maker": "Jane Doe",
        "relationship_to_decedent": "Daughter / Personal Representative",
    },
    "opportunity_profile": {
        "priority_tier": "PRIORITY_A",
        "composite_viability_score": 92.5,
    },
    "evidence_package": {},
}


def test_deterministic_client_inquiries():
    """Verify deterministic statutory client provides grounded Washington Title 11 analyses."""
    statutory_client = DeterministicStatutoryClient()
    info = statutory_client.check_availability()
    assert info.is_available is True
    assert info.provider == LLMProviderType.DETERMINISTIC_STATUTORY_ARE

    # 1. Priority inquiry
    req_pri = LLMRequest(query="Why is this Priority A?", opportunity_context=OPP_CONTEXT)
    res_pri = statutory_client.generate(req_pri)
    assert res_pri.provider_used == LLMProviderType.DETERMINISTIC_STATUTORY_ARE
    assert "PRIORITY_A" in res_pri.narrative
    assert len(res_pri.citations) >= 2
    assert any("RCW" in c.citation_id or "RCW" in c.source for c in res_pri.citations)

    # 2. Control inquiry
    req_ctrl = LLMRequest(query="Who controls disposition?", opportunity_context=OPP_CONTEXT)
    res_ctrl = statutory_client.generate(req_ctrl)
    assert "Jane Doe" in res_ctrl.narrative
    assert res_ctrl.confidence_score > 0.90

    # 3. Authority inquiry
    req_auth = LLMRequest(query="Explain statutory authority path", opportunity_context=OPP_CONTEXT)
    res_auth = statutory_client.generate(req_auth)
    assert "RCW 11.68.011" in res_auth.narrative or "TIER_1" in res_auth.narrative


def test_azure_client_availability():
    """Verify Azure client correctly reports availability based on credentials."""
    unconfigured = AzureOpenAIClient(endpoint="", api_key="")
    info = unconfigured.check_availability()
    assert info.is_available is False
    assert "Missing AZURE_OPENAI_ENDPOINT" in info.details

    configured = AzureOpenAIClient(
        endpoint="https://gieni-test.openai.azure.com/",
        api_key="mock-azure-key",
        deployment_name="gpt-4o",
    )
    info_ok = configured.check_availability()
    assert info_ok.is_available is True
    assert info_ok.model == "gpt-4o"


def test_azure_client_generate_success():
    """Verify Azure client correctly parses JSON output from AzureOpenAI completion."""
    client_azure = AzureOpenAIClient(
        endpoint="https://gieni-test.openai.azure.com/",
        api_key="mock-key",
        deployment_name="gpt-4o",
    )

    mock_chat_completion = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        '{"narrative": "Verified RCW 11.68 estate.", "citations": [{"source": "Court", "citation_id": "D-1", "details": "Letters recorded"}], '
        '"recommendations": ["Submit PSA"], "confidence_score": 0.98, "connected_agents": ["AuthorityAgent"]}'
    )
    mock_chat_completion.choices = [mock_choice]

    with patch("src.gieni_os.llm.clients.azure_client.AzureOpenAI") as mock_openai_cls:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = mock_chat_completion
        mock_openai_cls.return_value = mock_instance

        resp = client_azure.generate(LLMRequest(query="Status check", opportunity_context=OPP_CONTEXT))
        assert resp.provider_used == LLMProviderType.AZURE_OPENAI
        assert "Verified RCW 11.68" in resp.narrative
        assert resp.confidence_score == 0.98
        assert len(resp.citations) == 1
        assert resp.citations[0].citation_id == "D-1"


def test_ollama_client_check_and_generate():
    """Verify Ollama client tags checking and chat completions via HTTP."""
    ollama = OllamaClient(host="http://localhost:11434", model="llama3:latest")

    # 1. Test tags check reachable
    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"models": [{"name": "llama3:latest"}]})
        status = ollama.check_availability()
        assert status.is_available is True
        assert "Ollama operational" in status.details

    # 2. Test chat generation
    with patch("httpx.Client.get") as mock_get, patch("httpx.Client.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"models": [{"name": "llama3:latest"}]})
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "message": {
                    "role": "assistant",
                    "content": '{"narrative": "Ollama local inference response.", "citations": [], "recommendations": ["Review docket"], "confidence_score": 0.91, "connected_agents": []}',
                }
            },
        )
        resp = ollama.generate(LLMRequest(query="Local probe", opportunity_context=OPP_CONTEXT))
        assert resp.provider_used == LLMProviderType.OLLAMA
        assert resp.model_name == "ollama:llama3:latest"
        assert "Ollama local inference" in resp.narrative


def test_llm_gateway_resolution_order():
    """Verify LLM gateway selects highest precedence available provider."""
    mock_azure = MagicMock(spec=AzureOpenAIClient)
    mock_azure.provider_type = LLMProviderType.AZURE_OPENAI

    mock_ollama = MagicMock(spec=OllamaClient)
    mock_ollama.provider_type = LLMProviderType.OLLAMA

    mock_det = DeterministicStatutoryClient()

    gateway = LLMGateway(
        azure_client=mock_azure,
        ollama_client=mock_ollama,
        deterministic_client=mock_det,
    )

    import os
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "", "LLM_PROVIDER_OVERRIDE": ""}, clear=False):
        # Both Azure and Ollama unavailable -> Deterministic
        mock_azure.check_availability.return_value = MagicMock(is_available=False, model="gpt-4o")
        mock_ollama.check_availability.return_value = MagicMock(is_available=False, model="llama3:latest")
        active = gateway.resolve_active_client()
        assert active.provider_type == LLMProviderType.DETERMINISTIC_STATUTORY_ARE

        # Ollama available -> Ollama
        mock_ollama.check_availability.return_value = MagicMock(is_available=True, model="llama3:latest")
        active = gateway.resolve_active_client()
        assert active.provider_type == LLMProviderType.OLLAMA

        # Azure available -> Azure takes precedence
        mock_azure.check_availability.return_value = MagicMock(is_available=True, model="gpt-4o")
        active = gateway.resolve_active_client()
        assert active.provider_type == LLMProviderType.AZURE_OPENAI


def test_llm_gateway_resilience_fallback():
    """Verify that if live provider raises an exception during generation, gateway safely falls back."""
    failing_azure = MagicMock(spec=AzureOpenAIClient)
    failing_azure.provider_type = LLMProviderType.AZURE_OPENAI
    failing_azure.check_availability.return_value = MagicMock(is_available=True, model="gpt-4o")
    failing_azure.generate.side_effect = RuntimeError("Azure network timeout")

    gateway = LLMGateway(
        azure_client=failing_azure,
        deterministic_client=DeterministicStatutoryClient(),
    )

    resp = gateway.investigate(
        query="Explain authority",
        opportunity_context=OPP_CONTEXT,
        forced_provider=LLMProviderType.AZURE_OPENAI,
    )
    # Failed on Azure, but returned valid deterministic response
    assert resp.provider_used == LLMProviderType.DETERMINISTIC_STATUTORY_ARE
    assert "Statutory authority path" in resp.narrative


def test_api_llm_status_endpoint():
    """Verify GET /api/llm/status returns provider matrix."""
    res = client.get("/api/llm/status")
    assert res.status_code == 200
    data = res.json()
    assert "active_provider" in data
    assert "active_model" in data
    assert "providers" in data
    assert LLMProviderType.DETERMINISTIC_STATUTORY_ARE.value in data["providers"]
    assert LLMProviderType.AZURE_OPENAI.value in data["providers"]
    assert LLMProviderType.OLLAMA.value in data["providers"]


def test_api_llm_test_prompt_endpoint():
    """Verify POST /api/llm/test-prompt requires operator context and returns valid LLM response."""
    # 1. Unauthenticated / Client role without operator privileges
    res_forbidden = client.post(
        "/api/llm/test-prompt",
        json={"prompt": "Is this estate solvable?"},
        headers={"x-clerk-user-id": "client_user_1", "x-clerk-role": "Client"},
    )
    assert res_forbidden.status_code == 403

    # 2. Operator role
    res_ok = client.post(
        "/api/llm/test-prompt",
        json={"prompt": "Explain nonintervention powers", "forced_provider": "DETERMINISTIC_STATUTORY_ARE"},
        headers={"x-clerk-user-id": "operator_admin_1", "x-clerk-role": "Platform Admin"},
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert "narrative" in data
    assert "citations" in data
    assert "provider_used" in data
