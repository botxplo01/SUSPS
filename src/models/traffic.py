from __future__ import annotations

from typing import List, Dict
from pathlib import Path

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
    """Average veh/hour per clock hour from processed traffic_features.csv if present."""
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "traffic_features.csv"
        if not f.exists():
            return []
        import pandas as pd

        df = pd.read_csv(f)
        g = df.groupby("hour")["veh_per_hour"].mean().reset_index()
        return [
            {"hour": int(r["hour"]), "volume": int(r["veh_per_hour"])}
            for _, r in g.iterrows()
        ]
    except Exception:
        return []
