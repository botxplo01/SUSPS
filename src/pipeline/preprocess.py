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


def preprocess_traffic() -> Path:
    ensure_dirs()
    src = RAW_DIR / "traffic_flows.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Peak indicator and bus pax per hour (rough proxy)
    df["is_peak"] = df["hour"].isin([7, 8, 9, 16, 17, 18]).astype(int)
    df["bus_pax_per_hour"] = (df["veh_per_hour"] * df["mode_share_bus"] * 40).round(1)
    out = PROCESSED_DIR / "traffic_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_environment() -> Path:
    ensure_dirs()
    src = RAW_DIR / "environment_monthly.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Cooling/heating degree day style simple metrics
    base = 22
    df["cooling_deg"] = (df["temp_c"] - base).clip(lower=0)
    df["wet_month"] = (df["rain_mm"] >= 100).astype(int)
    out = PROCESSED_DIR / "environment_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_socioeconomic() -> Path:
    ensure_dirs()
    src = RAW_DIR / "socioeconomic.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Normalize income and simple employment score
    df["income_norm"] = (df["income_usd"] - df["income_usd"].min()) / (
        df["income_usd"].max() - df["income_usd"].min()
    )
    df["employment_score"] = (df["employment_rate"] * 100).round(1)
    out = PROCESSED_DIR / "socioeconomic_features.csv"
    df.to_csv(out, index=False)
    return out


def main() -> None:
    wp = preprocess_worldpop()
    en = preprocess_energy()
    tf = preprocess_traffic()
    env = preprocess_environment()
    se = preprocess_socioeconomic()
    print(f"Saved: {wp}")
    print(f"Saved: {en}")
    print(f"Saved: {tf}")
    print(f"Saved: {env}")
    print(f"Saved: {se}")


if __name__ == "__main__":
    main()
