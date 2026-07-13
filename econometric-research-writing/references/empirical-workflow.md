# Empirical Workflow

Use this reference to run or plan an econometric analysis from model-ready data to final paper tables. For initial dataset profiling, variable semantics, data quality, and causal/mechanism mapping, read `data-analysis-workflow.md` first. For final table/figure style and Word layout rules, read `tables-figures-style.md`.

## Table Of Contents

- Analysis Pipeline
- Execution Contract
- Reproducibility Contract
- Baseline Table Plan
- Robustness Menu
- Results Interpretation
- Table Writing Rules
- Failure Modes
- See Also

## Analysis Pipeline

1. Define the research question as a testable relationship.
2. Build the analysis sample and record every filter.
3. Create a variable dictionary that assigns economic roles: outcome, main regressor, controls, mechanisms, moderators, instruments, fixed effects, clustering unit, and bad controls.
4. Create variables with explicit formulas, units, logs, lags, differences, and winsorization rules.
5. Produce descriptive statistics and sample coverage tables.
6. Diagnose data structure: missingness, balance, outliers, stationarity, serial correlation, cross-sectional dependence, and identifying variation after fixed effects.
7. Map the likely pathway from main regressor to outcome and match robustness checks to each threat.
8. Freeze a machine-readable analysis specification: Python backend, method, variables, fixed effects, covariance estimator, clusters, sample filters, diagnostics, seed, and output directory.
9. Validate the specification, record Python/package availability, and generate the Python program before execution.
10. Estimate the baseline model without silently changing estimator, sample, or inference settings.
11. Inspect the run manifest, logs, coefficient output, warnings, and method-specific diagnostics before interpreting estimates.
12. Estimate alternative specifications that answer specific threats.
13. Run robustness checks matched to the method.
14. Convert estimates to economic magnitudes.
15. Produce final tables/figures with self-contained notes, source notes, and text callouts.
16. Write interpretation with limitations and citation-backed claims.

## Execution Contract

- The bundled execution layer runs in Python; `backend=auto` resolves to `python`.
- If the user's project already has a Python environment, inspect it and state the selected interpreter before estimation.
- Never replace an unsupported estimator with a simpler one after a failure without explicit disclosure.
- Keep raw data read-only and write generated programs, logs, manifests, diagnostics, coefficients, tables, and figures to a dedicated run directory.
- Validate every structured analysis specification against the bundled schema before execution.
- Treat a generated `analysis.py` from a dry run as reproducibility material, not evidence that estimation completed.
- For advanced estimators such as heterogeneous-adoption DiD, system GMM, high-dimensional FE, local projections, or robust-bias-corrected RDD, require a Python package or project implementation that preserves the requested estimand and diagnostics. Do not approximate silently.

See `python-execution.md` for execution capabilities and `inference-guide.md` for covariance and diagnostic selection.

## Reproducibility Contract

- Keep raw data read-only.
- Save cleaned data separately.
- Save scripts that transform raw to clean and clean to results.
- Save the validated analysis specification, generated Python program, run manifest, stdout/stderr log, normalized coefficient output, and diagnostics.
- Save final tables/figures under stable names.
- Save verified citation/reference metadata when literature is used.
- Record package versions when possible.
- Record the Python executable, backend, package versions, random seed, input-file hash, and analysis-spec hash.
- Do not overwrite final outputs without creating a formal archive or noting the authority change.

## Baseline Table Plan

Typical empirical paper tables should use clean economics-style three-line formatting in Word outputs unless the user requests a different journal/class template:

- Table 1: sample construction or descriptive statistics.
- Table 2: baseline estimates.
- Table 3: mechanism, heterogeneity, or dynamic response.
- Table 4: robustness and sensitivity.
- Figure 1: raw trend, event-study path, coefficient path, or key model visualization.

## Robustness Menu

Choose only checks that target real threats:

- Alternative dependent variable definitions.
- Alternative main regressor definitions.
- Additional fixed effects or time controls.
- Alternative clustering/standard errors.
- Few-cluster corrections, multiway clustering, or dependence-robust alternatives when justified.
- Lagged regressors or lagged outcome controls.
- Sample restrictions and influential-unit exclusion.
- Placebo outcomes or placebo timing.
- Pre-trend checks for event designs.
- Bandwidth/threshold sensitivity for nonparametric and threshold methods.
- Instrument set sensitivity for IV/dynamic panel.
- Weak-identification-robust inference for IV when instrument strength is uncertain.
- Lag order and stability diagnostics for VAR/time series.

## Results Interpretation

For every main coefficient:

1. State sign and statistical evidence.
2. Translate magnitude into the original economic unit or elasticity.
3. Compare with baseline mean or plausible benchmark.
4. State whether the estimate is robust across key specifications.
5. State the interpretation boundary.

Avoid reading too much into controls. Controls are often included to improve comparability or reduce omitted-variable concerns; they are not automatically substantive findings.

For mechanism variables, state whether the estimate is a separate mechanism test, a mediation-style specification, or a changed estimand after conditioning on a post-treatment variable.

## Table Writing Rules

- Put the main coefficient in the same row across columns.
- Use clear column labels, not only model numbers.
- Report sample size and fixed effects.
- Report standard-error type and clustering.
- Keep notes concise and specific.
- Keep source notes below other table notes.
- Avoid significance stars unless the user/course/journal requires them; if used, define thresholds.
- Do not bury important sample restrictions in prose only.

## Failure Modes

- Analysis has many specifications but no baseline.
- Robustness checks are unrelated to the threat model.
- Result interpretation repeats statistical significance but never explains economic magnitude.
- The paper claims causality while the design only supports association.
- Generated Word/PDF outputs are not rendered and visually checked.

## See Also

- [Data Analysis Workflow](data-analysis-workflow.md)
- [Method Selection](method-selection.md)
- [Inference Guide](inference-guide.md)
- [Tables and Figures Style](tables-figures-style.md)
