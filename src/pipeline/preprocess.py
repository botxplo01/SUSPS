from __future__ import annotations

from pathlib import Path
import pandas as pd

from . import config


def preprocess_census() -> Path:
    """Create a tidy census trend table: year, total_population, annual_rate.

    Uses CENSUS_TOTAL_PATH and POP_ANNUAL_CHANGE_PATH if available.
    If only totals are available, computes annual_rate from consecutive years.
    """
    config.ensure_dirs()
    totals = getattr(config, "CENSUS_PATH", None)
    changes = getattr(config, "POP_ANNUAL_CHANGE_PATH", None)
    if not totals or not Path(totals).exists():
        raise FileNotFoundError(
            "Missing census totals file (CENSUS_PATH / CENSUS_TOTAL_PATH)"
        )

    df_tot = pd.read_csv(Path(totals))
    # Normalize columns
    df_tot.columns = [str(c).strip().lower() for c in df_tot.columns]
    # Try to identify year and population columns
    year_col = next((c for c in df_tot.columns if c in {"year", "yr"}), None)
    pop_col = next(
        (
            c
            for c in df_tot.columns
            if any(k in c for k in ["total_population", "population", "total", "pop"])
            and pd.api.types.is_numeric_dtype(df_tot[c])
        ),
        None,
    )
    if not year_col or not pop_col:
        raise ValueError(
            "Could not identify year and population columns in census totals"
        )

    df_tot = df_tot[[year_col, pop_col]].rename(
        columns={year_col: "year", pop_col: "total_population"}
    )
    df_tot = df_tot.dropna(subset=["year", "total_population"]).copy()
    df_tot["year"] = df_tot["year"].astype(int)
    df_tot = df_tot.sort_values("year").reset_index(drop=True)

    # Optional: changes file
    rate_from_changes = None
    if changes and Path(changes).exists():
        df_ch = pd.read_csv(Path(changes))
        df_ch.columns = [str(c).strip().lower() for c in df_ch.columns]
        ycol = next((c for c in df_ch.columns if c in {"year", "yr"}), None)
        rcol = next(
            (
                c
                for c in df_ch.columns
                if any(k in c for k in ["rate", "annual", "%"])
                and pd.api.types.is_numeric_dtype(df_ch[c])
            ),
            None,
        )
        if ycol and rcol:
            df_ch = df_ch[[ycol, rcol]].rename(
                columns={ycol: "year", rcol: "annual_rate"}
            )
            # normalize percentage if likely
            if df_ch["annual_rate"].abs().max() > 1.0:
                df_ch["annual_rate"] = df_ch["annual_rate"].astype(float) / 100.0
            rate_from_changes = df_ch

    # Merge or compute rates
    out = df_tot.copy()
    if rate_from_changes is not None:
        out = out.merge(rate_from_changes, on="year", how="left")
    if "annual_rate" not in out.columns or out["annual_rate"].isna().all():
        # compute from consecutive totals
        out = out.sort_values("year").copy()
        out["annual_rate"] = out["total_population"].pct_change()

    # Clean
    out["annual_rate"] = (
        out["annual_rate"]
        .fillna(method="ffill")
        .fillna(method="bfill")
        .fillna(0.02)
        .clip(-0.1, 0.2)
    )

    out_path = config.PROCESSED_DIR / "census_trend.csv"
    out.to_csv(out_path, index=False)
    return out_path


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
    # Census is optional based on provided raw files
    cen = None
    try:
        cen = preprocess_census()
    except Exception:
        cen = None
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
    if cen:
        print(f"Saved: {cen}")
    if aq:
        print(f"Saved: {aq}")
    print(f"Saved: {se}")


if __name__ == "__main__":
    main()
