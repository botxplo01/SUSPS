#!/usr/bin/env bash
set -euo pipefail
FILE=${1:-"backend/app/seeds/seed_urban_areas.sql"}

# Ensure services are running
if ! docker compose ps --status=running --services | grep -q '^db$'; then
  echo "Starting docker compose..."
  docker compose up -d >/dev/null
fi

# Apply migrations via API container
docker compose exec -T api alembic upgrade head

# Copy seed file into DB container and run it
DB_ID=$(docker compose ps -q db)
if [ -z "$DB_ID" ]; then
  echo "DB container not found" >&2
  exit 1
fi

echo "Copying seed file $FILE to container $DB_ID:/seed.sql"
docker cp "$FILE" "$DB_ID:/seed.sql"

echo "Applying seed..."
docker compose exec -T db psql -U postgres -d susps -v ON_ERROR_STOP=1 -f /seed.sql

echo "Seed applied successfully."
