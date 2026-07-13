"""Generate the Python reproducibility entrypoint for a normalized spec."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .common import AnalysisSpecError


def generated_filename(backend: str) -> str:
    if backend != "python":
        raise AnalysisSpecError(f"Unsupported execution backend: {backend}")
    return "analysis.py"


def generate_code(
    backend: str,
    spec: Mapping[str, Any],
    normalized_spec_path: Path,
) -> str:
    if backend != "python":
        raise AnalysisSpecError(f"Unsupported execution backend: {backend}")
    del spec  # The normalized JSON is the generated program's sole input.
    return generate_python_code(normalized_spec_path)


def generate_python_code(normalized_spec_path: Path) -> str:
    scripts_dir = Path(__file__).resolve().parents[1]
    return f'''#!/usr/bin/env python3
"""Generated reproducibility entrypoint for a normalized Python analysis."""
from pathlib import Path
import sys

sys.path.insert(0, {str(scripts_dir)!r})
from econometric_execution.runner import execute_normalized_snapshot

if __name__ == "__main__":
    execute_normalized_snapshot(Path({str(normalized_spec_path)!r}))
'''
