---
name: scientific-image-prompting
description: Use this skill whenever the user asks for a graphical abstract, mechanism illustration, study design schematic, concept explainer, scientific cover art, or any non-data academic image that may appear in a paper, report, poster, or slides. Always use this skill before image-generation for scientific illustrations. Do not use it for real data figures such as ROC curves, heatmaps, volcano plots, UMAPs, bar charts, or any plot that should come from validated data.
---

# Scientific Image Prompting

## Purpose

This skill is for **scientific illustrations**, not data plots.

Use it to turn a research intent into a prompt package that is:
- publication-aware
- visually precise
- traceable
- explicit about what is conceptual vs. measured

## Hard Routing Rule

Before writing any prompt, classify the request into exactly one route:

1. `data_figure`
- Real experiment or statistical figure
- Examples: ROC, PR, heatmap, volcano, PCA, UMAP, histogram, line chart, confusion matrix
- Action: stop using this skill and route to `experiment-lab`, `nature-figure`, or validated Python/R plotting

2. `deterministic_diagram`
- Flowchart, architecture, workflow, study design, pipeline, mechanism path that should be clean and diagrammatic
- Action: prefer `fireworks-tech-graph` or another deterministic diagram workflow

3. `ai_scientific_illustration`
- Graphical abstract, concept art, mechanism imagination, cover art, non-quantitative scientific explainer
- Action: continue with this skill, then hand off to `image-generation`

If the request contains measured values, axes, significance claims, or looks like a result figure, it is **not** `ai_scientific_illustration`.

## Allowed Figure Types

Use one of these `figure_type` values:
- `graphical_abstract`
- `mechanism_illustration`
- `workflow_schematic`
- `study_design`
- `cover_art`
- `concept_explainer`

## Prompt Contract

Create `prompt.json` with this contract:

```json
{
  "prompt_contract_version": "scientific-image-prompting.v1",
  "route": "ai_scientific_illustration",
  "figure_type": "graphical_abstract",
  "scientific_goal": "What the figure should explain",
  "must_include": [
    "Required scientific entities, stages, organs, cells, devices, molecules, or scene elements"
  ],
  "must_not_invent": [
    "Any measured result, axis, p-value, or unsupported biological / technical claim"
  ],
  "label_strategy": "short labels only | no embedded labels | leave whitespace for post-edit annotation",
  "composition": "panel structure, focal path, camera angle, negative space",
  "style": "flat vector-like | polished 3D editorial | biomedical infographic | clean concept art",
  "lighting": "if applicable",
  "color_palette": "3-5 colors with scientific publishing intent",
  "reference_requirements": [
    "what reference images are needed and why"
  ],
  "prompt": "Final English generation prompt",
  "negative_prompt": "What must be excluded",
  "technical": {
    "aspect_ratio": "16:9",
    "image_size": "4K",
    "output_mime_type": "image/png",
    "scientific_mode": true
  }
}
```

## Writing Rules

- Always write the final generation prompt in English.
- Chinese may be used only for local explanation to the user.
- Keep the figure conceptual unless the user supplied real measured content to place into a non-plot illustration.
- Prefer white or very light backgrounds for paper-ready figures.
- Minimize embedded text inside the image. If labels are needed, keep them short and publication-like.
- If visual fidelity matters, gather reference images first.

## Scientific Guardrails

- Do not fabricate data-like figures.
- Do not generate fake microscopy, fake western blots, fake sequencing plots, fake statistical charts, or fake benchmark panels as if they were results.
- Do not imply that an imagined mechanism has been experimentally validated unless the user explicitly provided that evidence.
- If the figure is conceptual, ensure the downstream deliverables say so.

## Required Deliverables

For scientific illustration requests, prepare these files in outputs:
- `scientific-illustration-4k.png`
- `prompt.json`
- `prompt_audit.md`
- `caption.md`
- `ai_disclosure.md`

## Audit Notes

`prompt_audit.md` must briefly record:
- chosen route
- chosen `figure_type`
- why AIGC is appropriate here
- what was intentionally excluded to avoid fake data presentation
- provider/model choice, including whether it came from the active Settings configuration or an explicit override
- size/output target: `4K`, `PNG`

`ai_disclosure.md` must explicitly state that the image is a conceptual or illustrative figure generated with AI assistance and should not be interpreted as raw experimental evidence.

## Handoff to Image Generation

After `prompt.json` is ready, call `image-generation` in scientific mode with:

```bash
python /mnt/skills/public/image-generation/scripts/generate.py \
  --prompt-file /mnt/user-data/outputs/prompt.json \
  --output-file /mnt/user-data/outputs/scientific-illustration-4k.png \
  --manifest-file /mnt/user-data/outputs/generation_manifest.json \
  --aspect-ratio 16:9 \
  --scientific-mode \
  --image-size 4K \
  --output-mime-type image/png
```

Default to the active image provider/model configured in Settings. Only add `--provider`, `--model`, or `--base-url` when the user explicitly wants to override the configured provider.

If the user asked for a lower-cost draft, use:
- `--draft-mode`
- or explicitly `--model gemini-2.5-flash-image`

## Final Check

Before delivery, confirm:
- this is not a disguised data figure
- the image is conceptual and paper-appropriate
- prompt, manifest, caption, and disclosure files all exist
- the final output is `PNG` and intended as `4K`
