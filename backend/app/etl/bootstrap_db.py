from __future__ import annotations

from datetime import datetime, timezone

from backend.app.etl.load_processed_to_db import main as load_main

# Optionally bring down raw data from S3 to ensure parity with local 'raw/'
try:
    from src.pipeline.s3_sync import sync_raw_from_s3  # type: ignore
except Exception:
    def sync_raw_from_s3() -> int:  # fallback no-op if boto3 not installed
        return 0

# Optionally run preprocess steps to produce processed artifacts identically
from src.pipeline import preprocess as _pp


def main() -> None:
    # 1) Sync raw data from S3 if enabled
    try:
        n = sync_raw_from_s3()
        if n:
            print(f"S3 sync: downloaded {n} objects to data/raw/")
    except Exception as e:
        print(f"S3 sync skipped/failed: {e}")

    # 2) Produce processed artifacts (best-effort; continue on partial failures)
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

    # 3) Load processed artifacts into the DB for today
    load_main()


if __name__ == "__main__":
    main()
