#!/usr/bin/env bash
set -euo pipefail

# Ensure we run from backend/ (this script lives at backend/scripts/render_start.sh)
cd "$(dirname "$0")/.."

echo "[render-start] Starting SUSPS backend..."

# Optional one-time bootstrap for Render: pull raw data from S3, run the
# pipeline, and seed the Postgres database. Controlled via DB_BOOTSTRAP_ON_START
# so normal restarts stay fast.
if [ "${DB_BOOTSTRAP_ON_START:-0}" = "1" ]; then
  echo "[render-start] DB_BOOTSTRAP_ON_START=1 - running bootstrap pipeline"

  if [ "${USE_S3_STORAGE:-false}" = "true" ] || [ "${USE_S3_STORAGE:-0}" = "1" ]; then
    echo "[render-start] Syncing raw data from S3 into data/<CITY>/raw/..."
    python -m pipeline.s3_sync --pull
  else
    echo "[render-start] USE_S3_STORAGE is not enabled; skipping S3 pull"
  fi

  echo "[render-start] Running ingest (build canonical raw CSVs)..."
  python -m pipeline.ingest

  echo "[render-start] Running preprocess (build processed features)..."
  python -m pipeline.preprocess

  echo "[render-start] Creating database schema..."
  python -m scripts.create_schema

  echo "[render-start] Seeding Postgres from processed artifacts..."
  python -m db.seed_from_processed

  echo "[render-start] Bootstrap complete"
else
  echo "[render-start] DB_BOOTSTRAP_ON_START is not set to 1; skipping bootstrap"
fi

# Finally start Gunicorn + Uvicorn worker for FastAPI
exec gunicorn api:app -k uvicorn.workers.UvicornWorker --timeout 120 --bind 0.0.0.0:"${PORT:-8000}"
