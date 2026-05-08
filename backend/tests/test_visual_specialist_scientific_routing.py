from medrix_flow.agents.lead_agent.prompt_enhancements import VISUAL_SKILL_NAMES
from medrix_flow.subagents.builtins.visual_specialist import VISUAL_SPECIALIST_CONFIG


def test_visual_skill_names_include_scientific_image_prompting() -> None:
    assert "scientific-image-prompting" in VISUAL_SKILL_NAMES


def test_visual_specialist_prompt_contains_scientific_routing_contract() -> None:
    prompt = VISUAL_SPECIALIST_CONFIG.system_prompt
    assert "data_figure" in prompt
    assert "deterministic_diagram" in prompt
    assert "ai_scientific_illustration" in prompt
    assert "scientific-image-prompting" in prompt
    assert "currently active image provider/model from Settings" in prompt
