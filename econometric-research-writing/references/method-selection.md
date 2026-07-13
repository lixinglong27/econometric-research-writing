# Method Selection

Use this reference when the user asks what model to use, how to frame an empirical strategy, or whether a proposed method fits the data.

## Table Of Contents

- Intake Checklist
- Selection Rules
- Model Choice Output
- Red Flags
- See Also

## Intake Checklist

Identify:

- Unit: person, firm, country, region, asset, market, product, or aggregate series.
- Time: none, short panel, long panel, single time series, event window, repeated cross-sections.
- Outcome: continuous, binary, count, fractional, ordinal, censored/truncated, choice, duration, index, rate, log level, or growth rate.
- Main regressor: policy, treatment, price, GDP, exposure, lagged outcome, instrumented variable, latent factor.
- Variable roles: controls, mechanisms, moderators, instruments, fixed effects, clustering unit, sample flags, and bad controls.
- Target interpretation: prediction, association, elasticity, dynamic response, treatment effect, long-run relation, heterogeneity.
- Target population/estimand: ATE, ATT, ATC, overlap-population effect, LATE, local RDD effect, forecast, or descriptive parameter.
- Main threat: omitted variables, reverse causality, simultaneity, nonstationarity, serial correlation, cross-sectional dependence, selection, measurement error.
- Dependence/assignment level: unit, treatment group, geography, time, network, or multiple dimensions; record the effective number of independent clusters.

## Selection Rules

- Use OLS/cross-sectional regression when the outcome is continuous, units have no meaningful time dimension, and the target is association or prediction.
- Use fixed effects panel models when unobserved time-invariant unit heterogeneity is central and panel data are available.
- Use two-way fixed effects only when time shocks also matter; avoid causal language unless treatment timing/design assumptions are credible.
- Use random effects only when unit effects are plausibly uncorrelated with regressors.
- Use Mundlak-style correlated random effects when the report needs an explicit bridge between FE and RE or a direct test of correlation between regressors and unit effects.
- Use random coefficient or heterogeneous-slope models when unit-specific elasticities are the object of interest.
- Use dynamic panel IV/GMM when lagged outcomes are regressors and fixed effects create correlation after demeaning/differencing; use QMLE/conditional-mean approaches when the initial condition and regressor process assumptions are defensible.
- Use IV/2SLS when a regressor is endogenous and a defensible instrument is available.
- When instruments may be weak, use design-appropriate strength diagnostics and weak-instrument-robust confidence sets; a first-stage `F > 10` is not a universal validity rule.
- Use DiD/event study when there is a policy/treatment event with treated and control groups and credible parallel trends.
- Use modern staggered DiD estimators when treatment timing differs across cohorts and effects may be heterogeneous; do not rely only on a TWFE coefficient in that setting.
- Use RDD when treatment assignment changes discontinuously at a known cutoff in a running variable and continuity around the cutoff is credible.
- Use matching, IPW, or doubly robust weighting when selection on observables is the best defensible design and overlap/balance can be demonstrated.
- Use PSM-DiD or IPW-DiD when both observable imbalance and before-after treatment timing matter; parallel trends remains required after matching or weighting.
- Use panel synthetic counterfactual methods when one or more treated units have rich pre-treatment panels and the goal is a treatment-effect path relative to a constructed untreated outcome.
- Use time-series AR/ARIMA when a single series has persistence and forecasting is central.
- Use ADF/PP/KPSS and cointegration tools when series may be nonstationary.
- Use VAR when multiple endogenous time series interact and the goal is forecasting or dynamic dependence.
- Use structural VAR only if the identifying restrictions are explicitly justified.
- Use ARCH/GARCH-family models when conditional volatility, volatility clustering, or risk dynamics are central.
- Use Markov-switching models when regimes are latent and relationships change probabilistically across states.
- Use threshold/structural-change models when relationships change across regimes or candidate break points.
- When a threshold or break is estimated rather than fixed in advance, use nonstandard or bootstrap inference because the threshold is unidentified under the no-change null.
- Use kernel/nonparametric methods when the functional form is unknown and sample size supports local estimation.
- Use time-varying coefficient or TV-VAR methods when coefficient paths are central to the research question.
- Use binary-response models when the outcome is an indicator: conditional FE logit, RE/correlated-RE logit or probit, and the FE linear probability model answer different questions and impose different assumptions.
- Use Poisson/negative-binomial families for counts and fractional-response models for outcomes in `[0,1]`; do not substitute OLS merely because interpretation is familiar.
- Use ordered logit/probit for ordinal outcomes, multinomial models for unordered choices, and censored/truncated models only when the observation mechanism truly censors or truncates a latent outcome.
- Use duration/hazard models for time-to-event outcomes, with censoring, time origin, risk set, competing risks, and proportional-hazards assumptions stated explicitly.
- Use sample-selection models when outcome observability is nonrandom; credible correction normally needs an exclusion variable or strong functional-form assumptions, not an inverse Mills ratio added mechanically.
- Use quantile regression when conditional distributional heterogeneity is the target; its slope is not automatically an individual-level treatment effect or the effect on an unconditional quantile.
- Use local projections for horizon-specific dynamic responses when flexible impulse-response estimation is useful; causal shock language still requires a structural identification design.
- Treat mediation variables as post-treatment: causal direct/indirect effects require explicit sequential-identification assumptions and sensitivity analysis, while adding a mediator to a regression can induce bad-control bias.
- With complex surveys, preserve sampling weights, strata, clusters, and replicate-weight design in both estimation and variance calculations. For missing data, align multiple imputation with the analysis model and pool estimates and uncertainty rather than single-imputing silently.

Inference follows the design, not the estimator label:

- Cluster at the level where treatment or shocks are assigned and errors can co-move; use multiway clustering only when each clustering dimension has enough independent clusters.
- With few clusters, use a justified small-sample correction or wild-cluster procedure and disclose its limits.
- If common factors create cross-sectional dependence, time effects or clustered standard errors may be insufficient; consider common-factor/CCE modeling or large-`T` dependence-robust inference.
- When many outcomes, horizons, subgroups, or specifications are treated as confirmatory, define the testing family and use multiplicity control or simultaneous confidence bands; distinguish prespecified tests from exploratory ones.

## Model Choice Output

When recommending a method, provide:

1. Baseline model equation.
2. Why the method matches the data and question.
3. Key identifying or interpretation assumptions.
4. Required diagnostics.
5. Robustness checks.
6. Estimand, standard-error/clustering plan, and target population.
7. What the method cannot claim.

## Red Flags

- A causal claim with no treatment design, instrument, or credible identification story.
- A levels regression with nonstationary time series and no unit-root/cointegration discussion.
- A dynamic panel estimated by naive OLS after fixed effects without discussing Nickell bias/endogeneity.
- A random-effects estimate reported without considering whether regressors are correlated with unit effects; use Hausman or Mundlak logic.
- A synthetic-counterfactual estimate with poor pre-treatment fit, contaminated donor units, or no placebo/sensitivity checks.
- A staggered-adoption DiD design reported only as a TWFE coefficient without cohort/time heterogeneity checks.
- A matching or IPW estimate with no overlap and balance diagnostics.
- A doubly robust estimate described as automatically unbiased without overlap and without stating which treatment or outcome nuisance model must be correct.
- An RDD estimate without running-variable plots, manipulation checks, bandwidth sensitivity, or covariate continuity checks.
- A GARCH estimate interpreted as a mean effect rather than volatility dynamics.
- A threshold or time-varying model with no bandwidth/threshold sensitivity.
- An estimated threshold or structural break reported with ordinary fixed-threshold standard errors.
- A panel model that ignores cross-sectional dependence when units share macro shocks.
- A clustered analysis with few effective clusters and no small-sample discussion.
- Survey-weighted point estimates paired with ordinary model-based standard errors that ignore the survey design.
- A mediator included as a routine control and then interpreted as identifying a causal mechanism.
- Many outcomes, horizons, or subgroups highlighted selectively with no multiplicity or exploratory-analysis disclosure.
- Tables of coefficients with no economic magnitude interpretation.

## See Also

- [Time-Series Methods](time-series-methods.md)
- [Nonlinear And Volatility Time-Series Methods](time-series-nonlinear-volatility-methods.md)
- [Panel Methods](panel-methods.md)
- [Dynamic And Nonlinear Panel Methods](panel-dynamic-nonlinear-methods.md)
- [IV and Causal Methods](iv-causal-methods.md)
- [RDD and Matching Methods](rdd-matching-methods.md)
- [Data Analysis Workflow](data-analysis-workflow.md)
