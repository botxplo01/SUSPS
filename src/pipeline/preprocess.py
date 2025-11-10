from __future__ import annotations

from pathlib import Path
import pandas as pd

from . import config


def preprocess_worldpop() -> Path:
    config.ensure_dirs()
    src = config.RAW_DIR / "worldpop_summary.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Simple normalization: share of total population
    total = df["population"].sum()
    df["pop_share"] = df["population"] / total
    out = config.PROCESSED_DIR / "worldpop_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_energy() -> Path:
    config.ensure_dirs()
    src = config.RAW_DIR / "energy_demand.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Feature: percentage of sector demand
    total = df["demand_mwh"].sum()
    df["pct"] = (df["demand_mwh"] / total).round(4)
    out = config.PROCESSED_DIR / "energy_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_traffic() -> Path:
    config.ensure_dirs()
    src = config.RAW_DIR / "traffic_flows.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Peak indicator and bus pax per hour (rough proxy)
    df["is_peak"] = df["hour"].isin([7, 8, 9, 16, 17, 18]).astype(int)
    df["bus_pax_per_hour"] = (df["veh_per_hour"] * df["mode_share_bus"] * 40).round(1)
    out = config.PROCESSED_DIR / "traffic_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_environment() -> Path:
    config.ensure_dirs()
    src = config.RAW_DIR / "environment_monthly.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Cooling/heating degree day style simple metrics
    base = 22
    df["cooling_deg"] = (df["temp_c"] - base).clip(lower=0)
    df["wet_month"] = (df["rain_mm"] >= 100).astype(int)
    out = config.PROCESSED_DIR / "environment_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_air_quality() -> Path:
    """Create daily AQ means for pm25, pm10, o3 from raw OpenAQ (or fallback CSV)."""
    config.ensure_dirs()
    # Prefer API-fetched raw
    aqi = config.RAW_DIR / "air_quality_raw.csv"
    if not aqi.exists():
        # fallback to provided raw CSV name if present
        aqi = config.RAW_DIR / "Air_Quality_Data_2025.csv"
        if not aqi.exists():
            raise FileNotFoundError(f"Missing raw input: {aqi}")
    df = pd.read_csv(aqi)
    # Try to harmonize columns
    cols = {c.lower(): c for c in df.columns}
    if "datetime" in cols and "parameter" in cols and "value" in cols:
        # OpenAQ shape
        d = df.rename(
            columns={
                cols["datetime"]: "datetime",
                cols["parameter"]: "parameter",
                cols["value"]: "value",
            }
        ).copy()
        d["datetime"] = pd.to_datetime(d["datetime"], errors="coerce")
        d.dropna(subset=["datetime", "parameter", "value"], inplace=True)
        d["date"] = d["datetime"].dt.date
        daily = (
            d.groupby(["date", "parameter"])["value"]  # type: ignore
            .mean()
            .reset_index()
        )
        out_df = daily.pivot(
            index="date", columns="parameter", values="value"
        ).reset_index()
    else:
        # Attempt to coerce a generic CSV with date + pollutant columns
        # Find a date-like column
        date_col = None
        for c in df.columns:
            if "date" in c.lower():
                date_col = c
                break
        if date_col is None:
            raise ValueError("Could not find date/datetime columns for air quality")
        d = df.rename(columns={date_col: "date"}).copy()
        d["date"] = pd.to_datetime(d["date"], errors="coerce").dt.date
        # Keep common pollutant names if present
        keep = [c for c in d.columns if c.lower() in {"pm25", "pm10", "o3"}]
        if not keep:
            # if values are in a single column, just provide pm25 as proxy
            valcol = None
            for c in d.columns:
                if pd.api.types.is_numeric_dtype(d[c]):
                    valcol = c
                    break
            if valcol is None:
                raise ValueError("No numeric AQ columns found")
            d = d[["date", valcol]].rename(columns={valcol: "pm25"})
        else:
            d = d[["date", *keep]].copy()
        out_df = d.groupby("date").mean(numeric_only=True).reset_index()
    out = config.PROCESSED_DIR / "air_quality_daily.csv"
    out_df.to_csv(out, index=False)
    return out


def preprocess_socioeconomic() -> Path:
    config.ensure_dirs()
    src = config.RAW_DIR / "socioeconomic.csv"
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)
    # Normalize income and simple employment score
    df["income_norm"] = (df["income_usd"] - df["income_usd"].min()) / (
        df["income_usd"].max() - df["income_usd"].min()
    )
    df["employment_score"] = (df["employment_rate"] * 100).round(1)
    out = config.PROCESSED_DIR / "socioeconomic_features.csv"
    df.to_csv(out, index=False)
    return out


def main() -> None:
    wp = preprocess_worldpop()
    en = preprocess_energy()
    tf = preprocess_traffic()
    env = preprocess_environment()
    aq = None
    # Only preprocess air quality if a raw input exists
    if (config.RAW_DIR / "air_quality_raw.csv").exists() or (
        config.RAW_DIR / "Air_Quality_Data_2025.csv"
    ).exists():
        aq = preprocess_air_quality()
    se = preprocess_socioeconomic()
    print(f"Saved: {wp}")
    print(f"Saved: {en}")
    print(f"Saved: {tf}")
    print(f"Saved: {env}")
    if aq:
        print(f"Saved: {aq}")
    print(f"Saved: {se}")


if __name__ == "__main__":
    main()
