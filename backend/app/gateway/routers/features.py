"""Read-only feature inventory API."""

from __future__ import annotations

import logging
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from medrix_flow.config.agents_config import (
    AgentConfig,
    is_system_agent,
    list_custom_agents,
    list_system_agents,
)
from medrix_flow.config.extensions_config import ExtensionsConfig
from medrix_flow.skills import Skill, SkillCategory
from medrix_flow.skills.service import SkillService
from medrix_flow.subagents import list_subagents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["features"])


class FeatureAgentResponse(BaseModel):
    name: str = Field(..., description="Agent name")
    description: str = Field(default="", description="Agent description")
    model: str | None = Field(default=None, description="Optional model override")
    tool_groups: list[str] | None = Field(default=None, description="Optional tool group whitelist")
    kind: str = Field(default="custom", description="Agent kind: system or custom")
    readonly: bool = Field(default=False, description="Whether the agent is read-only")


class RedactedConfigKey(BaseModel):
    key: str = Field(..., description="Configuration key name")
    configured: bool = Field(default=True, description="Whether a value is configured")


class FeatureToolResponse(BaseModel):
    name: str = Field(..., description="MCP server name")
    enabled: bool = Field(default=True, description="Whether this MCP server is enabled")
    transport: str = Field(default="stdio", description="MCP transport type")
    description: str = Field(default="", description="Server description")
    command: str | None = Field(default=None, description="Command summary for stdio servers")
    url: str | None = Field(default=None, description="URL without query or fragment")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env_keys: list[RedactedConfigKey] = Field(default_factory=list, description="Redacted environment variable keys")
    header_keys: list[RedactedConfigKey] = Field(default_factory=list, description="Redacted HTTP header keys")
    oauth_enabled: bool = Field(default=False, description="Whether OAuth token injection is configured")


class FeatureSkillResponse(BaseModel):
    name: str = Field(..., description="Skill name")
    description: str = Field(default="", description="Skill description")
    license: str | None = Field(default=None, description="Skill license")
    category: SkillCategory | str = Field(..., description="Skill category")
    enabled: bool = Field(default=True, description="Whether this skill is enabled")


class FeaturesResponse(BaseModel):
    agents: list[FeatureAgentResponse] = Field(default_factory=list)
    tools: list[FeatureToolResponse] = Field(default_factory=list)
    skills: list[FeatureSkillResponse] = Field(default_factory=list)


def _agent_to_response(agent: AgentConfig) -> FeatureAgentResponse:
    kind = "system" if is_system_agent(agent.name) else "custom"
    return FeatureAgentResponse(
        name=agent.name,
        description=agent.description,
        model=agent.model,
        tool_groups=agent.tool_groups,
        kind=kind,
        readonly=kind == "system",
    )


def _default_agent_response() -> FeatureAgentResponse:
    return FeatureAgentResponse(
        name="default",
        description=(
            "Primary Anaxa orchestrator for chat, research routing, artifact "
            "generation, tool use, memory, and human-gated long-running workflows."
        ),
        model=None,
        tool_groups=None,
        kind="system",
        readonly=True,
    )


def _subagent_to_response(subagent) -> FeatureAgentResponse:
    return FeatureAgentResponse(
        name=subagent.name,
        description=subagent.description,
        model=None if subagent.model == "inherit" else subagent.model,
        tool_groups=subagent.tools,
        kind="subagent",
        readonly=True,
    )


def _load_agents() -> list[FeatureAgentResponse]:
    configured_agents = [_agent_to_response(agent) for agent in list_system_agents() + list_custom_agents()]
    subagents = [_subagent_to_response(subagent) for subagent in list_subagents() if subagent is not None]

    agents_by_name: dict[str, FeatureAgentResponse] = {}
    for agent in [_default_agent_response(), *configured_agents, *subagents]:
        agents_by_name.setdefault(agent.name, agent)
    return list(agents_by_name.values())


def _redacted_keys(values: dict[str, str]) -> list[RedactedConfigKey]:
    return [
        RedactedConfigKey(key=key, configured=bool(str(value).strip()))
        for key, value in sorted(values.items())
    ]


def _sanitize_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def _load_tools() -> list[FeatureToolResponse]:
    config = ExtensionsConfig.from_file()

    tools: list[FeatureToolResponse] = []
    for name, server in sorted(config.mcp_servers.items()):
        command = server.command
        tools.append(
            FeatureToolResponse(
                name=name,
                enabled=server.enabled,
                transport=server.type,
                description=server.description,
                command=command,
                url=_sanitize_url(server.url),
                args=list(server.args),
                env_keys=_redacted_keys(server.env),
                header_keys=_redacted_keys(server.headers),
                oauth_enabled=server.oauth is not None and server.oauth.enabled,
            )
        )
    return tools


def _skill_to_response(skill: Skill) -> FeatureSkillResponse:
    return FeatureSkillResponse(
        name=skill.name,
        description=skill.description,
        license=skill.license,
        category=skill.category,
        enabled=skill.enabled,
    )


@router.get(
    "/features",
    response_model=FeaturesResponse,
    summary="List Read-only Features",
    description="Return a read-only inventory of visible agents, MCP tools, and skills.",
)
async def list_features() -> FeaturesResponse:
    try:
        skills = SkillService().list_skills(enabled_only=False)
        return FeaturesResponse(
            agents=_load_agents(),
            tools=_load_tools(),
            skills=[_skill_to_response(skill) for skill in skills],
        )
    except Exception as exc:
        logger.error("Failed to load feature inventory: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load feature inventory: {str(exc)}") from exc
