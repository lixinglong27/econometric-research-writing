# Econometric Inference Guide

Use this reference after choosing the estimand and estimator. Do not select a covariance estimator only because it gives smaller standard errors. Match inference to the assignment mechanism, dependence structure, panel dimensions, and identification design.

## Table Of Contents

- Required Intake
- Cross-Section And Panel Dependence
- Time-Series Dependence
- Instrumental Variables And Weak Identification
- Dynamic Panel GMM
- Design-Based Inference
- Multiple Testing And Selective Reporting
- Output Contract

## Required Intake

Record before estimation:

- Unit of independent assignment or treatment.
- Sampling clusters and repeated-observation unit.
- Number and size distribution of clusters.
- Plausible serial and cross-sectional dependence.
- Whether regressors, instruments, or treatment vary at a coarser level than observations.
- Whether inference is model-based, design-based, or both.

Never cluster below the level at which the identifying variation or treatment is assigned. Fixed effects and clustered standard errors solve different problems.

## Cross-Section And Panel Dependence

- Use heteroskedasticity-robust covariance for independent cross-sectional observations when unequal variance is plausible.
- Cluster by unit for repeated observations with arbitrary within-unit dependence.
- Use two-way or multiway clustering when dependence is plausible along more than one non-nested dimension, such as firm and calendar time.
- With few clusters, report the cluster count and use an appropriate small-sample correction, wild-cluster bootstrap, randomization inference, or another design-matched procedure. Do not rely on asymptotic clustered standard errors without qualification.
- Unit clustering alone does not address common shocks across units. Consider time fixed effects, time clustering, two-way clustering, Driscoll-Kraay-type inference, common-factor methods, or spatial/network dependence methods as justified by the data structure.
- For spatial dependence, justify the distance or network structure and report sensitivity to plausible alternatives.

Report the clustering dimensions, cluster counts, finite-sample correction, and why they match the design.

## Time-Series Dependence

- Use HAC/Newey-West-type covariance only with a justified lag or bandwidth rule; report it.
- Check whether residual serial correlation reflects misspecified dynamics rather than treating HAC as a substitute for lag selection.
- For long-memory, structural breaks, or nonstationarity, use method-specific inference rather than ordinary HAC alone.
- For VAR, local projections, and impulse responses, report horizon-specific uncertainty and the bootstrap or asymptotic procedure used.

## Instrumental Variables And Weak Identification

Separate four questions:

1. Relevance: excluded instruments predict the endogenous regressor conditional on included exogenous variables.
2. Identification strength: the available first-stage variation is strong enough for conventional IV approximations.
3. Exogeneity/exclusion: instruments are independent of the structural error and affect the outcome only through the endogenous regressor.
4. Estimand: LATE or another instrument-specific effect when treatment effects are heterogeneous.

Required reporting:

- First-stage coefficients and partial fit for excluded instruments.
- A strength statistic appropriate to the covariance assumptions: conventional partial F under homoskedasticity, heteroskedasticity/cluster-robust Kleibergen-Paap-type statistics, or an effective-F diagnostic when applicable.
- Reduced form and sample definition.
- Instrument and endogenous-regressor counts.
- Exclusion reasoning that does not rely on an overidentification test alone.

When instruments may be weak:

- Prefer weak-identification-robust Anderson-Rubin or conditional likelihood-ratio inference where supported.
- Consider LIML or another weak-instrument-resistant estimator as a sensitivity check.
- Do not use a universal `F > 10` rule without matching it to the design, number of instruments, and target bias or size distortion.
- Treat overidentification tests as joint specification diagnostics, not proof of exclusion.

## Dynamic Panel GMM

For difference or system GMM, report:

- Transformation, endogenous/predetermined/exogenous classification, lag windows, collapsed status, and total instrument count.
- Why level moment conditions used by system GMM are credible.
- AR(1) and AR(2) tests in differenced residuals: first-order correlation is commonly expected after differencing; second-order correlation threatens the usual lag instruments.
- Hansen/Sargan diagnostics with the caveat that many instruments can weaken them.
- Difference-in-Hansen tests for instrument subsets when relevant.
- One-step and two-step estimates as useful, with finite-sample-corrected two-step standard errors such as Windmeijer correction where supported.
- Sensitivity to shorter lag windows, collapsed instruments, alternative transformations, and instrument count relative to the number of units.

Never choose the instrument set by the preferred coefficient alone.

## Design-Based Inference

- DiD/event studies: cluster at the treatment-assignment level; with few treated clusters, consider wild-cluster bootstrap or randomization/permutation procedures justified by the assignment process.
- Staggered DiD: report cohort-time support and inference for the stated group-time ATT aggregation; do not attach ordinary TWFE standard errors to a different estimand.
- RDD: use local-polynomial, bandwidth-matched, robust bias-corrected inference where available; cluster only when the sampling structure requires it.
- Synthetic counterfactuals: distinguish placebo/permutation distributions, prediction uncertainty, and sampling uncertainty.
- Matching/weighting: account for estimated weights or matching when the chosen estimator requires it; report effective sample size and extreme-weight handling.

## Multiple Testing And Selective Reporting

- Define primary outcomes, horizons, subgroups, and specifications before interpreting large result families.
- Report the number of hypotheses and use family-wise error, false-discovery-rate, simultaneous bands, or a prespecified index when multiplicity is material.
- Keep exploratory analyses labeled exploratory.
- Do not select a preferred specification only because it crosses a significance threshold.

## Output Contract

Every primary model result should record:

- Estimand and estimator.
- Coefficient, standard error, confidence interval, and sample size.
- Covariance/inference method and clustering dimensions/counts.
- Fixed effects, weights, sample restrictions, and missing-data rule.
- Method-specific diagnostics and thresholds used for interpretation.
- Runtime, package versions, random seed when relevant, and warnings.
- A bounded interpretation of what the design can and cannot identify.
