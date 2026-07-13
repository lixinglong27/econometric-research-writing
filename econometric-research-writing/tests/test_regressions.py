from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import pandas as pd


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SKILL_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


profiler = load_script("profile_econ_dataset", "profile_econ_dataset.py")
renderer = load_script("render_validate_docx", "render_validate_docx.py")


class ProfilerRegressionTests(unittest.TestCase):
    def test_single_row_formats_missing_standard_deviation(self):
        frame = pd.DataFrame({"value": [1.0]})
        report = profiler.build_report(Path("single.csv"), frame, {})
        markdown = profiler.markdown_report(report)
        self.assertIn("sd n/a", markdown)

    def test_xlsx_without_sheet_uses_first_worksheet(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.xlsx"
            with pd.ExcelWriter(path) as writer:
                pd.DataFrame({"first": [1]}).to_excel(
                    writer, sheet_name="first_sheet", index=False
                )
                pd.DataFrame({"second": [2]}).to_excel(
                    writer, sheet_name="second_sheet", index=False
                )
            loaded = profiler.read_data(path)
            self.assertIsInstance(loaded, pd.DataFrame)
            self.assertEqual(list(loaded.columns), ["first"])


class RendererRegressionTests(unittest.TestCase):
    def test_missing_renderer_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            argv = [
                "render_validate_docx.py",
                str(Path(tmp) / "paper.docx"),
                "--output-dir",
                str(Path(tmp) / "rendered"),
            ]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(
                renderer, "find_renderer", return_value=None
            ):
                with self.assertRaises(SystemExit) as caught:
                    renderer.main()
            self.assertNotEqual(caught.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
