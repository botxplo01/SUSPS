from __future__ import annotations

from typing import List, Dict


def daily_profile() -> List[Dict[str, float]]:
    """Return a synthetic 24h energy demand curve (MWh)."""
    hours = list(range(24))
    curve = [
        5.0 if h < 6 else 8.0 if h < 9 else 6.5 if h < 16 else 9.5 if h < 20 else 6.0
        for h in hours
    ]
    return [{"hour": h, "demand_mwh": float(v)} for h, v in zip(hours, curve)]
