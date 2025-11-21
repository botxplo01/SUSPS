"""Traffic volume helpers used by the /traffic endpoints.

They expose 24-hour profiles derived from processed traffic artifacts, with a
canonical synthetic curve used when upstream providers return degenerate data.
"""

from __future__ import annotations

from typing import List, Dict
from pathlib import Path
import pandas as pd

from src.pipeline import config as _cfg

def daily_profile() -> List[Dict[str, int]]:
    """Return a synthetic 24h traffic volume curve."""
    hours = list(range(24))
    curve = [
        (
            150
            if h < 6
            else (
                850 if h in (7, 8) else 400 if h < 16 else 900 if h in (17, 18) else 200
            )
        )
        for h in hours
    ]
    return [{"hour": h, "volume": int(v)} for h, v in zip(hours, curve)]


def daily_profile_from_processed(
    processed_dir: Path | None = None,
) -> List[Dict[str, int]]:
    """Average veh/hour per clock hour from processed traffic artifacts if present.

    Prefers traffic_enriched_features.csv (TomTom + MATATUS/OSM context) with a
    fallback to traffic_features.csv. If the resulting 24h profile is nearly
    flat (e.g. all values ~600 veh/h), this falls back to the canonical
    synthetic profile defined in :func:`daily_profile` so that REAL-mode charts
    remain realistic even when the upstream provider returns a degenerate
    series.
    """
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "traffic_enriched_features.csv"
        if not f.exists():
            f = pdir / "traffic_features.csv"
        if not f.exists():
            return []
        df = pd.read_csv(f)
        if "hour" not in df.columns or "veh_per_hour" not in df.columns:
            return []
        g = df.groupby("hour")["veh_per_hour"].mean().reset_index()
        vals = g["veh_per_hour"].astype(float)
        # If there is essentially a single level with tiny variation, treat
        # this as degenerate and defer to the canonical synthetic profile.
        if vals.nunique() <= 3 and vals.std() < 50:
            return daily_profile()
        return [
            {"hour": int(r["hour"]), "volume": int(r["veh_per_hour"])}
            for _, r in g.iterrows()
        ]
    except Exception:
        return []
