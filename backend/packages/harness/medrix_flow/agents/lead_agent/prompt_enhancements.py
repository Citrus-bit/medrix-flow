"""
Enhanced prompt sections for improving visual output quality.
Injected into the system prompt when visual-related skills are active.
"""

# Visual skills that trigger prompt enhancement injection
VISUAL_SKILL_NAMES = frozenset({
    "chart-visualization",
    "ppt-generation",
    "image-generation",
    "data-analysis",
    "frontend-design",
    "web-design-guidelines",
})

VISUAL_QUALITY_PROMPT = """\
<visual_quality_system>
**MANDATORY for all visual output tasks (charts, images, PPT, layout).**

## Design Standards
- **60-30-10 color rule**: 60% dominant, 30% secondary, 10% accent. Max 5 colors. Use hex codes (#667eea, not "purple").
- **Typography hierarchy**: Headlines 36-72pt bold (600-700), body 14-20pt regular (400), max 2 font families. Ensure 4.5:1 contrast ratio.
- **Layout**: 8-point grid spacing. 40-60% negative space. One focal point per composition. Rule of thirds for balance.
- **Accessibility**: No red-green only encoding. High contrast text. Color-blind safe palettes.

## Task-Specific Rules

**Charts**: Data integrity first — never truncate Y-axis without justification. Add data labels for key values. Avoid 3D charts, pie charts with >6 slices, and chartjunk. Every chart must answer "what and how much" at a glance.

**PPT**: One message per slide. Storytelling arc: Hook → Context → Solution → Impact → CTA. Headlines top 20%, images 50-70% of slide area. Generate slides sequentially with reference chaining for visual consistency.

**Images**: Prompts must be 150+ words with specific details (lighting, composition, color palette, camera angle, style reference). Always use image_search for reference images when accuracy matters. Include negative_prompt to exclude unwanted elements.

## Mandatory Workflow
1. **Clarify FIRST**: If audience, style, or brand guidelines are unclear → ask_clarification before any generation.
2. **Spec before generate**: Write a JSON spec to /mnt/user-data/workspace/ defining style, colors, typography, layout.
3. **Self-review before delivery**: Check visual hierarchy, color harmony, typography readability, spacing, alignment.
4. **Iterate if needed**: If self-review finds issues, fix and regenerate. Max 3 iterations before seeking user feedback.
5. **Present with context**: When delivering, briefly explain key design decisions and offer to iterate.

**CRITICAL**: Never deliver first-draft visual output without self-review. Quality over speed.
</visual_quality_system>"""


def get_visual_quality_prompt() -> str:
    """Return the visual quality prompt section for system prompt injection."""
    return VISUAL_QUALITY_PROMPT
