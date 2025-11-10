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
    # Note: Region defaults are placeholders; use .env paths for actual data
    region: str = "Zambia"
    seed: int = 42
    worldpop_country_code: str = "ZMB"


# Helper to get an optional Path from environment
def _env_path(name: str) -> Optional[Path]:
    val = os.getenv(name)
    return Path(val) if val else None


# Paths for external datasets (match .env names, provide aliases for compatibility)
# Demographics & Population
WORLDPOP_PATH: Optional[Path] = _env_path("WORLDPOP_PATH")
GRID3_POP_PATH: Optional[Path] = _env_path("GRID3_POP_PATH")
POP_ANNUAL_CHANGE_PATH: Optional[Path] = _env_path("POP_ANNUAL_CHANGE_PATH")
CENSUS_TOTAL_PATH: Optional[Path] = _env_path("CENSUS_TOTAL_PATH")
# Back-compat alias if older env name is used
CENSUS_PATH: Optional[Path] = CENSUS_TOTAL_PATH or _env_path("CENSUS_PATH")

# Mobility & Transport
MATATUS_PATH: Optional[Path] = _env_path("MATATUS_PATH")
OSM_PATH: Optional[Path] = _env_path("OSM_PATH")

# Environmental & Climate (Land cover)
LANDCOVER_PATH_2015: Optional[Path] = _env_path("LANDCOVER_PATH_2015")

# Energy & Infrastructure (directory with multiple files)
ENERGY_DIR: Optional[Path] = _env_path("ENERGY")
ENERGY_PATH: Optional[Path] = _env_path("ENERGY_PATH") or ENERGY_DIR

# Smart City & Urban Growth (directory with multiple files)
GRID3_SETTLEMENTS_PATH: Optional[Path] = _env_path("GRID3_SETTLEMENTS_PATH")
SETTLEMENTS_PATH: Optional[Path] = (
    _env_path("SETTLEMENTS_PATH") or GRID3_SETTLEMENTS_PATH
)


# API keys and providers
OPEN_AQ_API_KEY: Optional[str] = os.getenv("OPEN_AQ_API_KEY")
OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
TOMTOM_API_KEY: Optional[str] = os.getenv("TOMTOM_API_KEY")
# Weather provider preference: 'openweather' (default) or 'open-meteo'
WEATHER_PROVIDER: str = os.getenv("WEATHER_PROVIDER", "openweather")
# Traffic provider preference: 'tomtom' (default) or 'synthetic'
TRAFFIC_PROVIDER: str = os.getenv("TRAFFIC_PROVIDER", "tomtom")
