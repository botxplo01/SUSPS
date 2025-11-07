Param(
  [string[]]$Files = @(
    ".\\backend\\app\\seeds\\seed_urban_areas.sql",
    ".\\backend\\app\\seeds\\seed_energy.sql",
    ".\\backend\\app\\seeds\\seed_traffic.sql"
  )
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

# Copy seed files into DB container and run them
$dbId = docker compose ps -q db
if (-not $dbId) { throw "DB container not found" }

foreach ($File in $Files) {
  if (-not (Test-Path $File)) {
    Write-Host "Skipping missing file: $File"
    continue
  }
  $dest = "$dbId" + ":/seed.sql"
  Write-Host "Copying seed file $File to container $dest"
  docker cp $File $dest
  Write-Host "Applying seed $File ..."
  docker compose exec -T db psql -U postgres -d susps -v ON_ERROR_STOP=1 -f /seed.sql
}

Write-Host "All seeds applied successfully."
