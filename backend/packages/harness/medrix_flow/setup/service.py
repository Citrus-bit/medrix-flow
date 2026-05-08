from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv, set_key
from pydantic import BaseModel, Field

from medrix_flow.config.app_config import AppConfig, reload_app_config
from medrix_flow.setup.security import (
    validate_env_var_name,
    validate_optional_base_url,
    validate_setup_model_provider,
)

_ENV_VAR_PATTERN = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")


class ModelSetupItem(BaseModel):
    name: str = Field(..., description="Unique model identifier")
    provider: str = Field("langchain_openai:ChatOpenAI", description="Provider class path")
    model: str = Field(..., description="Model ID sent to the provider")
    base_url: str | None = Field(None, description="Custom API base URL")
    api_key: str | None = Field(None, description="API key (plain text on write, masked on read)")
    api_key_env_var: str | None = Field(None, description="Env var name that holds the API key")
    max_tokens: int | None = Field(None, description="Max tokens")
    temperature: float | None = Field(None, description="Sampling temperature")
    supports_thinking: bool = Field(False)
    supports_reasoning_effort: bool = Field(False)
    supports_vision: bool = Field(False)


class ToolKeyItem(BaseModel):
    service: str = Field(..., description="Service name: tavily, jina, openalex, or semantic-scholar")
    api_key: str | None = Field(None, description="API key (plain on write, masked on read)")
    env_var: str = Field(..., description="Environment variable name")


class SetupConfigResponse(BaseModel):
    models: list[ModelSetupItem]
    tool_keys: list[ToolKeyItem]


class SaveModelsRequest(BaseModel):
    models: list[ModelSetupItem]
    tool_keys: list[ToolKeyItem] | None = None


def find_config_path() -> Path:
    return AppConfig.resolve_config_path()


def find_env_path() -> Path:
    return find_config_path().parent / ".env"


def read_raw_config() -> dict[str, Any]:
    config_path = find_config_path()
    with open(config_path, encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_raw_config(data: dict[str, Any]) -> None:
    config_path = find_config_path()
    with open(config_path, "w", encoding="utf-8") as handle:
        yaml.dump(data, handle, default_flow_style=False, allow_unicode=True, sort_keys=False)


def refresh_env() -> None:
    load_dotenv(find_env_path(), override=True)


def get_env_value(var_name: str) -> str | None:
    return os.getenv(var_name)


def set_env_value(var_name: str, value: str) -> None:
    env_path = find_env_path()
    if not env_path.exists():
        env_path.touch()
    set_key(str(env_path), var_name, value)
    os.environ[var_name] = value


def get_setup_config_data() -> SetupConfigResponse:
    refresh_env()
    raw = read_raw_config()
    models_raw: list[dict[str, Any]] = raw.get("models") or []

    models: list[ModelSetupItem] = []
    for item in models_raw:
        api_key_raw = item.get("api_key", "")
        env_var: str | None = None
        actual_key = ""

        if isinstance(api_key_raw, str) and api_key_raw.startswith("$"):
            env_var = api_key_raw[1:]
            actual_key = get_env_value(env_var) or ""
        elif api_key_raw:
            actual_key = str(api_key_raw)

        models.append(
            ModelSetupItem(
                name=item.get("name", ""),
                provider=item.get("use", "langchain_openai:ChatOpenAI"),
                model=item.get("model", ""),
                base_url=item.get("base_url"),
                api_key=actual_key,
                api_key_env_var=env_var,
                max_tokens=item.get("max_tokens"),
                temperature=item.get("temperature"),
                supports_thinking=item.get("supports_thinking", True),
                supports_reasoning_effort=item.get("supports_reasoning_effort", False),
                supports_vision=item.get("supports_vision", True),
            )
        )

    tool_keys = [
        ToolKeyItem(service="tavily", api_key=get_env_value("TAVILY_API_KEY") or "", env_var="TAVILY_API_KEY"),
        ToolKeyItem(service="jina", api_key=get_env_value("JINA_API_KEY") or "", env_var="JINA_API_KEY"),
        ToolKeyItem(service="openalex", api_key=get_env_value("OPENALEX_API_KEY") or "", env_var="OPENALEX_API_KEY"),
        ToolKeyItem(
            service="semantic-scholar",
            api_key=get_env_value("SEMANTIC_SCHOLAR_API_KEY") or "",
            env_var="SEMANTIC_SCHOLAR_API_KEY",
        ),
    ]

    return SetupConfigResponse(models=models, tool_keys=tool_keys)


def save_setup_config_data(payload: SaveModelsRequest) -> None:
    raw = read_raw_config()
    models: list[dict[str, Any]] = []

    for model in payload.models:
        validate_setup_model_provider(model.provider)
        validate_optional_base_url(model.base_url)
        env_var = model.api_key_env_var or f"{model.name.upper().replace('-', '_')}_API_KEY"
        validate_env_var_name(env_var)

        if model.api_key and model.api_key.strip():
            set_env_value(env_var, model.api_key.strip())

        entry: dict[str, Any] = {
            "name": model.name or model.model,
            "display_name": model.model,
            "use": model.provider,
            "model": model.model,
            "api_key": f"${env_var}",
            "supports_thinking": model.supports_thinking,
            "supports_reasoning_effort": model.supports_reasoning_effort,
            "supports_vision": model.supports_vision,
        }
        if model.base_url:
            entry["base_url"] = model.base_url
        if model.max_tokens is not None:
            entry["max_tokens"] = model.max_tokens
        if model.temperature is not None:
            entry["temperature"] = model.temperature
        models.append(entry)

    raw["models"] = models

    if payload.tool_keys:
        for tool_key in payload.tool_keys:
            validate_env_var_name(tool_key.env_var, allow_tool_key=True)
            if tool_key.api_key and tool_key.api_key.strip():
                set_env_value(tool_key.env_var, tool_key.api_key.strip())

    write_raw_config(raw)
    reload_app_config()


def collect_referenced_env_vars(node: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(node, str):
        match = _ENV_VAR_PATTERN.match(node.strip())
        if match:
            found.add(match.group(1))
    elif isinstance(node, dict):
        for value in node.values():
            found.update(collect_referenced_env_vars(value))
    elif isinstance(node, list):
        for item in node:
            found.update(collect_referenced_env_vars(item))
    return found


def ensure_setup_files(project_root: Path) -> list[Path]:
    created: list[Path] = []
    pairs = [
        (project_root / "config.example.yaml", project_root / "config.yaml"),
        (project_root / ".env.example", project_root / ".env"),
        (project_root / "frontend" / ".env.example", project_root / "frontend" / ".env"),
    ]
    for source, target in pairs:
        if target.exists():
            continue
        if not source.exists():
            raise FileNotFoundError(f"Missing template file: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        created.append(target)
    return created
