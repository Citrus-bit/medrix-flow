"""Setup configuration endpoints.

Allows the frontend to read/write model configurations, tool API keys,
and test connectivity to external services — all persisted to config.yaml / .env.
"""

import logging

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.gateway.auth import require_admin_access
from medrix_flow.setup.service import (
    IMAGE_PROVIDER_GOOGLE,
    IMAGE_PROVIDER_OPENAI,
    SaveModelsRequest,
    SetupConfigResponse,
    get_setup_config_data,
    normalize_base_url,
    refresh_env,
    save_setup_config_data,
)
from medrix_flow.setup.security import validate_optional_base_url, validate_setup_model_provider
from medrix_flow.utils.google_image import (
    GOOGLE_IMAGE_SMOKE_IMAGE_SIZE,
    GOOGLE_IMAGE_SMOKE_MODEL,
    GOOGLE_IMAGE_SMOKE_PROMPT,
    GoogleImageRequestError,
    build_google_image_smoke_request,
    execute_google_image_request,
    has_google_image_content,
    summarize_google_image_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"], dependencies=[Depends(require_admin_access)])


class TestModelRequest(BaseModel):
    provider: str = Field(..., description="Provider class path (use field)")
    model: str = Field(..., description="Model ID")
    api_key: str | None = Field(None, description="API key (plain text)")
    base_url: str | None = Field(None, description="Custom base URL")


class TestToolKeyRequest(BaseModel):
    service: str = Field(..., description="tavily, jina, openalex, semantic-scholar, or google-ai-studio")
    api_key: str = Field(..., description="API key to test")


class ImageProviderTestRequest(BaseModel):
    provider: str = Field(..., description="google-ai-studio or openai-compatible")
    model: str = Field(..., description="Image model ID")
    api_key: str = Field(..., description="API key to test")
    base_url: str | None = Field(None, description="Custom base URL for openai-compatible image providers")


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
    description="Verify that a tool or academic API key is valid.",
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

        elif service == "openalex":
            import requests as http_requests

            resp = http_requests.get(
                "https://api.openalex.org/works",
                params={"search": "transformer", "per_page": 1, "api_key": api_key},
                timeout=15,
            )
            if resp.status_code == 200:
                return TestResult(success=True, message="OpenAlex API key is valid.")
            return TestResult(success=False, message=f"OpenAlex returned status {resp.status_code}.")

        elif service == "semantic-scholar":
            import requests as http_requests

            resp = http_requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": "transformer", "limit": 1, "fields": "title"},
                headers={"x-api-key": api_key},
                timeout=15,
            )
            if resp.status_code == 200:
                return TestResult(success=True, message="Semantic Scholar API key is valid.")
            return TestResult(success=False, message=f"Semantic Scholar returned status {resp.status_code}.")

        elif service == "google-ai-studio":
            import requests as http_requests

            result = execute_google_image_request(
                requests_module=http_requests,
                api_key=api_key,
                model=GOOGLE_IMAGE_SMOKE_MODEL,
                prompt_text=GOOGLE_IMAGE_SMOKE_PROMPT,
                inline_parts=[],
                aspect_ratio="1:1",
                image_size=GOOGLE_IMAGE_SMOKE_IMAGE_SIZE,
                timeout_seconds=30,
                force_image_size=True,
            )
            if has_google_image_content(result.payload):
                return TestResult(success=True, message="Google AI Studio API key is valid for image generation.")
            summary = summarize_google_image_response(result.payload)
            return TestResult(
                success=False,
                message=f"Google AI Studio key was accepted, but no image content was returned. {summary}",
            )

        else:
            return TestResult(success=False, message=f"Unknown service: {service}")

    except GoogleImageRequestError as e:
        logger.info("Tool key test for %s failed: %s", service, e)
        return TestResult(success=False, message=str(e)[:500])
    except Exception as e:
        logger.info("Tool key test for %s failed: %s", service, e)
        return TestResult(success=False, message=str(e)[:500])


@router.post(
    "/test-image-provider",
    response_model=TestResult,
    summary="Test Image Provider",
    description="Verify that an image generation provider configuration can return image content.",
)
async def test_image_provider(req: ImageProviderTestRequest) -> TestResult:
    refresh_env()
    provider = req.provider.lower().strip()
    model = req.model.strip()
    api_key = req.api_key.strip()
    try:
        if not model:
            return TestResult(success=False, message="Image provider test requires a model.")
        if not api_key:
            return TestResult(success=False, message="Image provider test requires an API key.")

        if provider == IMAGE_PROVIDER_GOOGLE:
            result = execute_google_image_request(
                requests_module=requests,
                api_key=api_key,
                model=model,
                prompt_text=GOOGLE_IMAGE_SMOKE_PROMPT,
                inline_parts=[],
                aspect_ratio="1:1",
                image_size=GOOGLE_IMAGE_SMOKE_IMAGE_SIZE,
                timeout_seconds=30,
                force_image_size=True,
            )
            if has_google_image_content(result.payload):
                return TestResult(success=True, message="Google AI Studio API key is valid for image generation.")
            summary = summarize_google_image_response(result.payload)
            return TestResult(
                success=False,
                message=f"Google AI Studio key was accepted, but no image content was returned. {summary}",
            )

        if provider == IMAGE_PROVIDER_OPENAI:
            validate_optional_base_url(req.base_url)
            base_url = normalize_base_url(req.base_url)
            if not base_url:
                return TestResult(success=False, message="OpenAI-compatible image provider requires a base URL.")
            resp = requests.post(
                f"{base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "prompt": "Generate a simple blue scientific icon on a white background.",
                    "size": "1024x1024",
                    "n": 1,
                    "response_format": "b64_json",
                },
                timeout=30,
            )
            if resp.status_code != 200:
                return TestResult(success=False, message=f"OpenAI-compatible image provider returned status {resp.status_code}.")
            payload = resp.json()
            data = payload.get("data") or []
            first = data[0] if data else {}
            if isinstance(first, dict) and (first.get("b64_json") or first.get("url")):
                return TestResult(success=True, message="OpenAI-compatible image provider is valid for image generation.")
            return TestResult(success=False, message="OpenAI-compatible provider was accepted, but no image content was returned.")

        return TestResult(success=False, message=f"Unknown image provider: {provider}")
    except GoogleImageRequestError as e:
        logger.info("Image provider test for %s failed: %s", provider, e)
        return TestResult(success=False, message=str(e)[:500])
    except Exception as e:
        logger.info("Image provider test for %s failed: %s", provider, e)
        return TestResult(success=False, message=str(e)[:500])
