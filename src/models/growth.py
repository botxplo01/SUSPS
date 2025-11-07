from __future__ import annotations

from typing import List, Dict


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
