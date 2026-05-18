from __future__ import annotations

from medrix_flow.agents.lead_agent import prompt as prompt_module
from medrix_flow.tools.tools import get_available_tools


def test_plan_mode_uses_guided_intake_prompt_not_visible_plan(monkeypatch) -> None:
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda agent_name=None, thread_id=None: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda agent_name: "")
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "load_skills", lambda enabled_only=True: [])

    normal = prompt_module.apply_prompt_template()
    plan_mode = prompt_module.apply_prompt_template(plan_mode=True)

    assert "<guided_intake_system>" not in normal
    assert "<guided_intake_system>" in plan_mode
    assert "ask_clarification" in plan_mode
    assert "write_plan" not in plan_mode
    assert "approval card" not in plan_mode
    assert "Plan tab" not in plan_mode


def test_plan_mode_does_not_expose_write_plan_tool() -> None:
    tool_names = {
        tool.name
        for tool in get_available_tools(
            include_mcp=False,
            plan_mode=True,
        )
    }

    assert "ask_clarification" in tool_names
    assert "write_plan" not in tool_names


def test_prompt_includes_startup_intake_rules(monkeypatch) -> None:
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda agent_name=None, thread_id=None: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda agent_name: "")
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "load_skills", lambda enabled_only=True: [])

    rendered = prompt_module.apply_prompt_template()

    assert "Startup Intake for Complex or High-Risk Tasks" in rendered
    assert "Before starting complex or high-risk work" in rendered
    assert "file/code changes" in rendered
    assert "whether file edits/commands are allowed" in rendered
    assert "Ask one high-impact question at a time" in rendered
    assert "Do not force intake for simple, low-risk, fully specified requests" in rendered
    assert "Subagents cannot interact with the user" in rendered


def test_legacy_plan_modules_are_removed() -> None:
    tool_names = {tool.name for tool in get_available_tools(include_mcp=False)}

    assert "write_plan" not in tool_names
