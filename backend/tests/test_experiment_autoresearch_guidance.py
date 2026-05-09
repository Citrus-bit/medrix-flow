from __future__ import annotations

from pathlib import Path

from medrix_flow.config.system_agents import CS_AI_LAB
from medrix_flow.subagents.builtins.cs_ai_experimenter import CS_AI_EXPERIMENTER_CONFIG
from medrix_flow.tools.builtins.experiment_lab_tool import experiment_lab_tool


def test_experiment_lab_skill_documents_iterative_experiment_loop():
    skill_path = Path(__file__).resolve().parents[2] / "skills/public/experiment-lab/SKILL.md"
    text = skill_path.read_text(encoding="utf-8")

    assert "Iterative Experiment Loop" in text
    assert "autoresearch-style loop" in text
    assert "baseline" in text
    assert "primary metric" in text
    assert "`keep`, `discard`, or `crash`" in text


def test_empirical_research_methods_skill_is_available_and_routed():
    root = Path(__file__).resolve().parents[2]
    skill_text = (root / "skills/public/empirical-research-methods/SKILL.md").read_text(encoding="utf-8")
    experiment_text = (root / "skills/public/experiment-lab/SKILL.md").read_text(encoding="utf-8")

    assert "Awesome-Agent-Skills-for-Empirical-Research" in skill_text
    assert "DID" in skill_text
    assert "IV" in skill_text
    assert "RDD" in skill_text
    assert "experiment_lab" in skill_text
    assert "manuscript_export" in skill_text
    assert "empirical-research-methods" in experiment_text
    assert "identification gates" in experiment_text


def test_cs_ai_experimenter_mentions_autoresearch_style_loop():
    prompt = CS_AI_EXPERIMENTER_CONFIG.system_prompt

    assert "autoresearch-style loop" in prompt
    assert "baseline" in prompt
    assert "primary metric" in prompt
    assert "keep/discard/crash" in prompt
    assert "empirical-research-methods" in prompt


def test_cs_ai_lab_mentions_autoresearch_style_loop():
    assert "autoresearch-style loop" in CS_AI_LAB.soul
    assert "fixed evaluation harness" in CS_AI_LAB.soul
    assert "keep/discard/crash" in CS_AI_LAB.soul
    assert "empirical-research-methods" in CS_AI_LAB.soul


def test_experiment_lab_tool_mentions_iterative_trial_log():
    assert experiment_lab_tool.description is not None
    assert "iterative or autonomous experiment requests" in experiment_lab_tool.description
    assert "keep/discard/crash" in experiment_lab_tool.description
