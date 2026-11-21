#!/usr/bin/env bash
set -euo pipefail

RUN_PIPELINE=0
if [ "${1:-}" = "--run-pipeline" ]; then
  RUN_PIPELINE=1
fi

if [ "$RUN_PIPELINE" = "1" ]; then
  python -m pipeline.ingest
  python -m pipeline.preprocess
fi

python -m scripts.create_schema
python -m db.seed_from_processed
