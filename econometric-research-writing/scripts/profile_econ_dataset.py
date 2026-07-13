import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROLE_HINTS = {
    "unit": ["id", "firm", "company", "country", "region", "province", "city", "person", "household", "bank"],
    "time": ["date", "year", "month", "quarter", "time", "period", "week", "day"],
    "outcome": ["outcome", "performance", "growth", "revenue", "profit", "sales", "productivity", "return", "score"],
    "treatment": ["treat", "policy", "post", "did", "exposure", "shock", "price", "tax", "subsidy", "intervention"],
    "mechanism": ["mechanism", "channel", "mediator", "innovation", "investment", "employment", "cost", "attention"],
    "instrument": ["instrument", "iv", "distance", "eligibility", "shift", "bartik", "z_"],
    "weight": ["weight", "population", "sample_weight"],
}


def name_tokens(name):
    return re.findall(r"[a-z0-9]+", str(name).lower())


def hint_matches(name, hint):
    tokens = name_tokens(name)
    hint_tokens = name_tokens(hint)
    if not hint_tokens:
        return False
    if len(hint_tokens) == 1:
        return hint_tokens[0] in tokens
    width = len(hint_tokens)
    return any(tokens[i : i + width] == hint_tokens for i in range(0, len(tokens) - width + 1))


def read_data(path, sheet=None):
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        # pandas returns a ``dict[str, DataFrame]`` when ``sheet_name=None``.
        # The profiler operates on one DataFrame, so default to the first sheet.
        return pd.read_excel(path, sheet_name=0 if sheet is None else sheet)
    raise SystemExit(f"unsupported file type: {suffix}")


def safe_float(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value)
    return value


def infer_roles(columns):
    inferred = {}
    for col in columns:
        hits = []
        for role, hints in ROLE_HINTS.items():
            if any(hint_matches(col, h) for h in hints):
                hits.append(role)
        if hits:
            inferred[col] = hits
    return inferred


def first_inferred_role(inferred, role, columns):
    for col in columns:
        if role in inferred.get(col, []):
            return col
    return None


def roles_with_inferred_panel_keys(roles, inferred, columns):
    """Return declared roles plus provisional structural keys.

    Column-name hints are not substantive research semantics. Only unit and time
    hints may be used for automatic structural checks; treatment, outcome,
    mechanism, instrument, and weight hints remain provisional until declared.
    """
    merged = dict(roles)
    sources = {k: "declared" for k in merged}
    for role in ["unit", "time"]:
        if role not in merged:
            value = first_inferred_role(inferred, role, columns)
            if value is not None:
                merged[role] = value
                sources[role] = "provisional_name_hint"
    return merged, sources


def column_profile(df):
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        unique = int(s.nunique(dropna=True))
        row = {
            "name": str(col),
            "dtype": str(s.dtype),
            "missing": missing,
            "missing_pct": round(missing / n, 4) if n else None,
            "unique": unique,
            "constant": unique <= 1,
        }
        if pd.api.types.is_numeric_dtype(s):
            desc = s.replace([np.inf, -np.inf], np.nan).dropna().describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99])
            for key in ["mean", "std", "min", "1%", "25%", "50%", "75%", "99%", "max"]:
                if key in desc:
                    row[key] = safe_float(desc[key])
            row["zero_count"] = int((s == 0).sum())
            row["negative_count"] = int((s < 0).sum())
        elif pd.api.types.is_datetime64_any_dtype(s):
            row["min"] = str(s.min()) if missing < n else None
            row["max"] = str(s.max()) if missing < n else None
        else:
            top = s.dropna().astype(str).value_counts().head(5)
            row["top_values"] = top.to_dict()
        rows.append(row)
    return rows


def top_correlations(df, max_pairs=20):
    num = df.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)
    if num.shape[1] < 2:
        return []
    corr = num.corr(numeric_only=True)
    pairs = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            val = corr.loc[a, b]
            if pd.notna(val):
                pairs.append({"var1": str(a), "var2": str(b), "corr": float(val), "abs_corr": abs(float(val))})
    pairs.sort(key=lambda x: x["abs_corr"], reverse=True)
    return [{k: v for k, v in p.items() if k != "abs_corr"} for p in pairs[:max_pairs]]


def panel_checks(df, roles):
    unit = roles.get("unit")
    time = roles.get("time")
    if not unit or not time or unit not in df.columns or time not in df.columns:
        return None
    key = df[[unit, time]]
    complete_keys = key.dropna()
    duplicate_count = int(complete_keys.duplicated().sum())
    missing_key_rows = int(key.isna().any(axis=1).sum())
    counts = complete_keys.groupby(unit, dropna=False)[time].nunique(dropna=True)
    n_units = int(complete_keys[unit].nunique(dropna=True))
    n_periods = int(complete_keys[time].nunique(dropna=True))
    observed_grid_cells = int(complete_keys.drop_duplicates().shape[0])
    expected_grid_cells = n_units * n_periods
    complete_unit_time_grid = bool(
        n_units
        and n_periods
        and duplicate_count == 0
        and missing_key_rows == 0
        and observed_grid_cells == expected_grid_cells
    )
    return {
        "unit": unit,
        "time": time,
        "n_units": n_units,
        "n_periods": n_periods,
        "duplicate_unit_time_rows": duplicate_count,
        "missing_unit_or_time_rows": missing_key_rows,
        "observed_grid_cells": observed_grid_cells,
        "expected_grid_cells": expected_grid_cells,
        "min_periods_per_unit": int(counts.min()) if len(counts) else 0,
        "median_periods_per_unit": safe_float(counts.median()) if len(counts) else None,
        "max_periods_per_unit": int(counts.max()) if len(counts) else 0,
        # Keep the legacy key for downstream consumers, but make it a true
        # rectangular-grid check rather than an equal-row-count heuristic.
        "balanced_candidate": complete_unit_time_grid,
        "complete_unit_time_grid": complete_unit_time_grid,
    }


def load_roles(path):
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if v}


def declared_regressor_names(roles, columns):
    """Return only variables explicitly declared to enter the same right-hand side."""

    names = []
    for role in ("treatment", "regressor", "regressors", "control", "controls"):
        value = roles.get(role)
        values = value if isinstance(value, list) else [value] if isinstance(value, str) else []
        names.extend(name for name in values if name in columns)
    return list(dict.fromkeys(names))


def warnings(df, profiles, roles):
    out = []
    for p in profiles:
        col_name = p["name"]
        if p["missing_pct"] and p["missing_pct"] > 0.2:
            out.append(f"{col_name}: missingness exceeds 20%; assess sample selection or imputation.")
        if p["constant"]:
            out.append(f"{col_name}: constant or nearly constant; not useful as a regressor in this sample.")
        if p.get("negative_count", 0) > 0 and any(token in col_name.lower() for token in ["price", "revenue", "sales", "asset", "population", "gdp"]):
            out.append(f"{col_name}: negative values in a variable that may be nonnegative by definition.")
        
        # Suggest log transformation for highly skewed positive continuous variables
        if col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name]):
            s = df[col_name].dropna()
            if len(s) > 30 and s.nunique() > 10 and (s > 0).all():
                try:
                    skew = s.skew()
                    if pd.notna(skew) and skew > 2.0:
                        out.append(f"{col_name}: highly skewed (skewness = {skew:.2f}) and positive; consider log transformation `log({col_name})` for elasticity interpretation or variance reduction.")
                except Exception:
                    pass

    # Correlation is a multicollinearity concern only when both variables are
    # explicitly declared to enter the same right-hand side. Outcome/regressor
    # association is expected and remains visible in the correlations table.
    declared = declared_regressor_names(roles, df.columns)
    num_cols = [name for name in declared if pd.api.types.is_numeric_dtype(df[name])]
    if len(num_cols) >= 2:
        try:
            corr_matrix = df[num_cols].corr().abs()
            cols_list = list(num_cols)
            for i, col1 in enumerate(cols_list):
                for col2 in cols_list[i+1:]:
                    r_val = corr_matrix.loc[col1, col2]
                    if pd.notna(r_val) and r_val > 0.8:
                        out.append(f"High correlation between declared regressors `{col1}` and `{col2}` (r = {r_val:.2f}); assess multicollinearity in the specified model.")
        except Exception:
            pass

    unit = roles.get("unit")
    time = roles.get("time")
    if unit and time and unit in df.columns and time in df.columns and df[[unit, time]].duplicated().any():
        out.append("Duplicate unit-time keys detected; aggregate or deduplicate before panel regression.")
    return out


def build_report(path, df, roles):
    inferred = infer_roles(df.columns)
    analysis_roles, role_sources = roles_with_inferred_panel_keys(roles, inferred, list(df.columns))
    profiles = column_profile(df)
    panel = panel_checks(df, analysis_roles)
    report = {
        "file": str(path),
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "roles": roles,
        "analysis_roles": {
            str(k): list(v) if isinstance(v, list) else str(v)
            for k, v in analysis_roles.items()
        },
        "role_sources": role_sources,
        "inferred_role_hints": {str(k): v for k, v in inferred.items()},
        "columns_profile": profiles,
        "top_correlations": top_correlations(df),
        "panel_checks": panel,
        "warnings": warnings(df, profiles, analysis_roles),
    }
    return report


def markdown_report(report):
    def role_value(value):
        values = value if isinstance(value, list) else [value]
        return ", ".join(f"`{item}`" for item in values)

    lines = [
        "# Econometric Dataset Profile",
        "",
        f"- File: `{report['file']}`",
        f"- Rows: {report['rows']}",
        f"- Columns: {report['columns']}",
        "",
        "## Declared Roles",
    ]
    if report["roles"]:
        for k, v in report["roles"].items():
            lines.append(f"- {k}: {role_value(v)}")
    else:
        lines.append("- None supplied. Treat role hints below as provisional.")
    if report["analysis_roles"]:
        lines += ["", "## Analysis Roles Used For Automatic Checks"]
        for k, v in report["analysis_roles"].items():
            source = report["role_sources"].get(k, "unknown")
            lines.append(f"- {k}: {role_value(v)} ({source})")
    lines += [
        "",
        "## Provisional Name-Based Role Hints",
        "",
        "These hints are candidates for review, not validated causal or measurement roles.",
    ]
    for col, hints in report["inferred_role_hints"].items():
        lines.append(f"- `{col}`: {', '.join(hints)}")
    if not report["inferred_role_hints"]:
        lines.append("- No obvious role hints from column names.")
    lines += ["", "## Data Quality Warnings"]
    for w in report["warnings"] or ["No automatic warnings. Still check economics-specific measurement issues."]:
        lines.append(f"- {w}")
    if report["panel_checks"]:
        p = report["panel_checks"]
        lines += [
            "",
            "## Panel Candidate Checks",
            f"- Unit key: `{p['unit']}`",
            f"- Time key: `{p['time']}`",
            f"- Units: {p['n_units']}",
            f"- Periods: {p['n_periods']}",
            f"- Duplicate unit-time rows: {p['duplicate_unit_time_rows']}",
            f"- Rows missing unit or time: {p['missing_unit_or_time_rows']}",
            f"- Observed/expected unit-time cells: {p['observed_grid_cells']}/{p['expected_grid_cells']}",
            f"- Periods per unit: min {p['min_periods_per_unit']}, median {p['median_periods_per_unit']}, max {p['max_periods_per_unit']}",
            f"- Complete rectangular unit-time grid: {p['complete_unit_time_grid']}",
        ]
    lines += ["", "## Column Profile"]
    for p in report["columns_profile"]:
        pct_val = p.get("missing_pct")
        pct_str = f"{pct_val:.1%}" if pct_val is not None else "0.0%"
        base = f"- `{p['name']}` ({p['dtype']}): missing {p['missing']} ({pct_str}), unique {p['unique']}"
        if "mean" in p and p["mean"] is not None:
            def fmt(value):
                return "n/a" if value is None or pd.isna(value) else f"{value:.4g}"

            base += (
                f", mean {fmt(p.get('mean'))}, sd {fmt(p.get('std'))}, "
                f"min {fmt(p.get('min'))}, max {fmt(p.get('max'))}"
            )
        lines.append(base)
    lines += ["", "## Top Numeric Correlations"]
    for pair in report["top_correlations"] or [{"var1": "n/a", "var2": "n/a", "corr": "n/a"}]:
        if pair["var1"] == "n/a":
            lines.append("- Not enough numeric columns.")
        else:
            lines.append(f"- `{pair['var1']}` vs `{pair['var2']}`: {pair['corr']:.3f}")
    lines += [
        "",
        "## Econometric Next Step",
        "- Build a variable dictionary with economic role, unit, timing, transformation, and measurement risk.",
        "- Map the pathway from treatment/main regressor to outcome before interpreting correlations.",
        "- Confirm model-ready sample, fixed effects, clustering, and identifying variation before regression.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Profile a CSV/XLSX/DTA dataset for econometric research planning.")
    parser.add_argument("data_file")
    parser.add_argument("--sheet")
    parser.add_argument(
        "--roles-json",
        help=(
            "JSON such as {'unit':'firm_id','time':'year','outcome':'y',"
            "'treatment':'policy','controls':['size','age']}."
        ),
    )
    parser.add_argument("--out", required=True, help="Markdown report path.")
    parser.add_argument("--json-out", help="Optional JSON report path.")
    args = parser.parse_args()

    path = Path(args.data_file)
    df = read_data(path, sheet=args.sheet)
    roles = load_roles(args.roles_json)
    report = build_report(path, df, roles)
    Path(args.out).write_text(markdown_report(report), encoding="utf-8")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
