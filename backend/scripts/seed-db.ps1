Param(
  [switch]$RunPipeline
)

$ErrorActionPreference = "Stop"

if ($RunPipeline) {
  python -m pipeline.ingest
  python -m pipeline.preprocess
}

python -m scripts.create_schema
python -m db.seed_from_processed
