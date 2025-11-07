from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Optionally load environment variables from a .env file if python-dotenv is installed
try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

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


# Helper to get an optional Path from environment
def _env_path(name: str) -> Optional[Path]:
    val = os.getenv(name)
    return Path(val) if val else None


# Paths for external datasets (from data_integration_guide)
WORLDPOP_PATH: Optional[Path] = _env_path("WORLDPOP_PATH")
CENSUS_PATH: Optional[Path] = _env_path("CENSUS_PATH")
MATATUS_PATH: Optional[Path] = _env_path("MATATUS_PATH")
OSM_PATH: Optional[Path] = _env_path("OSM_PATH")
COPERNICUS_PATH: Optional[Path] = _env_path("COPERNICUS_PATH")
ENERGY_PATH: Optional[Path] = _env_path("ENERGY_PATH")
NIGHTLIGHTS_PATH: Optional[Path] = _env_path("NIGHTLIGHTS_PATH")
GHSL_PATH: Optional[Path] = _env_path("GHSL_PATH")
SETTLEMENTS_PATH: Optional[Path] = _env_path("SETTLEMENTS_PATH")


# API keys (do not hardcode secrets)
GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
AIRQO_API_KEY: Optional[str] = os.getenv("AIRQO_API_KEY")
OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
