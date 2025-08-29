from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

# Project root = repo root (src/pipeline -> src -> root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Defaults:
    region: str = "Zambia"
    seed: int = 42
    worldpop_country_code: str = "ZMB"

