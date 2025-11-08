from __future__ import annotations

from typing import List, Dict
from pathlib import Path

from src.pipeline import config as _cfg


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


def predict_from_processed(
    processed_dir: Path | None = None,
    start_population: int = 800_000,
    years: int = 6,
    annual_rate: float = 0.03,
) -> List[Dict[str, int]]:
    """Placeholder: if processed data exists, derive a base population proxy.

    Uses `data/processed/worldpop_features.csv` pop_share sum as a lightweight
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
