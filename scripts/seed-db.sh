#!/usr/bin/env bash
set -euo pipefail
FILES=("${@}")
if [ ${#FILES[@]} -eq 0 ]; then
  FILES=(
    "backend/app/seeds/seed_urban_areas.sql"
    "backend/app/seeds/seed_energy.sql"
    "backend/app/seeds/seed_traffic.sql"
  )
fi

# Ensure services are running
if ! docker compose ps --status=running --services | grep -q '^db$'; then
  echo "Starting docker compose..."
  docker compose up -d >/dev/null
fi

# Apply migrations via API container
docker compose exec -T api alembic upgrade head

# Copy seed files into DB container and run them
DB_ID=$(docker compose ps -q db)
if [ -z "$DB_ID" ]; then
  echo "DB container not found" >&2
  exit 1
fi

for FILE in "${FILES[@]}"; do
  if [ ! -f "$FILE" ]; then
    echo "Skipping missing file: $FILE"
    continue
  fi
  echo "Copying seed file $FILE to container $DB_ID:/seed.sql"
  docker cp "$FILE" "$DB_ID:/seed.sql"
  echo "Applying seed $FILE ..."
  docker compose exec -T db psql -U postgres -d susps -v ON_ERROR_STOP=1 -f /seed.sql
done

echo "All seeds applied successfully."
