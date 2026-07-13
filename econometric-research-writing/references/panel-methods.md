# Panel Methods

Use this core reference for static linear panels, fixed versus random effects, correlated random effects, heterogeneous slopes, unbalanced panels, and dependence-robust inference. Use [Dynamic And Nonlinear Panel Methods](panel-dynamic-nonlinear-methods.md) for dynamic GMM/QMLE, panel unit roots and cointegration, binary/limited outcomes, time-varying coefficients, panel VAR, or spatial panels. Pair either file with `iv-causal-methods.md` for instruments, DiD, treatment effects, or causal claims.

## Table Of Contents

- Panel Data Setup
- Fixed Effects And Random Effects
- Static Fixed-Effect Estimators
- Random Effects, Variance Components, And GLS
- FE Versus RE, Mundlak, And Hausman
- Balanced And Unbalanced Panels
- Dependence And Panel Inference
- Random Coefficients And Heterogeneous Slopes
- Method-Matched Robustness
- Claim Boundaries
- See Also

## Panel Data Setup

Use panel methods when both unit and time variation matter.

Core linear families:

```text
Pooled/common slope:       Y_it = X_it' beta + e_it
Unit fixed effect:         Y_it = X_it' beta + alpha_i + e_it
Two-way fixed effects:     Y_it = X_it' beta + alpha_i + gamma_t + e_it
Heterogeneous slopes:      Y_it = X_it' beta_i + alpha_i + e_it
```

Before choosing an estimator, state:

- Unit `i`, time `t`, sample window, outcome, and balanced/unbalanced status.
- Which variation identifies each coefficient: within unit, between unit, or both.
- Whether regressors are strictly exogenous, predetermined, or endogenous.
- The likely dependence and treatment-assignment level for inference.
- Whether dynamics, nonlinear outcomes, nonstationarity, common factors, or spillovers require the advanced panel reference.

## Fixed Effects And Random Effects

Fixed-effects model:

```text
Y_it = X_it' beta + alpha_i + e_it
```

Random-effects model:

```text
Y_it = alpha + X_it' beta + a_i + u_it
E(a_i | X_i) = 0
E(u_it | X_i, a_i) = 0
```

Decision logic:

- FE allows unit effects to be correlated with time-varying regressors and identifies slopes from within-unit changes.
- RE combines within- and between-unit variation but requires the unit effect to be conditionally uncorrelated with the regressor history.
- Add time effects when common calendar shocks matter. Time effects absorb common shocks with common coefficients; they do not necessarily remove heterogeneous exposure to latent factors.
- Neither FE nor RE resolves simultaneity, reverse causality, time-varying omitted variables, or bad-control bias.

Report the estimator, included effects, identifying variation, and why the maintained exogeneity assumptions fit the setting.

## Static Fixed-Effect Estimators

One-way FE:

```text
Y_it = alpha_i + X_it' beta + u_it
```

The least-squares dummy-variable and within estimators give the same slope under the same specification. The within estimator uses:

```text
beta_hat_FE =
[sum_i sum_t (X_it - X_i_bar)'(X_it - X_i_bar)]^{-1}
 sum_i sum_t (X_it - X_i_bar)'(Y_it - Y_i_bar)
```

Implications:

- FE absorbs all time-invariant unit attributes, observed or unobserved.
- A coefficient on a time-invariant regressor is not identified with unrestricted unit FE.
- Variables with little within-unit variation can be weakly identified even in a large dataset.
- With a lagged outcome and short `T`, the within estimator generally has Nickell bias; route to the advanced dynamic-panel section.

## Random Effects, Variance Components, And GLS

Variance-components setup:

```text
Var(a_i) = sigma_a^2
Var(u_it) = sigma_u^2
```

Feasible RE GLS estimates the variance components and quasi-demeans each unit by subtracting a fraction of its time mean. It is a weighted combination of within and between variation.

Report:

- The assumption `E(a_i | X_i)=0`, not merely an efficiency argument.
- Variance components or the intra-class correlation when informative.
- How unbalanced units are handled.
- A correlated-RE/Mundlak check when correlation with unit effects is plausible.

Do not use a misspecified FGLS covariance model to manufacture small standard errors. Model-based GLS efficiency requires its covariance structure; dependence-robust inference addresses a different question.

## FE Versus RE, Mundlak, And Hausman

Mundlak correlated-random-effects formulation:

```text
alpha_i = X_i_bar' theta + omega_i
Y_it = X_it' beta + X_i_bar' theta + omega_i + u_it
```

Add unit means of time-varying regressors to RE. Jointly nonzero mean terms indicate that plain RE's orthogonality restriction is incompatible with the data. Correlated RE can retain time-invariant regressors while making the modeled source of correlation explicit.

Hausman logic:

```text
H = (beta_FE - beta_RE)'
    [Var(beta_FE) - Var(beta_RE)]^{-1}
    (beta_FE - beta_RE)
```

Use the Hausman comparison only when the two estimators, covariance estimates, and coefficient sets are genuinely comparable. If the covariance difference is indefinite or the test is unstable, do not select a model mechanically: prioritize the design's exogeneity argument and a Mundlak specification.

Report what FE sacrifices—time-invariant coefficients and a direct between-unit interpretation—and what RE assumes in exchange.

## Balanced And Unbalanced Panels

- A balanced panel has the same `T` for every unit; an unbalanced panel uses each available `T_i` in transformations and sums.
- Report units, time periods, observations, and the distribution of `T_i` when imbalance is material.
- Check whether attrition, entry, or missingness is related to treatment or outcomes; standard FE/RE does not repair informative sample selection.
- Describe every restriction used to form a balanced subsample and compare it with the main sample.
- Forward orthogonal deviations can preserve more observations than first differencing in some dynamic unbalanced panels, but the same moment-validity assumptions remain necessary.

## Dependence And Panel Inference

Choose the covariance estimator from the sampling and assignment process, not from whichever option yields significance.

Within-unit dependence:

- Serial correlation and heteroskedasticity within units usually motivate unit-clustered standard errors when the number of independent units is sufficiently large.
- If treatment is assigned at a higher group level, cluster at that assignment level even when observations are individual or unit-period records.
- With few clusters, conventional cluster-robust asymptotics can over-reject. Use an appropriate degrees-of-freedom correction, CR2/CR3-type adjustment, randomization inference, or wild-cluster procedure when its assumptions fit, and report the number and balance of clusters.

Cross-sectional and multiway dependence:

- Shared shocks, supply chains, geography, or networks can correlate errors across units. Inspect residual dependence and reason from the data-generating process rather than relying on one test.
- Two-way clustering by unit and time can cover arbitrary dependence within either dimension, but it needs enough independent clusters in both dimensions; a long list of observations is not a substitute.
- Driscoll–Kraay-type inference can be useful under broad cross-sectional and serial dependence when `T` is sufficiently large; it is not a cure for short panels or omitted common factors.
- If latent common factors correlate with regressors, add a factor structure or common-correlated-effects (CCE) terms. Changing standard errors alone does not repair slope inconsistency.
- Time FE absorb shocks common with homogeneous loadings. Interactive effects or CCE methods are needed when exposure is heterogeneous and substantively important.

Report the clustering dimensions, number of clusters, small-sample adjustment, and why they match assignment and residual dependence.

## Random Coefficients And Heterogeneous Slopes

Use when the distribution of unit-specific responses is a target rather than a nuisance.

```text
Y_it = X_it' beta_i + alpha_i + epsilon_it
```

Options:

- Mean-group estimation: estimate unit slopes and average them; it requires enough within-unit time observations for each slope.
- Random-coefficient/hierarchical models: partially pool unit slopes under an explicit distributional structure.
- CCE mean-group approaches: add cross-sectional averages or estimated factors when common correlated shocks coexist with heterogeneous slopes.

Report the mean, dispersion, quantiles, and supported unit-level estimates; do not show only the most favorable units. Compare with a common-slope model and distinguish true heterogeneity from noisy short-`T` estimates.

## Method-Matched Robustness

- FE/RE: within variation, time effects, correlated-RE terms, and substantive exogeneity reasoning.
- Hausman/Mundlak: comparable coefficient sets, covariance choice, joint tests of unit means, and instability of mechanical Hausman decisions.
- Unbalanced panels: attrition/entry patterns and a transparently defined balanced-sample sensitivity check.
- Inference: assignment-level clustering, alternative credible dependence structures, cluster counts, and few-cluster corrections.
- Cross-sectional dependence: time effects versus heterogeneous common factors, CCE/factor controls, and large-`T` dependence-robust inference.
- Heterogeneous slopes: distribution and precision of unit estimates, shrinkage/mean-group sensitivity, and comparison with pooled slopes.

## Claim Boundaries

- FE controls time-invariant unit heterogeneity, not all endogeneity.
- RE and model-based GLS depend on their orthogonality and covariance assumptions.
- Clustered or dependence-robust standard errors change inference, not identification or the point-estimand target.
- Mundlak and Hausman diagnostics assess compatibility with RE restrictions; they do not create exogeneity.
- Heterogeneous-slope estimates are associations unless a separate identification design supports causal effects.

## See Also

- [Method Selection](method-selection.md)
- [Dynamic And Nonlinear Panel Methods](panel-dynamic-nonlinear-methods.md)
- [IV and Causal Methods](iv-causal-methods.md)
- [RDD and Matching Methods](rdd-matching-methods.md)
