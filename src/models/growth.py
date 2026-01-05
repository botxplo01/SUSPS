# @author: David Lameck

"""Population growth helpers for REAL and SIMULATE modes.

These functions read processed census and worldpop features when available and
fall back to deterministic compounded projections otherwise.
"""

from __future__ import annotations

from typing import List, Dict
from pathlib import Path
import pandas as pd

from src.pipeline import config as _cfg

def forecast_from_processed(
    processed_dir: Path | None = None,
) -> List[Dict[str, int]]:
    """Read precomputed city forecast if available."""
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "growth_forecast_city.csv"
        if not f.exists():
            raise FileNotFoundError
        import pandas as pd  # local import safe

        df = pd.read_csv(f)
        return [
            {
                "year": int(r["year"]),
                "predicted_population": int(r["predicted_population"]),
            }
            for _, r in df.iterrows()
        ]
    except Exception:
        return []


def predict_growth(
    start_population: int = 800_000,
    start_year: int = 2025,
    end_year: int = 2030,
    annual_rate: float = 0.03,
) -> List[Dict[str, int]]:
    """Return simple compounded growth projections per year.

    Items: {"year": int, "predicted_population": int}
    """
    items: List[Dict[str, int]] = []
    for i, year in enumerate(range(start_year, end_year + 1)):
        pop = int(start_population * ((1.0 + annual_rate) ** i))
        items.append({"year": year, "predicted_population": pop})
    return items


def growth_from_census(
    horizon_years: int = 6,
    processed_dir: Path | None = None,
) -> List[Dict[str, int]]:
    """Forecast city population using processed census_trend.csv if present.

    Uses last known total_population as the base and the mean of the last
    few annual_rate observations. Falls back to predict_from_processed/predict_growth.
    """
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "census_trend.csv"
        if not f.exists():
            raise FileNotFoundError
        df = pd.read_csv(f)
        if "year" not in df.columns or "total_population" not in df.columns:
            raise ValueError("census_trend missing required columns")
        df = df.sort_values("year")
        base_year = int(df["year"].iloc[-1])
        base_pop = float(df["total_population"].iloc[-1])
        rate_series = df.get("annual_rate")
        if rate_series is None or rate_series.isna().all():
            # compute from totals
            rate_series = df["total_population"].pct_change()
        # use mean of last 3 valid rates
        recent = rate_series.dropna().tail(3)
        r = float(recent.mean()) if len(recent) else 0.03
        # Cap to realistic bounds
        r = max(min(r, 0.08), -0.02)
        items: List[Dict[str, int]] = []
        pop = base_pop
        for i in range(1, horizon_years + 1):
            year = base_year + i
            pop = pop * (1.0 + r)
            items.append({"year": year, "predicted_population": int(pop)})
        return items
    except Exception:
        return predict_from_processed(processed_dir=processed_dir)


def predict_from_processed(
    processed_dir: Path | None = None,
    start_population: int = 800_000,
    years: int = 6,
    annual_rate: float = 0.03,
) -> List[Dict[str, int]]:
    """Derive a population baseline from processed artifacts when available.

    Uses `data/<CITY>/processed/worldpop_features.csv` pop_share sum as a lightweight
    proxy for base scaling; falls back to predict_growth otherwise.
    """
    try:
        pdir = processed_dir or _cfg.PROCESSED_DIR
        f = pdir / "worldpop_features.csv"
        if not f.exists():
            return predict_growth(
                start_population=start_population, end_year=2024 + years
            )
        import pandas as pd

        df = pd.read_csv(f)
        scale = float(df.get("pop_share", pd.Series([1.0])).sum()) or 1.0
        base = int(start_population * scale)
        return predict_growth(
            start_population=base, end_year=2024 + years, annual_rate=annual_rate
        )
    except Exception:
        return predict_growth(
            start_population=start_population,
            end_year=2024 + years,
            annual_rate=annual_rate,
        )

