# Dynamic And Nonlinear Panel Methods

Use this focused reference for lagged outcomes, difference/system GMM, dynamic-panel QMLE, panel unit roots and cointegration, nonlinear trends or thresholds, binary and other limited outcomes, time-varying panels, panel VAR, and spatial panels. Use [Panel Methods](panel-methods.md) for static FE/RE, Mundlak, unbalanced panels, heterogeneous slopes, and dependence-robust inference.

## Table Of Contents

- Dynamic Panels
- Difference And System GMM
- Likelihood And Bias-Corrected Alternatives
- Panel Unit Roots And Cointegration
- Nonlinear Trends And Panel Thresholds
- Binary And Other Limited-Outcome Panels
- Time-Varying And Trending Panels
- Panel VAR
- Spatial Panel Models
- Method-Matched Robustness
- Claim Boundaries
- See Also

## Dynamic Panels

Use a lagged outcome only when persistence, adjustment, or state dependence is part of the economic model.

```text
Y_it = rho Y_{i,t-1} + X_it' beta + alpha_i + lambda_t + u_it
```

First differencing removes `alpha_i` but creates correlation between the transformed lag and transformed error:

```text
Delta Y_it = rho Delta Y_{i,t-1} + Delta X_it' beta + Delta u_it
```

In short-`T` panels, within OLS has Nickell bias. Choose among GMM, bias-corrected FE, QMLE, and conditional-mean approaches according to `N`, `T`, persistence, regressor timing, and initial-condition assumptions. A lagged outcome does not by itself justify GMM.

Classify every time-varying regressor before constructing moments:

- Strictly exogenous: uncorrelated with errors in every period.
- Predetermined: may respond to past errors but is uncorrelated with current and future errors.
- Endogenous: may correlate with the current error, so deeper lags are needed.

The exact valid lag window follows from that classification and the assumed serial-correlation structure; do not accept software defaults silently.

## Difference And System GMM

Difference GMM uses suitably lagged levels as instruments for differenced equations. Under serially uncorrelated level errors, common starting points are current values for strictly exogenous regressors, lags dated `t-1` or earlier for predetermined regressors, and `t-2` or earlier for endogenous regressors and the lagged outcome. Adjust these dates if the maintained error process differs.

System GMM adds level equations instrumented with lagged differences:

```text
Differenced moments: E[Z_it Delta u_it] = 0
Additional level moments: E[Delta Z_it (alpha_i + u_it)] = 0
```

The additional level moments require restrictions on initial conditions/mean stationarity and correlation with unit effects. System GMM is not automatically valid or preferable; it can strengthen weak difference-GMM instruments for persistent series only when those extra restrictions are credible.

Workflow:

1. State the asymptotic setting, usually large `N` and short/moderate `T`.
2. Classify regressors and specify lag windows separately for differenced and level equations.
3. Limit and usually collapse instruments; instrument proliferation can overfit endogenous variables and weaken specification tests.
4. Report one-step robust estimates and, if using two-step GMM, finite-sample-corrected two-step standard errors such as the Windmeijer correction.
5. In differenced residuals, first-order serial correlation is expected; failure to reject no second-order serial correlation supports—but does not prove—the validity of lags dated `t-2` and earlier.
6. Report the number of units and instruments. Keeping instruments below `N` is only a rough discipline, not a validity criterion.
7. Report Hansen's robust overidentification test cautiously; it can have low power with many instruments. The Sargan test relies on homoskedasticity. Use difference-in-Hansen tests for added system-GMM moment subsets while recognizing their own finite-sample weakness.
8. Compare credible lag windows, transformations, and difference versus system GMM. Large shifts are evidence that the identifying moments are fragile.

If instruments are weak because the series is highly persistent, do not present precise GMM output as a solution. Consider system moments only when defensible, or use bias-corrected/QMLE alternatives and report sensitivity.

## Likelihood And Bias-Corrected Alternatives

- Bias-corrected FE/LSDV estimators can be attractive when `T` is moderate and the dynamic model is otherwise correctly specified.
- Dynamic-panel QMLE models the conditional likelihood or covariance structure and can be more efficient, but it requires explicit treatment of the initial observation and regressor process.
- Correlated-random-effects/conditional-mean approaches model `E(alpha_i | Y_i0, X_i)` using the initial outcome and regressor histories or means. Report that specification rather than calling the unit effect exogenous.
- Forward orthogonal deviations subtract a scaled mean of future observations and can preserve observations in unbalanced panels; transformation does not relax instrument-timing assumptions.

Compare GMM and non-GMM estimators only when their maintained assumptions and targets are clear. Agreement is supportive, not a specification test.

## Panel Unit Roots And Cointegration

Use a levels autoregression or its ADF reparameterization consistently:

```text
Levels form:
Y_it = mu_i + delta_i t + phi_i Y_{i,t-1}
     + sum_j psi_ij Delta Y_{i,t-j} + e_it
H0: phi_i = 1

Equivalent ADF form:
Delta Y_it = mu_i + delta_i t + rho_i Y_{i,t-1}
           + sum_j psi_ij Delta Y_{i,t-j} + e_it
rho_i = phi_i - 1; H0: rho_i = 0
```

Do not test `beta_i=1` on a coefficient multiplying `Delta Y_{i,t-1}`; that is not the unit-root null.

Workflow:

- Choose intercept/trend terms and lag lengths from the data-generating story and residual behavior.
- Use a test matching slope heterogeneity: LLC-type procedures impose a common persistence alternative, while IPS/Fisher-type procedures allow heterogeneous alternatives.
- First-generation tests assume cross-sectional independence or limited dependence. With common shocks, use cross-sectionally augmented/CIPS-type tests or an explicit factor structure.
- Unit-root statistics have nonstandard null distributions; use test-specific critical values or p-values, not ordinary normal/t critical values.
- Check structural-break sensitivity and report which share of units drives rejection; panel rejection does not imply that every unit is stationary.

Panel cointegration means that a stated linear combination of nonstationary variables is stationary:

```text
Y_it - X_it' beta_i is I(0), although Y_it and X_it may be I(1).
```

Use residual-based Pedroni/Kao-type or error-correction/Westerlund-type procedures according to the heterogeneity assumptions. Address common factors with bootstrap, factor-augmented, or CCE-compatible procedures. Estimate long-run coefficients with a method suited to endogeneity and serial correlation, such as panel DOLS/FMOLS or CCE-based estimators, and report whether slopes are pooled or heterogeneous.

Cointegration supports a stable long-run relation, not causal identification.

## Nonlinear Trends And Panel Thresholds

Flexible trend panel:

```text
Y_it = X_it' beta + alpha_i + g_i(t/T) + e_it
```

Use time FE when common time shocks are nuisance controls; estimate explicit polynomial/spline/smooth trends only when their shape is substantively relevant. Choose polynomial order conservatively and plot the supported trend range.

Observed-threshold panel:

```text
Y_it = alpha_i + X_it' beta_1 I(q_it <= c)
     + X_it' beta_2 I(q_it > c) + e_it
```

If `c` is estimated, trim candidate values to maintain adequate observations/units in every regime. Because the threshold is unidentified under the no-threshold null, ordinary Wald/F reference distributions are invalid; use a sup-type statistic with bootstrap or the method-specific nonstandard distribution and construct a threshold confidence set by profile-likelihood inversion or bootstrap. Treat endogenous threshold variables/regressors with an identification method designed for that problem.

## Binary And Other Limited-Outcome Panels

Latent-index binary model:

```text
Y_it = I(X_it' beta + alpha_i + epsilon_it >= 0)
Pr(Y_it=1 | X_it, alpha_i) = F(X_it' beta + alpha_i)
```

The main estimators are not interchangeable:

- FE linear probability model: removes `alpha_i` by within transformation and permits simple clustered inference, but is heteroskedastic and can predict outside `[0,1]`.
- Conditional FE logit: conditions out `alpha_i`; units with no within-unit outcome change do not identify `beta`. It estimates conditional log-odds slopes, while average partial effects require additional treatment of unit effects.
- Unconditional FE logit/probit: estimating many unit intercepts creates incidental-parameter bias when `T` is short. Bias correction or large-`T` justification is required. Probit has no conditional-likelihood analogue that removes unrestricted unit effects as conditional logit does.
- RE logit/probit: integrates over a specified unit-effect distribution and requires conditional independence. A Mundlak/correlated-RE formulation can model correlation with regressors but does not remove all misspecification risk.
- Dynamic binary models: distinguish true state dependence from persistent heterogeneity and address the initial-conditions problem explicitly.

Report probability-scale quantities or average partial effects with their target population, not raw latent-index coefficients alone. For rare outcomes, separation, or few within-unit switches, report effective identifying observations.

For counts, FE Poisson QMLE can consistently estimate conditional-mean slopes under correct mean specification without equidispersion, using robust inference; negative-binomial FE variants impose different heterogeneity structures. Fractional outcomes require a fractional-response mean model rather than treating a two-limit outcome as an ordinary uncensored continuous variable.

## Time-Varying And Trending Panels

```text
Y_it = f(t/T) + X_it' beta(t/T) + alpha_i + e_it
```

Local linear methods estimate coefficient paths with kernel weights around each normalized date. Factor-augmented versions can separate common latent shocks from coefficient drift.

Workflow:

- Impose a fixed-effect normalization such as `sum_i alpha_i=0`.
- Select and report the kernel, bandwidth, boundary treatment, and effective local sample.
- Plot coefficient paths with pointwise or simultaneous uncertainty bands, labeled correctly.
- Test constancy with method-specific or bootstrap inference and compare with a constant-slope benchmark.
- Add common factors when heterogeneous exposure to aggregate shocks could masquerade as coefficient change.

Time variation describes evolving relationships; it does not identify why coefficients changed.

## Panel VAR

Use when a vector of panel variables is jointly endogenous and dynamic feedback is the target.

```text
y_it = A_1 y_{i,t-1} + ... + A_p y_{i,t-p}
     + alpha_i + lambda_t + epsilon_it
```

Define the endogenous vector, choose lag order, remove fixed effects appropriately, and use GMM or bias-corrected methods when short `T` makes transformed lags endogenous. Check companion-matrix stability and report impulse responses with uncertainty bands.

Reduced-form PVAR identifies predictive feedback. Structural shock language requires a defended ordering, external instruments, sign/long-run restrictions, or another identification strategy. Cross-sectional dependence and common factors must be handled rather than assumed away.

## Spatial Panel Models

Common forms:

```text
Spatial lag:    Y_it = rho W Y_it + X_it' beta + alpha_i + lambda_t + e_it
Spatial error:  Y_it = X_it' beta + alpha_i + lambda_t + u_it
                u_it = rho W u_it + e_it
Spatial Durbin: Y_it = rho W Y_it + X_it' beta + W X_it' theta
                + alpha_i + lambda_t + e_it
```

Workflow:

1. Define and justify `W` before inspecting preferred results; state normalization.
2. Distinguish endogenous outcome interaction, correlated shocks, and contextual covariate spillovers.
3. Use an estimator that addresses simultaneity in `W Y_it`.
4. Report direct, indirect, and total effects when feedback makes raw coefficients non-marginal.
5. Test plausible alternative weights matrices and treatment/spillover exposure definitions.

Spatial correlation alone does not establish causal spillovers, and arbitrary choices of `W` can drive results.

## Method-Matched Robustness

- Dynamic panels: lag depth, regressor classification, difference versus system moments, instrument count/collapse, AR(1)/AR(2), Hansen/Sargan limits, Windmeijer correction, and QMLE/bias-corrected sensitivity.
- Panel unit roots/cointegration: deterministic terms, lag selection, heterogeneous alternatives, cross-sectional dependence, breaks, and estimator/test family.
- Thresholds: candidate range, trimming, regime support, bootstrap/nonstandard inference, and threshold confidence set.
- Binary/limited outcomes: estimator-specific identifying sample, link, incidental parameters, initial conditions, marginal effects, and separation/rare outcomes.
- Time-varying panels: bandwidth, boundary behavior, simultaneous bands, constancy tests, and factor controls.
- PVAR: lag order, stability, transformation, impulse-response uncertainty, and structural restrictions.
- Spatial panels: weights matrix, direct/indirect effects, simultaneity, and alternative network definitions.

## Claim Boundaries

- Dynamic-panel estimates depend on timing, serial-correlation, initial-condition, and instrument restrictions.
- A non-rejected overidentification or AR(2) test does not prove moment validity.
- Panel unit-root rejection may concern only part of the panel; panel cointegration is not causal proof.
- Threshold and time-varying models describe heterogeneity unless paired with credible treatment or shock identification.
- Binary-panel coefficients are link- and estimator-specific; report probability-scale effects only when identified.
- PVAR and spatial dependence are not structurally causal without explicit shock or spillover identification.

## See Also

- [Panel Methods](panel-methods.md)
- [Method Selection](method-selection.md)
- [IV And Causal Methods](iv-causal-methods.md)
- [Time-Series Methods](time-series-methods.md)
