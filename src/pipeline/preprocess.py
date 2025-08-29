from __future__ import annotations

from pathlib import Path
import pandas as pd

from .config import RAW_DIR, PROCESSED_DIR, ensure_dirs


def preprocess_worldpop() -> Path:
    ensure_dirs()
    src = RAW_DIR / "worldpop_summary.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Simple normalization: share of total population
    total = df["population"].sum()
    df["pop_share"] = df["population"] / total
    out = PROCESSED_DIR / "worldpop_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_energy() -> Path:
    ensure_dirs()
    src = RAW_DIR / "energy_demand.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Feature: percentage of sector demand
    total = df["demand_mwh"].sum()
    df["pct"] = (df["demand_mwh"] / total).round(4)
    out = PROCESSED_DIR / "energy_features.csv"
    df.to_csv(out, index=False)
    return out


def main() -> None:
    wp = preprocess_worldpop()
    en = preprocess_energy()
    print(f"Saved: {wp}")
    print(f"Saved: {en}")


if __name__ == "__main__":
    main()
