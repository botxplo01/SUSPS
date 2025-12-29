#!/usr/bin/env bash
set -euo pipefail

RUN_PIPELINE=0
if [ "${1:-}" = "--run-pipeline" ]; then
  RUN_PIPELINE=1
fi

if [ "$RUN_PIPELINE" = "1" ]; then
  python -m src.pipeline.ingest
  python -m src.pipeline.preprocess
fi

python -m scripts.create_schema
python -m src.backend.db.seed_from_processed
