---
name: experiment-lab
description: Use this skill whenever the user wants reproducible CS/AI experiments, model evaluation, regression/classification/clustering analyses, bioinformatics workflows, QC, differential expression, single-cell starter analysis, or manuscript-ready experiment bundles with scientific figures. Also use it when the user asks for heatmaps, ROC/PR curves, volcano plots, UMAP/PCA projections, or wants experimental results packaged for a paper or report.
---

# Experiment Lab Skill

This skill governs MedrixFlow's experiment workflow. It does not replace execution tools. It tells the agent when to use the structured experiment pipeline and how to keep results defensible.

## Use This Skill For

- CS/AI experiments on local structured data
- Regression, classification, clustering, PCA/UMAP, and simple ablation tasks
- Bioinformatics workflows on local expression data, metadata tables, `h5ad`, or 10x matrix bundles
- QC, differential expression, enrichment attempts, marker-gene summaries
- Requests for manuscript-grade figures or experiment bundles for a report

## Core Rules

- Do not invent datasets, metrics, plots, baselines, enrichments, or scientific conclusions.
- If the task requires actual experimental output, prefer the `experiment_lab` tool instead of ad hoc reasoning.
- Ask for missing inputs before running a workflow when the absence would invalidate the result:
  - no dataset
  - no target column for supervised CS/AI work
  - no metadata/group labels for requested differential analysis
- Keep literature evidence separate from experimental evidence. Use `academic_research` only for related work or method framing.
- Default to Python-first execution. Do not ask the user to choose Python or R unless they explicitly request R output.

## CS/AI Routing

- Supervised tabular prediction: run regression or classification through `experiment_lab`
- Diagnostics:
  - binary classification -> confusion matrix, ROC, PR, feature importance if available
  - regression -> predicted-vs-actual, residual distribution, feature importance if available
- Unsupervised tasks:
  - clustering -> cluster projection + silhouette
  - dimensionality reduction -> PCA/UMAP embedding

## Bioinformatics Routing

- Bulk expression:
  - sample QC
  - sample PCA
  - top-variable-gene heatmap
  - differential analysis when metadata allows
  - enrichment attempt when significant genes and dependencies allow
- Single-cell starter:
  - cell QC
  - PCA/UMAP embedding
  - clustering
  - marker summary
  - marker heatmap or violin plot

## Expected Deliverables

When using the structured pipeline, prefer returning a concise summary plus artifacts. The artifact bundle should usually include:

- `experiment_plan.md`
- `methods.md`
- `results.md`
- `metrics.json`
- `figure_manifest.json`
- `figures/`
- `tables/`

If the experiment is linked to an academic project, also retain:

- `paper_ready_results.md`
- `evidence.json`

## Tool Contract

Use `experiment_lab` when the user needs execution, metrics, or figure generation. Pass:

- `topic`
- `dataset_paths`
- `domain` when clear
- `analysis_type` when explicit
- `target_column` for supervised CS/AI work
- `metadata_path`, `sample_id_column`, and `group_column` for bulk expression tasks when available
- `linked_academic_project_id` when the experiment should feed a formal report

## Final Response Pattern

- Say what analysis ran
- Report the main metrics or biological outputs
- Mention important fallbacks or skipped stages
- Point to the generated artifact bundle instead of dumping long raw output into chat
