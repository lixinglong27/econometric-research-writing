---
name: econometric-research-writing
description: End-to-end econometric analysis and economics/management paper-writing workflow. Use for dataset profiling, model selection (panels, IV, GMM, DiD, time-series, volatility, regimes), literature/citation verification, academic prose polishing, and generating publication-style Word DOCX reports with native OMML equations and three-line tables.
---

# Econometric Research Writing

## Overview

Use this skill to turn a research question, dataset, assignment, draft, result table, or literature need into a rigorous econometric analysis and a standard economics/management paper-style Word document. The skill combines method selection, empirical workflow, modular econometric method references, field-specific writing style, top-journal table/figure conventions, literature/citation integrity, and DOCX/OMML generation and validation.

## Routing

1. For topic, identification, model choice, or method fit, read `references/method-selection.md`.
2. For single-series, multivariate time-series, nonstationarity, VAR, threshold, kernel, GARCH/ARCH, Markov-switching, or time-varying coefficient methods, read `references/time-series-methods.md`.
3. For static FE/RE, Mundlak/Hausman, GLS variance components, dynamic panels, heterogeneous slopes, panel trends, binary panels, panel VAR, spatial panels, or time-varying panels, read `references/panel-methods.md`.
4. For IV, dynamic-panel IV/GMM, panel treatment effects, synthetic counterfactuals, DiD/event-study logic, or causal claim boundaries, read `references/iv-causal-methods.md`.
5. For RDD, fuzzy RDD, propensity score matching, IPW, doubly robust weighting, PSM-DiD, or IPW-DiD, read `references/rdd-matching-methods.md`.
6. For dataset intake, variable profiling, data quality, semantic roles, mechanism paths, model-ready checks, or EDA before econometric modeling, read `references/data-analysis-workflow.md`.
7. For regression workflow, robustness, tables, or reproducibility, read `references/empirical-workflow.md`.
8. For table/figure style, regression tables, descriptive tables, event-study figures, coefficient plots, visual QA, or top-journal layout conventions, read `references/tables-figures-style.md`.
9. For paper search, literature review, source provenance, citation honesty, reference formatting, data/code citations, or Word superscript citations, read `references/literature-citation-workflow.md`.
10. For abstract, introduction, empirical strategy, results, robustness, conclusion, or style polishing, read `references/econ-writing-style.md`.
11. For Word output, formulas, rendering, superscript citation markers, or document QA, read `references/docx-workflow.md`.
12. For deterministic dataset profiling, use `scripts/profile_econ_dataset.py`; for reference verification and enriched bibliography metadata, use `scripts/verify_references.py`; for DOCX generation, use `scripts/build_paper_docx.py`; for OMML helpers, use `scripts/omml_math.py`; for structural QA, use `scripts/check_docx_integrity.py`.

## Default Workflow

1. Clarify the research claim: outcome, treatment/regressor, unit, time, sample, and target interpretation.
2. Audit the data structure: cross-section, time series, panel, balanced/unbalanced panel, binary outcome, nonstationary series, or high-dimensional nonlinear setting.
3. Build a variable dictionary and causal/mechanism map before interpreting correlations: outcome, treatment/main regressor, controls, mechanisms, moderators, instruments, fixed effects, clustering unit, and bad controls.
4. Choose one primary econometric family and one optional supporting robustness family. Do not mix methods without a clear identification or modeling reason.
5. Define the baseline equation, assumptions, estimator, diagnostics, and threat model.
6. Run or request method-matched checks: data quality, missingness, identifying variation, stationarity, lag order, FE/RE logic, IV validity, bandwidth sensitivity, residual diagnostics, placebo/falsification, or robustness by specification.
7. If external literature is used, build a claim-to-source ledger, verify paper metadata, and never include fabricated or unsupported citations.
8. Write the paper in economics/management style: claim first, method bounded by assumptions, results tied to tables/figures, limitations explicit.
9. Format empirical tables and figures in top-journal style: three-line tables by default, self-contained notes, source notes, readable figures, and text callouts explaining what to look for.
10. If the deliverable is Word, generate a `.docx` using the script/template, insert Word-native OMML formulas, use Word superscript runs for numeric citation markers when required, render pages, inspect layout, then run structural integrity checks.
11. Classify files as final, formal archive, or temporary; remove scratch scripts/renders unless they are intentional reproducibility materials.

## Method Boundaries

- Treat Granger causality as predictive precedence, not structural causality.
- Treat fixed effects as controls for time-invariant heterogeneity, not a full endogeneity solution.
- Treat IV/dynamic panel estimates as assumption-dependent; state instrument relevance and exclusion restrictions.
- Treat nonparametric/time-varying coefficient models as flexible heterogeneity or evolving association unless a separate identification design exists.
- Treat cointegration as a stable long-run relation, not causal proof.

## DOCX Generation

Use `assets/econ-paper-template.docx` as the long-term Word style template when a template is needed. For net-new papers from structured content, prefer:

```bash
python3 scripts/build_paper_docx.py input.json output.docx --template assets/econ-paper-template.docx
python3 scripts/check_docx_integrity.py output.docx
python3 scripts/render_validate_docx.py output.docx --output-dir .qa/econ_docx_render
```

Rendered PNG/PDF files are temporary QA artifacts unless the user asks to keep them.

## Validation

Before final delivery:

1. Confirm the final file path and authority status.
2. Confirm formulas are Word-native OMML when formulas matter.
3. Confirm expected headings, tables, figures/media, references, and page count when applicable.
4. Confirm citations are verified, source-backed, and formatted in the requested style; if superscript markers are expected, confirm they are true superscript runs.
5. Render and visually inspect the `.docx`; if rendering is unavailable, state that visual QA could not be completed.
6. Remove temporary files or explicitly mark them as temporary.

## References And Assets

- `references/method-selection.md`: choose models from research question and data structure.
- `references/time-series-methods.md`: AR, unit-root, threshold, kernel, cointegration, Granger, VAR, TV-VAR, and nonlinear time-series methods.
- `references/panel-methods.md`: FE/RE, balanced/unbalanced panels, heterogeneous slopes, dynamic panels, panel nonstationarity, binary panels, and time-varying panels.
- `references/iv-causal-methods.md`: IV/2SLS, dynamic-panel IV, DiD/event studies, and causal claim boundaries.
- `references/rdd-matching-methods.md`: RDD, fuzzy RDD, propensity score matching, IPW, and combined matching/weighting DiD designs.
- `references/data-analysis-workflow.md`: econometric dataset intake, variable semantics, quality checks, mechanism maps, and model-readiness rules.
- `references/empirical-workflow.md`: end-to-end econometric analysis and robustness workflow.
- `references/tables-figures-style.md`: economics/management top-journal table and figure conventions.
- `references/literature-citation-workflow.md`: literature search, citation integrity, reference verification, and Word citation markers.
- `references/econ-writing-style.md`: economics/management academic writing style and section templates.
- `references/docx-workflow.md`: Word, OMML, render QA, and file-handling rules.
- `assets/econ-paper-template.docx`: reusable standard paper template.
