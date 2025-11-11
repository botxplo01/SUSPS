from __future__ import annotations

from pathlib import Path
import os

from backend.app.etl.load_processed_to_db import main as load_main

# Optionally bring down raw data from S3 to ensure parity with local 'raw/'
try:
    from src.pipeline.s3_sync import sync_raw_from_s3  # type: ignore
except Exception:

    def sync_raw_from_s3() -> int:  # fallback no-op if boto3 not installed
        return 0


# Pipeline modules
from src.pipeline import preprocess as _pp
from src.pipeline import ingest as _ing
from src.pipeline import config as _cfg


def _s3_to_local(s3_url: str) -> Path:
    """Map s3://bucket/prefix/... to local data/raw/... using AWS_S3_DATA_PREFIX.

    If the key starts with the prefix, strip it; otherwise keep the full key under data/raw/.
    """
    if not s3_url.startswith("s3://"):
        return Path(s3_url)
    # split into bucket and key
    try:
        _, rest = s3_url.split("s3://", 1)
        bucket, key = rest.split("/", 1)
    except ValueError:
        return _cfg.RAW_DIR / rest  # type: ignore[name-defined]
    prefix = os.getenv("AWS_S3_DATA_PREFIX", "") or ""
    rel = key[len(prefix) :] if prefix and key.startswith(prefix) else key
    return _cfg.RAW_DIR / rel


def _remap_config_paths_from_env() -> None:
    """After S3 sync, rewrite config paths that point to s3:// to their local counterparts."""
    mapping = {
        "WORLDPOP_PATH": os.getenv("WORLDPOP_PATH"),
        "GRID3_POP_PATH": os.getenv("GRID3_POP_PATH"),
        "POP_ANNUAL_CHANGE_PATH": os.getenv("POP_ANNUAL_CHANGE_PATH"),
        "CENSUS_TOTAL_PATH": os.getenv("CENSUS_TOTAL_PATH"),
        "CENSUS_PATH": os.getenv("CENSUS_TOTAL_PATH") or os.getenv("CENSUS_PATH"),
        "MATATUS_PATH": os.getenv("MATATUS_PATH"),
        "OSM_PATH": os.getenv("OSM_PATH"),
        "LANDCOVER_PATH_2015": os.getenv("LANDCOVER_PATH_2015"),
        "ENERGY_PATH": os.getenv("ENERGY_PATH"),
        "ENERGY": os.getenv("ENERGY"),
        "GRID3_SETTLEMENTS_PATH": os.getenv("GRID3_SETTLEMENTS_PATH"),
        "SETTLEMENTS_PATH": os.getenv("SETTLEMENTS_PATH"),
    }
    for name, val in mapping.items():
        if not val:
            continue
        if val.startswith("s3://"):
            local = _s3_to_local(val)
            try:
                setattr(_cfg, name, local)
            except Exception:
                pass
    # Normalize ENERGY alias -> ENERGY_PATH/ENERGY_DIR used by ingest
    if getattr(_cfg, "ENERGY_PATH", None) is None and getattr(_cfg, "ENERGY_DIR", None) is not None:  # type: ignore[attr-defined]
        setattr(_cfg, "ENERGY_PATH", getattr(_cfg, "ENERGY_DIR"))  # type: ignore[attr-defined]


def main() -> None:
    # 1) Sync raw data from S3 if enabled
    try:
        n = sync_raw_from_s3()
        if n:
            print(f"S3 sync: downloaded {n} objects to data/raw/")
    except Exception as e:
        print(f"S3 sync skipped/failed: {e}")

    # 2) Remap s3:// env paths to local data/raw equivalents for this process
    try:
        _remap_config_paths_from_env()
    except Exception as e:
        print(f"Path remap skipped: {e}")

    # 3) Build canonical raw CSVs (worldpop_summary.csv, energy_demand.csv, etc.)
    try:
        _ing.main()
    except Exception as e:
        print(f"ingest main skipped/failed: {e}")

    # 4) Produce processed artifacts (best-effort; continue on partial failures)
    try:
        _pp.preprocess_worldpop()
    except Exception as e:
        print(f"preprocess_worldpop skipped: {e}")
    try:
        _pp.preprocess_energy()
    except Exception as e:
        print(f"preprocess_energy skipped: {e}")
    try:
        _pp.preprocess_traffic()
    except Exception as e:
        print(f"preprocess_traffic skipped: {e}")
    try:
        _pp.preprocess_environment()
    except Exception as e:
        print(f"preprocess_environment skipped: {e}")
    try:
        _pp.preprocess_census()
        _pp.preprocess_growth_forecast()
    except Exception as e:
        print(f"preprocess_census/growth skipped: {e}")

    # 5) Load processed artifacts into the DB for today
    load_main()


if __name__ == "__main__":
    main()
