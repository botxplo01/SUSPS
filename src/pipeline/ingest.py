# @author: Lameck David Musumpuka

"""Raw data ingestion utilities for the SUSPS pipeline.

This module fetches or synthesizes demographic, energy, traffic, climate, air
quality, and socio-economic inputs and writes them under data/<CITY>/raw/.
"""

from __future__ import annotations

from pathlib import Path
import time
import os
import pandas as pd
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional
import hashlib

from . import config
from .osm_overpass import fetch_osm_for_city_bbox, save_geojson

# --- Helpers ---


def _city_coords() -> tuple[float, float]:
    """Return city coordinates; defaults to Nairobi CBD if no env provided."""
    try:
        lat = float(os.getenv("CITY_LAT", "-1.286389"))
        lon = float(os.getenv("CITY_LON", "36.817223"))
    except Exception:
        lat, lon = -1.286389, 36.817223
    return lat, lon


def _safe_df(df: pd.DataFrame, fallback: pd.DataFrame) -> pd.DataFrame:
    try:
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            return df
    except Exception:
        pass
    return fallback


# --- Ingestors ---


def fetch_worldpop(
    country_code: str = config.Defaults.worldpop_country_code,
) -> pd.DataFrame:
    """Fetch a WorldPop-style population summary.

    The current implementation returns a small synthetic sample when no
    provider-specific integration is configured.
    """
    data = {
        "admin_unit": ["UnitA", "UnitB", "UnitC"],
        "population": [12000, 8000, 15000],
    }
    return pd.DataFrame(data)


def fetch_energy_demand(region: str = config.Defaults.region) -> pd.DataFrame:
    """Energy demand by sector from raw directory if available.

    If ENERGY_PATH/ENERGY_DIR points to a directory with multiple CSVs (for
    coverage, access, and use), this function attempts to aggregate all
    consumption-like columns into a single sector-level demand table. It
    looks for columns whose names suggest energy quantities (gwh, mwh,
    demand, consumption, energy, use, usage, value) and ignores purely
    categorical/coverage-only fields.

    When no suitable raw inputs are found, it returns a small synthetic
    dataset.
    """
    try:
        energy_dir = getattr(config, "ENERGY_PATH", None)
        if energy_dir and Path(energy_dir).exists() and Path(energy_dir).is_dir():
            root = Path(energy_dir)
            frames: list[pd.DataFrame] = []

            for csv_path in root.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_path)
                except Exception:
                    continue
                if df.empty:
                    continue

                # Normalize columns to lower-case for matching
                df = df.copy()
                df.columns = [str(c).strip().lower() for c in df.columns]

                # Identify numeric columns that look like energy quantities
                energy_cols: list[str] = []
                for c in df.columns:
                    if not pd.api.types.is_numeric_dtype(df[c]):
                        continue
                    cl = c.lower()
                    if any(
                        token in cl
                        for token in [
                            "gwh",
                            "mwh",
                            "kwh",
                            "demand",
                            "consumption",
                            "energy",
                            "use",
                            "usage",
                            "value",
                        ]
                    ):
                        energy_cols.append(c)

                if not energy_cols:
                    # Skip files that do not contain obvious energy quantities
                    continue

                # Case 1: long-form with explicit "sector" column
                if "sector" in df.columns:
                    out = df[["sector"] + energy_cols].copy()
                    # Sum numeric energy columns into a single demand_mwh field
                    out["demand_mwh"] = out[energy_cols].sum(axis=1).astype(float)
                    out = out[["sector", "demand_mwh"]]
                    frames.append(out)
                    continue

                # Case 2: wide-form where each numeric column represents a sector
                # (e.g. residential, commercial, industrial). Melt into sector/value
                if len(energy_cols) > 1:
                    melted = df[energy_cols].sum().reset_index()
                    melted.columns = ["sector", "demand_mwh"]
                    frames.append(melted)
                    continue

                # Case 3: a single numeric energy column without sectors. Use a
                # generic sector name based on the file and column.
                if len(energy_cols) == 1:
                    c = energy_cols[0]
                    total_val = float(df[c].sum())
                    if total_val <= 0:
                        continue
                    sector_name = root.name or "energy"
                    frames.append(
                        pd.DataFrame(
                            {"sector": [sector_name], "demand_mwh": [total_val]}
                        )
                    )

            if frames:
                merged = pd.concat(frames, ignore_index=True)
                # Convert any GWh-like totals to MWh when clearly in GWh
                # (heuristic: very small numbers are assumed to be GWh)
                if merged["demand_mwh"].max() < 1_000:
                    merged["demand_mwh"] = merged["demand_mwh"].astype(float) * 1000.0

                # Group by sector to avoid duplicates across files
                grouped = (
                    merged.groupby("sector", as_index=False)["demand_mwh"]
                    .sum()
                    .sort_values("demand_mwh", ascending=False)
                )
                if not grouped.empty:
                    return grouped
        # fallback synthetic
    except Exception:
        pass
    data = {
        "sector": ["household", "commercial", "industrial"],
        "demand_mwh": [250.0, 180.0, 520.0],
    }
    return pd.DataFrame(data)


# --- Weather (OpenWeather default; Open-Meteo optional) ---


def _weather_openweather_monthly(lat: float, lon: float, api_key: str) -> pd.DataFrame:
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/onecall",
            params={
                "lat": lat,
                "lon": lon,
                "exclude": "minutely,alerts",
                "appid": api_key,
                "units": "metric",
            },
            timeout=15,
        )
        r.raise_for_status()
        js = r.json()
        daily = js.get("daily", [])
        if not daily:
            raise ValueError("no daily data")
        rows = []
        for d in daily:
            dt = datetime.fromtimestamp(d.get("dt", time.time()), tz=timezone.utc)
            month = dt.month
            temp_c = float(d.get("temp", {}).get("day", 0.0))
            rain = float(d.get("rain", 0.0))
            rows.append({"month": month, "temp_c": temp_c, "rain_mm": rain})
        df = pd.DataFrame(rows)
        agg = df.groupby("month", as_index=False).agg(
            temp_c=("temp_c", "mean"), rain_mm=("rain_mm", "sum")
        )
        return agg.sort_values("month")
    except Exception:
        raise


def _weather_open_meteo_monthly(lat: float, lon: float) -> pd.DataFrame:
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m,precipitation",
                "past_days": 92,
                "forecast_days": 0,
                "timezone": "auto",
            },
            timeout=15,
        )
        r.raise_for_status()
        js = r.json()
        hours = js.get("hourly", {})
        times = hours.get("time", [])
        temps = hours.get("temperature_2m", [])
        precs = hours.get("precipitation", [])
        if not times or not temps:
            raise ValueError("no hourly data")
        rows = []
        for t, tc, pr in zip(times, temps, precs or [0] * len(times)):
            dt = datetime.fromisoformat(t)
            rows.append({"month": dt.month, "temp_c": float(tc), "rain_mm": float(pr)})
        df = pd.DataFrame(rows)
        agg = df.groupby("month", as_index=False).agg(
            temp_c=("temp_c", "mean"), rain_mm=("rain_mm", "sum")
        )
        return agg.sort_values("month")
    except Exception:
        raise


def fetch_environment() -> pd.DataFrame:
    """Monthly climate summary (temp C, rainfall mm) with provider selection.

    Falls back to synthetic monthly when provider/API not available.
    """
    fallback = pd.DataFrame(
        {
            "month": list(range(1, 13)),
            "temp_c": [24, 24, 23, 22, 21, 20, 20, 22, 25, 27, 28, 26],
            "rain_mm": [180, 160, 140, 60, 20, 5, 2, 5, 15, 40, 120, 170],
        }
    )
    try:
        lat, lon = _city_coords()
        provider = (
            getattr(config, "WEATHER_PROVIDER", "openweather") or "openweather"
        ).lower()
        if provider == "openweather" and getattr(config, "OPENWEATHER_API_KEY", None):
            df = _weather_openweather_monthly(lat, lon, config.OPENWEATHER_API_KEY)  # type: ignore[arg-type]
            # If too few months, fall back
            if len(df["month"].unique()) < 6:
                return fallback
            return _safe_df(df, fallback)
        elif provider == "open-meteo":
            df = _safe_df(_weather_open_meteo_monthly(lat, lon), fallback)
            return df
        else:
            return fallback
    except Exception:
        return fallback


# --- Traffic (TomTom default; synthetic fallback) ---


def _tomtom_sample_flows(lat: float, lon: float, api_key: str) -> pd.DataFrame:
    """Sample TomTom flow segment data and derive a 24h pseudo volume profile.

    This helper attempts to build an hourly profile for the past 24 hours by
    querying TomTom's flowSegmentData endpoint. If historical data is sparse
    (often due to API plan limits), it fetches the current congestion and
    scales a synthetic profile to provide a dynamic, representative 24h curve.
    """
    steps = [(-0.03, -0.03), (-0.03, 0.03), (0.0, 0.0), (0.03, -0.03), (0.03, 0.03)]
    ratios: list[float] = []
    current_speeds: list[float] = []
    free_speeds: list[float] = []
    confidences: list[float] = []
    road_closures: list[bool] = []
    for dlat, dlon in steps:
        plat, plon = lat + dlat, lon + dlon
        try:
            r = requests.get(
                "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json",
                params={"point": f"{plat},{plon}", "key": api_key},
                timeout=10,
            )
            r.raise_for_status()
            js = r.json().get("flowSegmentData", {})
            # Treat responses without real speed fields as unusable. Otherwise
            # we'd silently fall back to defaults (e.g. 30/30 => ratio 1.0)
            # which makes it look like traffic never changes.
            has_speed = ("currentSpeed" in js) or ("currentSpeedUncapped" in js)
            has_free = "freeFlowSpeed" in js
            if not js or not has_speed or not has_free:
                continue

            speed = float(js.get("currentSpeed", js.get("currentSpeedUncapped", 0.0)))
            free = float(js.get("freeFlowSpeed", 0.0))
            if speed <= 0 or free <= 0:
                continue

            ratio = min(max(free / max(speed, 1.0), 0.5), 2.5)
            ratios.append(ratio)
            current_speeds.append(speed)
            free_speeds.append(free)
            try:
                confidences.append(float(js.get("confidence", 0.0)))
            except Exception:
                confidences.append(0.0)
            road_closures.append(bool(js.get("roadClosure", False)))
        except Exception:
            continue

    if not ratios:
        return pd.DataFrame()

    current_congestion_ratio = sum(ratios) / len(ratios)
    avg_current_speed = (sum(current_speeds) / len(current_speeds)) if current_speeds else None
    avg_free_speed = (sum(free_speeds) / len(free_speeds)) if free_speeds else None
    avg_confidence = (sum(confidences) / len(confidences)) if confidences else None
    any_road_closure = any(road_closures) if road_closures else None

    hours = list(range(24))
    synthetic_curve = [
        (
            150
            if h < 6
            else (
                850 if h in (7, 8) else 400 if h < 16 else 900 if h in (17, 18) else 200
            )
        )
        for h in hours
    ]

    # TomTom flowSegmentData does not include veh/hour volume, so we derive a
    # pseudo 24h volume profile by modulating the canonical curve using the
    # observed congestion ratio.
    #
    # When congestion is near free-flow (ratio ~= 1.0), naive global scaling
    # would reproduce the canonical curve exactly. The modulation below avoids
    # that degenerate case while remaining deterministic.
    now = datetime.now(timezone.utc)
    current_hour = int(now.hour)
    base_scale = min(max(float(current_congestion_ratio), 0.6), 1.6)

    date_key = now.date().isoformat()
    speed_key = ""
    try:
        if avg_current_speed is not None and avg_free_speed is not None:
            speed_key = f"{float(avg_current_speed):.1f}/{float(avg_free_speed):.1f}"
    except Exception:
        speed_key = ""

    def _hour_distance(a: int, b: int) -> int:
        d = abs(a - b) % 24
        return min(d, 24 - d)

    scaled_curve: list[int] = []
    for h, vph in zip(hours, synthetic_curve):
        # Emphasize the scaling more near the current hour and less far away.
        # proximity: 1.0 at current hour, ~0.0 at 12h away.
        proximity = 1.0 - (_hour_distance(h, current_hour) / 12.0)
        proximity = min(max(proximity, 0.0), 1.0)

        # Blend base_scale toward 1.0 as you move away from current hour.
        hour_scale = 1.0 + (base_scale - 1.0) * (0.35 + 0.65 * proximity)

        # Add a small deterministic variation so free-flow (ratio~1) doesn't
        # collapse to the exact canonical curve. This is stable per (date,hour)
        # and depends on TomTom signals so it still "tracks" real conditions.
        seed = f"{date_key}|h={h}|n={len(ratios)}|r={current_congestion_ratio:.3f}|s={speed_key}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        jitter_u = int(digest[:8], 16) / float(0xFFFFFFFF)
        jitter = (jitter_u - 0.5) * 0.10  # +/- 5%

        # Reduce jitter impact when congestion is clearly high/low.
        # When ratio is near 1.0, allow full jitter; when far, damp it.
        jitter_weight = max(0.2, 1.0 - min(abs(base_scale - 1.0) / 0.5, 1.0))
        adj = max(0.65, min(1.75, hour_scale * (1.0 + jitter * jitter_weight)))

        scaled_curve.append(int(round(float(vph) * adj)))

    return pd.DataFrame(
        {
            "corridor": ["TT_live"] * 24,
            "hour": hours,
            "veh_per_hour": scaled_curve,
            "mode_share_bus": [0.18] * 24,
            "congestion_ratio": [float(current_congestion_ratio)] * 24,
            "current_speed": [avg_current_speed] * 24,
            "free_flow_speed": [avg_free_speed] * 24,
            "confidence": [avg_confidence] * 24,
            "road_closure": [any_road_closure] * 24,
            "samples_used": [int(len(ratios))] * 24,
        }
    )


def fetch_traffic() -> pd.DataFrame:
    """Traffic flows by corridor and hour with provider selection.

    Defaults to TomTom if configured, which now includes a dynamic fallback.
    Otherwise, it provides a static synthetic 24h profile.
    """
    hours = list(range(24))
    synthetic_curve = [
        (
            150
            if h < 6
            else (
                850 if h in (7, 8) else 400 if h < 16 else 900 if h in (17, 18) else 200
            )
        )
        for h in hours
    ]
    fallback = pd.DataFrame(
        {
            "corridor": ["A1"] * 24,
            "hour": hours,
            "veh_per_hour": synthetic_curve,
            "mode_share_bus": [0.18] * 24,
        }
    )
    try:
        provider = (getattr(config, "TRAFFIC_PROVIDER", "tomtom") or "tomtom").lower()
        if provider == "tomtom" and getattr(config, "TOMTOM_API_KEY", None):
            lat, lon = _city_coords()
            df = _tomtom_sample_flows(
                lat, lon, config.TOMTOM_API_KEY  # type: ignore[arg-type]
            )
            # The flow sampler now returns a dynamic profile; use if valid.
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        return fallback
    except Exception:
        return fallback


# --- OSM / Overpass (optional, env-gated) ---


def _truthy(val: Optional[str]) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on"}


def fetch_osm_snapshot() -> Optional[Path]:
    """Optionally fetch an OSM snapshot via Overpass and save as GeoJSON.

    This is guarded by the SUSPS_FETCH_OSM environment variable to keep the
    default pipeline fully offline and deterministic (including under pytest).
    When enabled, it queries a city-scale bounding box around CITY_LAT/CITY_LON
    and writes `osm_snapshot.geojson` under RAW_DIR for reuse.
    """

    if not _truthy(os.getenv("SUSPS_FETCH_OSM")):
        return None

    try:
        lat, lon = _city_coords()
        gj = fetch_osm_for_city_bbox(lat, lon)
        if not gj.get("features"):
            return None
        config.ensure_dirs()
        out_path = config.RAW_DIR / "osm_snapshot.geojson"
        save_geojson(gj, out_path)
        return out_path
    except Exception:
        # Network or Overpass errors should never break the core pipeline.
        return None


# --- Air quality (OpenAQ if key; fallback to existing CSV) ---


def fetch_air_quality() -> pd.DataFrame:
    """Fetch recent AQ measurements from OpenAQ for Nairobi (pm25, pm10, o3).

    Returns a raw records DataFrame with columns: datetime, parameter, value, unit.
    """
    try:
        api_key = getattr(config, "OPEN_AQ_API_KEY", None)
        if not api_key:
            raise RuntimeError("OPEN_AQ_API_KEY not set")
        # Query last 30 days in Nairobi; OpenAQ v2
        # Use timezone-aware UTC timestamps (PEP 495/PEP 564 compliant)
        now_utc = datetime.now(timezone.utc)
        date_from = (
            (now_utc - timedelta(days=30))
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        params = {
            "city": "Nairobi",
            "country": "KE",
            "parameter": "pm25,pm10,o3",
            "date_from": date_from,
            "limit": 10000,
            "order_by": "date",
            "sort": "desc",
        }
        headers = {"X-API-Key": api_key}
        r = requests.get(
            "https://api.openaq.org/v2/measurements",
            params=params,
            headers=headers,
            timeout=20,
        )
        r.raise_for_status()
        js = r.json()
        results = js.get("results", [])
        rows: list[dict] = []
        for it in results:
            dt = it.get("date", {}).get("utc") or it.get("date", {}).get("local")
            param = it.get("parameter")
            value = it.get("value")
            unit = it.get("unit")
            if dt and param is not None and value is not None:
                rows.append(
                    {
                        "datetime": dt,
                        "parameter": param,
                        "value": float(value),
                        "unit": unit,
                    }
                )
        return pd.DataFrame(rows)
    except Exception:
        # Fallback to existing raw CSV if present (search RAW_DIR and
        # Environmental_and_Climate subfolder).
        try:
            candidates = [
                getattr(
                    config,
                    "ENVIRONMENT_RAW_DIR",
                    config.RAW_DIR / "Environmental_and_Climate",
                ),
                config.RAW_DIR,
            ]
            for d in candidates:
                p = Path(d) / "Air_Quality_Data_2025.csv"
                if p.exists():
                    df = pd.read_csv(p)
                    return df
        except Exception:
            pass
        return pd.DataFrame([])


# --- Socioeconomic (synthetic) ---


def fetch_socioeconomic() -> pd.DataFrame:
    """Return a small socio-economic indicator table.

    Acts as a lightweight fallback when no external socioeconomic dataset is
    configured.
    """
    data = {
        "admin_unit": ["UnitA", "UnitB", "UnitC"],
        "income_usd": [2100, 1600, 1850],
        "employment_rate": [0.62, 0.48, 0.55],
    }
    return pd.DataFrame(data)


# --- IO ---


def save_raw(df: pd.DataFrame, name: str) -> Path:
    """Persist a raw CSV under the appropriate domain subfolder.

    Generated raw files are grouped alongside their curated counterparts in
    data/<CITY>/raw/<Domain>/ while remaining backward compatible when
    domain hints are unavailable.
    """
    config.ensure_dirs()

    domain_map = {
        "worldpop_summary": getattr(config, "DEMOGRAPHICS_RAW_DIR", config.RAW_DIR),
        "energy_demand": getattr(config, "ENERGY_RAW_DIR", config.RAW_DIR),
        "traffic_flows": getattr(config, "MOBILITY_RAW_DIR", config.RAW_DIR),
        "environment_monthly": getattr(config, "ENVIRONMENT_RAW_DIR", config.RAW_DIR),
        "air_quality_raw": getattr(config, "ENVIRONMENT_RAW_DIR", config.RAW_DIR),
        "socioeconomic": getattr(config, "DEMOGRAPHICS_RAW_DIR", config.RAW_DIR),
    }
    base_dir = domain_map.get(name, config.RAW_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)

    path = base_dir / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


# --- Main orchestrator ---


def main() -> None:
    config.ensure_dirs()
    wp = fetch_worldpop()
    ed = fetch_energy_demand()
    tf = fetch_traffic()
    env = fetch_environment()
    aq = fetch_air_quality()
    se = fetch_socioeconomic()

    wp_path = save_raw(wp, "worldpop_summary")
    ed_path = save_raw(ed, "energy_demand")
    tf_path = save_raw(tf, "traffic_flows")
    env_path = save_raw(env, "environment_monthly")
    aq_path = save_raw(aq, "air_quality_raw") if not aq.empty else None
    se_path = save_raw(se, "socioeconomic")
    osm_path = fetch_osm_snapshot()

    print(f"Saved: {wp_path}")
    print(f"Saved: {ed_path}")
    print(f"Saved: {tf_path}")
    print(f"Saved: {env_path}")
    if aq_path:
        print(f"Saved: {aq_path}")
    print(f"Saved: {se_path}")
    if osm_path:
        print(f"Saved: {osm_path}")


if __name__ == "__main__":
    main()

