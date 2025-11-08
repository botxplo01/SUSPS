from __future__ import annotations

from typing import List, Dict
from pathlib import Path

from src.pipeline import config as _cfg


def daily_profile() -> List[Dict[str, float]]:
    """Return a synthetic 24h energy demand curve (MWh)."""
    hours = list(range(24))
    curve = [
        5.0 if h < 6 else 8.0 if h < 9 else 6.5 if h < 16 else 9.5 if h < 20 else 6.0
        for h in hours
    ]
    return [{"hour": h, "demand_mwh": float(v)} for h, v in zip(hours, curve)]


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
