---
name: experiment-lab
description: Use this skill whenever the user wants reproducible CS/AI experiments, model evaluation, regression/classification/clustering analyses, bioinformatics workflows, QC, differential expression, single-cell starter analysis, or manuscript-ready experiment bundles with scientific figures. Also use it when the user asks for heatmaps, ROC/PR curves, volcano plots, UMAP/PCA projections, or wants experimental results packaged for a paper or report.
---

# Experiment Lab Skill

This skill governs MedrixFlow's experiment workflow. It does not replace execution tools. It tells the agent when to use the structured experiment pipeline and how to keep results defensible.

## Use This Skill For

- CS/AI experiments on local structured data
- Regression, classification, clustering, PCA/UMAP, and simple ablation tasks
- Empirical social-science or public-health data analysis when paired with
  `/mnt/skills/public/empirical-research-methods/SKILL.md`
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
- For empirical methods such as DID, IV, RDD, PSM/IPW, synthetic control, DML,
  causal forest, target-trial emulation, TMLE, survival, Table 1, event study,
  robustness, heterogeneity, or mechanism analysis, first load
  `/mnt/skills/public/empirical-research-methods/SKILL.md` and follow its
  identification gates.

## Iterative Experiment Loop

For code-tuning, model-training, ablation, or autonomous experiment requests, use an autoresearch-style loop when the environment supports it:

- Establish a baseline before changing code or hyperparameters.
- Define one primary metric and direction up front, such as lower validation loss or higher AUROC.
- Keep the evaluation harness, dataset split, and comparison budget fixed unless the user explicitly asks to change them.
- Change one coherent idea per trial so the result remains attributable.
- Record each trial with commit or run id, metric, memory/runtime if available, status (`keep`, `discard`, or `crash`), and a short description.
- Keep a change only when it improves the primary metric or clearly simplifies the system without hurting the metric.
- Treat crashes, OOMs, timeout, missing metrics, or incompatible dependencies as failed trials; summarize the failure and move on.
- Do not start an indefinite or overnight loop unless the user explicitly asks for a long-running autonomous run.

## CS/AI Routing

- Supervised tabular prediction: run regression or classification through `experiment_lab`
- Diagnostics:
  - binary classification -> confusion matrix, ROC, PR, feature importance if available
  - regression -> predicted-vs-actual, residual distribution, feature importance if available
- Unsupervised tasks:
  - clustering -> cluster projection + silhouette
  - dimensionality reduction -> PCA/UMAP embedding

## Empirical Research Routing

For empirical social-science and public-health datasets, the `empirical-research-methods`
skill defines the method contract. Use it to decide whether the requested work is
descriptive, predictive, or causal, then pass method details into `experiment_lab`
metadata:

- `empirical_method`: `did`, `staggered_did`, `iv`, `rdd`, `psm`, `synthetic_control`,
  `dml`, `causal_forest`, `target_trial`, `tmle`, `survival`, or `regression`
- `estimand`: ATE, ATT, LATE, CATE, event-time effect, risk difference, hazard ratio, or predictive metric
- `outcome`, `treatment`, `unit_id`, `time`, `treatment_time`, `instrument`,
  `running_variable`, `cutoff`, `covariates`, `fixed_effects`, `cluster`
- `required_outputs`: Table 1, main results, identification graphic, robustness,
  heterogeneity, mechanism, and reproducibility ledger

If the current backend cannot execute the requested causal estimator, run only
the closest safe descriptive/regression workflow, record the requested method as
not executed, and avoid causal claims.

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
- `metadata` with empirical method, estimand, variables, identification assumptions,
  and required outputs for empirical research tasks

## Final Response Pattern

- Say what analysis ran
- Report the main metrics or biological outputs
- Mention important fallbacks or skipped stages
- Point to the generated artifact bundle instead of dumping long raw output into chat
