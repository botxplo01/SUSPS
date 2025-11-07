Param(
  [string]$File = ".\backend\app\seeds\seed_urban_areas.sql"
)

$ErrorActionPreference = "Stop"

# Ensure services are running
$running = (docker compose ps --status=running --services) -split "\r?\n" | Where-Object { $_ -ne "" }
if (-not ($running -contains "db")) {
  Write-Host "Starting docker compose..."
  docker compose up -d | Out-Null
}

# Apply migrations via API container (ensures extension/tables)
docker compose exec -T api alembic upgrade head

# Copy seed file into DB container and run it
$dbId = docker compose ps -q db
if (-not $dbId) { throw "DB container not found" }

$dest = "$dbId" + ":/seed.sql"
Write-Host "Copying seed file $File to container $dest"
docker cp $File $dest

Write-Host "Applying seed..."
docker compose exec -T db psql -U postgres -d susps -v ON_ERROR_STOP=1 -f /seed.sql

Write-Host "Seed applied successfully."
