"""Dependency-light Python estimators for the common execution contract.

This module deliberately implements a small, auditable estimator set with
numpy/pandas instead of silently falling back when a requested design is more
advanced than the local runtime supports.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .common import AnalysisExecutionError, AnalysisSpecError


def _normal_p_value(statistic: float) -> float:
    if not math.isfinite(statistic):
        return 0.0 if math.isinf(statistic) else math.nan
    return math.erfc(abs(statistic) / math.sqrt(2.0))


def _coefficient_frame(
    terms: Sequence[str], beta: np.ndarray, covariance: np.ndarray
) -> pd.DataFrame:
    variances = np.diag(covariance)
    variances = np.where((variances < 0) & (variances > -1e-12), 0.0, variances)
    if np.any(variances < 0):
        raise AnalysisExecutionError("Estimated covariance has negative diagonal entries")
    std_error = np.sqrt(variances)
    statistic = np.divide(
        beta,
        std_error,
        out=np.full(beta.shape, np.nan, dtype=float),
        where=std_error > 0,
    )
    p_value = np.array([_normal_p_value(float(value)) for value in statistic])
    return pd.DataFrame(
        {
            "term": list(terms),
            "estimate": beta,
            "std_error": std_error,
            "statistic": statistic,
            "p_value": p_value,
            "ci_lower": beta - 1.96 * std_error,
            "ci_upper": beta + 1.96 * std_error,
        }
    )


def _fit_linear(
    y: np.ndarray,
    x: np.ndarray,
    terms: Sequence[str],
    covariance_type: str,
    clusters: Optional[np.ndarray] = None,
    weights: Optional[np.ndarray] = None,
    absorbed_degrees_of_freedom: int = 0,
) -> Tuple[pd.DataFrame, Dict[str, Any], np.ndarray]:
    y = np.asarray(y, dtype=float).reshape(-1)
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or len(y) != x.shape[0] or x.shape[1] != len(terms):
        raise AnalysisExecutionError("Internal design-matrix shape mismatch")
    nobs, nparams = x.shape
    if nobs <= nparams:
        raise AnalysisSpecError(
            f"Insufficient observations: n={nobs}, estimated parameters={nparams}"
        )
    if weights is None:
        root_w = np.ones(nobs)
    else:
        weights = np.asarray(weights, dtype=float).reshape(-1)
        if len(weights) != nobs or np.any(~np.isfinite(weights)) or np.any(weights <= 0):
            raise AnalysisSpecError("Weights must be finite, positive, and match the sample")
        root_w = np.sqrt(weights)
    xw = x * root_w[:, None]
    yw = y * root_w
    beta, _, rank, singular_values = np.linalg.lstsq(xw, yw, rcond=None)
    if rank < nparams:
        aliased = nparams - int(rank)
        raise AnalysisSpecError(
            f"Design matrix is rank deficient ({aliased} aliased parameter(s)); "
            "remove collinear terms or revise fixed effects"
        )
    # numpy 2.0 linked against some Accelerate builds emits spurious floating-
    # point matmul warnings for finite vectors. Suppress the ufunc warning and
    # enforce the real safety condition explicitly immediately afterwards.
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        fitted = x @ beta
    if not np.all(np.isfinite(fitted)):
        raise AnalysisExecutionError("Linear fit produced non-finite fitted values")
    residual = y - fitted
    weighted_residual = residual * root_w
    residual_ss = float(np.sum(np.square(weighted_residual), dtype=np.float64))
    if not math.isfinite(residual_ss):
        raise AnalysisExecutionError("Linear fit produced a non-finite residual sum of squares")
    bread = np.linalg.pinv(xw.T @ xw)
    dof_resid = nobs - nparams - int(absorbed_degrees_of_freedom)
    if dof_resid <= 0:
        raise AnalysisSpecError(
            "Non-positive residual degrees of freedom after accounting for absorbed fixed effects"
        )
    if covariance_type == "homoskedastic":
        sigma2 = residual_ss / dof_resid
        vcov = bread * sigma2
        clusters_count = None
    elif covariance_type == "hc1":
        score = xw * weighted_residual[:, None]
        meat = score.T @ score
        vcov = bread @ meat @ bread * (nobs / dof_resid)
        clusters_count = None
    elif covariance_type == "cluster":
        if clusters is None:
            raise AnalysisSpecError("Cluster covariance requires a cluster variable")
        clusters = np.asarray(clusters)
        if len(clusters) != nobs:
            raise AnalysisExecutionError("Cluster vector does not match estimation sample")
        labels, inverse = np.unique(clusters.astype(str), return_inverse=True)
        clusters_count = len(labels)
        if clusters_count < 2:
            raise AnalysisSpecError("Cluster covariance requires at least two clusters")
        meat = np.zeros((nparams, nparams), dtype=float)
        for group in range(clusters_count):
            mask = inverse == group
            score_g = xw[mask].T @ weighted_residual[mask]
            meat += np.outer(score_g, score_g)
        correction = (clusters_count / (clusters_count - 1)) * (
            (nobs - 1) / dof_resid
        )
        vcov = bread @ meat @ bread * correction
    else:
        raise AnalysisSpecError(f"Unsupported covariance type: {covariance_type}")

    centered = y - np.average(y, weights=root_w**2)
    total_ss = float(np.sum((root_w * centered) ** 2))
    r_squared = 1.0 - residual_ss / total_ss if total_ss > 0 else math.nan
    diagnostics: Dict[str, Any] = {
        "nobs": int(nobs),
        "n_parameters": int(nparams),
        "rank": int(rank),
        "degrees_of_freedom_residual": int(dof_resid),
        "absorbed_degrees_of_freedom": int(absorbed_degrees_of_freedom),
        "r_squared": float(r_squared),
        "residual_sum_squares": residual_ss,
        "condition_number": float(
            singular_values.max() / singular_values.min()
            if singular_values.size and singular_values.min() > 0
            else math.inf
        ),
        "covariance": covariance_type,
        "p_value_reference": "standard normal approximation",
    }
    if clusters_count is not None:
        diagnostics["clusters"] = int(clusters_count)
    return _coefficient_frame(terms, beta, vcov), diagnostics, residual


def _matrix(frame: pd.DataFrame, columns: Sequence[str]) -> np.ndarray:
    if not columns:
        return np.empty((len(frame), 0), dtype=float)
    return frame.loc[:, list(columns)].to_numpy(dtype=float)


def _add_intercept(
    x: np.ndarray, terms: List[str], enabled: bool
) -> Tuple[np.ndarray, List[str]]:
    if not enabled:
        return x, terms
    return np.column_stack([np.ones(x.shape[0]), x]), ["intercept"] + terms


def _absorb(
    values: np.ndarray,
    frame: pd.DataFrame,
    fixed_effects: Sequence[str],
    tolerance: float = 1e-10,
    max_iterations: int = 1000,
) -> Tuple[np.ndarray, int, float]:
    """Absorb one or more categorical fixed effects by alternating projections."""

    transformed = np.asarray(values, dtype=float).copy()
    if transformed.ndim == 1:
        transformed = transformed[:, None]
    if not fixed_effects:
        return transformed, 0, 0.0
    group_structures = []
    for fixed_effect in fixed_effects:
        group_codes, _ = pd.factorize(frame[fixed_effect], sort=False)
        if np.any(group_codes < 0):
            raise AnalysisExecutionError("Fixed-effect group contains missing values")
        group_structures.append(
            (group_codes, np.bincount(group_codes).astype(float))
        )
    max_change = math.inf
    for iteration in range(1, max_iterations + 1):
        previous = transformed.copy()
        for group_codes, counts in group_structures:
            for column in range(transformed.shape[1]):
                totals = np.bincount(group_codes, weights=transformed[:, column])
                transformed[:, column] -= totals[group_codes] / counts[group_codes]
        max_change = float(np.max(np.abs(transformed - previous)))
        if max_change <= tolerance:
            return transformed, iteration, max_change
    raise AnalysisExecutionError(
        f"Fixed-effect absorption did not converge after {max_iterations} iterations "
        f"(max change={max_change:.3g})"
    )


def _absorbed_degrees_of_freedom(
    frame: pd.DataFrame, fixed_effects: Sequence[str]
) -> Tuple[int, bool]:
    """Return absorbed design rank and whether it is exact.

    One-way rank is the number of observed levels. For two-way effects, a
    union-find over the bipartite incidence graph accounts for disconnected
    components exactly. Higher-way rank uses the standard connected-design
    approximation and is flagged in diagnostics.
    """

    if not fixed_effects:
        return 0, True
    levels = [int(frame[name].nunique(dropna=False)) for name in fixed_effects]
    if len(fixed_effects) == 1:
        return levels[0], True
    if len(fixed_effects) == 2:
        left_codes, _ = pd.factorize(frame[fixed_effects[0]], sort=False)
        right_codes, _ = pd.factorize(frame[fixed_effects[1]], sort=False)
        right_offset = levels[0]
        parent = list(range(levels[0] + levels[1]))

        def find(item: int) -> int:
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(first: int, second: int) -> None:
            root_first, root_second = find(first), find(second)
            if root_first != root_second:
                parent[root_second] = root_first

        for left, right in zip(left_codes, right_codes):
            union(int(left), right_offset + int(right))
        components = len({find(item) for item in range(len(parent))})
        return levels[0] + levels[1] - components, True
    return sum(levels) - len(levels) + 1, False


def _covariance_inputs(
    frame: pd.DataFrame, model: Mapping[str, Any]
) -> Tuple[str, Optional[np.ndarray], Optional[np.ndarray]]:
    covariance = model["covariance"]
    clusters = (
        frame[covariance["cluster"]].to_numpy()
        if covariance["type"] == "cluster"
        else None
    )
    weights = (
        frame[model["weights"]].to_numpy(dtype=float) if model.get("weights") else None
    )
    return covariance["type"], clusters, weights


def _run_ols(frame: pd.DataFrame, model: Mapping[str, Any]) -> Dict[str, Any]:
    terms = list(model["regressors"] + model["controls"])
    x, terms = _add_intercept(
        _matrix(frame, terms), terms, bool(model["add_intercept"])
    )
    covariance, clusters, weights = _covariance_inputs(frame, model)
    coefficients, diagnostics, _ = _fit_linear(
        frame[model["outcome"]].to_numpy(dtype=float),
        x,
        terms,
        covariance,
        clusters,
        weights,
    )
    diagnostics["estimator"] = "ordinary least squares"
    return {"coefficients": coefficients, "diagnostics": diagnostics, "warnings": []}


def _run_fe(
    frame: pd.DataFrame,
    model: Mapping[str, Any],
    fixed_effects: Optional[Sequence[str]] = None,
    substantive_terms: Optional[Sequence[str]] = None,
    estimator_label: str = "fixed effects (within)",
) -> Dict[str, Any]:
    fes = list(fixed_effects or model["fixed_effects"])
    terms = list(substantive_terms or (model["regressors"] + model["controls"]))
    stacked = np.column_stack(
        [frame[model["outcome"]].to_numpy(dtype=float), _matrix(frame, terms)]
    )
    transformed, iterations, max_change = _absorb(stacked, frame, fes)
    y = transformed[:, 0]
    x = transformed[:, 1:]
    covariance, clusters, weights = _covariance_inputs(frame, model)
    absorbed_df, absorbed_df_exact = _absorbed_degrees_of_freedom(frame, fes)
    coefficients, diagnostics, _ = _fit_linear(
        y,
        x,
        terms,
        covariance,
        clusters,
        weights,
        absorbed_degrees_of_freedom=absorbed_df,
    )
    diagnostics.update(
        {
            "estimator": estimator_label,
            "fixed_effects": fes,
            "fixed_effect_levels": {
                name: int(frame[name].nunique(dropna=False)) for name in fes
            },
            "absorption_iterations": int(iterations),
            "absorption_max_change": float(max_change),
            "absorbed_df_exact": absorbed_df_exact,
            "r_squared_definition": "within/transformed sample",
        }
    )
    warnings = []
    if not absorbed_df_exact:
        warnings.append(
            "Residual degrees of freedom for more than two fixed effects use a connected-design rank approximation."
        )
    return {"coefficients": coefficients, "diagnostics": diagnostics, "warnings": warnings}


def _audit_did_panel_keys(frame: pd.DataFrame, did: Mapping[str, Any]) -> None:
    unit, time = did["unit"], did["time"]
    if frame.duplicated([unit, time]).any():
        raise AnalysisSpecError("DID requires unique unit-time observations")


def audit_classic_did_data(
    frame: pd.DataFrame, did: Mapping[str, Any]
) -> Dict[str, Any]:
    unit, time, treatment = did["unit"], did["time"], did["treatment"]
    _audit_did_panel_keys(frame, did)
    values = set(frame[treatment].dropna().astype(float).unique().tolist())
    if not values.issubset({0.0, 1.0}) or len(values) < 2:
        raise AnalysisSpecError("Classic DID treatment must be a varying binary 0/1 variable")
    ordered = frame.sort_values([unit, time])
    reversals = ordered.groupby(unit, sort=False)[treatment].diff().lt(0).any()
    if bool(reversals):
        raise AnalysisSpecError("Classic DID treatment reverses from 1 to 0 within a unit")
    treated = ordered.loc[ordered[treatment] == 1, [unit, time]]
    first_treated = treated.groupby(unit, sort=False)[time].min()
    adoption_times = list(pd.unique(first_treated))
    if len(adoption_times) > 1:
        raise AnalysisSpecError(
            "Observed adoption is staggered although model.did.design=classic. "
            "The bundled runner refuses an ordinary TWFE substitution; use a dedicated "
            "heterogeneous-adoption estimator outside this execution contract."
        )
    ever_treated = set(first_treated.index.tolist())
    all_units = set(frame[unit].unique().tolist())
    if not ever_treated or ever_treated == all_units:
        raise AnalysisSpecError(
            "Classic DID requires treated units and a never-treated comparison group"
        )
    adoption_time = adoption_times[0]
    treated_panel = ordered.loc[ordered[unit].isin(ever_treated)]
    pre_units = set(
        treated_panel.loc[
            (treated_panel[treatment] == 0)
            & (treated_panel[time] < adoption_time),
            unit,
        ].unique().tolist()
    )
    post_units = set(
        treated_panel.loc[
            (treated_panel[treatment] == 1)
            & (treated_panel[time] >= adoption_time),
            unit,
        ].unique().tolist()
    )
    if pre_units != ever_treated or post_units != ever_treated:
        raise AnalysisSpecError(
            "Classic DID requires every treated unit to have observed pre-adoption untreated rows and post-adoption treated rows; a time-invariant group indicator is not a treatment variable"
        )
    return {
        "treated_units": len(ever_treated),
        "control_units": len(all_units - ever_treated),
        "common_adoption_time": str(adoption_times[0]),
        "treated_units_with_pre_support": len(pre_units),
        "treated_units_with_post_support": len(post_units),
    }


def _run_did(frame: pd.DataFrame, model: Mapping[str, Any]) -> Dict[str, Any]:
    did = model["did"]
    if did["design"] != "classic" or did["method"] != "twfe":
        raise AnalysisSpecError(
            "The Python execution contract supports classic/common-adoption DID only"
        )
    design_diagnostics = audit_classic_did_data(frame, did)
    terms = [did["treatment"]] + list(model["regressors"] + model["controls"])
    if len(terms) != len(set(terms)):
        raise AnalysisSpecError("DID treatment must not also appear in regressors or controls")
    result = _run_fe(
        frame,
        model,
        fixed_effects=[did["unit"], did["time"]],
        substantive_terms=terms,
        estimator_label="classic DID via unit and time fixed effects",
    )
    result["diagnostics"]["did_design"] = "classic/common adoption"
    result["diagnostics"].update(design_diagnostics)
    result["warnings"].append(
        "Parallel trends is an identifying assumption and is not established by this regression."
    )
    return result


def _run_iv(frame: pd.DataFrame, model: Mapping[str, Any]) -> Dict[str, Any]:
    exogenous_terms = list(model["regressors"] + model["controls"])
    endogenous_terms = list(model["endogenous"])
    instrument_terms = list(model["instruments"])
    x_terms = exogenous_terms + endogenous_terms
    z_terms = exogenous_terms + instrument_terms
    y = frame[model["outcome"]].to_numpy(dtype=float)[:, None]
    x = _matrix(frame, x_terms)
    z = _matrix(frame, z_terms)
    fixed_effects = list(model["fixed_effects"])
    absorption_iterations = 0
    absorption_max_change = 0.0
    absorbed_df, absorbed_df_exact = _absorbed_degrees_of_freedom(
        frame, fixed_effects
    )
    if fixed_effects:
        stacked = np.column_stack([y, x, z])
        transformed, absorption_iterations, absorption_max_change = _absorb(
            stacked, frame, fixed_effects
        )
        y = transformed[:, :1]
        x = transformed[:, 1 : 1 + len(x_terms)]
        z = transformed[:, 1 + len(x_terms) :]
    else:
        x, x_terms = _add_intercept(x, x_terms, bool(model["add_intercept"]))
        z, z_terms = _add_intercept(z, z_terms, bool(model["add_intercept"]))

    nobs, nparams = x.shape
    if nobs <= nparams:
        raise AnalysisSpecError("Insufficient observations for IV/2SLS")
    rank_x = int(np.linalg.matrix_rank(x))
    rank_z = int(np.linalg.matrix_rank(z))
    if rank_x < x.shape[1]:
        raise AnalysisSpecError("IV structural design matrix is rank deficient")
    if rank_z < z.shape[1]:
        raise AnalysisSpecError("IV instrument matrix is rank deficient")
    if rank_z < x.shape[1]:
        raise AnalysisSpecError("IV/2SLS model is underidentified after transformations")

    ztz_inv = np.linalg.pinv(z.T @ z)
    xz = x.T @ z
    a = xz @ ztz_inv @ xz.T
    if np.linalg.matrix_rank(a) < x.shape[1]:
        raise AnalysisSpecError(
            "IV/2SLS projected design is rank deficient; instruments do not identify all coefficients"
        )
    a_inv = np.linalg.pinv(a)
    beta = a_inv @ xz @ ztz_inv @ z.T @ y
    beta = beta.reshape(-1)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        fitted = x @ beta
    if not np.all(np.isfinite(fitted)):
        raise AnalysisExecutionError("IV/2SLS produced non-finite fitted values")
    residual = y.reshape(-1) - fitted
    residual_ss = float(np.sum(np.square(residual), dtype=np.float64))
    if not math.isfinite(residual_ss):
        raise AnalysisExecutionError("IV/2SLS produced a non-finite residual sum of squares")
    covariance_spec = model["covariance"]
    covariance_type = covariance_spec["type"]
    dof_resid = nobs - nparams - absorbed_df
    if dof_resid <= 0:
        raise AnalysisSpecError(
            "Non-positive IV residual degrees of freedom after absorbed fixed effects"
        )
    if covariance_type == "homoskedastic":
        sigma2 = residual_ss / dof_resid
        vcov = a_inv * sigma2
        cluster_count = None
    else:
        if covariance_type == "hc1":
            score = z * residual[:, None]
            meat = score.T @ score * (nobs / dof_resid)
            cluster_count = None
        elif covariance_type == "cluster":
            cluster_values = frame[covariance_spec["cluster"]].astype(str).to_numpy()
            labels, inverse = np.unique(cluster_values, return_inverse=True)
            cluster_count = len(labels)
            if cluster_count < 2:
                raise AnalysisSpecError("Cluster covariance requires at least two clusters")
            meat = np.zeros((z.shape[1], z.shape[1]))
            for group in range(cluster_count):
                mask = inverse == group
                score_g = z[mask].T @ residual[mask]
                meat += np.outer(score_g, score_g)
            meat *= (cluster_count / (cluster_count - 1)) * (
                (nobs - 1) / dof_resid
            )
        else:
            raise AnalysisSpecError(f"Unsupported IV covariance: {covariance_type}")
        d = xz @ ztz_inv
        vcov = a_inv @ d @ meat @ d.T @ a_inv

    first_stages: List[Dict[str, Any]] = []
    exog_count = len(exogenous_terms) + (0 if fixed_effects or not model["add_intercept"] else 1)
    restricted = x[:, :exog_count] if exog_count else np.empty((nobs, 0))
    excluded_count = len(instrument_terms)
    for index, term in enumerate(endogenous_terms):
        target = x[:, len(x_terms) - len(endogenous_terms) + index]
        unrestricted_beta = np.linalg.lstsq(z, target, rcond=None)[0]
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            unrestricted_fitted = z @ unrestricted_beta
        if not np.all(np.isfinite(unrestricted_fitted)):
            raise AnalysisExecutionError("IV first stage produced non-finite fitted values")
        rss_unrestricted = float(np.sum((target - unrestricted_fitted) ** 2))
        if restricted.shape[1]:
            restricted_beta = np.linalg.lstsq(restricted, target, rcond=None)[0]
            with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                restricted_fitted = restricted @ restricted_beta
            if not np.all(np.isfinite(restricted_fitted)):
                raise AnalysisExecutionError(
                    "Restricted IV first stage produced non-finite fitted values"
                )
            rss_restricted = float(np.sum((target - restricted_fitted) ** 2))
        else:
            rss_restricted = float(np.sum(np.square(target), dtype=np.float64))
        denominator_df = nobs - z.shape[1] - absorbed_df
        f_statistic = (
            ((rss_restricted - rss_unrestricted) / excluded_count)
            / (rss_unrestricted / denominator_df)
            if rss_unrestricted > 0 and denominator_df > 0
            else math.inf
        )
        first_stages.append(
            {
                "endogenous": term,
                "excluded_instruments": instrument_terms,
                "partial_f_statistic": float(max(0.0, f_statistic)),
                "numerator_df": int(excluded_count),
                "denominator_df": int(denominator_df),
                "note": "Conventional first-stage partial F; not a weak-IV-robust test.",
            }
        )

    warnings = [
        "Instrument validity (exclusion and independence) is an identifying assumption, not a regression diagnostic."
    ]
    if any(stage["partial_f_statistic"] < 10 for stage in first_stages):
        warnings.append(
            "At least one conventional first-stage partial F is below 10; use weak-IV-robust inference."
        )
    if not absorbed_df_exact:
        warnings.append(
            "Residual degrees of freedom for more than two fixed effects use a connected-design rank approximation."
        )
    diagnostics: Dict[str, Any] = {
        "estimator": "two-stage least squares",
        "nobs": int(nobs),
        "n_parameters": int(nparams),
        "rank_structural": rank_x,
        "rank_instruments": rank_z,
        "degrees_of_freedom_residual": int(dof_resid),
        "absorbed_degrees_of_freedom": int(absorbed_df),
        "absorbed_df_exact": absorbed_df_exact,
        "covariance": covariance_type,
        "first_stages": first_stages,
        "fixed_effects": fixed_effects,
        "absorption_iterations": int(absorption_iterations),
        "absorption_max_change": float(absorption_max_change),
        "p_value_reference": "standard normal approximation",
    }
    if cluster_count is not None:
        diagnostics["clusters"] = int(cluster_count)
    return {
        "coefficients": _coefficient_frame(x_terms, beta, vcov),
        "diagnostics": diagnostics,
        "warnings": warnings,
    }


def _run_rdd(frame: pd.DataFrame, model: Mapping[str, Any]) -> Dict[str, Any]:
    rdd = model["rdd"]
    running = frame[rdd["running"]].to_numpy(dtype=float) - float(rdd["cutoff"])
    bandwidth = float(rdd["bandwidth"])
    mask = np.abs(running) <= bandwidth
    local = frame.loc[mask].copy()
    running = running[mask]
    right = (running >= 0).astype(float)
    if len(local) == 0:
        raise AnalysisSpecError("RDD bandwidth selects no observations")
    left_count = int(np.sum(right == 0))
    right_count = int(np.sum(right == 1))
    if min(left_count, right_count) < 5:
        raise AnalysisSpecError(
            "RDD requires at least five complete observations on each side within the bandwidth"
        )

    columns = [right]
    terms = ["rdd_jump"]
    for power in range(1, int(rdd["polynomial_order"]) + 1):
        base = running**power
        columns.extend([base, right * base])
        terms.extend([f"rdd_running_{power}", f"rdd_right_running_{power}"])
    controls = list(model["regressors"] + model["controls"])
    if controls:
        columns.extend(
            [local[column].to_numpy(dtype=float) for column in controls]
        )
        terms.extend(controls)
    x = np.column_stack(columns)
    x, terms = _add_intercept(x, terms, True)
    if rdd["kernel"] == "triangular":
        weights = np.maximum(1e-12, 1.0 - np.abs(running) / bandwidth)
    else:
        weights = np.ones(len(local))
    covariance = model["covariance"]
    clusters = (
        local[covariance["cluster"]].to_numpy()
        if covariance["type"] == "cluster"
        else None
    )
    coefficients, diagnostics, _ = _fit_linear(
        local[model["outcome"]].to_numpy(dtype=float),
        x,
        terms,
        covariance["type"],
        clusters,
        weights,
    )
    diagnostics.update(
        {
            "estimator": "local polynomial sharp RDD",
            "cutoff": float(rdd["cutoff"]),
            "bandwidth": bandwidth,
            "kernel": rdd["kernel"],
            "polynomial_order": int(rdd["polynomial_order"]),
            "observations_left": left_count,
            "observations_right": right_count,
        }
    )
    return {
        "coefficients": coefficients,
        "diagnostics": diagnostics,
        "warnings": [
            "Bandwidth is user-supplied; density, sorting, and placebo diagnostics are not automated."
        ],
    }


def _run_ar(frame: pd.DataFrame, model: Mapping[str, Any]) -> Dict[str, Any]:
    time_series = model["time_series"]
    time_name = time_series["time"]
    lag_order = int(time_series["lags"])
    ordered = frame.sort_values(time_name).reset_index(drop=True)
    time_values = ordered[time_name].to_numpy(dtype=float)
    if len(np.unique(time_values)) != len(time_values):
        raise AnalysisSpecError("AR time variable must uniquely identify each observation")
    differences = np.diff(time_values)
    if len(differences) and (
        np.any(differences <= 0) or not np.allclose(differences, differences[0])
    ):
        raise AnalysisSpecError(
            "AR time variable must be strictly increasing and regularly spaced; fill or model gaps explicitly"
        )
    if len(ordered) <= lag_order + 2:
        raise AnalysisSpecError("AR model has too few observations after constructing lags")

    outcome = model["outcome"]
    outcome_values = ordered[outcome].to_numpy(dtype=float)
    terms = [f"{outcome}_lag_{lag}" for lag in range(1, lag_order + 1)]
    columns = [
        outcome_values[lag_order - lag : len(outcome_values) - lag]
        for lag in range(1, lag_order + 1)
    ]
    substantive = list(model["regressors"] + model["controls"])
    columns.extend(
        ordered[name].to_numpy(dtype=float)[lag_order:] for name in substantive
    )
    terms.extend(substantive)
    if time_series["include_trend"]:
        columns.append(np.arange(lag_order, len(ordered), dtype=float))
        terms.append("linear_trend")
    x = np.column_stack(columns)
    x, terms = _add_intercept(x, terms, bool(model["add_intercept"]))
    coefficients, diagnostics, _ = _fit_linear(
        outcome_values[lag_order:],
        x,
        terms,
        model["covariance"]["type"],
    )

    indexed = coefficients.set_index("term")
    phi = np.array(
        [indexed.loc[f"{outcome}_lag_{lag}", "estimate"] for lag in range(1, lag_order + 1)],
        dtype=float,
    )
    companion = np.zeros((lag_order, lag_order), dtype=float)
    companion[0, :] = phi
    if lag_order > 1:
        companion[1:, :-1] = np.eye(lag_order - 1)
    roots = np.linalg.eigvals(companion)
    maximum_root = float(np.max(np.abs(roots)))
    stable = bool(maximum_root < 1.0)
    diagnostics.update(
        {
            "estimator": f"conditional AR({lag_order}) via OLS",
            "time_variable": time_name,
            "lag_order": lag_order,
            "observations_lost_to_lags": lag_order,
            "companion_eigenvalues": [
                {"real": float(value.real), "imag": float(value.imag), "modulus": float(abs(value))}
                for value in roots
            ],
            "maximum_companion_root_modulus": maximum_root,
            "stable_ar": stable,
        }
    )
    warnings = []
    if not stable:
        warnings.append(
            "The fitted AR companion matrix is not stable (maximum root modulus is at least one)."
        )
    return {"coefficients": coefficients, "diagnostics": diagnostics, "warnings": warnings}


def execute_python(frame: pd.DataFrame, spec: Mapping[str, Any]) -> Dict[str, Any]:
    """Execute a normalized spec and return coefficients/diagnostics/warnings."""

    model = spec["model"]
    model_type = model["type"]
    if model_type == "ols":
        result = _run_ols(frame, model)
    elif model_type in ("fe", "twfe"):
        result = _run_fe(frame, model)
        result["diagnostics"]["estimator"] = (
            "two-or-more-way fixed effects (within)"
            if model_type == "twfe"
            else "fixed effects (within)"
        )
    elif model_type == "did":
        result = _run_did(frame, model)
    elif model_type == "iv_2sls":
        result = _run_iv(frame, model)
    elif model_type == "rdd":
        result = _run_rdd(frame, model)
    elif model_type == "ar":
        result = _run_ar(frame, model)
    else:
        raise AnalysisSpecError(f"Python backend does not support model type: {model_type}")

    cluster_count = result["diagnostics"].get("clusters")
    if cluster_count is not None and cluster_count < 30:
        result["warnings"].append(
            f"Only {cluster_count} clusters are available. The reported standard-normal "
            "p-values can over-reject with few clusters; use a design-appropriate "
            "small-sample correction, wild-cluster bootstrap, or randomization inference."
        )
        result["diagnostics"]["few_cluster_inference"] = True
    else:
        result["diagnostics"]["few_cluster_inference"] = False
    return result
