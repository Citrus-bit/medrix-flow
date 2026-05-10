from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.gateway.routers import features
from medrix_flow.config.agents_config import AgentConfig
from medrix_flow.config.extensions_config import ExtensionsConfig, McpServerConfig
from medrix_flow.skills import Skill, SkillCategory


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(features.router)
    return TestClient(app)


def test_features_route_lists_agents_tools_and_skills_without_secrets():
    extensions = ExtensionsConfig(
        mcp_servers={
            "paper-search": McpServerConfig(
                enabled=True,
                type="http",
                url="https://mcp.example.com/sse?token=secret#frag",
                headers={"Authorization": "Bearer secret", "X-Empty": ""},
                env={"API_KEY": "secret"},
                description="Academic search tools",
            )
        },
        skills={},
    )
    skill_service = SimpleNamespace(
        list_skills=lambda enabled_only=False: [
            Skill(
                name="literature-finder",
                description="Find relevant papers",
                license="MIT",
                skill_dir=Path("/skills/public/literature-finder"),
                skill_file=Path("/skills/public/literature-finder/SKILL.md"),
                relative_path=Path("literature-finder"),
                category=SkillCategory.PUBLIC,
                enabled=True,
            )
        ]
    )

    with (
        patch("app.gateway.routers.features.list_system_agents", return_value=[AgentConfig(name="academic-researcher", description="Research agent")]),
        patch("app.gateway.routers.features.list_custom_agents", return_value=[AgentConfig(name="domain-reviewer", description="Custom reviewer", model="gpt-5.5", tool_groups=["academic"])]),
        patch("app.gateway.routers.features.is_system_agent", side_effect=lambda name: name == "academic-researcher"),
        patch("app.gateway.routers.features.list_subagents", return_value=[]),
        patch("app.gateway.routers.features.ExtensionsConfig.from_file", return_value=extensions),
        patch("app.gateway.routers.features.SkillService", return_value=skill_service),
    ):
        with _client() as client:
            response = client.get("/api/features")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agents"][0] == {
        "name": "default",
        "description": "Primary Anaxa orchestrator for chat, research routing, artifact generation, tool use, memory, and human-gated long-running workflows.",
        "model": None,
        "tool_groups": None,
        "kind": "system",
        "readonly": True,
    }
    assert payload["agents"][1] == {
        "name": "academic-researcher",
        "description": "Research agent",
        "model": None,
        "tool_groups": None,
        "kind": "system",
        "readonly": True,
    }
    assert payload["agents"][2]["kind"] == "custom"
    assert payload["tools"][0]["url"] == "https://mcp.example.com/sse"
    assert payload["tools"][0]["env_keys"] == [{"key": "API_KEY", "configured": True}]
    assert payload["tools"][0]["header_keys"] == [
        {"key": "Authorization", "configured": True},
        {"key": "X-Empty", "configured": False},
    ]
    assert "secret" not in response.text
    assert payload["skills"][0]["name"] == "literature-finder"


def test_features_route_handles_empty_inventory():
    skill_service = SimpleNamespace(list_skills=lambda enabled_only=False: [])

    with (
        patch("app.gateway.routers.features.list_system_agents", return_value=[]),
        patch("app.gateway.routers.features.list_custom_agents", return_value=[]),
        patch("app.gateway.routers.features.list_subagents", return_value=[]),
        patch("app.gateway.routers.features.ExtensionsConfig.from_file", return_value=ExtensionsConfig(mcp_servers={}, skills={})),
        patch("app.gateway.routers.features.SkillService", return_value=skill_service),
    ):
        with _client() as client:
            response = client.get("/api/features")

    assert response.status_code == 200
    assert response.json() == {
        "agents": [
            {
                "name": "default",
                "description": "Primary Anaxa orchestrator for chat, research routing, artifact generation, tool use, memory, and human-gated long-running workflows.",
                "model": None,
                "tool_groups": None,
                "kind": "system",
                "readonly": True,
            }
        ],
        "tools": [],
        "skills": [],
    }
