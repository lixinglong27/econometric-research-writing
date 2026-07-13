# IV And Causal Methods

Use this reference for endogeneity, instruments, dynamic-panel IV/GMM, DiD/event studies, staggered adoption, synthetic counterfactuals, and causal-language boundaries. Pair it with [Panel Methods](panel-methods.md), [Dynamic And Nonlinear Panel Methods](panel-dynamic-nonlinear-methods.md), or [Time-Series Methods](time-series-methods.md) for the underlying data structure.

## Table Of Contents

- Causal Framing
- IV And 2SLS
- Weak-Instrument Diagnostics And Inference
- Dynamic Panel IV And GMM
- Difference-In-Differences And Event Studies
- Modern Staggered DiD
- Panel Treatment Effects And Synthetic Counterfactuals
- Granger, VAR, Cointegration, And Causal Language
- Robustness And Validity Checks
- Writing Templates
- Claim Boundaries
- See Also

## Causal Framing

Before using causal language, define:

- Treatment/endogenous regressor, outcome, unit, time, and target population.
- Estimand: ATE, ATT, LATE, group-time ATT, dynamic effect path, or another explicit target.
- Counterfactual comparison and source of identifying variation.
- Assignment level and corresponding inference level.
- Main threats: omitted variables, reverse causality, selection, measurement error, anticipation, spillovers, attrition, nonstationarity, or common shocks.

An estimator is not an identification strategy. State which assumption links observed variation to the counterfactual; otherwise use association, prediction, dynamic relation, or long-run relation.

## IV And 2SLS

For one endogenous regressor:

```text
Structural:  Y_i = beta X_i + W_i' gamma + u_i
First stage: X_i = Z_i' pi + W_i' delta + v_i
```

2SLS projects every endogenous regressor on all excluded instruments and included exogenous controls, then estimates the structural equation using the projected endogenous variation. Compute 2SLS covariance from the IV estimator; OLS standard errors from a regression on fitted values are not valid.

Core assumptions:

- Relevance/rank: excluded instruments supply enough linearly independent conditional variation for all endogenous regressors.
- Independence/exogeneity: instruments are conditionally uncorrelated with unobserved structural determinants of the outcome.
- Exclusion: instruments affect the outcome only through the specified endogenous treatment channels.
- Monotonicity and a well-defined treatment version when interpreting a binary-instrument estimate as LATE.

Workflow:

1. Explain why OLS may be endogenous and why each instrument shifts each endogenous variable.
2. Defend exclusion and independence institutionally; balance or overidentification tests cannot prove them.
3. Report first stages, reduced forms, partial strength diagnostics, instrument/endogenous-variable counts, and sample changes.
4. Match heteroskedasticity/cluster-robust inference to the assignment and sampling process in both diagnostics and structural estimates.
5. State the estimand. With heterogeneous effects, IV generally weights effects for units whose treatment responds to instrument-induced variation; multiple instruments need not identify one simple universal LATE.

Overidentification tests assess whether moment conditions are mutually compatible under maintained assumptions. A non-rejection does not validate exclusion; a just-identified model has no overidentifying restrictions to test.

## Weak-Instrument Diagnostics And Inference

Do not use `first-stage F > 10` as a universal rule. Strength is conditional on controls, all endogenous variables, the covariance structure, and the inferential target.

Report as applicable:

- Excluded-instrument partial `R^2` and first-stage coefficient(s).
- The conventional partial F statistic under homoskedastic i.i.d. errors.
- A heteroskedasticity/cluster-robust rank/strength statistic such as the Kleibergen–Paap rk Wald F, computed with the same dependence structure as the outcome inference.
- For one endogenous regressor, an effective-F diagnostic designed for heteroskedasticity/autocorrelation when available.
- For multiple endogenous regressors, Sanderson–Windmeijer conditional first-stage statistics or another diagnostic that assesses identification of each equation conditional on the others.

Stock–Yogo critical values were derived for the homoskedastic Cragg–Donald setting and do not transfer mechanically to a robust Kleibergen–Paap statistic. No single cutoff proves adequate strength.

When weakness is plausible:

- Report Anderson–Rubin confidence sets/tests and, when supported, conditional likelihood-ratio or weak-IV-robust score/LM procedures. These remain valid under weak relevance only if instrument exogeneity/exclusion and the covariance procedure are valid.
- Consider LIML or Fuller-type estimators as sensitivity checks because they can reduce 2SLS median bias with many/weak instruments; they do not repair invalid instruments.
- Show reduced-form estimates and confidence intervals. A strong-looking first-stage p-value alone does not establish precise structural inference.
- Limit many instruments and prespecify or justify instrument selection; instrument proliferation can overfit the first stage and bias 2SLS toward OLS.

If weak-IV-robust confidence sets are wide, unbounded, or disjoint, report that identification is weak rather than selecting a convenient conventional interval.

## Dynamic Panel IV And GMM

```text
Y_it = rho Y_{i,t-1} + X_it' beta + alpha_i + u_it
Delta Y_it = rho Delta Y_{i,t-1} + Delta X_it' beta + Delta u_it
```

Differencing removes `alpha_i` but makes `Delta Y_{i,t-1}` correlated with `Delta u_it`. Valid instruments follow from explicit regressor timing and serial-correlation assumptions.

- Difference GMM instruments differenced equations with suitably lagged levels.
- System GMM adds level equations instrumented by lagged differences under additional initial-condition/mean-stationarity restrictions.
- Strictly exogenous, predetermined, and endogenous regressors require different lag windows; specify each rather than using one default set.
- With highly persistent series, difference-GMM level instruments can be weak. System GMM can help only when its extra level moments are defensible.

Minimum reporting:

- Difference or system GMM, first differences or forward orthogonal deviations, one-step or two-step.
- Exact lag windows by variable/equation, collapsed status, unit and instrument counts.
- Robust one-step inference and finite-sample-corrected two-step covariance (for example, Windmeijer) when two-step estimates are reported.
- Arellano–Bond residual tests: differenced AR(1) is expected; failure to reject AR(2) is relevant for common `t-2` instruments.
- Hansen/Sargan and difference-in-Hansen results with their limitations; many instruments can make these tests uninformative.
- Sensitivity to lag limits, instrument reduction, difference versus system moments, and a credible bias-corrected FE/QMLE alternative when possible.

See the advanced panel reference for full moment and initial-condition guidance. Do not write that GMM “solves endogeneity.”

## Difference-In-Differences And Event Studies

For a single treatment date:

```text
Y_it = alpha_i + gamma_t + beta (Treat_i x Post_t)
     + X_it' delta + epsilon_it
```

Event study:

```text
Y_it = alpha_i + gamma_t
     + sum_{k != -1} beta_k I(event_time_it=k)
     + X_it' delta + epsilon_it
```

Workflow:

1. Define treatment, comparison group, treatment timing, event-time binning, and reference period.
2. Defend parallel trends for the target counterfactual, conditional on any covariates.
3. Use only pre-treatment covariates unless a time-varying control has a clearly defended causal role.
4. Assess pre-treatment dynamics, but do not treat insignificant leads as proof; low power and selective windows can hide violations.
5. Address anticipation, spillovers, treatment reversals, composition/attrition, and concurrent policies.
6. Cluster at the treatment-assignment level; with few treated/assignment clusters, use design-appropriate small-sample or randomization-based inference.

With repeated cross-sections, confirm that population composition is comparable over time and use the estimator for repeated samples rather than implying unit-level changes.

## Modern Staggered DiD

When adoption timing differs and effects vary by cohort or event time, a single TWFE coefficient can combine treated-versus-not-yet-treated and already-treated comparisons with opaque or negative weights.

Preferred workflow:

1. Define cohorts by first treatment date and identify never-treated or valid not-yet-treated controls.
2. Estimate group-time ATT effects using a heterogeneity-robust design such as a Callaway–Sant'Anna family estimator, an interaction-weighted Sun–Abraham event study, or a suitable imputation/stacked design.
3. Aggregate only supported cohort-time cells and state the weighting target.
4. Report observations/units by cohort and event time, not only a balanced event plot.
5. Check comparison-group choice, anticipation windows, treatment reversals, cohort composition, and pre-treatment support.
6. Use simultaneous event-study bands or multiplicity-aware inference when the full path is confirmatory.

TWFE can remain a descriptive benchmark, not the only causal estimate under heterogeneous staggered adoption. The target is generally an ATT for treated cohorts under the chosen parallel-trends and comparison-group assumptions, not a universal ATE.

## Panel Treatment Effects And Synthetic Counterfactuals

```text
Y_it = D_it Y_it(1) + (1-D_it)Y_it(0)
tau_it = Y_it(1) - Y_it(0)
```

Use synthetic-control, matrix-completion, interactive fixed-effect, or related counterfactual methods when treated units have rich pre-treatment outcomes and untreated donors can recover the untreated path.

Workflow:

1. Define treated units, donor pool, intervention date, anticipation period, and post-treatment target.
2. Exclude donors that are treated, indirectly affected, or mechanically tied to treated outcomes.
3. Use pre-treatment outcomes/covariates only to fit the counterfactual and report fit over the whole pre-period.
4. Plot observed and constructed paths plus the post-treatment gap `tau_hat_t = Y_t - Y_hat_t(0)`.
5. Report placebo/permutation inference, leave-one-out results, donor/predictor-window sensitivity, and uncertainty suited to the method.

Poor pre-treatment fit undermines post-treatment attribution. Placebo ranks are discrete with few donors, and low pre-period error can mechanically inflate post/pre fit ratios; disclose the comparison set. Interpret results as gaps for treated units relative to a constructed counterfactual, not a universal effect.

## Granger, VAR, Cointegration, And Causal Language

- Granger causality: incremental predictive precedence, conditional on the included history.
- Reduced-form VAR/PVAR: dynamic dependence; causal shocks require structural restrictions or external variation.
- Cointegration/VECM: stable long-run combinations and adjustment, not causal mechanisms.
- Threshold/time-varying models: regime-dependent or evolving associations unless joined to an identification design.

Prefer “predicts future changes,” “is associated with,” “consistent with,” or “under the maintained identification assumptions.” Avoid “proves,” “fully identifies,” and “solves endogeneity.”

## Robustness And Validity Checks

- IV: conditional first stages, reduced forms, weak-IV-robust intervals, alternative defensible instruments, instrument count, and exclusion falsification where logically possible.
- Dynamic panel: regressor timing, lag windows, instrument reduction, AR(1)/AR(2), GMM step/correction, system-moment tests, and QMLE/bias-corrected sensitivity.
- DiD/event study: pre-period support, placebo dates/groups, alternative windows, assignment-level inference, anticipation/spillovers, and composition.
- Staggered DiD: group-time support, comparison group, aggregation weights, treatment reversals, simultaneous bands, and heterogeneity-robust estimators.
- Synthetic counterfactuals: fit, donor contamination, placebo reference set, leave-one-out checks, and alternative donor/predictor windows.
- Time-series causal claims: stationarity/cointegration, lag order, reverse direction, structural restrictions, and break sensitivity.

## Writing Templates

IV:

```text
I instrument [X] with [Z]. Relevance requires [Z] to shift [X] conditional on [controls], while exclusion and independence require [Z] to affect [Y] only through [X] and to be conditionally unrelated to structural outcome shocks. I report conditional first-stage diagnostics and weak-instrument-robust inference; the estimate pertains to variation in [X] induced by [Z] under these assumptions.
```

Dynamic panel:

```text
Because lagged [Y] is correlated with the transformed error in a short panel, I estimate [difference/system] GMM using the declared lag windows. Validity requires the stated regressor-timing, serial-correlation, and [for system GMM] level-moment restrictions. I limit the instrument set and report corrected inference and residual/moment diagnostics.
```

DiD:

```text
The design compares changes in [Y] for treated units with contemporaneous changes in [comparison units]. The ATT interpretation requires that, absent treatment and conditional on [covariates if any], the groups would have followed parallel trends, with no anticipation or spillovers over the stated window.
```

Staggered DiD:

```text
Because adoption timing varies, I estimate cohort-by-time effects relative to [never-treated/not-yet-treated] units and aggregate only supported cells. This targets an ATT for treated cohorts under cohort-specific parallel trends and no anticipation; TWFE is reported only as a benchmark.
```

Synthetic counterfactual:

```text
I construct [treated unit]'s untreated path from unaffected donors using pre-intervention information. The post-treatment gap is interpretable only if pre-treatment fit captures the untreated dynamics and the intervention does not contaminate donors.
```

## Claim Boundaries

- IV identifies an instrument-induced estimand only under relevance, exclusion, independence, and any required monotonicity/treatment-version assumptions.
- Weak-IV-robust procedures protect against weak relevance, not invalid instruments.
- Dynamic-panel GMM depends on timing, serial-correlation, initial-condition, and moment restrictions; diagnostics do not prove them.
- DiD estimates a treatment effect only under the stated parallel-trends, anticipation, spillover, and composition assumptions.
- Staggered estimators target supported group-time effects under their comparison-group assumptions.
- Synthetic methods estimate a treated-unit gap relative to a modeled counterfactual whose credibility rests on donor validity and pre-treatment fit.

## See Also

- [Method Selection](method-selection.md)
- [Panel Methods](panel-methods.md)
- [Dynamic And Nonlinear Panel Methods](panel-dynamic-nonlinear-methods.md)
- [RDD And Matching Methods](rdd-matching-methods.md)
- [Time-Series Methods](time-series-methods.md)
