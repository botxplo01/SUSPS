from __future__ import annotations

from typing import List, Dict


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
