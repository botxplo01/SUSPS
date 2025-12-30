# @author: Lameck David Musumpuka

"""Deterministic simulation helpers used by the SIMULATE API endpoints.

These functions adjust baseline growth, energy, and traffic series using
simple parameterised rules (scaling, peak shifting, flattening, shocks)
so that SIMULATE mode remains transparent, reproducible, and free of
external model dependencies.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _get_float(params: Dict[str, Any], key: str, default: float) -> float:
    """Best-effort float extraction from a parameters dict.

    Keeps simulation helpers tolerant of missing or malformed values.
    """
    try:
        raw = params.get(key, default)
    except Exception:
        return default

    if raw is None:
        return default

    if isinstance(raw, (int, float)):
        return float(raw)

    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return default
        try:
            return float(raw)
        except Exception:
            return default

    try:
        return float(raw)  # type: ignore[arg-type]
    except Exception:
        return default


def simulate_growth(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply scenario adjustments to growth projections.

    This is a lightweight, deterministic simulation layer over the existing
    growth model output. It stays free of external dependencies so it works in
    both local and Render environments without paid APIs or closed-source
    models.

    Supported parameters (all optional):
    - population_scale: multiplier applied to all predicted_population values.
    - annual_rate_delta_pct: percentage delta applied to an inferred annual
      growth rate (e.g. +10 means +10% faster growth, -20 means slower).
    - min_annual_rate_pct / max_annual_rate_pct: clamp the effective annual
      growth rate within these bounds (defaults roughly match pipeline bounds
      of [-2%, 8%]).
    - shock_year: optional calendar year in which a one-off shock is applied.
    - shock_pct: percentage shock to population for shock_year
      (e.g. +10 increases that year by 10% on top of the trend).
    """

    if not base_items:
        return []

    params = params or {}
    pop_scale = _get_float(params, "population_scale", 1.0)
    rate_delta_pct = _get_float(params, "annual_rate_delta_pct", 0.0)
    min_rate_pct = _get_float(params, "min_annual_rate_pct", -2.0)
    max_rate_pct = _get_float(params, "max_annual_rate_pct", 8.0)

    shock_year_val = params.get("shock_year")
    shock_year = None
    if shock_year_val is not None:
        try:
            shock_year = int(shock_year_val)
        except Exception:
            shock_year = None
    shock_pct = _get_float(params, "shock_pct", 0.0)

    # Infer a baseline annual rate from the first two points if possible.
    inferred_rate = 0.0
    if len(base_items) >= 2:
        try:
            y0 = float(base_items[0]["predicted_population"])
            y1 = float(base_items[1]["predicted_population"])
            if y0 > 0:
                inferred_rate = (y1 - y0) / y0
        except Exception:
            inferred_rate = 0.0

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

    # Convert to percentage space, apply delta and clamp, then convert back.
    inferred_rate_pct = inferred_rate * 100.0
    effective_rate_pct = inferred_rate_pct + rate_delta_pct
    if max_rate_pct < min_rate_pct:
        max_rate_pct, min_rate_pct = min_rate_pct, max_rate_pct
    effective_rate_pct = max(min(effective_rate_pct, max_rate_pct), min_rate_pct)
    adjusted_rate = effective_rate_pct / 100.0

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
    pop = max(base_pop, 0.0)
    for i, _ in enumerate(base_items):
        year = base_year + i
        if i > 0:
            pop = pop * (1.0 + adjusted_rate)
        # Apply a one-off population shock for the specified year.
        if shock_year is not None and year == shock_year:
            pop = pop * (1.0 + shock_pct / 100.0)
        simulated.append(
            {
                "year": year,
                "predicted_population": int(max(pop, 0.0)),
                "mode": "SIMULATE",
            }
        )
    return simulated

def simulate_energy(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply scenario adjustments to hourly energy demand.

    Supported parameters (all optional):
    - demand_scale: global multiplier for demand_mwh.
    - peak_hour_shift: integer hour shift for peak load (positive shifts peak
      later in the day, negative shifts earlier). This is applied with a simple
      rotation over the 24h profile.
    - peak_scale: additional multiplier applied to a fixed set of peak hours
      (07â€“08 and 17â€“18) after rotation.
    - offpeak_scale: multiplier applied to non-peak hours (default 1.0).
    - flatten_ratio: 0..1 factor that pulls values toward the daily average
      (0 = no change, 1 = fully flattened profile at the mean).
    - max_demand_mwh: optional cap on hourly demand (<=0 disables the cap).
    """

    if not base_items:
        return []

    params = params or {}
    demand_scale = _get_float(params, "demand_scale", 1.0)
    peak_shift = int(_get_float(params, "peak_hour_shift", 0.0))
    peak_scale = _get_float(params, "peak_scale", 1.0)
    offpeak_scale = _get_float(params, "offpeak_scale", 1.0)
    flatten_ratio = _get_float(params, "flatten_ratio", 0.0)
    max_demand_mwh = _get_float(params, "max_demand_mwh", -1.0)

    if flatten_ratio < 0.0:
        flatten_ratio = 0.0
    if flatten_ratio > 1.0:
        flatten_ratio = 1.0

    # Normalize to 0-23 and rotate if requested.
    items = list(base_items)
    for idx, it in enumerate(items):
        if it.get("hour") is None:
            it["hour"] = idx
        if it.get("demand_mwh") is None:
            it["demand_mwh"] = it.get("predicted")
            if it.get("demand_mwh") is None:
                it["demand_mwh"] = it.get("actual")
    if peak_shift % 24 != 0 and len(items) == 24:
        # sort by hour, rotate list, and then reassign hours 0-23
        items = sorted(items, key=lambda x: int(x.get("hour", 0)))
        shift = peak_shift % 24
        items = items[-shift:] + items[:-shift]
        for h, it in enumerate(items):
            it["hour"] = h

    # Apply scaling, then optional flattening and capping.
    peak_hours = {7, 8, 17, 18}
    hours: List[int] = []
    values: List[float] = []

    for it in items:
        h = int(it.get("hour", 0))
        hours.append(h)
        try:
            base_v = float(it.get("demand_mwh", 0.0))
        except Exception:
            base_v = 0.0
        v = base_v * demand_scale
        if h in peak_hours:
            v *= peak_scale
        else:
            v *= offpeak_scale
        values.append(v)

    if values and flatten_ratio > 0.0:
        avg = sum(values) / float(len(values))
        values = [v * (1.0 - flatten_ratio) + avg * flatten_ratio for v in values]

    if max_demand_mwh > 0.0:
        values = [min(v, max_demand_mwh) for v in values]

    simulated: List[Dict[str, Any]] = []
    for h, v in zip(hours, values):
        simulated.append(
            {
                "hour": int(h),
                "demand_mwh": float(max(v, 0.0)),
                "mode": "SIMULATE",
            }
        )
    return simulated


def simulate_traffic(
    base_items: List[Dict[str, Any]],
    params: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Apply scenario adjustments to hourly traffic volumes.

    Supported parameters (all optional):
    - volume_scale: global multiplier for volume.
    - peak_hour_shift: integer hour shift for rush-hour peaks, similar to
      simulate_energy.
    - peak_scale: additional multiplier applied to morning/evening peak hours
      (07â€“09 and 16â€“19) after rotation.
    - offpeak_scale: multiplier applied to non-peak hours (default 1.0).
    - flatten_ratio: 0..1 factor that pulls volumes toward the daily average
      (0 = no change, 1 = fully flattened profile at the mean).
    - max_volume: optional cap on hourly volume (<=0 disables the cap).
    """

    if not base_items:
        return []

    params = params or {}
    volume_scale = _get_float(params, "volume_scale", 1.0)
    peak_shift = int(_get_float(params, "peak_hour_shift", 0.0))
    peak_scale = _get_float(params, "peak_scale", 1.0)
    offpeak_scale = _get_float(params, "offpeak_scale", 1.0)
    flatten_ratio = _get_float(params, "flatten_ratio", 0.0)
    max_volume = _get_float(params, "max_volume", -1.0)

    if flatten_ratio < 0.0:
        flatten_ratio = 0.0
    if flatten_ratio > 1.0:
        flatten_ratio = 1.0

    items = list(base_items)
    if peak_shift % 24 != 0 and len(items) == 24:
        items = sorted(items, key=lambda x: int(x.get("hour", 0)))
        shift = peak_shift % 24
        items = items[-shift:] + items[:-shift]
        for h, it in enumerate(items):
            it["hour"] = h

    # Apply scaling, then optional flattening and capping.
    peak_hours = {7, 8, 9, 16, 17, 18, 19}
    hours: List[int] = []
    values: List[float] = []

    for it in items:
        h = int(it.get("hour", 0))
        hours.append(h)
        try:
            base_v = float(it.get("volume", 0))
        except Exception:
            base_v = 0.0
        v = base_v * volume_scale
        if h in peak_hours:
            v *= peak_scale
        else:
            v *= offpeak_scale
        values.append(v)

    if values and flatten_ratio > 0.0:
        avg = sum(values) / float(len(values))
        values = [v * (1.0 - flatten_ratio) + avg * flatten_ratio for v in values]

    if max_volume > 0.0:
        values = [min(v, max_volume) for v in values]

    simulated: List[Dict[str, Any]] = []
    for h, v in zip(hours, values):
        simulated.append(
            {
                "hour": int(h),
                "volume": int(max(round(v), 0)),
                "mode": "SIMULATE",
            }
        )
    return simulated

