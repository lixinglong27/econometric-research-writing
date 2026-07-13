"""Shared validation, data loading, and artifact helpers.

The runtime intentionally validates the important semantic constraints itself so
that the command line remains usable without the optional ``jsonschema`` package.
The JSON Schema in ``schemas/`` remains the machine-readable interchange contract.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import pandas as pd
import numpy as np


SPEC_VERSION = "1.0"
CONTRACT_VERSION = "1.0"
BACKENDS = ("auto", "python")
MODEL_TYPES = ("ols", "fe", "twfe", "did", "iv_2sls", "rdd", "ar")
COEFFICIENT_COLUMNS = (
    "term",
    "estimate",
    "std_error",
    "statistic",
    "p_value",
    "ci_lower",
    "ci_upper",
)
KNOWN_ARTIFACTS = (
    "analysis.py",
    "coefficients.csv",
    "diagnostics.json",
    "manifest.json",
    "normalized-spec.json",
    "run.log",
)
_VARIABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,31}$")


class AnalysisSpecError(ValueError):
    """Raised when an analysis specification is invalid or unsupported."""


class BackendUnavailableError(RuntimeError):
    """Raised when an optional Python data dependency is unavailable."""


class AnalysisExecutionError(RuntimeError):
    """Raised when a backend starts but does not complete successfully."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def object_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _as_list(value: Any, field: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise AnalysisSpecError(f"{field} must be an array of variable names")
    return list(value)


def _validate_variable(name: Any, field: str) -> str:
    if not isinstance(name, str) or not _VARIABLE_RE.fullmatch(name):
        raise AnalysisSpecError(
            f"{field} must be a portable Python variable name "
            "(letter or underscore, then up to 31 letters, digits, or underscores)"
        )
    return name


def _validate_variable_list(names: Sequence[str], field: str) -> None:
    for index, name in enumerate(names):
        _validate_variable(name, f"{field}[{index}]")
    if len(names) != len(set(names)):
        raise AnalysisSpecError(f"{field} contains duplicate variable names")


def _reject_unknown_keys(value: Mapping[str, Any], allowed: Sequence[str], field: str) -> None:
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise AnalysisSpecError(f"{field} contains unknown field(s): {', '.join(unknown)}")


def validate_and_normalize_spec(
    raw_spec: Mapping[str, Any],
    spec_path: Path,
    output_override: Optional[Path] = None,
) -> Dict[str, Any]:
    """Return a normalized copy with absolute data/output paths.

    Defaults are materialized before hashing so a run can be reproduced from
    ``normalized-spec.json`` without relying on implicit CLI behavior.
    """

    if not isinstance(raw_spec, Mapping):
        raise AnalysisSpecError("The analysis spec root must be a JSON object")
    spec: Dict[str, Any] = copy.deepcopy(dict(raw_spec))
    _reject_unknown_keys(
        spec,
        ("$schema", "spec_version", "analysis_id", "backend", "data", "model", "output"),
        "analysis spec",
    )
    if spec.get("spec_version") != SPEC_VERSION:
        raise AnalysisSpecError(
            f"spec_version must be {SPEC_VERSION!r}; got {spec.get('spec_version')!r}"
        )
    analysis_id = spec.get("analysis_id")
    if not isinstance(analysis_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", analysis_id):
        raise AnalysisSpecError(
            "analysis_id must be 1-80 portable characters and start with a letter or digit"
        )

    backend = spec.setdefault("backend", "auto")
    if backend not in BACKENDS:
        raise AnalysisSpecError(f"backend must be one of {', '.join(BACKENDS)}")

    data = spec.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("path"), str):
        raise AnalysisSpecError("data.path is required")
    _reject_unknown_keys(data, ("path", "format", "encoding", "sheet"), "data")
    data_path = Path(data["path"]).expanduser()
    if not data_path.is_absolute():
        data_path = (spec_path.parent / data_path).resolve()
    data["path"] = str(data_path)
    data_format = data.setdefault("format", infer_data_format(data_path))
    if data_format not in ("csv", "tsv", "xlsx", "parquet", "feather"):
        raise AnalysisSpecError(
            "data.format must be csv, tsv, xlsx, parquet, or feather"
        )
    if "encoding" in data and not isinstance(data["encoding"], str):
        raise AnalysisSpecError("data.encoding must be a string")
    if "sheet" in data:
        sheet = data["sheet"]
        if not isinstance(sheet, (str, int)) or isinstance(sheet, bool) or (
            isinstance(sheet, int) and sheet < 0
        ):
            raise AnalysisSpecError("data.sheet must be a nonnegative integer or sheet name")

    output = spec.setdefault("output", {})
    if not isinstance(output, dict):
        raise AnalysisSpecError("output must be an object")
    _reject_unknown_keys(output, ("directory", "overwrite"), "output")
    output.setdefault("overwrite", False)
    if not isinstance(output["overwrite"], bool):
        raise AnalysisSpecError("output.overwrite must be true or false")
    if output_override is not None:
        output_path = output_override.expanduser()
    else:
        output_value = output.get("directory", f"outputs/{analysis_id}")
        if not isinstance(output_value, str):
            raise AnalysisSpecError("output.directory must be a path string")
        output_path = Path(output_value).expanduser()
    if not output_path.is_absolute():
        output_path = (spec_path.parent / output_path).resolve()
    output["directory"] = str(output_path)

    model = spec.get("model")
    if not isinstance(model, dict):
        raise AnalysisSpecError("model is required and must be an object")
    _reject_unknown_keys(
        model,
        (
            "type", "outcome", "regressors", "controls", "fixed_effects",
            "endogenous", "instruments", "add_intercept", "weights",
            "covariance", "did", "rdd", "time_series",
        ),
        "model",
    )
    model_type = model.get("type")
    if model_type not in MODEL_TYPES:
        raise AnalysisSpecError(f"model.type must be one of {', '.join(MODEL_TYPES)}")
    outcome = _validate_variable(model.get("outcome"), "model.outcome")
    regressors = _as_list(model.setdefault("regressors", []), "model.regressors")
    controls = _as_list(model.setdefault("controls", []), "model.controls")
    fixed_effects = _as_list(
        model.setdefault("fixed_effects", []), "model.fixed_effects"
    )
    for field, values in (
        ("model.regressors", regressors),
        ("model.controls", controls),
        ("model.fixed_effects", fixed_effects),
    ):
        _validate_variable_list(values, field)
    substantive = regressors + controls
    if outcome in substantive:
        raise AnalysisSpecError("model.outcome cannot also be a regressor or control")
    if len(substantive) != len(set(substantive)):
        raise AnalysisSpecError("regressors and controls must not overlap")
    model.setdefault(
        "add_intercept",
        model_type not in ("fe", "twfe", "did")
        and not (model_type == "iv_2sls" and bool(fixed_effects)),
    )
    if not isinstance(model["add_intercept"], bool):
        raise AnalysisSpecError("model.add_intercept must be true or false")

    covariance = model.setdefault("covariance", {"type": "hc1"})
    if not isinstance(covariance, dict):
        raise AnalysisSpecError("model.covariance must be an object")
    _reject_unknown_keys(covariance, ("type", "cluster"), "model.covariance")
    covariance_type = covariance.setdefault("type", "hc1")
    if covariance_type not in ("homoskedastic", "hc1", "cluster"):
        raise AnalysisSpecError(
            "model.covariance.type must be homoskedastic, hc1, or cluster"
        )
    if covariance_type == "cluster":
        _validate_variable(covariance.get("cluster"), "model.covariance.cluster")
    elif "cluster" in covariance:
        raise AnalysisSpecError(
            "model.covariance.cluster is only valid when covariance.type is cluster"
        )
    if "weights" in model:
        _validate_variable(model["weights"], "model.weights")
        if model["weights"] in set(substantive + fixed_effects + [outcome]):
            raise AnalysisSpecError(
                "model.weights must not duplicate the outcome, regressors, controls, or fixed effects"
            )
        if model_type != "ols":
            raise AnalysisSpecError(
                "Analytic weights are currently supported for OLS only in the common contract"
            )

    if set(fixed_effects).intersection(substantive + [outcome]):
        raise AnalysisSpecError(
            "fixed_effects must not overlap the outcome, regressors, or controls"
        )
    if fixed_effects and model["add_intercept"] and model_type in ("fe", "twfe", "iv_2sls"):
        raise AnalysisSpecError(
            "add_intercept must be false when fixed effects are absorbed"
        )
    if model_type == "did" and model["add_intercept"]:
        raise AnalysisSpecError("add_intercept must be false for DID with unit/time effects")
    if model_type == "rdd" and not model["add_intercept"]:
        raise AnalysisSpecError("Sharp RDD requires add_intercept=true")
    if model_type not in ("fe", "twfe", "iv_2sls") and fixed_effects:
        raise AnalysisSpecError(
            f"fixed_effects are not used by model.type={model_type}; choose FE/TWFE/IV or remove them"
        )
    if model_type != "iv_2sls" and (model.get("endogenous") or model.get("instruments")):
        raise AnalysisSpecError("endogenous and instruments are only valid for model.type=iv_2sls")
    if model_type != "did" and "did" in model:
        raise AnalysisSpecError("model.did is only valid for model.type=did")
    if model_type != "rdd" and "rdd" in model:
        raise AnalysisSpecError("model.rdd is only valid for model.type=rdd")
    if model_type != "ar" and "time_series" in model:
        raise AnalysisSpecError("model.time_series is only valid for model.type=ar")

    if model_type == "ols" and not substantive:
        raise AnalysisSpecError("OLS requires at least one regressor or control")
    if model_type == "fe":
        if not fixed_effects:
            raise AnalysisSpecError("FE requires at least one model.fixed_effects variable")
        if not substantive:
            raise AnalysisSpecError("FE requires at least one regressor or control")
    if model_type == "twfe":
        if len(fixed_effects) < 2:
            raise AnalysisSpecError("TWFE requires at least two fixed effects")
        if not substantive:
            raise AnalysisSpecError("TWFE requires at least one regressor or control")

    if model_type == "did":
        did = model.get("did")
        if not isinstance(did, dict):
            raise AnalysisSpecError("DID requires model.did")
        _reject_unknown_keys(
            did, ("design", "method", "unit", "time", "treatment"), "model.did"
        )
        design = did.get("design")
        if design != "classic":
            raise AnalysisSpecError(
                "The Python execution contract supports model.did.design=classic only"
            )
        for field in ("unit", "time", "treatment"):
            _validate_variable(did.get(field), f"model.did.{field}")
        did_roles = [did["unit"], did["time"], did["treatment"]]
        if len(did_roles) != len(set(did_roles)):
            raise AnalysisSpecError("DID unit, time, and treatment variables must be distinct")
        if outcome in did_roles or set(substantive).intersection(did_roles):
            raise AnalysisSpecError(
                "DID unit/time/treatment must not overlap the outcome, regressors, or controls"
            )
        method = did.setdefault("method", "twfe")
        if method != "twfe":
            raise AnalysisSpecError("Classic DID currently requires method=twfe")

    if model_type == "iv_2sls":
        endogenous = _as_list(model.get("endogenous"), "model.endogenous")
        instruments = _as_list(model.get("instruments"), "model.instruments")
        _validate_variable_list(endogenous, "model.endogenous")
        _validate_variable_list(instruments, "model.instruments")
        if not endogenous or not instruments:
            raise AnalysisSpecError("IV/2SLS requires endogenous and instruments")
        if len(instruments) < len(endogenous):
            raise AnalysisSpecError(
                "IV/2SLS is underidentified: fewer excluded instruments than endogenous variables"
            )
        occupied = set(substantive + fixed_effects + [outcome])
        if occupied.intersection(endogenous) or occupied.intersection(instruments):
            raise AnalysisSpecError(
                "endogenous/instruments must not overlap outcome, exogenous regressors, controls, or fixed effects"
            )
        if set(endogenous).intersection(instruments):
            raise AnalysisSpecError("endogenous variables and instruments must not overlap")
        if "weights" in model:
            raise AnalysisSpecError("Analytic weights are not implemented for IV/2SLS")

    if model_type == "rdd":
        rdd = model.get("rdd")
        if not isinstance(rdd, dict):
            raise AnalysisSpecError("RDD requires model.rdd")
        _reject_unknown_keys(
            rdd,
            ("design", "running", "cutoff", "bandwidth", "polynomial_order", "kernel"),
            "model.rdd",
        )
        if rdd.setdefault("design", "sharp") != "sharp":
            raise AnalysisSpecError(
                "Only sharp RDD is supported; fuzzy RDD must be specified as IV/2SLS"
            )
        _validate_variable(rdd.get("running"), "model.rdd.running")
        if rdd["running"] == outcome or rdd["running"] in substantive:
            raise AnalysisSpecError(
                "RDD running variable must not duplicate the outcome, regressors, or controls"
            )
        cutoff = rdd.get("cutoff")
        if (
            not isinstance(cutoff, (int, float))
            or isinstance(cutoff, bool)
            or not math.isfinite(float(cutoff))
        ):
            raise AnalysisSpecError("model.rdd.cutoff must be a finite number")
        bandwidth = rdd.get("bandwidth")
        if (
            not isinstance(bandwidth, (int, float))
            or isinstance(bandwidth, bool)
            or float(bandwidth) <= 0
        ):
            raise AnalysisSpecError(
                "model.rdd.bandwidth must be explicitly supplied and positive; "
                "this runner does not pretend to select an optimal bandwidth"
            )
        order = rdd.setdefault("polynomial_order", 1)
        if not isinstance(order, int) or isinstance(order, bool) or order not in (1, 2):
            raise AnalysisSpecError("model.rdd.polynomial_order must be 1 or 2")
        if rdd.setdefault("kernel", "triangular") not in ("triangular", "uniform"):
            raise AnalysisSpecError("model.rdd.kernel must be triangular or uniform")

    if model_type == "ar":
        time_series = model.get("time_series")
        if not isinstance(time_series, dict):
            raise AnalysisSpecError("AR requires model.time_series")
        _reject_unknown_keys(
            time_series, ("time", "lags", "include_trend"), "model.time_series"
        )
        time_name = _validate_variable(time_series.get("time"), "model.time_series.time")
        if time_name in set(substantive + [outcome]):
            raise AnalysisSpecError(
                "model.time_series.time must not duplicate the outcome, regressors, or controls"
            )
        lags = time_series.get("lags")
        if not isinstance(lags, int) or isinstance(lags, bool) or not 1 <= lags <= 20:
            raise AnalysisSpecError("model.time_series.lags must be an integer from 1 to 20")
        time_series.setdefault("include_trend", False)
        if not isinstance(time_series["include_trend"], bool):
            raise AnalysisSpecError("model.time_series.include_trend must be true or false")
        if covariance_type == "cluster":
            raise AnalysisSpecError(
                "The single-series AR runner supports homoskedastic or HC1 covariance, not clustered covariance"
            )

    required = required_columns(spec)
    if len(required) != len(set(required)):
        # Duplicate roles are normally harmless, but this catches less obvious
        # cases such as clustering on a weight variable only after all defaults.
        required = list(dict.fromkeys(required))
    return spec


def infer_data_format(path: Path) -> str:
    suffix = path.suffix.lower()
    mapping = {
        ".csv": "csv",
        ".tsv": "tsv",
        ".txt": "csv",
        ".xlsx": "xlsx",
        ".xls": "xlsx",
        ".parquet": "parquet",
        ".feather": "feather",
    }
    if suffix not in mapping:
        raise AnalysisSpecError(
            f"Cannot infer data format from {path.name!r}; set data.format explicitly"
        )
    return mapping[suffix]


def required_columns(spec: Mapping[str, Any]) -> List[str]:
    model = spec["model"]
    columns: List[str] = [model["outcome"]]
    for field in ("regressors", "controls", "fixed_effects", "endogenous", "instruments"):
        columns.extend(model.get(field, []))
    if model.get("weights"):
        columns.append(model["weights"])
    covariance = model.get("covariance", {})
    if covariance.get("type") == "cluster":
        columns.append(covariance["cluster"])
    if model["type"] == "did":
        did = model["did"]
        columns.extend([did["unit"], did["time"], did["treatment"]])
    if model["type"] == "rdd":
        columns.append(model["rdd"]["running"])
    if model["type"] == "ar":
        columns.append(model["time_series"]["time"])
    return list(dict.fromkeys(columns))


def numeric_columns(spec: Mapping[str, Any]) -> List[str]:
    model = spec["model"]
    columns: List[str] = [model["outcome"]]
    for field in ("regressors", "controls", "endogenous", "instruments"):
        columns.extend(model.get(field, []))
    if model.get("weights"):
        columns.append(model["weights"])
    if model["type"] == "did":
        columns.extend([model["did"]["time"], model["did"]["treatment"]])
    if model["type"] == "rdd":
        columns.append(model["rdd"]["running"])
    if model["type"] == "ar":
        columns.append(model["time_series"]["time"])
    return list(dict.fromkeys(columns))


def load_analysis_data(spec: Mapping[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    data_spec = spec["data"]
    path = Path(data_spec["path"])
    if not path.is_file():
        raise AnalysisSpecError(f"Data file does not exist: {path}")
    fmt = data_spec["format"]
    try:
        if fmt == "csv":
            frame = pd.read_csv(path, encoding=data_spec.get("encoding", "utf-8"))
        elif fmt == "tsv":
            frame = pd.read_csv(
                path, sep="\t", encoding=data_spec.get("encoding", "utf-8")
            )
        elif fmt == "xlsx":
            frame = pd.read_excel(path, sheet_name=data_spec.get("sheet", 0))
        elif fmt == "parquet":
            frame = pd.read_parquet(path)
        elif fmt == "feather":
            frame = pd.read_feather(path)
        else:  # guarded by validation
            raise AnalysisSpecError(f"Unsupported data format: {fmt}")
    except ImportError as exc:
        raise BackendUnavailableError(
            f"Reading {fmt} requires an optional pandas engine: {exc}"
        ) from exc
    except Exception as exc:
        raise AnalysisSpecError(f"Could not read data file {path}: {exc}") from exc
    if not isinstance(frame, pd.DataFrame):
        raise AnalysisSpecError("The selected data source did not produce one table")

    required = required_columns(spec)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise AnalysisSpecError(f"Data is missing required columns: {', '.join(missing)}")
    raw_rows = len(frame)
    frame = frame.loc[:, required].copy()
    for column in numeric_columns(spec):
        try:
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        except Exception as exc:
            raise AnalysisSpecError(
                f"Column {column!r} must be numeric for this model"
            ) from exc
        if not np.isfinite(frame[column].dropna().to_numpy(dtype=float)).all():
            raise AnalysisSpecError(
                f"Column {column!r} contains infinite or non-finite numeric values"
            )
    frame = frame.dropna(subset=required)
    if frame.empty:
        raise AnalysisSpecError("No complete observations remain after dropping required-field missingness")
    weights = spec["model"].get("weights")
    if weights and (frame[weights] <= 0).any():
        raise AnalysisSpecError("All analytic weights must be positive")
    data_info = {
        "rows_read": int(raw_rows),
        "rows_complete": int(len(frame)),
        "rows_dropped_missing": int(raw_rows - len(frame)),
        "columns_used": required,
    }
    covariance = spec["model"].get("covariance", {})
    if covariance.get("type") == "cluster":
        cluster = covariance["cluster"]
        cluster_count = int(frame[cluster].nunique(dropna=False))
        if cluster_count < 2:
            raise AnalysisSpecError(
                "Cluster covariance requires at least two complete-sample clusters"
            )
        data_info["cluster_variable"] = cluster
        data_info["cluster_count"] = cluster_count
    return frame, data_info


def load_spec_file(
    spec_path: Path, output_override: Optional[Path] = None
) -> Dict[str, Any]:
    spec_path = spec_path.expanduser().resolve()
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AnalysisSpecError(f"Spec file does not exist: {spec_path}") from exc
    except json.JSONDecodeError as exc:
        raise AnalysisSpecError(f"Spec is not valid JSON: {exc}") from exc
    return validate_and_normalize_spec(raw, spec_path, output_override)


def prepare_output_directory(path: Path, overwrite: bool) -> None:
    if path.exists() and not path.is_dir():
        raise AnalysisSpecError(f"Output path exists and is not a directory: {path}")
    if path.exists() and any(path.iterdir()) and not overwrite:
        raise AnalysisSpecError(
            f"Output directory is not empty: {path}. Use --overwrite or output.overwrite=true."
        )
    path.mkdir(parents=True, exist_ok=True)
    if overwrite:
        for name in KNOWN_ARTIFACTS:
            candidate = path / name
            if candidate.is_file() or candidate.is_symlink():
                candidate.unlink()


def empty_coefficients(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerow(COEFFICIENT_COLUMNS)


def environment_info(backend: str) -> Dict[str, Any]:
    """Return a compact, JSON-safe execution-environment snapshot."""

    if backend != "python":
        raise AnalysisSpecError(f"Unsupported execution backend: {backend}")
    return {
        "python_runtime": str(Path(sys.executable).resolve()),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }


def select_backend(spec: Mapping[str, Any], override: Optional[str] = None) -> str:
    requested = override or spec.get("backend", "auto")
    if requested not in BACKENDS:
        raise AnalysisSpecError(f"Unknown backend: {requested}")
    return "python"


def supported_matrix() -> Dict[str, Any]:
    return {
        "python": {
            "models": ["ols", "fe", "twfe", "classic did", "iv_2sls", "sharp rdd", "conditional ar(p)"],
            "notes": "Locally executed with numpy/pandas; one-way clustered, HC1, or homoskedastic covariance.",
        }
    }


def base_manifest(
    spec: Mapping[str, Any], backend: str, status: str, started_at: str
) -> Dict[str, Any]:
    data_path = Path(spec["data"]["path"])
    return {
        "contract_version": CONTRACT_VERSION,
        "analysis_id": spec["analysis_id"],
        "backend": backend,
        "model_type": spec["model"]["type"],
        "status": status,
        "started_at": started_at,
        "finished_at": utc_now(),
        "spec_sha256": object_sha256(spec),
        "data_sha256": file_sha256(data_path) if data_path.is_file() else None,
        "environment": environment_info(backend),
        "artifacts": {
            "coefficients": "coefficients.csv",
            "diagnostics": "diagnostics.json",
            "log": "run.log",
            "normalized_spec": "normalized-spec.json",
        },
    }


def write_failure_contract(
    output_dir: Path,
    spec: Mapping[str, Any],
    backend: str,
    started_at: str,
    error: Exception,
    log_text: str = "",
) -> None:
    if not (output_dir / "coefficients.csv").exists():
        empty_coefficients(output_dir / "coefficients.csv")
    diagnostics = {
        "status": "failed",
        "error_type": type(error).__name__,
        "error": str(error),
        "environment": environment_info(backend),
    }
    write_json(output_dir / "diagnostics.json", diagnostics)
    manifest = base_manifest(spec, backend, "failed", started_at)
    manifest["error_type"] = type(error).__name__
    manifest["error"] = str(error)
    generated_name = "analysis.py" if backend == "python" else None
    if generated_name and (output_dir / generated_name).is_file():
        manifest["generated_code"] = generated_name
        manifest["artifacts"]["generated_code"] = generated_name
    write_json(output_dir / "manifest.json", manifest)
    message = log_text.rstrip()
    if message:
        message += "\n"
    environment = environment_info(backend)
    message += (
        f"python runtime: {environment['python_runtime']}\n"
        f"python version: {environment['python_version']}\n"
        f"numpy: {environment['packages']['numpy']}; "
        f"pandas: {environment['packages']['pandas']}\n"
        f"ERROR [{type(error).__name__}]: {error}\n"
    )
    (output_dir / "run.log").write_text(message, encoding="utf-8")
