---
name: econometric-research-writing
description: End-to-end econometric research with executable Python workflows, dataset profiling, identification and model selection (panels, IV/GMM, DiD/RDD, time series, volatility, regimes), inference diagnostics, reproducible result contracts, citation verification, and economics/management DOCX reporting with native OMML equations and three-line tables. Use when econometric design or estimation must carry through to interpretation or manuscript writing; prefer dedicated skills for pure literature lookup, generic prose polishing, generic charting, or Word-only formatting.
---

# Econometric Research Writing

## Overview

Turn a research question, dataset, draft, or result table into a defensible econometric design, an auditable Python model run, and an economics/management-style report. Keep identification, estimation, inference, writing, and document production connected through explicit specifications and validated artifacts.

Resolve `SKILL_ROOT` to the directory containing this `SKILL.md` before running bundled scripts. Never assume the user's working directory is the skill directory.

## Routing

Read only the references needed for the task:

1. Identification, estimand, outcome family, or model fit: `references/method-selection.md`.
2. Static FE/RE, Mundlak/Hausman, unbalanced panels, heterogeneous slopes, or panel dependence: `references/panel-methods.md`.
3. Dynamic panels, difference/system GMM, panel unit roots, binary panels, panel thresholds/PVAR/spatial panels: `references/panel-dynamic-nonlinear-methods.md`.
4. AR, unit roots, cointegration, ECM/VECM, Granger tests, VAR, or local projections: `references/time-series-methods.md`.
5. Thresholds/breaks, nonparametric or time-varying series, bootstrap, GARCH, Markov switching, or flexible prediction: `references/time-series-nonlinear-volatility-methods.md`.
6. IV/2SLS, weak instruments, DiD/event studies, heterogeneous adoption, synthetic counterfactuals, or causal-language boundaries: `references/iv-causal-methods.md`.
7. RDD, fuzzy RDD, matching, IPW/AIPW, PSM-DiD, or IPW-DiD: `references/rdd-matching-methods.md`.
8. Dataset intake, semantic roles, quality checks, mechanism maps, or model readiness: `references/data-analysis-workflow.md`.
9. Python analysis JSON, supported estimators, execution, or normalized outputs: `references/python-execution.md`.
10. Standard errors, clustering, few-cluster methods, weak-IV inference, GMM diagnostics, or multiplicity: `references/inference-guide.md`.
11. Regression workflow, robustness, reproducibility, and authoritative result files: `references/empirical-workflow.md`.
12. Tables, figures, event-study plots, coefficient plots, or visual QA: `references/tables-figures-style.md`.
13. Literature search boundaries, citation integrity, metadata verification, or Word citation markers: `references/literature-citation-workflow.md`.
14. Abstract, introduction, strategy, results, robustness, conclusion, or economics prose: `references/econ-writing-style.md`.
15. Word generation, OMML, template behavior, rendering, and structural QA: `references/docx-workflow.md`.

## Default Workflow

1. Define outcome, treatment/regressor, unit, time, sample, estimand, target population, and claim boundary.
2. Audit data structure and measurement before modeling.
3. Build a declared variable dictionary and causal/mechanism map. Treat name-based role hints as provisional.
4. Choose one primary estimator family and only threat-matched supporting specifications.
5. State the baseline equation, identifying assumptions, covariance estimator, cluster dimensions, diagnostics, and failure conditions.
6. Confirm that the requested estimator is implemented by the bundled Python core.
7. Freeze and validate a versioned analysis JSON against `schemas/analysis-spec.schema.json`.
8. Generate `analysis.py`, then execute it unless the user requested code generation only.
9. Inspect `manifest.json`, `run.log`, `coefficients.csv`, `diagnostics.json`, warnings, and sample accounting before interpretation.
10. Run method-matched robustness and falsification checks. Do not select specifications by significance.
11. Write from authoritative run artifacts, report economic magnitudes and uncertainty, and keep causal claims within the design.
12. If Word is required, validate the paper JSON, build DOCX, run assertion-based structural QA, render, and visually inspect every page.
13. Classify outputs as final, formal archive, reproducibility material, or temporary; remove temporary test and render artifacts.

## Python Execution Rules

- The bundled execution layer runs in Python. `backend=auto` resolves to `python`.
- Respect unsupported-estimator boundaries. Never replace heterogeneous-adoption DiD with ordinary TWFE, system GMM with naive FE, fuzzy RDD with sharp RDD, or another unrequested approximation.
- `--dry-run` means validated Python code generation, not estimation.
- Keep raw data read-only. Use dedicated run directories and preserve successful specifications, programs, manifests, logs, normalized coefficients, diagnostics, and environment information.
- The local core implements OLS, FE/TWFE, classic/common-adoption DID, IV/2SLS, sharp local-polynomial RDD, and conditional AR(p). Advanced estimators remain design guidance unless implemented in the user's Python project.

Inspect capabilities:

```bash
python3 "$SKILL_ROOT/scripts/run_econometric_analysis.py" --print-supported
```

Generate without estimating:

```bash
python3 "$SKILL_ROOT/scripts/run_econometric_analysis.py" analysis.json \
  --backend python --dry-run --output-dir .qa/python_dry_run
```

Execute an accepted specification:

```bash
python3 "$SKILL_ROOT/scripts/run_econometric_analysis.py" analysis.json \
  --backend python --output-dir results/baseline
```

Use `examples/analysis-spec.example.json` as a starting structure, not as substantive defaults.

## Method Boundaries

- Granger causality is predictive precedence, not structural causality.
- Fixed effects absorb time-invariant heterogeneity; they do not solve simultaneity or time-varying confounding.
- IV and dynamic-panel estimates remain conditional on instrument/moment validity; weak-IV-robust inference does not repair invalid instruments.
- Cointegration is a stable long-run relation, not causal proof.
- Nonparametric, threshold, regime, and time-varying models describe flexible or evolving relationships unless separately identified.
- Clustered or robust standard errors change inference, not identification.
- An insignificant diagnostic is not proof that the maintained assumption holds.

## Dataset Profiling

```bash
python3 "$SKILL_ROOT/scripts/profile_econ_dataset.py" data.csv \
  --roles-json roles.json --out .qa/data-profile.md --json-out .qa/data-profile.json
```

The profiler performs deterministic structural and quality checks. It does not perform automatic unit-root tests or validate causal roles inferred from names.

## Citation Verification

```bash
python3 "$SKILL_ROOT/scripts/verify_references.py" references.json \
  --out-md .qa/reference-verification.md \
  --out-json .qa/reference-verification.json \
  --out-enriched-json references-verified.json
```

Only DOI-resolved or independently corroborated metadata is verified automatically. A title-only candidate remains manual review. Metadata identity does not establish that a source supports a manuscript claim; maintain a claim-to-source ledger.

## DOCX Generation And QA

Use `schemas/paper-docx.schema.json`, `examples/paper-docx.example.json`, and `assets/econ-paper-template.docx`.

```bash
python3 "$SKILL_ROOT/scripts/build_paper_docx.py" paper.json paper.docx \
  --template "$SKILL_ROOT/assets/econ-paper-template.docx"
python3 "$SKILL_ROOT/scripts/check_docx_integrity.py" paper.docx \
  --require-headings --require-three-line-tables --forbid-grid-tables \
  --fail-on-plain-citations --fail-on-nonblack-headings
python3 "$SKILL_ROOT/scripts/render_validate_docx.py" paper.docx \
  --output-dir .qa/econ_docx_render
```

Represent table math explicitly with `{"text": "beta_1", "math": true}` or `{"math": "beta_1"}`. Do not infer math from underscores or Greek-letter words in ordinary labels.

## Validation Before Delivery

1. Confirm the authoritative final file/run and any formal archive.
2. Confirm the analysis spec, sample, estimator, covariance method, clusters, and diagnostics match the prose and tables.
3. Confirm citations are verified and claim-supported; flag every unresolved candidate.
4. Confirm formulas are native OMML when required and unsupported formula syntax failed explicitly.
5. Run assertion-based DOCX checks with task-appropriate minimum counts.
6. Render and visually inspect the DOCX. If rendering cannot run, report that QA as incomplete rather than successful.
7. Run the bundled regression tests after modifying the skill.
8. Remove temporary data, generated smoke-test programs, renders, PDFs/PNGs, lock files, and caches unless intentionally retained as reproducibility materials.

## Long-Term Resources

- `scripts/run_econometric_analysis.py`: validate, generate, execute, and normalize Python analyses.
- `schemas/analysis-spec.schema.json`: versioned Python econometric execution contract.
- `scripts/profile_econ_dataset.py`: deterministic dataset profiling.
- `scripts/verify_references.py`: conservative Crossref metadata verification.
- `scripts/build_paper_docx.py` and `scripts/omml_math.py`: DOCX and editable OMML generation.
- `scripts/check_docx_integrity.py`: assertion-based structural validation.
- `scripts/render_validate_docx.py`: page rendering for visual QA.
- `assets/econ-paper-template.docx`: reusable paper template.
