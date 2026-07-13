"""Orchestrate Python econometric runs and normalized output artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from .codegen import generate_code, generated_filename
from .common import (
    COEFFICIENT_COLUMNS,
    AnalysisExecutionError,
    AnalysisSpecError,
    base_manifest,
    empty_coefficients,
    environment_info,
    load_analysis_data,
    load_spec_file,
    prepare_output_directory,
    select_backend,
    utc_now,
    validate_and_normalize_spec,
    write_failure_contract,
    write_json,
)
from .python_backend import audit_classic_did_data, execute_python


def _validate_coefficient_contract(
    coefficients: pd.DataFrame, spec: Mapping[str, Any]
) -> None:
    missing_columns = [
        name for name in COEFFICIENT_COLUMNS if name not in coefficients.columns
    ]
    if missing_columns:
        raise AnalysisExecutionError(
            f"Coefficient output is missing columns: {', '.join(missing_columns)}"
        )
    if coefficients.empty:
        raise AnalysisExecutionError(
            "The estimator returned no coefficient rows; the run cannot be marked succeeded"
        )
    terms = coefficients["term"].astype(str)
    if bool(terms.str.strip().eq("").any()) or bool(terms.duplicated().any()):
        raise AnalysisExecutionError(
            "Coefficient terms must be non-empty and unique"
        )
    for column in COEFFICIENT_COLUMNS[1:]:
        try:
            values = pd.to_numeric(coefficients[column], errors="raise").to_numpy(
                dtype=float
            )
        except Exception as exc:
            raise AnalysisExecutionError(
                f"Coefficient column {column} must be numeric"
            ) from exc
        if not np.isfinite(values).all():
            raise AnalysisExecutionError(
                f"Coefficient column {column} contains non-finite values"
            )

    model = spec["model"]
    substantive = list(model["regressors"] + model["controls"])
    model_type = model["type"]
    if model_type in ("ols", "fe", "twfe"):
        required_terms = substantive
    elif model_type == "did":
        required_terms = [model["did"]["treatment"], *substantive]
    elif model_type == "iv_2sls":
        required_terms = [*substantive, *model["endogenous"]]
    elif model_type == "rdd":
        required_terms = ["rdd_jump", *substantive]
    elif model_type == "ar":
        outcome = model["outcome"]
        required_terms = [
            f"{outcome}_lag_{lag}"
            for lag in range(1, int(model["time_series"]["lags"]) + 1)
        ] + substantive
        if model["time_series"]["include_trend"]:
            required_terms.append("linear_trend")
    else:
        required_terms = []
    term_set = set(terms.tolist())
    missing_terms = [term for term in required_terms if term not in term_set]
    if missing_terms:
        raise AnalysisExecutionError(
            "Coefficient output is missing requested term(s): "
            + ", ".join(missing_terms)
        )


def _write_success(
    output_dir: Path,
    spec: Mapping[str, Any],
    backend: str,
    started_at: str,
    coefficients: pd.DataFrame,
    diagnostics: Mapping[str, Any],
    warnings: Sequence[str],
    data_info: Mapping[str, Any],
    log_text: str,
) -> Dict[str, Any]:
    _validate_coefficient_contract(coefficients, spec)
    coefficients.loc[:, COEFFICIENT_COLUMNS].to_csv(
        output_dir / "coefficients.csv", index=False
    )
    environment = environment_info(backend)
    diagnostic_payload = dict(diagnostics)
    diagnostic_payload["data"] = dict(data_info)
    diagnostic_payload["warnings"] = list(warnings)
    diagnostic_payload["environment"] = environment
    write_json(output_dir / "diagnostics.json", diagnostic_payload)
    manifest = base_manifest(spec, backend, "succeeded", started_at)
    manifest.update(
        {
            "estimator": diagnostic_payload.get("estimator"),
            "nobs": diagnostic_payload.get("nobs", data_info.get("rows_complete")),
            "warnings": list(warnings),
            "generated_code": generated_filename(backend),
        }
    )
    manifest["artifacts"]["generated_code"] = generated_filename(backend)
    write_json(output_dir / "manifest.json", manifest)
    (output_dir / "run.log").write_text(
        log_text.rstrip()
        + "\n"
        + f"python runtime: {environment['python_runtime']}\n"
        + f"python version: {environment['python_version']}\n"
        + f"numpy: {environment['packages']['numpy']}; "
        + f"pandas: {environment['packages']['pandas']}\n",
        encoding="utf-8",
    )
    return manifest


def _write_dry_run(
    output_dir: Path,
    spec: Mapping[str, Any],
    backend: str,
    started_at: str,
) -> Dict[str, Any]:
    empty_coefficients(output_dir / "coefficients.csv")
    environment = environment_info(backend)
    diagnostics = {
        "status": "dry_run",
        "backend": backend,
        "model_type": spec["model"]["type"],
        "message": "Python code was generated and no estimator was executed.",
        "environment": environment,
    }
    write_json(output_dir / "diagnostics.json", diagnostics)
    manifest = base_manifest(spec, backend, "dry_run", started_at)
    manifest["generated_code"] = generated_filename(backend)
    manifest["artifacts"]["generated_code"] = generated_filename(backend)
    write_json(output_dir / "manifest.json", manifest)
    (output_dir / "run.log").write_text(
        f"dry-run: generated {generated_filename(backend)}; no estimation executed\n"
        f"python runtime: {environment['python_runtime']}\n"
        f"python version: {environment['python_version']}\n"
        f"numpy: {environment['packages']['numpy']}; "
        f"pandas: {environment['packages']['pandas']}\n",
        encoding="utf-8",
    )
    return manifest


def run_analysis(
    spec_path: Path,
    backend_override: Optional[str] = None,
    output_override: Optional[Path] = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Validate, generate Python code, optionally estimate, and write artifacts."""

    started_at = utc_now()
    spec = load_spec_file(Path(spec_path), output_override)
    backend = select_backend(spec, backend_override)
    output_dir = Path(spec["output"]["directory"])
    allow_overwrite = bool(overwrite or spec["output"]["overwrite"])
    prepare_output_directory(output_dir, allow_overwrite)
    normalized_path = output_dir / "normalized-spec.json"
    write_json(normalized_path, spec)
    try:
        code_path = output_dir / generated_filename(backend)
        code_path.write_text(
            generate_code(backend, spec, normalized_path), encoding="utf-8"
        )
        code_path.chmod(0o755)
        if dry_run:
            return _write_dry_run(output_dir, spec, backend, started_at)

        frame, data_info = load_analysis_data(spec)
        if spec["model"]["type"] == "did":
            data_info["classic_did_audit"] = audit_classic_did_data(
                frame, spec["model"]["did"]
            )
        result = execute_python(frame, spec)
        log_text = (
            f"backend: python\nmodel: {spec['model']['type']}\n"
            f"rows read: {data_info['rows_read']}\n"
            f"rows complete: {data_info['rows_complete']}\n"
            f"estimator: {result['diagnostics'].get('estimator')}"
        )
        return _write_success(
            output_dir,
            spec,
            backend,
            started_at,
            result["coefficients"],
            result["diagnostics"],
            result.get("warnings", []),
            data_info,
            log_text,
        )
    except Exception as exc:
        write_failure_contract(output_dir, spec, backend, started_at, exc)
        raise


def execute_normalized_snapshot(
    normalized_spec_path: Path, backend: str = "python"
) -> Dict[str, Any]:
    """Re-execute a generated Python entrypoint without directory refusal."""

    if backend != "python":
        raise AnalysisSpecError("Only the Python execution backend is supported")
    started_at = utc_now()
    path = Path(normalized_spec_path).expanduser().resolve()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AnalysisSpecError(f"Could not read normalized spec {path}: {exc}") from exc
    spec = validate_and_normalize_spec(raw, path)
    selected = select_backend(spec, "python")
    output_dir = Path(spec["output"]["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        frame, data_info = load_analysis_data(spec)
        if spec["model"]["type"] == "did":
            data_info["classic_did_audit"] = audit_classic_did_data(
                frame, spec["model"]["did"]
            )
        result = execute_python(frame, spec)
        return _write_success(
            output_dir,
            spec,
            selected,
            started_at,
            result["coefficients"],
            result["diagnostics"],
            result.get("warnings", []),
            data_info,
            f"generated Python entrypoint re-executed model={spec['model']['type']}",
        )
    except Exception as exc:
        write_failure_contract(output_dir, spec, selected, started_at, exc)
        raise
