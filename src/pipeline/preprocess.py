"""Preprocessing steps that turn raw ingested files into canonical features.

Functions here read data/<CITY>/raw/ artifacts, derive lightweight features for
growth, energy, traffic, environment, air quality, hotspots, and rasters, and
write them under data/<CITY>/processed/.
"""

from __future__ import annotations

from pathlib import Path
import os
import re
import zipfile
import pandas as pd

# Support both `python -m src.pipeline.preprocess` (preferred) and direct
# script invocation like `python src/pipeline/preprocess.py`.
try:  # pragma: no cover - normal path when run as a module
    from . import config
except ImportError:  # pragma: no cover - fallback for script usage
    import sys
    from pathlib import Path as _Path

    ROOT = _Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.pipeline import config


# Common raw search order: flat RAW_DIR first (backwards compat), then
# domain-specific subfolders when present. This is computed dynamically so
# monkeypatching RAW_DIR in tests (or changing DATA_CITY) continues to work.


def _raw_search_dirs() -> list[Path]:
    dirs: list[Path] = []
    try:
        # Ensure domain directories reflect the current RAW_DIR
        config.ensure_dirs()
    except Exception:
        pass
    dirs.append(config.RAW_DIR)
    dirs.append(
        getattr(
            config,
            "DEMOGRAPHICS_RAW_DIR",
            config.RAW_DIR / "Demographics_and_Population",
        )
    )
    dirs.append(
        getattr(
            config,
            "ENERGY_RAW_DIR",
            config.RAW_DIR / "Energy_and_Infrastructure",
        )
    )
    dirs.append(
        getattr(
            config,
            "ENVIRONMENT_RAW_DIR",
            config.RAW_DIR / "Environmental_and_Climate",
        )
    )
    dirs.append(
        getattr(
            config,
            "MOBILITY_RAW_DIR",
            config.RAW_DIR / "Mobility_and_Transport",
        )
    )
    return dirs


def _find_raw_file(filename: str) -> Path:
    """Locate a raw file by name across RAW_DIR and domain-specific folders.

    This keeps preprocess tolerant of both the legacy flat layout and the
    newer domain-scoped raw layout. The returned Path may not exist; caller
    should still assert existence and raise a helpful error if needed.
    """

    for d in _raw_search_dirs():
        p = Path(d) / filename
        if p.exists():
            return p
    # Default path for error messages
    return Path(config.RAW_DIR / filename)


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


def preprocess_growth_forecast(horizon_years: int = 6) -> Path:
    """Produce a city-level growth forecast CSV from census_trend.csv.

    Output: growth_forecast_city.csv with columns: year, predicted_population, scenario
    """
    config.ensure_dirs()
    cens = config.PROCESSED_DIR / "census_trend.csv"
    if not cens.exists():
        raise FileNotFoundError(
            "census_trend.csv not found; run preprocess_census first"
        )
    df = pd.read_csv(cens).sort_values("year")
    base_year = int(df["year"].iloc[-1])
    base_pop = float(df["total_population"].iloc[-1])
    rate_series = df.get("annual_rate")
    if rate_series is None or rate_series.isna().all():
        rate_series = df["total_population"].pct_change()
    recent = rate_series.dropna().tail(3)
    r = float(recent.mean()) if len(recent) else 0.03
    r = max(min(r, 0.08), -0.02)
    rows = []
    pop = base_pop
    for i in range(1, horizon_years + 1):
        year = base_year + i
        pop = pop * (1.0 + r)
        rows.append(
            {"year": year, "predicted_population": int(pop), "scenario": "base"}
        )
    out = config.PROCESSED_DIR / "growth_forecast_city.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    return out


def preprocess_worldpop() -> Path:
    config.ensure_dirs()
    src = _find_raw_file("worldpop_summary.csv")
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
    src = _find_raw_file("energy_demand.csv")
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
    src = _find_raw_file("traffic_flows.csv")
    if not src.exists():
        raise FileNotFoundError(f"Missing raw input: {src}")
    df = pd.read_csv(src)

    # If the raw TomTom or placeholder data is essentially flat (e.g. 600 veh/h
    # at every hour), derive a more realistic canonical 24h profile from the
    # synthetic traffic model and apply it per hour. This keeps REAL-mode
    # traffic charts informative even when the upstream provider returns a
    # degenerate series.
    try:
        if "veh_per_hour" in df.columns and "hour" in df.columns:
            vals = df["veh_per_hour"].astype(float)
            # Treat as degenerate when there is effectively a single level and
            # almost no variation across the day.
            if vals.nunique() <= 3 and vals.std() < 50:
                from src.models.traffic import daily_profile as _traffic_profile  # type: ignore

                profile = {int(p["hour"]): int(p["volume"]) for p in _traffic_profile()}
                df["veh_per_hour"] = df["hour"].astype(int).map(
                    lambda h: profile.get(h, profile.get(0, int(vals.iloc[0])))
                )
    except Exception:
        # Never let this heuristic break the pipeline; fall back to the raw
        # series if anything goes wrong.
        pass

    # Peak indicator and bus pax per hour (rough proxy)
    df["is_peak"] = df["hour"].isin([7, 8, 9, 16, 17, 18]).astype(int)
    df["bus_pax_per_hour"] = (df["veh_per_hour"] * df["mode_share_bus"] * 40).round(1)
    out = config.PROCESSED_DIR / "traffic_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_environment() -> Path:
    config.ensure_dirs()
    src = _find_raw_file("environment_monthly.csv")
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


def preprocess_environment_aq() -> Path:
    """Combine environment and air-quality features into a single monthly table.

    This function is intentionally lightweight and tolerant of missing inputs.
    It joins `environment_features.csv` with `air_quality_daily.csv` on month
    (derived from the date column), computes monthly mean PM2.5/PM10/O3, and
    derives a simple pollution_index (0..1 based on PM2.5).
    """

    config.ensure_dirs()
    env_path = config.PROCESSED_DIR / "environment_features.csv"
    aq_path = config.PROCESSED_DIR / "air_quality_daily.csv"
    if not env_path.exists() or not aq_path.exists():
        raise FileNotFoundError(
            "preprocess_environment_aq requires environment_features.csv and "
            "air_quality_daily.csv; run preprocess_environment and "
            "preprocess_air_quality first."
        )

    env_df = pd.read_csv(env_path)
    aq_df = pd.read_csv(aq_path)

    if "month" not in env_df.columns:
        raise ValueError("environment_features.csv must contain a month column")

    # Derive month from date and aggregate pollutants to monthly means.
    if "date" not in aq_df.columns:
        raise ValueError("air_quality_daily.csv must contain a date column")
    aq_df["date"] = pd.to_datetime(aq_df["date"], errors="coerce")
    aq_df["month"] = aq_df["date"].dt.month
    monthly = (
        aq_df.groupby("month")[[c for c in aq_df.columns if c.lower() in {"pm25", "pm10", "o3"}]]
        .mean(numeric_only=True)
        .reset_index()
    )

    merged = env_df.merge(monthly, on="month", how="left")

    # Simple pollution index based on normalized PM2.5
    if "pm25" in merged.columns:
        max_pm = float(merged["pm25"].max() or 1.0)
        merged["pollution_index"] = (merged["pm25"] / max_pm).clip(0.0, 1.0)
    else:
        merged["pollution_index"] = 0.0

    out = config.PROCESSED_DIR / "environment_aq_features.csv"
    merged.to_csv(out, index=False)
    return out


def preprocess_air_quality() -> Path:
    """Create daily AQ means for pm25, pm10, o3 from raw OpenAQ (or fallback CSV)."""
    config.ensure_dirs()
    # Prefer API-fetched raw
    aqi = _find_raw_file("air_quality_raw.csv")
    if not aqi.exists():
        # fallback to provided raw CSV name if present
        aqi = _find_raw_file("Air_Quality_Data_2025.csv")
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
        # Attempt to coerce a generic CSV with date/time-like + pollutant columns
        # Find a date-like column (supports 'date', 'time', 'timestamp', 'month')
        date_col = None
        for c in df.columns:
            cl = c.lower()
            if any(tok in cl for tok in ["date", "time", "stamp", "month"]):
                date_col = c
                break
        if date_col is None:
            raise ValueError("Could not find date/datetime columns for air quality")

        d = df.rename(columns={date_col: "date"}).copy()
        d["date"] = pd.to_datetime(d["date"], errors="coerce").dt.date

        # Map pollutant-like columns to canonical pm25/pm10/o3 buckets. This
        # handles schemas like Air_Quality_Data_2025.csv where we have pm2_5,
        # s1_pm2_5, s2_pm2_5, etc.
        pollutant_map: dict[str, list[str]] = {}
        for c in d.columns:
            cl = c.lower()
            if c == "date":
                continue
            if (cl == "pm25") or ("pm2_5" in cl) or ("pm2.5" in cl):
                pollutant_map.setdefault("pm25", []).append(c)
            elif (cl == "pm10") or ("pm10" in cl):
                pollutant_map.setdefault("pm10", []).append(c)
            elif cl == "o3" or "ozone" in cl:
                pollutant_map.setdefault("o3", []).append(c)

        if pollutant_map:
            # Build a compact frame with averaged pollutant buckets
            out_rows = {"date": d["date"]}
            for key, cols_list in pollutant_map.items():
                # Robust against missing/NaN values
                out_rows[key] = d[cols_list].mean(axis=1)
            d2 = pd.DataFrame(out_rows)
            out_df = d2.groupby("date").mean(numeric_only=True).reset_index()
        else:
            # Fallback: choose a numeric column as pm25 proxy
            valcol = None
            for c in d.columns:
                if c == "date":
                    continue
                if pd.api.types.is_numeric_dtype(d[c]):
                    valcol = c
                    break
            if valcol is None:
                raise ValueError("No numeric AQ columns found")
            d2 = d[["date", valcol]].rename(columns={valcol: "pm25"})
            out_df = d2.groupby("date").mean(numeric_only=True).reset_index()
    out = config.PROCESSED_DIR / "air_quality_daily.csv"
    out_df.to_csv(out, index=False)
    return out


def preprocess_socioeconomic() -> Path:
    config.ensure_dirs()
    src = _find_raw_file("socioeconomic.csv")
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


def preprocess_demographic_rasters() -> Path:
    """Summarize demographic raster TIFFs under Demographics_and_Population.

    Uses rasterio if available for basic statistics; otherwise records file
    metadata only. This ensures population rasters are incorporated into the
    processed layer even in lightweight environments.
    """

    config.ensure_dirs()
    root = getattr(
        config,
        "DEMOGRAPHICS_RAW_DIR",
        config.RAW_DIR / "Demographics_and_Population",
    )
    root_path = Path(root)

    try:  # optional dependency
        import rasterio  # type: ignore

        has_rasterio = True
    except Exception:
        has_rasterio = False

    rows: list[dict] = []
    for p in root_path.glob("*.tif"):
        entry: dict = {
            "name": p.name,
            "path": str(p),
            "bytes": p.stat().st_size,
        }
        if has_rasterio:
            try:
                with rasterio.open(p) as src:  # type: ignore[attr-defined]
                    band = src.read(1, masked=True)
                    data = band.compressed()
                    if data.size:
                        entry["min"] = float(data.min())
                        entry["max"] = float(data.max())
                        entry["mean"] = float(data.mean())
                        entry["sum"] = float(data.sum())
                        entry["count"] = int(data.size)
                    entry["crs"] = str(src.crs) if src.crs is not None else None
                    entry["width"] = src.width
                    entry["height"] = src.height
                    try:
                        rx, ry = src.res
                        entry["res_x"] = float(rx)
                        entry["res_y"] = float(ry)
                    except Exception:
                        pass
            except Exception:
                # Fall back to metadata-only entry on any raster read error
                pass
        rows.append(entry)

    df = pd.DataFrame(rows)
    out = config.PROCESSED_DIR / "demographic_raster_summary.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_landcover() -> Path:
    """Summarize land-cover raster TIFFs under Environmental_and_Climate."""

    config.ensure_dirs()
    root = getattr(
        config,
        "ENVIRONMENT_RAW_DIR",
        config.RAW_DIR / "Environmental_and_Climate",
    )
    root_path = Path(root)

    try:  # optional dependency
        import rasterio  # type: ignore

        has_rasterio = True
    except Exception:
        has_rasterio = False

    rows: list[dict] = []
    for p in root_path.glob("*.tif"):
        entry: dict = {
            "name": p.name,
            "path": str(p),
            "bytes": p.stat().st_size,
        }
        if has_rasterio:
            try:
                with rasterio.open(p) as src:  # type: ignore[attr-defined]
                    band = src.read(1, masked=True)
                    data = band.compressed()
                    if data.size:
                        entry["min"] = float(data.min())
                        entry["max"] = float(data.max())
                        entry["mean"] = float(data.mean())
                        entry["sum"] = float(data.sum())
                        entry["count"] = int(data.size)
                    entry["crs"] = str(src.crs) if src.crs is not None else None
                    entry["width"] = src.width
                    entry["height"] = src.height
                    try:
                        rx, ry = src.res
                        entry["res_x"] = float(rx)
                        entry["res_y"] = float(ry)
                    except Exception:
                        pass
            except Exception:
                # Fall back to metadata-only entry on any raster read error
                pass
        rows.append(entry)

    df = pd.DataFrame(rows)
    out = config.PROCESSED_DIR / "landcover_raster_summary.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_mobility_gis() -> Path:
    """Summarize GIS layers from GIS_DATA_2019.zip under Mobility_and_Transport.

    Uses geopandas if available to count features per layer; otherwise records
    basic layer metadata from the ZIP archive only.
    """

    config.ensure_dirs()
    root = getattr(
        config,
        "MOBILITY_RAW_DIR",
        config.RAW_DIR / "Mobility_and_Transport",
    )
    zip_path = Path(root) / "GIS_DATA_2019.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Missing raw input: {zip_path}")

    try:  # optional dependency
        import geopandas as gpd  # type: ignore

        has_gpd = True
    except Exception:
        has_gpd = False

    rows: list[dict] = []
    with zipfile.ZipFile(zip_path) as zf:
        for zi in zf.infolist():
            if not zi.filename.lower().endswith(".shp"):
                continue
            entry: dict = {
                "layer": Path(zi.filename).stem,
                "filename": zi.filename,
                "bytes": zi.file_size,
            }
            if has_gpd:
                try:
                    layer_path = f"zip://{zip_path}!{zi.filename}"
                    gdf = gpd.read_file(layer_path)
                    entry["records"] = int(len(gdf))
                    if gdf.crs is not None:
                        entry["crs"] = str(gdf.crs)
                    if not gdf.geom_type.empty:
                        try:
                            entry["geometry_type"] = str(gdf.geom_type.mode().iat[0])
                        except Exception:
                            pass
                except Exception:
                    # Keep metadata-only entry on any read failure
                    pass
            rows.append(entry)

    df = pd.DataFrame(rows)
    out = config.PROCESSED_DIR / "mobility_gis_layers.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_hotspots() -> Path:
    """Compute simple area-level hotspots from processed features.

    This is a deterministic, resource-efficient hotspot score built from
    existing processed tables (worldpop_features and socioeconomic_features).
    It does not require any external APIs or ML models and is suitable for
    driving map overlays (by joining on admin_unit in a separate GeoJSON).

    Output: hotspots_areas.csv with columns:
      - admin_unit
      - population
      - pop_share
      - income_norm
      - employment_score
      - hotspot_score (0..1, higher = more pressure/vulnerability)
    """

    config.ensure_dirs()
    wp = config.PROCESSED_DIR / "worldpop_features.csv"
    se = config.PROCESSED_DIR / "socioeconomic_features.csv"
    if not wp.exists() or not se.exists():
        raise FileNotFoundError(
            "hotspot preprocessing requires worldpop_features.csv and "
            "socioeconomic_features.csv; run preprocess_worldpop and "
            "preprocess_socioeconomic first."
        )

    df_wp = pd.read_csv(wp)
    df_se = pd.read_csv(se)

    if "admin_unit" not in df_wp.columns:
        raise ValueError("worldpop_features.csv must contain admin_unit column")
    if "admin_unit" not in df_se.columns:
        raise ValueError("socioeconomic_features.csv must contain admin_unit column")

    df = df_wp.merge(df_se, on="admin_unit", how="left")

    # Defaults for missing socio-economic values
    if "income_norm" not in df.columns:
        df["income_norm"] = 0.5
    df["income_norm"] = df["income_norm"].fillna(0.5).clip(0.0, 1.0)

    emp_score = df.get("employment_score")
    if emp_score is None:
        df["employment_score"] = 50.0
    df["employment_score"] = df["employment_score"].fillna(50.0).clip(0.0, 100.0)
    df["employment_norm"] = df["employment_score"] / 100.0

    # Vulnerability: high when income is low and employment is low
    df["vulnerability"] = (1.0 - df["income_norm"]) * (1.0 - df["employment_norm"])

    # Base pressure from population share (already sums to ~1 across units)
    df["pop_share"] = df["pop_share"].fillna(0.0)

    # Combine into a hotspot score and normalize to 0..1
    df["raw_score"] = df["pop_share"] * (0.5 + df["vulnerability"])
    max_score = df["raw_score"].max() or 1.0
    df["hotspot_score"] = (df["raw_score"] / max_score).clip(0.0, 1.0)

    out_cols = [
        c
        for c in [
            "admin_unit",
            "population",
            "pop_share",
            "income_norm",
            "employment_score",
            "hotspot_score",
        ]
        if c in df.columns
    ]
    out_df = df[out_cols].copy() if out_cols else df.copy()
    out_df = out_df.sort_values("hotspot_score", ascending=False)

    out = config.PROCESSED_DIR / "hotspots_areas.csv"
    out_df.to_csv(out, index=False)
    return out


def preprocess_hotspots_forecast(horizon_years: int = 6) -> Path:
    """Forecast area-level hotspots over multiple years.

    This uses deterministic, vulnerability-weighted growth at area level
    combined with a city-level population forecast. It does not depend on
    external APIs or paid models and is suitable for driving time-forward
    hotspot maps.

    Output: hotspots_areas_forecast.csv with columns including:
      - year
      - admin_unit
      - population
      - pop_share
      - income_norm
      - employment_score
      - hotspot_score
    """

    config.ensure_dirs()
    base_path = config.PROCESSED_DIR / "hotspots_areas.csv"
    if not base_path.exists():
        raise FileNotFoundError(
            "hotspots_areas.csv not found; run preprocess_hotspots first"
        )

    df_base = pd.read_csv(base_path)
    if "population" not in df_base.columns or "pop_share" not in df_base.columns:
        raise ValueError(
            "hotspots_areas.csv must contain population and pop_share columns"
        )

    # Reconstruct vulnerability used in preprocess_hotspots
    if "income_norm" not in df_base.columns:
        df_base["income_norm"] = 0.5
    df_base["income_norm"] = df_base["income_norm"].fillna(0.5).clip(0.0, 1.0)

    emp_score = df_base.get("employment_score")
    if emp_score is None:
        df_base["employment_score"] = 50.0
    df_base["employment_score"] = (
        df_base["employment_score"].fillna(50.0).clip(0.0, 100.0)
    )
    df_base["employment_norm"] = df_base["employment_score"] / 100.0

    df_base["vulnerability"] = (1.0 - df_base["income_norm"]) * (
        1.0 - df_base["employment_norm"]
    )

    # Derive vulnerability-normalized growth weights per area
    vmin = float(df_base["vulnerability"].min())
    vmax = float(df_base["vulnerability"].max())
    if vmax > vmin:
        v_norm = (df_base["vulnerability"] - vmin) / (vmax - vmin)
    else:
        v_norm = 0.5
    beta = 0.4  # sensitivity of growth to vulnerability
    df_base["growth_weight"] = (1.0 + beta * (v_norm - 0.5)).clip(lower=0.5)

    base_total_pop = float(df_base["population"].sum()) or 1.0

    # Obtain city-level population forecast
    future_years: list[tuple[int, float]] = []
    gfc_path = config.PROCESSED_DIR / "growth_forecast_city.csv"
    if gfc_path.exists():
        df_gfc = pd.read_csv(gfc_path).sort_values("year")
        for _, r in df_gfc.iterrows():
            year = int(r["year"])
            val = float(r["predicted_population"])
            if val > 0:
                future_years.append((year, val))

    if not future_years:
        # Fallback: derive from census_trend if available
        ct_path = config.PROCESSED_DIR / "census_trend.csv"
        if ct_path.exists():
            df_ct = pd.read_csv(ct_path).sort_values("year")
            base_year = int(df_ct["year"].iloc[-1])
            base_pop_ct = float(df_ct["total_population"].iloc[-1])
            rate_series = df_ct.get("annual_rate")
            if rate_series is None or rate_series.isna().all():
                rate_series = df_ct["total_population"].pct_change()
            recent = rate_series.dropna().tail(3)
            r = float(recent.mean()) if len(recent) else 0.03
            r = max(min(r, 0.08), -0.02)
            pop_ct = base_pop_ct
            for i in range(1, horizon_years + 1):
                year = base_year + i
                pop_ct = pop_ct * (1.0 + r)
                future_years.append((year, pop_ct))
        else:
            # Last-resort: constant city population over horizon
            base_year = 2025
            for i in range(1, horizon_years + 1):
                future_years.append((base_year + i, base_total_pop))

    rows = []
    # If growth_forecast_city.csv exists, preserve its horizon length
    for step, (year, city_pop) in enumerate(future_years, start=1):
        df_year = df_base.copy()
        df_year["year"] = year
        df_year["population_future_raw"] = df_year["population"].fillna(0.0) * (
            df_year["growth_weight"] ** step
        )
        total_raw = float(df_year["population_future_raw"].sum()) or 1.0
        scale = float(city_pop) / total_raw if total_raw > 0 else 1.0
        df_year["population"] = df_year["population_future_raw"] * scale
        df_year["pop_share"] = df_year["population"] / max(float(city_pop), 1.0)

        # Recompute hotspot score for this year
        df_year["raw_score"] = df_year["pop_share"] * (0.5 + df_year["vulnerability"])
        max_score = float(df_year["raw_score"].max()) or 1.0
        df_year["hotspot_score"] = (df_year["raw_score"] / max_score).clip(0.0, 1.0)

        out_cols = [
            c
            for c in [
                "year",
                "admin_unit",
                "population",
                "pop_share",
                "income_norm",
                "employment_score",
                "hotspot_score",
            ]
            if c in df_year.columns
        ]
        rows.append(df_year[out_cols])

    if not rows:
        raise ValueError("No forecast rows produced for hotspots")

    out_df = pd.concat(rows, ignore_index=True)
    out = config.PROCESSED_DIR / "hotspots_areas_forecast.csv"
    out_df.to_csv(out, index=False)
    return out


def preprocess_traffic_enriched() -> Path:
    """Enrich traffic_features.csv with MATATUS/OSM-derived context.

    This is deliberately conservative: it augments each row in
    `traffic_features.csv` with city-level indicators where available,
    without making strong assumptions about MATATUS/OSM schema.
    """

    config.ensure_dirs()
    base_path = config.PROCESSED_DIR / "traffic_features.csv"
    if not base_path.exists():
        raise FileNotFoundError(f"Missing processed input: {base_path}")

    df = pd.read_csv(base_path)

    # MATATUS_PATH: count records (or unique route id) as a simple intensity
    matatus_count = None
    mat_path = getattr(config, "MATATUS_PATH", None)
    if mat_path is not None and Path(mat_path).exists():
        try:
            mdf = pd.read_csv(mat_path)
            route_col = next(
                (c for c in mdf.columns if "route" in str(c).lower()),
                None,
            )
            if route_col:
                matatus_count = int(mdf[route_col].nunique())
            else:
                matatus_count = int(len(mdf))
        except Exception:
            matatus_count = None

    # OSM_PATH: if a vector file is provided and geopandas is available, count
    # features and approximate total length (if geometry is present).
    osm_feature_count = None
    osm_total_km = None
    osm_path = getattr(config, "OSM_PATH", None)
    if osm_path is not None and Path(osm_path).exists():
        try:
            import geopandas as gpd  # type: ignore

            gdf = gpd.read_file(osm_path)
            osm_feature_count = int(len(gdf))
            # If projected CRS, approximate length in km; otherwise skip length.
            if gdf.crs is not None and not gdf.crs.is_geographic:
                with pd.option_context("mode.use_inf_as_na", True):
                    total_area = float(gdf.geometry.length.sum())
                    osm_total_km = total_area / 1000.0
        except Exception:
            osm_feature_count = None
            osm_total_km = None

    if matatus_count is not None:
        df["matatu_route_count"] = matatus_count
    else:
        df["matatu_route_count"] = None

    df["osm_feature_count"] = osm_feature_count
    df["osm_total_km"] = osm_total_km

    out = config.PROCESSED_DIR / "traffic_enriched_features.csv"
    df.to_csv(out, index=False)
    return out


def preprocess_urban_growth() -> tuple[Path, Path]:
    """Integrate Urban_Growth directory by producing a catalog and simple features.

    - Reads files under GRID3_SETTLEMENTS_PATH (or SETTLEMENTS_PATH) if available
    - For CSVs: counts records and tries to sum area if an area-like column is present
    - For SHP/GPKG: attempts geopandas if installed; otherwise catalogs only
    - Outputs:
      - urban_growth_catalog.csv: file metadata and basic info
      - urban_growth_features.csv: per-year summary of records (and area if derivable)
    """
    config.ensure_dirs()
    root = getattr(config, "SETTLEMENTS_PATH", None)
    if not root or not Path(root).exists():
        raise FileNotFoundError(
            "GRID3_SETTLEMENTS_PATH / SETTLEMENTS_PATH not configured or missing"
        )

    root_path = Path(root)
    rows = []
    feats = {}

    def parse_year(name: str) -> int | None:
        m = re.search(r"(20\d{2}|19\d{2})", name)
        return int(m.group(1)) if m else None

    # Optional geopandas
    try:
        import geopandas as gpd  # type: ignore

        has_gpd = True
    except Exception:
        has_gpd = False

    for p in root_path.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        year = parse_year(p.name)
        size = p.stat().st_size
        entry = {
            "path": str(p),
            "name": p.name,
            "ext": ext,
            "bytes": size,
            "year": year,
        }

        if ext == ".csv":
            try:
                df = pd.read_csv(p)
                entry["records"] = int(len(df))
                # area-like column
                area_col = next(
                    (
                        c
                        for c in df.columns
                        if re.search(r"area|km2|sqkm", str(c), re.I)
                    ),
                    None,
                )
                total_area = float(df[area_col].sum()) if area_col is not None else None
                if total_area is not None:
                    entry["area_km2"] = total_area
                    if year is not None:
                        feats.setdefault(year, {"records": 0, "area_km2": 0.0})
                        feats[year]["area_km2"] += total_area
                if year is not None:
                    feats.setdefault(
                        year,
                        {
                            "records": 0,
                            "area_km2": feats.get(year, {}).get("area_km2", 0.0),
                        },
                    )
                    feats[year]["records"] += int(len(df))
            except Exception:
                pass
        elif ext in {".shp", ".gpkg"}:
            if has_gpd:
                try:
                    gdf = gpd.read_file(p)
                    entry["records"] = int(len(gdf))
                    # approximate area in km2 if projected; else skip
                    area_km2 = None
                    if gdf.crs is not None and not gdf.crs.is_geographic:
                        with pd.option_context("mode.use_inf_as_na", True):
                            area_km2 = float((gdf.geometry.area.sum()) / 1_000_000.0)
                    entry["area_km2"] = area_km2
                    if year is not None:
                        feats.setdefault(year, {"records": 0, "area_km2": 0.0})
                        feats[year]["records"] += int(len(gdf))
                        if area_km2:
                            feats[year]["area_km2"] += area_km2
                except Exception:
                    pass
        rows.append(entry)

    # Write catalog
    catalog = pd.DataFrame(rows)
    cat_out = config.PROCESSED_DIR / "urban_growth_catalog.csv"
    catalog.to_csv(cat_out, index=False)

    # Write features summary
    if feats:
        years = sorted(feats.keys())
        feat_rows = [
            {
                "year": y,
                "records": feats[y]["records"],
                "area_km2": feats[y].get("area_km2"),
            }
            for y in years
        ]
        feats_df = pd.DataFrame(feat_rows)
    else:
        feats_df = pd.DataFrame(columns=["year", "records", "area_km2"])  # empty
    feat_out = config.PROCESSED_DIR / "urban_growth_features.csv"
    feats_df.to_csv(feat_out, index=False)

    return cat_out, feat_out


def main() -> None:
    wp = preprocess_worldpop()
    en = preprocess_energy()
    tf = preprocess_traffic()
    tf_enriched = None
    try:
        tf_enriched = preprocess_traffic_enriched()
    except Exception:
        tf_enriched = None

    demo_rasters = None
    try:
        demo_rasters = preprocess_demographic_rasters()
    except Exception:
        demo_rasters = None

    landcover = None
    try:
        landcover = preprocess_landcover()
    except Exception:
        landcover = None

    mobility_gis = None
    try:
        mobility_gis = preprocess_mobility_gis()
    except Exception:
        mobility_gis = None

    env = preprocess_environment()
    env_aq = None
    try:
        env_aq = preprocess_environment_aq()
    except Exception:
        env_aq = None
    # Census is optional based on provided raw files
    cen = None
    try:
        cen = preprocess_census()
    except Exception:
        cen = None
    # If census trend exists, generate city growth forecast
    gfc = None
    try:
        gfc = preprocess_growth_forecast()
    except Exception:
        gfc = None
    aq = None
    # Only preprocess air quality if a raw input exists (in any raw search dir)
    aq_raw = _find_raw_file("air_quality_raw.csv")
    aq_fallback = _find_raw_file("Air_Quality_Data_2025.csv")
    if aq_raw.exists() or aq_fallback.exists():
        aq = preprocess_air_quality()

    # Urban growth (optional, requires SETTLEMENTS_PATH / GRID3_SETTLEMENTS_PATH).
    # This step can be expensive when pointed at large settlement datasets, so it
    # is gated behind an environment flag and fully optional for tests and
    # lightweight local runs.
    ug = None
    run_ug_env = os.getenv("SUSPS_PREPROCESS_URBAN_GROWTH", "").strip().lower()
    if run_ug_env in {"1", "true", "yes", "on"}:
        try:
            ug_cat, ug_feat = preprocess_urban_growth()
            ug = (ug_cat, ug_feat)
        except Exception:
            ug = None

    se = preprocess_socioeconomic()
    # Hotspots depend on worldpop + socioeconomics; compute after both.
    hs = None
    try:
        hs = preprocess_hotspots()
    except Exception:
        hs = None

    hs_forecast = None
    try:
        hs_forecast = preprocess_hotspots_forecast()
    except Exception:
        hs_forecast = None

    print(f"Saved: {wp}")
    print(f"Saved: {en}")
    print(f"Saved: {tf}")
    if tf_enriched:
        print(f"Saved: {tf_enriched}")
    if demo_rasters:
        print(f"Saved: {demo_rasters}")
    if landcover:
        print(f"Saved: {landcover}")
    if mobility_gis:
        print(f"Saved: {mobility_gis}")
    print(f"Saved: {env}")
    if env_aq:
        print(f"Saved: {env_aq}")
    if cen:
        print(f"Saved: {cen}")
    if gfc:
        print(f"Saved: {gfc}")
    if aq:
        print(f"Saved: {aq}")
    if ug:
        print(f"Saved: {ug[0]}")
        print(f"Saved: {ug[1]}")
    print(f"Saved: {se}")
    if hs:
        print(f"Saved: {hs}")
    if hs_forecast:
        print(f"Saved: {hs_forecast}")


if __name__ == "__main__":
    main()
