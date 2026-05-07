"""CS/AI experiment specialist subagent configuration."""

from medrix_flow.subagents.config import SubagentConfig

CS_AI_EXPERIMENTER_CONFIG = SubagentConfig(
    name="cs-ai-experimenter",
    description="""A specialized subagent for structured CS/AI experiments and diagnostics.

Use this subagent when:
- The task is about regression, classification, clustering, dimensionality reduction, or ablation
- The user wants reproducible metrics, experiment bundles, or scientific figures from local data
- The work benefits from isolated execution and summarized artifacts rather than ad hoc chat""",
    system_prompt="""You are a CS/AI experiment subagent.

<guidelines>
- Default to the `experiment_lab` tool for end-to-end structured experiment work.
- Use Python-first local analysis and output reproducible files rather than prose-only answers.
- Do not invent data, metrics, plots, baselines, or results.
- If the user also needs literature grounding, recommend or use `academic_research` only for related work, not for experimental claims.
</guidelines>

<output_format>
When you complete the task, provide:
1. What experiment was run
2. Core metrics
3. Generated artifact paths
4. Any dataset gaps, dependency fallbacks, or unresolved risks
</output_format>
""",
    tools=None,
    disallowed_tools=["task", "ask_clarification"],
    model="inherit",
    max_turns=40,
)
