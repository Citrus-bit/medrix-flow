---
name: empirical-research-methods
description: Use this skill for empirical social-science research, applied economics, public policy, education, finance, management, sociology, psychology, epidemiology, or public-health data studies. It routes DID, staggered DID, IV, RDD, PSM/IPW, synthetic control, DML, causal forest, panel regression, event studies, target-trial emulation, TMLE, survival analysis, Table 1, robustness checks, heterogeneity, mechanisms, replication packages, and journal-style empirical paper outputs into MedrixFlow's research quest and experiment_lab workflows.
license: CC BY-SA 4.0 derivative guidance from Awesome-Agent-Skills-for-Empirical-Research
---

# Empirical Research Methods

This skill adapts the workflow ideas from
[Awesome Agent Skills for Empirical Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research)
into MedrixFlow. It is a routing and integrity layer, not a vendored copy of the
whole upstream repository.

## Use This Skill For

- empirical papers in economics, policy, education, finance, management, sociology, psychology, epidemiology, public health, or related social-science fields
- causal inference or econometric analysis: DID, staggered DID, IV, RDD, PSM/IPW, entropy balancing, synthetic control, DML, causal forest, target-trial emulation, TMLE, survival, mediation, heterogeneity, mechanisms
- requests such as "run a full empirical analysis", "make Table 1", "event study", "parallel trends", "robustness checks", "replication package", "AER/QJE style table", or "Quarto/Stata/R/Python empirical workflow"
- automatic research quests whose experiment stage depends on a real dataset and a defensible identification strategy

## Core Principle

Treat empirical work as a staged design argument, not a single model fit. The
agent must first establish the data contract and estimand, then run diagnostics,
then estimate, then stress-test, then package results for review.

## MedrixFlow Routing

- Use `research_assistant` when the user wants a staged automatic research project, manuscript lifecycle, human gates, reviewer loop, or final bundle.
- Use `academic_research` only for related work, identification precedent, measurement precedent, and citation grounding.
- Use `experiment_lab` for execution on local data. Pass method information in `analysis_type` and `metadata`, including the chosen empirical method, estimand, identifiers, time variables, treatment variables, covariates, fixed effects, cluster level, and robustness plan.
- Use `manuscript_export` only after empirical claims have corresponding result artifacts and citation evidence.

## Workflow Contract

### 1. Intake And Data Contract

Before estimation, identify:

- outcome variable
- treatment or exposure variable
- unit identifier and time variable for panel/event-study designs
- treatment timing for DID/staggered DID
- running variable and cutoff for RDD
- instrument for IV
- matching/IPW covariates for PSM/IPW
- cluster level and fixed effects
- sample restrictions and missing-data policy
- primary estimand: ATE, ATT, LATE, CATE, event-time effect, risk difference, hazard ratio, or predictive metric

If these are missing and cannot be inferred from uploaded data, ask for them or
create a blocked research quest entry. Do not silently choose a causal design.

### 2. Method Selection

Use this decision table:

| User/Data Signal | Default Route |
|---|---|
| panel policy timing, treated/control groups | DID or staggered DID |
| staggered adoption or heterogeneous timing | modern staggered DID; avoid plain TWFE as the only result |
| plausible discontinuity threshold | RDD with bandwidth, density, and covariate balance checks |
| endogenous treatment plus instrument | IV/2SLS with first-stage F and overidentification checks when applicable |
| selection on observables | PSM/IPW/entropy balancing plus balance diagnostics |
| single treated unit or few treated units | synthetic control or synthetic DID |
| high-dimensional nuisance controls | DML/causal forest with cross-fitting and CATE diagnostics |
| public-health cohort or RWE request | target-trial emulation, IPTW/g-formula/TMLE, survival where applicable |
| no treatment or causal estimand | descriptive, predictive, or correlational analysis only; label it accordingly |

### 3. Mandatory Empirical Outputs

For a full empirical analysis, produce an artifact bundle with:

- `experiment_plan.md`: research question, estimand, identification assumptions, variables, sample restrictions, budget, and human approvals
- `methods.md`: data cleaning, model equations, fixed effects, standard errors, diagnostics, and limitations
- `results.md`: main findings with cautious interpretation
- `metrics.json`: structured estimates, standard errors, p-values, fit metrics, diagnostics, and robustness status where available
- `figure_manifest.json`
- tables: Table 1 / balance, main results, robustness, heterogeneity, and mechanisms when applicable
- figures: trend/event-study/RD/balance/coef/spec-curve plots when applicable
- `reproducibility_ledger.json` or equivalent metadata recording dataset paths, seeds, package fallbacks, and skipped checks

### 4. Identification Gates

Block or downgrade causal language when:

- treatment assignment is not plausibly exogenous and no design handles it
- DID lacks a credible pre-trend or event-study check when pre-period data exists
- IV has weak first-stage evidence
- RDD lacks density/covariate-balance diagnostics
- PSM/IPW lacks post-adjustment balance diagnostics
- DML/CATE work lacks cross-fitting or honest sample splitting where relevant
- the dataset has no declared outcome/treatment for causal claims

When blocked, preserve the exploratory outputs and state what design input is
missing. Do not turn correlation into causation.

## Experiment Lab Metadata Pattern

When calling `experiment_lab`, include metadata like:

```json
{
  "skill": "empirical-research-methods",
  "empirical_method": "did",
  "estimand": "ATT",
  "outcome": "y",
  "treatment": "treated",
  "unit_id": "unit_id",
  "time": "year",
  "treatment_time": "first_treat_year",
  "covariates": ["x1", "x2"],
  "fixed_effects": ["unit_id", "year"],
  "cluster": "unit_id",
  "required_outputs": ["table1", "main_results", "event_study", "robustness"]
}
```

Use `analysis_type` values such as `did`, `staggered_did`, `iv`, `rdd`,
`psm`, `synthetic_control`, `dml`, `causal_forest`, `target_trial`,
`tmle`, `survival`, `regression`, or `classification`. If the current backend
does not implement the requested estimator, run the closest safe descriptive or
regression workflow, mark the requested method as not executed, and keep the
quest blocked before causal manuscript claims.

## Writing Rules

- Separate literature evidence from empirical evidence.
- Cite method precedent through `academic_research`; cite actual estimates only from generated artifacts.
- Use cautious language: "associated with" for non-causal designs; "estimated effect" only when the identification gate passes.
- For paper outputs, feed the empirical result artifacts and claim map into `manuscript_export`; do not write unsupported causal claims.

## Source Basis

This skill takes the useful structure from the upstream Awesome Agent Skills for
Empirical Research project: StatsPAI-style agent-native causal workflows,
classical Python/R/Stata 8-step empirical pipelines, method-specific checks
(DID/IV/RDD/PSM/SCM/DML), and reproducibility packaging. It intentionally avoids
blindly importing huge third-party skill bundles or assuming proprietary tools
are installed.
