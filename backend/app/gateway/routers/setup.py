"""Setup configuration endpoints.

Allows the frontend to read/write model configurations, tool API keys,
and test connectivity to external services — all persisted to config.yaml / .env.
"""

import logging
import os
import re
from pathlib import Path

import yaml
from dotenv import load_dotenv, set_key
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from medrix_flow.config import get_app_config
from medrix_flow.config.app_config import AppConfig, reload_app_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["setup"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ENV_VAR_PATTERN = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")


def _find_env_path() -> Path:
    """Locate the .env file (project root)."""
    config_path = AppConfig.resolve_config_path()
    return config_path.parent / ".env"


def _find_config_path() -> Path:
    return AppConfig.resolve_config_path()


def _read_raw_config() -> dict:
    """Read config.yaml as raw dict (before env-var resolution)."""
    config_path = _find_config_path()
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _write_raw_config(data: dict) -> None:
    """Write a raw dict back to config.yaml, preserving YAML style."""
    config_path = _find_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _get_env_value(var_name: str) -> str | None:
    """Get env var value, refreshing from .env first."""
    return os.getenv(var_name)


def _refresh_env() -> None:
    """Reload .env file into process environment. Call once per request."""
    load_dotenv(_find_env_path(), override=True)


_TOOL_KEY_ENV_MAP = {"tavily": "TAVILY_API_KEY", "jina": "JINA_API_KEY"}


def _set_env_value(var_name: str, value: str) -> None:
    """Write an env var to the .env file and update current process env."""
    env_path = _find_env_path()
    if not env_path.exists():
        env_path.touch()
    set_key(str(env_path), var_name, value)
    os.environ[var_name] = value


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ModelSetupItem(BaseModel):
    """A single model configuration as seen by the setup UI."""

    name: str = Field(..., description="Unique model identifier")
    provider: str = Field("langchain_openai:ChatOpenAI", description="Provider class path (use field)")
    model: str = Field(..., description="Model ID sent to the provider")
    base_url: str | None = Field(None, description="Custom API base URL")
    api_key: str | None = Field(None, description="API key (plain text on write, masked on read)")
    api_key_env_var: str | None = Field(None, description="Env var name that holds the API key (e.g. OPENAI_API_KEY)")
    max_tokens: int | None = Field(None, description="Max tokens")
    temperature: float | None = Field(None, description="Sampling temperature")
    supports_thinking: bool = Field(False)
    supports_vision: bool = Field(False)


class ToolKeyItem(BaseModel):
    """An API key for a tool service (Tavily / Jina)."""

    service: str = Field(..., description="Service name: tavily or jina")
    api_key: str | None = Field(None, description="API key (plain on write, masked on read)")
    env_var: str = Field(..., description="Environment variable name")


class SetupConfigResponse(BaseModel):
    """Full setup configuration returned to the frontend."""

    models: list[ModelSetupItem]
    tool_keys: list[ToolKeyItem]


class SaveModelsRequest(BaseModel):
    models: list[ModelSetupItem]
    tool_keys: list[ToolKeyItem] | None = None


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
    _refresh_env()
    raw = _read_raw_config()
    models_raw: list[dict] = raw.get("models") or []

    items: list[ModelSetupItem] = []
    for m in models_raw:
        api_key_raw = m.get("api_key", "")
        env_var: str | None = None
        actual_key = ""

        if isinstance(api_key_raw, str) and api_key_raw.startswith("$"):
            env_var = api_key_raw[1:]
            actual_key = _get_env_value(env_var) or ""
        elif api_key_raw:
            actual_key = str(api_key_raw)

        items.append(
            ModelSetupItem(
                name=m.get("name", ""),
                provider=m.get("use", "langchain_openai:ChatOpenAI"),
                model=m.get("model", ""),
                base_url=m.get("base_url"),
                api_key=actual_key,
                api_key_env_var=env_var,
                max_tokens=m.get("max_tokens"),
                temperature=m.get("temperature"),
                supports_thinking=m.get("supports_thinking", False),
                supports_vision=m.get("supports_vision", False),
            )
        )

    tool_keys: list[ToolKeyItem] = []
    for svc, env in [("tavily", "TAVILY_API_KEY"), ("jina", "JINA_API_KEY")]:
        actual = _get_env_value(env) or ""
        tool_keys.append(
            ToolKeyItem(
                service=svc,
                api_key=actual,
                env_var=env,
            )
        )

    return SetupConfigResponse(models=items, tool_keys=tool_keys)


@router.put(
    "/models",
    summary="Save Model & Tool Key Configuration",
    description="Write model configs to config.yaml and API keys to .env, then hot-reload.",
)
async def save_models(req: SaveModelsRequest) -> dict:
    raw = _read_raw_config()

    new_models: list[dict] = []
    for m in req.models:
        entry: dict = {
            "name": m.name or m.model,
            "display_name": m.model,
            "use": m.provider,
            "model": m.model,
        }

        env_var = m.api_key_env_var or f"{m.name.upper().replace('-', '_')}_API_KEY"

        if m.api_key and m.api_key.strip():
            _set_env_value(env_var, m.api_key.strip())

        entry["api_key"] = f"${env_var}"

        if m.base_url:
            entry["base_url"] = m.base_url
        if m.max_tokens is not None:
            entry["max_tokens"] = m.max_tokens
        if m.temperature is not None:
            entry["temperature"] = m.temperature
        if m.supports_thinking:
            entry["supports_thinking"] = True
        if m.supports_vision:
            entry["supports_vision"] = True

        new_models.append(entry)

    raw["models"] = new_models

    if req.tool_keys:
        for tk in req.tool_keys:
            if tk.api_key and tk.api_key.strip():
                _set_env_value(tk.env_var, tk.api_key.strip())

    _write_raw_config(raw)

    try:
        reload_app_config()
    except Exception as e:
        logger.warning("Config reload after save failed: %s", e)

    return {"success": True, "message": "Configuration saved and reloaded."}


@router.post(
    "/test-model",
    response_model=TestResult,
    summary="Test Model Connectivity",
    description="Send a lightweight request to verify the model provider is reachable.",
)
async def test_model(req: TestModelRequest) -> TestResult:
    _refresh_env()
    try:
        from medrix_flow.reflection import resolve_variable

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
    _refresh_env()
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
