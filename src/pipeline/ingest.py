from __future__ import annotations

from pathlib import Path
import pandas as pd
from typing import Optional

from .config import RAW_DIR, ensure_dirs, Defaults


def fetch_worldpop(country_code: str = Defaults.worldpop_country_code) -> pd.DataFrame:
    """Placeholder: fetch or mock WorldPop population grid summary.
    Returns a small DataFrame to keep the pipeline runnable offline.
    """
    # Mocked summary by admin unit
    data = {
        "admin_unit": ["UnitA", "UnitB", "UnitC"],
        "population": [12000, 8000, 15000],
    }
    return pd.DataFrame(data)


def fetch_energy_demand(region: str = Defaults.region) -> pd.DataFrame:
    """Placeholder synthetic energy demand by sector."""
    data = {
        "sector": ["household", "commercial", "industrial"],
        "demand_mwh": [250.0, 180.0, 520.0],
    }
    return pd.DataFrame(data)


def save_raw(df: pd.DataFrame, name: str) -> Path:
    ensure_dirs()
    path = RAW_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


def main() -> None:
    ensure_dirs()
    wp = fetch_worldpop()
    ed = fetch_energy_demand()

    wp_path = save_raw(wp, "worldpop_summary")
    ed_path = save_raw(ed, "energy_demand")

    print(f"Saved: {wp_path}")
    print(f"Saved: {ed_path}")


if __name__ == "__main__":
    main()
