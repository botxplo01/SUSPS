from __future__ import annotations

from typing import Any, Dict, List


def _get_float(params: Dict[str, Any], key: str, default: float) -> float:
    try:
        v = params.get(key, default)
        return float(v)
    except Exception:
        return default


def simulate_growth(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply simple scenario adjustments to growth projections.

    This is a lightweight, deterministic simulation layer over the existing
    growth model output. It is intentionally simple and free of external
    dependencies so it works in both local and Render environments
    without paid APIs or closed-source models.

    Supported parameters (all optional):
    - population_scale: multiplier applied to all predicted_population values.
    - annual_rate_delta_pct: percentage delta applied to an inferred annual
      growth rate (e.g. +10 means +10% faster growth, -20 means slower).
    """

    if not base_items:
        return []

    params = params or {}
    pop_scale = _get_float(params, "population_scale", 1.0)
    rate_delta_pct = _get_float(params, "annual_rate_delta_pct", 0.0)

    # Infer a baseline annual rate from the first two points if possible
    inferred_rate = 0.0
    if len(base_items) >= 2:
        try:
            y0 = float(base_items[0]["predicted_population"])
            y1 = float(base_items[1]["predicted_population"])
            if y0 > 0:
                inferred_rate = (y1 - y0) / y0
        except Exception:
            inferred_rate = 0.0

    # Adjust rate by the delta percentage (e.g. +10% => rate * 1.1)
    rate_factor = 1.0 + (rate_delta_pct / 100.0)
    adjusted_rate = inferred_rate * rate_factor

    # If we could not infer a rate, fall back to pure scaling.
    if inferred_rate == 0.0:
        return [
            {
                **item,
                "predicted_population": int(
                    float(item.get("predicted_population", 0)) * pop_scale
                ),
                "mode": "SIMULATE",
            }
            for item in base_items
        ]

    # Recompute the series starting from the first year using the adjusted rate.
    try:
        base_year = int(base_items[0]["year"])
        base_pop = float(base_items[0]["predicted_population"]) * pop_scale
    except Exception:
        # If the structure is unexpected, fall back to pure scaling.
        return [
            {
                **item,
                "predicted_population": int(
                    float(item.get("predicted_population", 0)) * pop_scale
                ),
                "mode": "SIMULATE",
            }
            for item in base_items
        ]

    simulated: List[Dict[str, Any]] = []
    pop = base_pop
    for i, _ in enumerate(base_items):
        year = base_year + i
        if i > 0:
            pop = pop * (1.0 + adjusted_rate)
        simulated.append(
            {
                "year": year,
                "predicted_population": int(pop),
                "mode": "SIMULATE",
            }
        )
    return simulated


def simulate_energy(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply simple scenario adjustments to hourly energy demand.

    Supported parameters (all optional):
    - demand_scale: global multiplier for demand_mwh.
    - peak_hour_shift: integer hour shift for peak load (positive shifts peak
      later in the day, negative shifts earlier). This is applied with a simple
      rotation over the 24h profile.
    """

    if not base_items:
        return []

    params = params or {}
    demand_scale = _get_float(params, "demand_scale", 1.0)
    peak_shift = int(_get_float(params, "peak_hour_shift", 0.0))

    # Normalize to 0-23 and rotate if requested.
    items = list(base_items)
    if peak_shift % 24 != 0 and len(items) == 24:
        # sort by hour, rotate list, and then reassign hours 0-23
        items = sorted(items, key=lambda x: int(x.get("hour", 0)))
        shift = peak_shift % 24
        items = items[-shift:] + items[:-shift]
        for h, it in enumerate(items):
            it["hour"] = h

    simulated: List[Dict[str, Any]] = []
    for it in items:
        try:
            v = float(it.get("demand_mwh", 0.0)) * demand_scale
        except Exception:
            v = 0.0
        simulated.append(
            {
                "hour": int(it.get("hour", 0)),
                "demand_mwh": float(v),
                "mode": "SIMULATE",
            }
        )
    return simulated


def simulate_traffic(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply simple scenario adjustments to hourly traffic volumes.

    Supported parameters (all optional):
    - volume_scale: global multiplier for volume.
    - peak_hour_shift: integer hour shift for rush-hour peaks, similar to
      simulate_energy.
    """

    if not base_items:
        return []

    params = params or {}
    volume_scale = _get_float(params, "volume_scale", 1.0)
    peak_shift = int(_get_float(params, "peak_hour_shift", 0.0))

    items = list(base_items)
    if peak_shift % 24 != 0 and len(items) == 24:
        items = sorted(items, key=lambda x: int(x.get("hour", 0)))
        shift = peak_shift % 24
        items = items[-shift:] + items[:-shift]
        for h, it in enumerate(items):
            it["hour"] = h

    simulated: List[Dict[str, Any]] = []
    for it in items:
        try:
            v = int(float(it.get("volume", 0)) * volume_scale)
        except Exception:
            v = 0
        simulated.append(
            {
                "hour": int(it.get("hour", 0)),
                "volume": v,
                "mode": "SIMULATE",
            }
        )
    return simulated
