"""Setup configuration endpoints.

Allows the frontend to read/write model configurations, tool API keys,
and test connectivity to external services — all persisted to config.yaml / .env.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.gateway.auth import require_admin_access
from medrix_flow.setup.service import (
    SaveModelsRequest,
    SetupConfigResponse,
    get_setup_config_data,
    refresh_env,
    save_setup_config_data,
)
from medrix_flow.setup.security import validate_optional_base_url, validate_setup_model_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"], dependencies=[Depends(require_admin_access)])


class TestModelRequest(BaseModel):
    provider: str = Field(..., description="Provider class path (use field)")
    model: str = Field(..., description="Model ID")
    api_key: str | None = Field(None, description="API key (plain text)")
    base_url: str | None = Field(None, description="Custom base URL")


class TestToolKeyRequest(BaseModel):
    service: str = Field(..., description="tavily or jina")
    api_key: str = Field(..., description="API key to test")


class TestResult(BaseModel):
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/config",
    response_model=SetupConfigResponse,
    summary="Get Setup Configuration",
    description="Read current model configs and tool API key status.",
)
async def get_setup_config() -> SetupConfigResponse:
    return get_setup_config_data()


@router.put(
    "/models",
    summary="Save Model & Tool Key Configuration",
    description="Write model configs to config.yaml and API keys to .env, then hot-reload.",
)
async def save_models(req: SaveModelsRequest) -> dict:
    try:
        save_setup_config_data(req)
        return {"success": True, "message": "Configuration saved and reloaded."}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/test-model",
    response_model=TestResult,
    summary="Test Model Connectivity",
    description="Send a lightweight request to verify the model provider is reachable.",
)
async def test_model(req: TestModelRequest) -> TestResult:
    refresh_env()
    try:
        from medrix_flow.reflection import resolve_variable

        validate_setup_model_provider(req.provider)
        validate_optional_base_url(req.base_url)

        provider_class = resolve_variable(req.provider)
        kwargs: dict = {"model": req.model}
        if req.api_key:
            kwargs["api_key"] = req.api_key
        if req.base_url:
            kwargs["base_url"] = req.base_url

        llm = provider_class(**kwargs)
        response = await llm.ainvoke("Hi")
        if response and response.content:
            return TestResult(success=True, message="Connection successful.")
        return TestResult(success=True, message="Connected but received empty response.")
    except Exception as e:
        logger.info("Model connectivity test failed: %s", e)
        return TestResult(success=False, message=str(e)[:500])


@router.post(
    "/test-tool-key",
    response_model=TestResult,
    summary="Test Tool API Key",
    description="Verify that a Tavily or Jina API key is valid.",
)
async def test_tool_key(req: TestToolKeyRequest) -> TestResult:
    refresh_env()
    service = req.service.lower()
    api_key = req.api_key
    try:
        if service == "tavily":
            from tavily import TavilyClient

            client = TavilyClient(api_key=api_key)
            result = client.search("test", max_results=1)
            if "results" in result:
                return TestResult(success=True, message="Tavily API key is valid.")
            return TestResult(success=False, message="Unexpected Tavily response.")

        elif service == "jina":
            import requests as http_requests

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-Return-Format": "html",
                "X-Timeout": "10",
            }
            resp = http_requests.post(
                "https://r.jina.ai/",
                headers=headers,
                json={"url": "https://example.com"},
                timeout=15,
            )
            if resp.status_code == 200:
                return TestResult(success=True, message="Jina API key is valid.")
            return TestResult(success=False, message=f"Jina returned status {resp.status_code}.")

        else:
            return TestResult(success=False, message=f"Unknown service: {service}")

    except Exception as e:
        logger.info("Tool key test for %s failed: %s", service, e)
        return TestResult(success=False, message=str(e)[:500])
