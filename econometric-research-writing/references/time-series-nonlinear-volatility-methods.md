# Nonlinear And Volatility Time-Series Methods

Use this focused reference for estimated thresholds and structural breaks, kernel/nonparametric regression, time-varying coefficients and TV-VAR, dependence-aware bootstrap, ARCH/GARCH volatility, Markov switching, and flexible semiparametric prediction. Use [Time-Series Methods](time-series-methods.md) for AR, unit roots, cointegration, ECM/VECM, Granger tests, VAR, and local projections.

## Table Of Contents

- Thresholds And Structural Change
- Kernel And Nonparametric Regression
- Time-Varying VAR And Coefficients
- Dependence-Aware Bootstrap
- ARCH And GARCH Volatility Models
- Markov-Switching Models
- Semiparametric And Flexible Prediction
- Method-Matched Robustness
- Claim Boundaries
- See Also

## Thresholds And Structural Change

Use when dynamics or slopes differ across an observed state, an estimated threshold, or break dates.

```text
y_t = x_t' beta_1 I(q_t <= c) + x_t' beta_2 I(q_t > c) + e_t
```

Common variants include threshold autoregression (`x_t` and `q_t` contain lagged `y`), smooth-transition models, and break models with `q_t=t`.

Workflow:

1. Define the threshold variable, delay, candidate range, and economic meaning before emphasizing results.
2. For fixed `c`, estimate side-specific dynamics and use inference appropriate to time dependence.
3. For unknown `c`, trim candidate values so every regime has adequate effective observations, search the declared grid, and report the criterion profile and regime sizes.
4. Because `c` is unidentified under the linear/no-threshold null, ordinary fixed-threshold Wald/F/LR reference distributions are invalid. Use a method-specific sup-Wald/sup-LR/sup-LM test with bootstrap or its nonstandard asymptotic distribution.
5. Construct a confidence set for `c` through profile-likelihood/criterion inversion or a valid bootstrap; do not report the minimizing grid point as if known exactly.
6. For multiple breaks, use a multiple-break procedure such as Bai–Perron with minimum segment lengths and report break-date uncertainty. A pre-specified Chow test and an unknown-date Quandt/sup test answer different questions.

Threshold-unit-root tests also have nonstandard distributions specific to the nonlinear null/alternative. Do not reuse ordinary ADF critical values. A threshold model describes regime-dependent dynamics; it does not identify the cause of a regime.

## Kernel And Nonparametric Regression

Conditional mean:

```text
m_hat(x) = sum_t K((x_t-x)/h) y_t / sum_t K((x_t-x)/h)
```

Use local linear rather than local constant smoothing when boundary bias or local slope estimation matters. State the kernel, bandwidth, polynomial order, boundary treatment, and effective local sample size.

Time-series observations are dependent. Bandwidth selection, standard errors, and confidence bands must allow for serial dependence through a justified HAC, block bootstrap, sieve/bootstrap, or other method-matched procedure. Ordinary i.i.d. cross-validation and pointwise i.i.d. bands can be misleading.

Always show bandwidth sensitivity and avoid interpreting unsupported edge behavior. Flexible fit is not evidence of causal nonlinearity.

## Time-Varying VAR And Coefficients

```text
y_t = a(tau_t) + sum_{j=1}^p A_j(tau_t)y_{t-j} + eta_t
tau_t = t/T
```

Estimate coefficient matrices and innovation covariance locally in normalized time, usually with local linear kernel weights. At each reported date, check the effective sample and local stability; an apparently smooth path can be a bandwidth artifact.

Workflow:

- Fix or select lag order transparently and report the bandwidth rule.
- Plot coefficient/response paths with pointwise or simultaneous bands labeled correctly.
- Test constancy with an integrated/sup statistic whose critical values account for smoothing and dependence.
- Compare with constant-parameter and discrete-break alternatives.
- If reporting time-varying impulse responses, state whether shocks are reduced-form or structurally identified at each date.

## Dependence-Aware Bootstrap

Use a dynamic/dependent wild bootstrap, block bootstrap, sieve bootstrap, or model-based residual bootstrap when serial dependence makes i.i.d. resampling invalid.

Generic dependent-wild workflow:

1. Estimate the null or unrestricted mean/coefficient path with the bandwidth required by the test.
2. Center residuals as the procedure requires.
3. Multiply them by a mean-zero, unit-variance dependent multiplier process with a declared dependence tuning parameter.
4. Reconstruct the bootstrap series under the correct null, re-estimate all selected/generated quantities, and recompute the statistic.
5. Use enough repetitions for the requested tail probability and report Monte Carlo uncertainty when material.

Bootstrap validity is procedure-specific. Re-selecting lags, thresholds, or bandwidths in the original analysis but fixing them in bootstrap samples understates model-selection uncertainty unless the method explicitly permits it.

## ARCH And GARCH Volatility Models

```text
r_t = mu_t + epsilon_t
epsilon_t = sigma_t z_t

ARCH(q):
sigma_t^2 = omega + sum_{j=1}^q alpha_j epsilon_{t-j}^2

GARCH(1,1):
sigma_t^2 = omega + alpha epsilon_{t-1}^2 + beta sigma_{t-1}^2
```

Workflow:

1. Specify and diagnose the conditional mean before modeling residual variance.
2. Test for remaining ARCH behavior and inspect squared/absolute residual dependence.
3. Enforce positivity constraints and state the innovation distribution.
4. For covariance stationarity in standard GARCH(1,1), check `alpha + beta < 1`; values near one imply very persistent volatility and make unconditional-variance interpretation fragile.
5. Under non-Gaussian innovations, Gaussian QMLE can estimate variance dynamics under conditions, but use robust QML covariance estimates. Student-t or skewed distributions may improve tails without solving mean misspecification.
6. Check standardized residuals and squared standardized residuals, and evaluate out-of-sample volatility forecasts when forecasting is the goal.

EGARCH/GJR-GARCH address asymmetry; GARCH-in-mean links modeled risk to the conditional mean; multivariate GARCH requires enough data for covariance parameters. Report persistence and half-life only when the fitted model is stationary and stable.

GARCH models conditional variance, not a causal mechanism and not necessarily the conditional mean.

## Markov-Switching Models

```text
y_t = mu_{s_t} + phi_{s_t}y_{t-1} + sigma_{s_t}epsilon_t
s_t in {1,...,M}
Pr(s_t=j | s_{t-1}=i) = p_ij
```

Define which parameters switch and estimate the filtered likelihood with multiple starting values. Report transition probabilities, expected durations, filtered versus smoothed state probabilities, and classification uncertainty.

The usual likelihood-ratio chi-square reference distribution is generally invalid for testing an additional regime because parameters are unidentified under the smaller model and transition probabilities can lie on boundaries. Use a method-specific bootstrap or other valid nonstandard procedure. Check label normalization, near-empty regimes, local maxima, and sensitivity to the number of states.

Latent regimes are model-implied states. Label them by estimated behavior rather than retrofitting desired historical narratives.

## Semiparametric And Flexible Prediction

Partially linear representation:

```text
y_t = theta d_t + g(x_t) + epsilon_t
```

Flexible nuisance models—splines, forests, boosting, or localized neural networks—can estimate nonlinear prediction surfaces. Use rolling/blocked validation rather than random folds when random splitting would leak future information. Compare against simple baselines and report tuning, sample period, forecast origin, and genuine out-of-sample loss.

If `theta` is a low-dimensional target, use orthogonal residualization and time/dependence-aware sample splitting where theory supports it. Double/debiased machine learning does not create identification: causal interpretation still needs an exogenous treatment/shock and valid nuisance, overlap, and dependence assumptions.

Localized neural approximations can partition the covariate domain and fit local components, but report support and stability; high-dimensional flexibility can amplify sparse-region behavior.

## Method-Matched Robustness

- Threshold/break: candidate range, trimming/minimum segment, regime sizes, sup/bootstrap inference, threshold/break-date confidence sets, and alternative threshold variables.
- Kernel: bandwidth, local polynomial order, boundary behavior, dependence-robust bands, and effective local sample.
- Time-varying coefficients: lag/bandwidth, local stability, constancy tests, simultaneous bands, and constant/break alternatives.
- Bootstrap: resampling scheme, null reconstruction, dependence tuning, repetitions, and re-estimation of selected tuning parameters.
- ARCH/GARCH: mean specification, positivity/stationarity, innovation distribution, robust QML inference, residual ARCH, and forecast loss.
- Markov switching: starting values, state count, label normalization, regime support, transition stability, and nonstandard state-count tests.
- Flexible prediction: blocked validation, leakage checks, tuning, simple benchmarks, and sensitivity across subperiods.

## Claim Boundaries

- An estimated threshold or break needs nonstandard inference because it is unidentified under the no-change null.
- Smooth nonlinear and time-varying paths are bandwidth- and support-dependent associations unless separately identified.
- ARCH/GARCH estimates conditional variance dynamics, not structural causes of risk.
- Markov regimes are latent statistical classifications, not observed institutional states.
- Flexible prediction and double machine learning do not replace a causal identification strategy.

## See Also

- [Time-Series Methods](time-series-methods.md)
- [Method Selection](method-selection.md)
- [Dynamic And Nonlinear Panel Methods](panel-dynamic-nonlinear-methods.md)
- [IV And Causal Methods](iv-causal-methods.md)
