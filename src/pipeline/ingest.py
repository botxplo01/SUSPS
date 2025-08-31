from __future__ import annotations

from pathlib import Path
import pandas as pd
from typing import Optional

from . import config


def fetch_worldpop(country_code: str = config.Defaults.worldpop_country_code) -> pd.DataFrame:
    """Placeholder: fetch or mock WorldPop population grid summary.
    Returns a small DataFrame to keep the pipeline runnable offline.
    """
    # Mocked summary by admin unit
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


def fetch_traffic() -> pd.DataFrame:
    """Placeholder traffic flows by corridor and hour."""
    data = {
        "corridor": ["A1", "A1", "M4", "M4"],
        "hour": [8, 17, 8, 17],
        "veh_per_hour": [850, 1200, 420, 700],
        "mode_share_bus": [0.15, 0.12, 0.22, 0.18],
    }
    return pd.DataFrame(data)


def fetch_environment() -> pd.DataFrame:
    """Placeholder monthly climate summary (temp C, rainfall mm)."""
    data = {
        "month": list(range(1, 13)),
        "temp_c": [24, 24, 23, 22, 21, 20, 20, 22, 25, 27, 28, 26],
        "rain_mm": [180, 160, 140, 60, 20, 5, 2, 5, 15, 40, 120, 170],
    }
    return pd.DataFrame(data)


def fetch_socioeconomic() -> pd.DataFrame:
    """Placeholder socio-economic indicators by admin unit."""
    data = {
        "admin_unit": ["UnitA", "UnitB", "UnitC"],
        "income_usd": [2100, 1600, 1850],
        "employment_rate": [0.62, 0.48, 0.55],
    }
    return pd.DataFrame(data)


def save_raw(df: pd.DataFrame, name: str) -> Path:
    config.ensure_dirs()
    path = config.RAW_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


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
