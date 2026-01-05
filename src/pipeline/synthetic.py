# @author: David Lameck

"""Synthetic data generators.

These utilities provide small, deterministic datasets used when external raw
inputs are unavailable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

from . import config

def generate_demographics(
    n: int = 1000, seed: int = config.Defaults.seed
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    income = rng.lognormal(mean=8.5, sigma=0.6, size=n)
    household_size = rng.integers(1, 8, size=n)
    urban = rng.choice([0, 1], p=[0.4, 0.6], size=n)
    return pd.DataFrame(
        {
            "income": income,
            "household_size": household_size,
            "urban": urban,
        }
    )


def save_synthetic(df: pd.DataFrame, name: str = "synthetic_demographics") -> Path:
    config.ensure_dirs()
    path = config.PROCESSED_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    return path


def main() -> None:
    df = generate_demographics()
    out = save_synthetic(df)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()

