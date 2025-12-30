# @author: Lameck David Musumpuka

"""Central configuration for the SUSPS data pipeline.

Defines project- and city-scoped data directories, domain-specific raw folders,
default parameters, external dataset paths, and provider API keys/toggles.
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Load environment variables from a .env file when python-dotenv is available.
try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Project root = repo root (src/pipeline -> src -> repo)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
# Optional city scoping: put data under data/<CITY>/{raw,processed}
_CITY = os.getenv("DATA_CITY") or os.getenv("CITY_NAME") or "Nairobi"
CITY_DIR = DATA_DIR / _CITY
RAW_DIR = CITY_DIR / "raw"
PROCESSED_DIR = CITY_DIR / "processed"

# Domain-specific raw subdirectories to group raw inputs and ingest outputs.
# These are created lazily by ensure_dirs but the pipeline remains backward
# compatible with flat layouts under RAW_DIR.
DEMOGRAPHICS_RAW_DIR = RAW_DIR / "Demographics_and_Population"
ENERGY_RAW_DIR = RAW_DIR / "Energy_and_Infrastructure"
ENVIRONMENT_RAW_DIR = RAW_DIR / "Environmental_and_Climate"
MOBILITY_RAW_DIR = RAW_DIR / "Mobility_and_Transport"
URBAN_GROWTH_RAW_DIR = RAW_DIR / "Urban_Growth"


def ensure_dirs() -> None:
    """Ensure raw/processed directories (and domain subfolders) exist.

    Domain directories are recomputed from the current RAW_DIR on each call so
    monkeypatching RAW_DIR in tests (or changing DATA_CITY) continues to work
    as expected.
    """

    global DEMOGRAPHICS_RAW_DIR, ENERGY_RAW_DIR, ENVIRONMENT_RAW_DIR, MOBILITY_RAW_DIR, URBAN_GROWTH_RAW_DIR

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    DEMOGRAPHICS_RAW_DIR = RAW_DIR / "Demographics_and_Population"
    ENERGY_RAW_DIR = RAW_DIR / "Energy_and_Infrastructure"
    ENVIRONMENT_RAW_DIR = RAW_DIR / "Environmental_and_Climate"
    MOBILITY_RAW_DIR = RAW_DIR / "Mobility_and_Transport"
    URBAN_GROWTH_RAW_DIR = RAW_DIR / "Urban_Growth"

    DEMOGRAPHICS_RAW_DIR.mkdir(parents=True, exist_ok=True)
    ENERGY_RAW_DIR.mkdir(parents=True, exist_ok=True)
    ENVIRONMENT_RAW_DIR.mkdir(parents=True, exist_ok=True)
    MOBILITY_RAW_DIR.mkdir(parents=True, exist_ok=True)
    URBAN_GROWTH_RAW_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Defaults:
    # Region defaults should be overridden via environment configuration.
    region: str = "Zambia"
    seed: int = 42
    worldpop_country_code: str = "ZMB"


# Helper to read an optional Path from environment
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

