# Python Execution

Use this reference when an econometric design must become an executable,
auditable Python run. The bundled runner validates a versioned JSON
specification, generates `analysis.py`, estimates supported models, and writes a
normalized result contract.

## Commands

Inspect the supported matrix:

```bash
python3 "$SKILL_ROOT/scripts/run_econometric_analysis.py" --print-supported
```

Validate and generate without estimating:

```bash
python3 "$SKILL_ROOT/scripts/run_econometric_analysis.py" analysis.json \
  --backend python --dry-run --output-dir .qa/python_dry_run
```

Execute:

```bash
python3 "$SKILL_ROOT/scripts/run_econometric_analysis.py" analysis.json \
  --backend python --output-dir results/baseline
```

`backend=auto` resolves to `python`. A dry run proves that the specification was
accepted and the program was generated; it does not prove that estimation ran.

## Supported Core

| Design | Bundled Python implementation |
|---|---|
| OLS | Constant and declared regressors |
| One- or multiway FE/TWFE | Within transformation |
| Classic/common-adoption DID | Unit and time FE with adoption-timing audit |
| IV/2SLS | Declared excluded instruments, controls, and optional absorbed FE |
| Sharp RDD | Local polynomial within the declared bandwidth |
| Conditional AR(p) | Regular-spacing check and companion-root stability |

The core deliberately refuses unsupported substitutes. In particular, observed
heterogeneous adoption is not estimated with ordinary TWFE under the classic DID
contract. System GMM, fuzzy RDD, robust-bias-corrected RDD, local projections,
ARIMA/state-space models, and advanced high-dimensional estimators require an
explicit Python implementation outside this bundled core.

## Output Contract

Each accepted run directory contains:

- `normalized-spec.json`;
- `analysis.py`;
- `manifest.json`;
- `run.log`;
- `coefficients.csv`;
- `diagnostics.json`.

Successful coefficient output uses stable columns for term, estimate, standard
error, statistic, p-value, confidence interval, sample size, covariance method,
and model metadata. Diagnostics contain estimator-specific checks and warnings.
The manifest records status, hashes, environment information, output files, and
timestamps.

On validation or execution failure, preserve the failure manifest and log, but
do not fabricate coefficients or diagnostics.

## Reproducibility And Inference

- Keep raw data read-only and use a dedicated run directory.
- Record the Python executable and the installed NumPy and pandas versions.
- Preserve the normalized specification and generated `analysis.py` with the
  authoritative results.
- Treat cluster-robust normal-approximation inference cautiously with few
  clusters; the runner emits a warning but does not supply a small-sample cure.
- Inspect sample counts, dropped observations, fixed-effect absorption,
  first-stage diagnostics, bandwidth support, and AR stability before writing.
- Never infer identification from successful execution alone.
