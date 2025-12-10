# @author: Lameck David Musumpuka

"""Energy model helpers backing the /energy endpoints.

Functions here derive a 24-hour demand profile and simple sector summary from
processed pipeline artifacts, with synthetic fallbacks when files are missing.
"""

from __future__ import annotations

from typing import List, Dict
from pathlib import Path
import pandas as pd

from src.pipeline import config as _cfg

def daily_profile() -> List[Dict[str, float]]:
    """Return a synthetic 24h energy demand curve (MWh)."""
    hours = list(range(24))
    curve = [
        5.0 if h < 6 else 8.0 if h < 9 else 6.5 if h < 16 else 9.5 if h < 20 else 6.0
        for h in hours
    ]
    return [{"hour": h, "demand_mwh": float(v)} for h, v in zip(hours, curve)]


def daily_profile_from_processed(
    processed_dir: Path | None = None,
) -> List[Dict[str, float]]:
    """Return a 24h profile scaled from energy_features.csv totals.

    Assumes energy_features.csv contains annual demand (MWh). We convert to a typical
    daily budget by dividing by 365, then distribute across a canonical 24h shape.
    """
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "energy_features.csv"
        if not f.exists():
            raise FileNotFoundError
        df = pd.read_csv(f)
        total_annual = float(df.get("demand_mwh", pd.Series([0.0])).sum())
        if total_annual <= 0:
            raise ValueError("non-positive total demand")
        daily_budget = total_annual / 365.0
        hours = list(range(24))
        base = [
            (
                0.5
                if h < 6
                else 0.9 if h < 9 else 0.7 if h < 16 else 1.0 if h < 20 else 0.6
            )
            for h in hours
        ]
        s = sum(base)
        scaled = [daily_budget * (v / s) for v in base]
        return [{"hour": h, "demand_mwh": float(v)} for h, v in zip(hours, scaled)]
    except Exception:
        return daily_profile()


def summary_from_processed(
    processed_dir: Path | None = None,
) -> List[Dict[str, float | str]]:
    """Return sector demand summary from processed energy_features.csv if present.

    Keys: "sector" (str), "demand_mwh" (float), "pct" (float).
    """
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "energy_features.csv"
        if not f.exists():
            return []
        import pandas as pd

        df = pd.read_csv(f)
        return [
            {
                "sector": str(r["sector"]),
                "demand_mwh": float(r["demand_mwh"]),
                "pct": float(r.get("pct", 0.0)),
            }
            for _, r in df.iterrows()
        ]
    except Exception:
        return []
