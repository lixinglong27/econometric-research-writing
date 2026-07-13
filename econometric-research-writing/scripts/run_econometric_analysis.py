#!/usr/bin/env python3
"""Run a versioned econometric analysis specification with Python."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from econometric_execution.common import supported_matrix
from econometric_execution.runner import run_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an econometric JSON spec, generate reproducible Python code, "
            "and optionally execute it into a common artifact contract."
        )
    )
    parser.add_argument("spec", nargs="?", type=Path, help="Path to analysis spec JSON")
    parser.add_argument(
        "--backend",
        choices=("auto", "python"),
        help="Override spec backend; auto resolves to the bundled Python core",
    )
    parser.add_argument("--output-dir", type=Path, help="Override output.directory")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and generate code/artifact skeleton without running the estimator",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace known contract artifacts in a non-empty output directory",
    )
    parser.add_argument(
        "--print-supported",
        action="store_true",
        help="Print the Python estimator support matrix and exit",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.print_supported:
        print(json.dumps(supported_matrix(), indent=2, sort_keys=True))
        return 0
    if args.spec is None:
        print("error: spec is required unless --print-supported is used", file=sys.stderr)
        return 2
    try:
        manifest = run_analysis(
            args.spec,
            backend_override=args.backend,
            output_override=args.output_dir,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
        )
    except Exception as exc:
        print(f"error [{type(exc).__name__}]: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
