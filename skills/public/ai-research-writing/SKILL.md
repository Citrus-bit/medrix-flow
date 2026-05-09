---
name: ai-research-writing
description: Use when the user wants academic writing prompts, paper polishing workflows, translation/rewrite guidance, reviewer-style paper critique, experiment write-up help, title/caption drafting, or practical AI-assisted research writing support. This skill adapts the prompt library and usage guidance curated in the awesome-ai-research-writing repository into a MedrixFlow-compatible writing workflow.
author: Leey21-inspired MedrixFlow adaptation
version: "1.0.0"
---

# AI Research Writing

This skill adapts the practical academic-writing prompt collection from the
`awesome-ai-research-writing` repository into a MedrixFlow-compatible workflow.

Use it when the user asks for:

- Chinese-to-English or English-to-Chinese academic translation
- paper polishing or de-AI-ification
- logic checking for manuscript sections
- title or caption drafting
- reviewer-style critique of a paper draft
- experiment analysis write-up support
- research-writing prompt recommendations

## Scope

This is a writing-support skill, not an execution-heavy tool skill.

It should help the agent:

- choose an appropriate writing mode
- structure the task before editing
- apply concise academic-writing constraints
- return polished output plus brief rationale when useful

## Working Method

1. Identify the writing intent first:
   - translation
   - polishing
   - logic audit
   - reviewer critique
   - title/caption generation
   - experiment analysis
2. Preserve factual meaning. Do not invent claims, citations, results, or
   novelty.
3. If the user provides draft text, work directly on that text rather than
   answering abstractly.
4. If the user asks for publication-grade wording, prefer concise, natural,
   reviewer-resistant academic prose over flashy wording.
5. For full paper/manuscript generation, default to LaTeX source and PDF output.
   Use exact BibTeX keys from `references.bib`, call `manuscript_export` for
   final delivery, and avoid `\nocite{*}` unless explicitly requested.
6. If the user is writing in Chinese, you may explain decisions in Chinese, but
   produce the requested target-language result exactly as asked.

## Output Modes

### 1. Translation

- Keep technical meaning stable.
- Preserve formulas, symbols, and explicit numeric claims.
- Escape LaTeX-sensitive characters only when the user wants LaTeX-ready output.

### 2. Polishing

- Remove awkward AI-style phrasing.
- Prefer precise verbs, concrete logical connectors, and shorter sentences.
- Do not over-intensify novelty claims.

### 3. Logic Audit

- Flag missing assumptions, unsupported jumps, repeated points, and vague
  conclusions.
- Prefer reviewer-style comments tied to the specific text.

### 4. Reviewer Critique

- Evaluate contribution clarity, methodological trust, evidence sufficiency,
  limitation handling, and writing clarity.
- Separate major issues from minor issues when helpful.

### 5. Titles and Captions

- Optimize for specificity and information density.
- Avoid hype and vague adjectives.

## Suggested Response Pattern

When editing concrete text, prefer:

1. the revised output
2. a short list of the main fixes if the user would benefit

When auditing text, prefer:

1. key issues
2. a revised version or repair strategy

## References

The source repository also contains a broader prompt library and usage notes for
research writing. This adaptation is intentionally lightweight so the skill can
be loaded by MedrixFlow's native skill loader without requiring external
tooling.
