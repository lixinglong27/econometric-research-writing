from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from econometric_execution.common import (
    COEFFICIENT_COLUMNS,
    AnalysisExecutionError,
    AnalysisSpecError,
    supported_matrix,
    validate_and_normalize_spec,
)
from econometric_execution.python_backend import audit_classic_did_data
from econometric_execution.runner import _validate_coefficient_contract, run_analysis


class ExecutionLayerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_case(self, frame: pd.DataFrame, model: dict) -> Path:
        data_path = self.root / "data.csv"
        frame.to_csv(data_path, index=False)
        spec = {
            "spec_version": "1.0",
            "analysis_id": "test_analysis",
            "backend": "python",
            "data": {"path": str(data_path), "format": "csv"},
            "model": model,
            "output": {"directory": str(self.root / "result"), "overwrite": True},
        }
        spec_path = self.root / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        return spec_path

    def coefficients(self) -> pd.DataFrame:
        return pd.read_csv(self.root / "result" / "coefficients.csv")

    def test_python_ols_writes_contract(self) -> None:
        x = np.arange(1.0, 31.0)
        y = 1.5 + 2.25 * x + np.sin(x) * 0.05
        spec_path = self.write_case(
            pd.DataFrame({"y": y, "x": x}),
            {
                "type": "ols",
                "outcome": "y",
                "regressors": ["x"],
                "covariance": {"type": "hc1"},
            },
        )
        manifest = run_analysis(spec_path)
        self.assertEqual(manifest["status"], "succeeded")
        self.assertEqual(manifest["environment"]["packages"]["numpy"], np.__version__)
        diagnostics = json.loads((self.root / "result" / "diagnostics.json").read_text())
        self.assertEqual(diagnostics["environment"]["packages"]["pandas"], pd.__version__)
        self.assertIn("python runtime:", (self.root / "result" / "run.log").read_text())
        coefficients = self.coefficients().set_index("term")
        self.assertAlmostEqual(coefficients.loc["x", "estimate"], 2.25, places=2)
        for name in (
            "analysis.py",
            "coefficients.csv",
            "diagnostics.json",
            "manifest.json",
            "normalized-spec.json",
            "run.log",
        ):
            self.assertTrue((self.root / "result" / name).is_file(), name)

    def test_generated_python_entrypoint_reexecutes_snapshot(self) -> None:
        spec_path = self.write_case(
            pd.DataFrame({"y": [1.0, 2.2, 2.9, 4.1], "x": [0.0, 1.0, 2.0, 3.0]}),
            {
                "type": "ols",
                "outcome": "y",
                "regressors": ["x"],
                "covariance": {"type": "hc1"},
            },
        )
        run_analysis(spec_path)
        completed = subprocess.run(
            [sys.executable, str(self.root / "result" / "analysis.py")],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        manifest = json.loads((self.root / "result" / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "succeeded")

    def test_python_dry_run_writes_only_artifact_skeleton(self) -> None:
        spec_path = self.write_case(
            pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [0.0, 1.0, 2.0]}),
            {
                "type": "ols",
                "outcome": "y",
                "regressors": ["x"],
                "covariance": {"type": "hc1"},
            },
        )
        manifest = run_analysis(spec_path, dry_run=True)
        self.assertEqual(manifest["status"], "dry_run")
        self.assertEqual(len(self.coefficients()), 0)
        self.assertIn("no estimation executed", (self.root / "result" / "run.log").read_text())

    def test_support_matrix_is_python_only(self) -> None:
        matrix = supported_matrix()
        self.assertEqual(set(matrix), {"python"})
        self.assertIn("classic did", matrix["python"]["models"])

    def test_python_fe_absorbs_entity_effects(self) -> None:
        rng = np.random.default_rng(42)
        entity = np.repeat(np.arange(12), 6)
        x = rng.normal(size=len(entity))
        alpha = np.repeat(rng.normal(scale=5, size=12), 6)
        y = alpha + 3.0 * x + rng.normal(scale=0.01, size=len(entity))
        spec_path = self.write_case(
            pd.DataFrame({"y": y, "x": x, "entity": entity}),
            {
                "type": "fe",
                "outcome": "y",
                "regressors": ["x"],
                "fixed_effects": ["entity"],
                "covariance": {"type": "cluster", "cluster": "entity"},
            },
        )
        run_analysis(spec_path)
        coefficient = self.coefficients().set_index("term").loc["x", "estimate"]
        self.assertAlmostEqual(coefficient, 3.0, places=2)
        diagnostics = json.loads((self.root / "result" / "diagnostics.json").read_text())
        self.assertTrue(diagnostics["few_cluster_inference"])
        self.assertTrue(any("Only 12 clusters" in item for item in diagnostics["warnings"]))

    def test_classic_did_audits_heterogeneous_adoption_timing(self) -> None:
        rows = []
        for unit in range(6):
            for time in range(4):
                if unit < 2:
                    treated = int(time >= 1)
                elif unit < 4:
                    treated = int(time >= 2)
                else:
                    treated = 0
                rows.append(
                    {"unit": unit, "time": time, "treated": treated, "y": unit + time + treated}
                )
        spec_path = self.write_case(
            pd.DataFrame(rows),
            {
                "type": "did",
                "outcome": "y",
                "did": {
                    "design": "classic",
                    "method": "twfe",
                    "unit": "unit",
                    "time": "time",
                    "treatment": "treated",
                },
                "covariance": {"type": "cluster", "cluster": "unit"},
            },
        )
        with self.assertRaisesRegex(AnalysisSpecError, "Observed adoption is staggered"):
            run_analysis(spec_path)
        manifest = json.loads((self.root / "result" / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "failed")

    def test_python_classic_did_common_adoption(self) -> None:
        rng = np.random.default_rng(19)
        rows = []
        unit_effects = rng.normal(size=20)
        for unit in range(20):
            for time in range(6):
                treated = int(unit < 10 and time >= 3)
                y = unit_effects[unit] + 0.4 * time + 3.5 * treated + rng.normal(scale=0.01)
                rows.append({"unit": unit, "time": time, "treated": treated, "y": y})
        spec_path = self.write_case(
            pd.DataFrame(rows),
            {
                "type": "did",
                "outcome": "y",
                "did": {
                    "design": "classic",
                    "method": "twfe",
                    "unit": "unit",
                    "time": "time",
                    "treatment": "treated",
                },
                "covariance": {"type": "cluster", "cluster": "unit"},
            },
        )
        run_analysis(spec_path)
        estimate = self.coefficients().set_index("term").loc["treated", "estimate"]
        self.assertAlmostEqual(estimate, 3.5, delta=0.03)
        diagnostics = json.loads((self.root / "result" / "diagnostics.json").read_text())
        self.assertEqual(diagnostics["did_design"], "classic/common adoption")

    def test_classic_did_rejects_time_invariant_group_indicator(self) -> None:
        rows = []
        for unit in range(4):
            for time in range(3):
                rows.append(
                    {
                        "unit": unit,
                        "time": time,
                        "treated": int(unit < 2),
                        "y": float(unit + time),
                    }
                )
        with self.assertRaisesRegex(AnalysisSpecError, "pre-adoption"):
            audit_classic_did_data(
                pd.DataFrame(rows),
                {"unit": "unit", "time": "time", "treatment": "treated"},
            )

    def test_nonclassic_did_is_rejected_by_python_contract(self) -> None:
        spec_path = self.write_case(
            pd.DataFrame({"y": [1.0], "unit": [1], "time": [1], "d": [0]}),
            {
                "type": "did",
                "outcome": "y",
                "did": {
                    "design": "heterogeneous_adoption",
                    "method": "advanced",
                    "unit": "unit",
                    "time": "time",
                    "treatment": "d",
                },
            },
        )
        with self.assertRaisesRegex(AnalysisSpecError, "design=classic only"):
            run_analysis(spec_path)

    def test_python_iv_2sls(self) -> None:
        rng = np.random.default_rng(7)
        n = 1200
        z = rng.normal(size=n)
        u = rng.normal(size=n)
        v = 0.6 * u + rng.normal(size=n)
        x = 1.2 * z + v
        y = 0.5 + 2.0 * x + u
        spec_path = self.write_case(
            pd.DataFrame({"y": y, "x": x, "z": z}),
            {
                "type": "iv_2sls",
                "outcome": "y",
                "endogenous": ["x"],
                "instruments": ["z"],
                "covariance": {"type": "hc1"},
            },
        )
        run_analysis(spec_path)
        coefficient = self.coefficients().set_index("term").loc["x", "estimate"]
        self.assertAlmostEqual(coefficient, 2.0, delta=0.08)
        diagnostics = json.loads((self.root / "result" / "diagnostics.json").read_text())
        self.assertGreater(diagnostics["first_stages"][0]["partial_f_statistic"], 10)

    def test_python_sharp_rdd(self) -> None:
        rng = np.random.default_rng(5)
        running = np.linspace(-1, 1, 400)
        right = (running >= 0).astype(float)
        y = 2 + 4 * right + 0.5 * running + 0.2 * right * running + rng.normal(
            scale=0.05, size=400
        )
        spec_path = self.write_case(
            pd.DataFrame({"y": y, "running": running}),
            {
                "type": "rdd",
                "outcome": "y",
                "rdd": {
                    "design": "sharp",
                    "running": "running",
                    "cutoff": 0,
                    "bandwidth": 0.8,
                    "polynomial_order": 1,
                    "kernel": "triangular",
                },
                "covariance": {"type": "hc1"},
            },
        )
        run_analysis(spec_path)
        jump = self.coefficients().set_index("term").loc["rdd_jump", "estimate"]
        self.assertAlmostEqual(jump, 4.0, delta=0.08)

    def test_rdd_rejects_boolean_numeric_fields(self) -> None:
        frame = pd.DataFrame(
            {"y": np.linspace(0, 1, 20), "running": np.linspace(-1, 1, 20)}
        )
        invalid_fields = (
            ("cutoff", False, "cutoff"),
            ("bandwidth", True, "bandwidth"),
            ("polynomial_order", True, "polynomial_order"),
        )
        for field, value, marker in invalid_fields:
            with self.subTest(field=field):
                rdd = {
                    "design": "sharp",
                    "running": "running",
                    "cutoff": 0,
                    "bandwidth": 0.8,
                    "polynomial_order": 1,
                }
                rdd[field] = value
                spec_path = self.write_case(
                    frame,
                    {
                        "type": "rdd",
                        "outcome": "y",
                        "rdd": rdd,
                        "covariance": {"type": "hc1"},
                    },
                )
                with self.assertRaisesRegex(AnalysisSpecError, marker):
                    run_analysis(spec_path, overwrite=True)

    def test_python_conditional_ar_reports_stability(self) -> None:
        rng = np.random.default_rng(123)
        y = np.zeros(300)
        for index in range(2, len(y)):
            y[index] = 0.55 * y[index - 1] - 0.20 * y[index - 2] + rng.normal(
                scale=0.05
            )
        spec_path = self.write_case(
            pd.DataFrame({"time": np.arange(len(y)), "y": y}),
            {
                "type": "ar",
                "outcome": "y",
                "time_series": {"time": "time", "lags": 2},
                "covariance": {"type": "hc1"},
            },
        )
        run_analysis(spec_path)
        coefficients = self.coefficients().set_index("term")
        self.assertAlmostEqual(coefficients.loc["y_lag_1", "estimate"], 0.55, delta=0.08)
        self.assertAlmostEqual(coefficients.loc["y_lag_2", "estimate"], -0.20, delta=0.08)
        diagnostics = json.loads((self.root / "result" / "diagnostics.json").read_text())
        self.assertTrue(diagnostics["stable_ar"])
        self.assertEqual(diagnostics["lag_order"], 2)

    def test_example_and_schema_are_valid_json(self) -> None:
        schema = json.loads(
            (SKILL_ROOT / "schemas" / "analysis-spec.schema.json").read_text()
        )
        example_path = SKILL_ROOT / "examples" / "analysis-spec.example.json"
        example = json.loads(example_path.read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(set(schema["properties"]["backend"]["enum"]), {"auto", "python"})
        self.assertEqual(
            set(schema["$defs"]["data"]["properties"]["format"]["enum"]),
            {"csv", "tsv", "xlsx", "parquet", "feather"},
        )
        normalized = validate_and_normalize_spec(example, example_path)
        self.assertEqual(normalized["model"]["type"], "fe")
        self.assertTrue(Path(normalized["data"]["path"]).is_absolute())

    def test_unknown_spec_fields_are_rejected(self) -> None:
        spec_path = self.write_case(
            pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [0.0, 1.0, 2.0]}),
            {
                "type": "ols",
                "outcome": "y",
                "regressors": ["x"],
                "covariance": {"type": "hc1", "typo": True},
            },
        )
        with self.assertRaisesRegex(AnalysisSpecError, "unknown field"):
            run_analysis(spec_path)

    def test_empty_covariance_object_materializes_hc1_default(self) -> None:
        spec_path = self.write_case(
            pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [0.0, 1.0, 2.0]}),
            {"type": "ols", "outcome": "y", "regressors": ["x"], "covariance": {}},
        )
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
        normalized = validate_and_normalize_spec(raw, spec_path)
        self.assertEqual(normalized["model"]["covariance"]["type"], "hc1")

    def test_unknown_backend_is_rejected(self) -> None:
        spec_path = self.write_case(
            pd.DataFrame({"y": [1.0, 2.0, 3.0], "x": [0.0, 1.0, 2.0]}),
            {"type": "ols", "outcome": "y", "regressors": ["x"]},
        )
        raw = json.loads(spec_path.read_text())
        raw["backend"] = "other"
        with self.assertRaisesRegex(AnalysisSpecError, "backend must be one of"):
            validate_and_normalize_spec(raw, spec_path)

    def test_coefficient_contract_rejects_empty_or_nonfinite_output(self) -> None:
        spec = {
            "model": {
                "type": "ols",
                "outcome": "y",
                "regressors": ["x"],
                "controls": [],
            }
        }
        empty = pd.DataFrame(columns=COEFFICIENT_COLUMNS)
        with self.assertRaisesRegex(AnalysisExecutionError, "no coefficient rows"):
            _validate_coefficient_contract(empty, spec)
        invalid = pd.DataFrame(
            [["x", 1.0, np.nan, 1.0, 0.1, 0.5, 1.5]],
            columns=COEFFICIENT_COLUMNS,
        )
        with self.assertRaisesRegex(AnalysisExecutionError, "non-finite"):
            _validate_coefficient_contract(invalid, spec)


if __name__ == "__main__":
    unittest.main()
