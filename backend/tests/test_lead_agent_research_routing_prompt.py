from __future__ import annotations

from medrix_flow.agents.lead_agent import prompt as prompt_module


def test_apply_prompt_template_includes_research_routing_guidance(monkeypatch):
    monkeypatch.setattr(prompt_module, "_get_memory_context", lambda agent_name=None, thread_id=None: "")
    monkeypatch.setattr(prompt_module, "get_agent_soul", lambda agent_name: "")
    monkeypatch.setattr(prompt_module, "get_skills_prompt_section", lambda available_skills=None: "")
    monkeypatch.setattr(prompt_module, "get_deferred_tools_prompt_section", lambda: "")
    monkeypatch.setattr(prompt_module, "load_skills", lambda enabled_only=True: [])

    rendered = prompt_module.apply_prompt_template(subagent_enabled=True)

    assert "<research_routing_system>" in rendered
    assert "科研" in rendered
    assert "论文" in rendered
    assert "文献" in rendered
    assert "academic_research" in rendered
    assert "research_assistant" in rendered
    assert "run_pipeline" in rendered
    assert "action=\"run_pipeline\"" in rendered
    assert "experiment_execution" in rendered
    assert "pre_review" in rendered
    assert "final_release" in rendered
    assert "academic-researcher" in rendered
    assert "experiment_lab" in rendered
    assert "empirical-research-methods" in rendered
    assert "DID" in rendered
