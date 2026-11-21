Param(
  [switch]$Fix
)

$ErrorActionPreference = "Stop"

if ($Fix) {
  python -m ruff check --fix .
  python -m black .
} else {
  python -m ruff check .
  python -m black --check .
}
