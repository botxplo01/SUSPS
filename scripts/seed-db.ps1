Param(
  [switch]$RunPipeline
)

$ErrorActionPreference = "Stop"

if ($RunPipeline) {
  python -m src.pipeline.ingest
  python -m src.pipeline.preprocess
}

python -m scripts.create_schema
python -m src.backend.db.seed_from_processed
