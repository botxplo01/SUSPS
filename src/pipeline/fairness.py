from __future__ import annotations

from pathlib import Path
import pandas as pd

from . import config


def demographic_parity_gap(df: pd.DataFrame, group: str, score: str) -> float:
    """Absolute difference between group mean scores for a binary group.

    Example: group="urban" in {0,1}, score="income" or a model score.
    """
    values = sorted(df[group].dropna().unique().tolist())
    if len(values) != 2:
        raise ValueError("Expected exactly 2 unique group values for parity gap")
    g0, g1 = values
    m0 = df.loc[df[group] == g0, score].mean()
    m1 = df.loc[df[group] == g1, score].mean()
    return float(abs(m1 - m0))


def geographic_coverage(df: pd.DataFrame, region_col: str) -> float:
    """Share of regions represented at least once (0..1)."""
    total_regions = df[region_col].nunique(dropna=True)
    represented = df.dropna(subset=[region_col])[region_col].nunique()
    if total_regions == 0:
        return 0.0
    return float(represented / total_regions)


def run_audits(
    input_path: Path, group_col: str, score_col: str, region_col: str | None = None
) -> pd.DataFrame:
    """Run a minimal audit suite and return a one-row report."""
    df = pd.read_csv(input_path)

    report = {
        "input": input_path.name,
        "rows": len(df),
    }

    # Demographic parity gap if columns exist
    if group_col in df.columns and score_col in df.columns:
        try:
            report["demographic_parity_gap"] = demographic_parity_gap(
                df, group_col, score_col
            )
        except Exception as e:
            report["demographic_parity_gap"] = f"error: {e}"

    # Geographic coverage if requested
    if region_col and region_col in df.columns:
        try:
            report["geographic_coverage"] = geographic_coverage(df, region_col)
        except Exception as e:
            report["geographic_coverage"] = f"error: {e}"

    return pd.DataFrame([report])


def save_report(report: pd.DataFrame, name: str = "fairness_report.csv") -> Path:
    config.ensure_dirs()
    out = config.PROCESSED_DIR / name
    report.to_csv(out, index=False)
    return out


def main() -> None:
    # Example: audit synthetic demographics if available
    syn = config.PROCESSED_DIR / "synthetic_demographics.csv"
    if syn.exists():
        rep = run_audits(syn, group_col="urban", score_col="income")
        out = save_report(rep)
        print(f"Saved audit: {out}")
    else:
        print("No synthetic_demographics.csv found to audit.")


if __name__ == "__main__":
    main()
