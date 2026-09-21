"""
Gieni OS LLM Gateway API Router
Provides diagnostic health checks, provider configuration inspection,
and test prompt execution for Ollama and Azure OpenAI.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from gieni_os.api.deps import require_operator_role
from gieni_os.llm.models import (
    LLMStatusResponse,
    LLMResponse,
    LLMProviderType,
)
from gieni_os.llm.gateway import default_llm_gateway

router = APIRouter(prefix="/llm", tags=["LLM Gateway"])


class TestPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=2, description="Test prompt to run")
    forced_provider: Optional[LLMProviderType] = Field(None, description="Optional provider override")


@router.get("/status", response_model=LLMStatusResponse)
def get_llm_status():
    """Returns the connectivity status and active model for Ollama, Azure OpenAI, and Fallback engine."""
    return default_llm_gateway.get_status()


@router.post("/test-prompt", response_model=LLMResponse)
def execute_test_prompt(
    req: TestPromptRequest,
    clerk_context: dict = Depends(require_operator_role),
):
    """
    Executes a test prompt against the active LLM provider.
    Requires operator credentials.
    """
    try:
        return default_llm_gateway.test_prompt(
            prompt=req.prompt,
            forced_provider=req.forced_provider,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM execution failed: {str(e)}")
