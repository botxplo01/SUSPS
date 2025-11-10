from __future__ import annotations

from pathlib import Path
import time
import os
import pandas as pd
import requests
from datetime import datetime, timezone

from . import config

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
    """Placeholder: fetch or mock WorldPop population grid summary.
    Returns a small DataFrame to keep the pipeline runnable offline.
    """
    data = {
        "admin_unit": ["UnitA", "UnitB", "UnitC"],
        "population": [12000, 8000, 15000],
    }
    return pd.DataFrame(data)


def fetch_energy_demand(region: str = config.Defaults.region) -> pd.DataFrame:
    """Placeholder synthetic energy demand by sector."""
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
    """Sample TomTom flow segment data around a center point and derive pseudo volumes.

    Note: TomTom does not provide volumes directly here; we derive a rough proxy.
    """
    rows = []
    # small grid around center
    steps = [(-0.03, -0.03), (-0.03, 0.03), (0.0, 0.0), (0.03, -0.03), (0.03, 0.03)]
    for i, (dlat, dlon) in enumerate(steps, start=1):
        plat, plon = lat + dlat, lon + dlon
        try:
            r = requests.get(
                "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json",
                params={"point": f"{plat},{plon}", "key": api_key},
                timeout=10,
            )
            r.raise_for_status()
            js = r.json().get("flowSegmentData", {})
            speed = float(js.get("currentSpeed", js.get("currentSpeedUncapped", 30.0)))
            free = float(js.get("freeFlowSpeed", max(speed, 30.0)))
            ratio = min(max(free / max(speed, 1.0), 0.5), 4.0)
            # proxy capacity (veh/h) scaled by ratio
            base_cap = 600
            vph = int(base_cap * ratio)
            rows.append(
                {
                    "corridor": f"TT_{i}",
                    "hour": datetime.now().hour,
                    "veh_per_hour": vph,
                    "mode_share_bus": 0.18,
                }
            )
        except Exception:
            # skip point on failure
            continue
    return pd.DataFrame(rows)


def fetch_traffic() -> pd.DataFrame:
    """Traffic flows by corridor and hour with provider selection.

    Defaults to TomTom if configured; falls back to synthetic.
    """
    fallback = pd.DataFrame(
        {
            "corridor": ["A1", "A1", "M4", "M4"],
            "hour": [8, 17, 8, 17],
            "veh_per_hour": [850, 1200, 420, 700],
            "mode_share_bus": [0.15, 0.12, 0.22, 0.18],
        }
    )
    try:
        provider = (getattr(config, "TRAFFIC_PROVIDER", "tomtom") or "tomtom").lower()
        if provider == "tomtom" and getattr(config, "TOMTOM_API_KEY", None):
            lat, lon = _city_coords()
            df = _tomtom_sample_flows(lat, lon, config.TOMTOM_API_KEY)  # type: ignore[arg-type]
            return _safe_df(df, fallback)
        # placeholder for future OSM-based option
        return fallback
    except Exception:
        return fallback


# --- Socioeconomic (synthetic) ---


def fetch_socioeconomic() -> pd.DataFrame:
    """Placeholder socio-economic indicators by admin unit."""
    data = {
        "admin_unit": ["UnitA", "UnitB", "UnitC"],
        "income_usd": [2100, 1600, 1850],
        "employment_rate": [0.62, 0.48, 0.55],
    }
    return pd.DataFrame(data)


# --- IO ---


def save_raw(df: pd.DataFrame, name: str) -> Path:
    config.ensure_dirs()
    path = config.RAW_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


# --- Main orchestrator ---


def main() -> None:
    config.ensure_dirs()
    wp = fetch_worldpop()
    ed = fetch_energy_demand()
    tf = fetch_traffic()
    env = fetch_environment()
    se = fetch_socioeconomic()

    wp_path = save_raw(wp, "worldpop_summary")
    ed_path = save_raw(ed, "energy_demand")
    tf_path = save_raw(tf, "traffic_flows")
    env_path = save_raw(env, "environment_monthly")
    se_path = save_raw(se, "socioeconomic")

    print(f"Saved: {wp_path}")
    print(f"Saved: {ed_path}")
    print(f"Saved: {tf_path}")
    print(f"Saved: {env_path}")
    print(f"Saved: {se_path}")


if __name__ == "__main__":
    main()
