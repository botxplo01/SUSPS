# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common commands

- Python setup (3.11.x as per `render.yaml`)
  - Create venv and install deps
    - Windows (PowerShell): `py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
    - macOS/Linux: `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

- Run the app locally (FastAPI + Dash, no DB)
  - Start: `uvicorn src.backend.api:app --reload`
  - Open: http://127.0.0.1:8000/dash/ (health: http://127.0.0.1:8000/health)

- Tests (pytest)
  - All tests: `pytest -q`
  - With coverage: `pytest --cov=src --cov=backend --cov-report=term-missing -q`
  - Single file: `pytest tests/test_api.py -q`
  - Single test: `pytest tests/test_api.py::test_health -q`
  - Note: `pytest.ini` sets `pythonpath = .` and `asyncio_default_fixture_loop_scope = function` to avoid import errors and asyncio warnings.

- Data pipeline
  - Ingest raw placeholders: `python -m src.pipeline.ingest`
  - Preprocess: `python -m src.pipeline.preprocess`
  - Generate synthetic data (optional): `python -m src.pipeline.synthetic`
  - Fairness report (optional): `python -m src.pipeline.fairness`
  - Outputs are written to `data/raw/` and `data/processed/` (see `README.md`).

- Docker/PostGIS stack (optional, DB-enabled API)
  - Copy env: `cp .env.example .env` (or create `.env`) to supply optional variables
  - Start services: `docker compose up --build`
    - API (FastAPI+Dash) listens on http://localhost:8000 with Dash at `/dash`
    - PostGIS is exposed on port 5432
  - Rebuild only API: `docker compose build api`
  - Apply DB migrations (inside container): `docker compose exec api alembic upgrade head`
  - Seed demo data (areas, energy, traffic):
    - PowerShell: `.\\scripts\\seed-db.ps1` (seeds default files)
    - Bash: `./scripts/seed-db.sh` (seeds default files)
    - Custom: pass file paths to seed only specific files
  - Optional DB-backed tests:
    - Enable: set `E2E_DOCKER=1`, start stack (`docker compose up -d`), then `pytest -q`
    - Tests live in `tests/test_db_endpoints.py` and hit `http://localhost:8000`

- Linting/formatting
  - Install dev tools: `pip install -r requirements-dev.txt`
  - Check: `ruff check .` and `black --check .`
  - Fix: `ruff check --fix .` and `black .`
  - Scripts:
    - PowerShell: `.\\scripts\\lint.ps1` (or `.\\scripts\\lint.ps1 -Fix`), `.\\scripts\\format.ps1`
    - Bash: `./scripts/lint.sh`, `./scripts/format.sh`
  - Git hooks (pre-commit):
    - Install: `pip install -r requirements-dev.txt && pre-commit install`
    - Run on all files: `pre-commit run --all-files`
    - Hooks include: Ruff (with autofix), Black, and Mypy
- Type checking (mypy)
  - Install dev tools: `pip install -r requirements-dev.txt`
  - Run type check: `mypy -p src -p backend`

- Deployment (Render)
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn src.backend.api:app -k uvicorn.workers.UvicornWorker --timeout 120`
  - Health check path: `/health` (see `render.yaml`, `Procfile`).
  - Dash mounting uses `a2wsgi.WSGIMiddleware` (replaces deprecated Starlette WSGI middleware).

## Architecture and structure (big picture)

SUSPS is organized around a lightweight FastAPI app that mounts a Dash UI, plus an optional, database-enabled variant for local development with PostGIS.

- Web application (no-DB path used for dev/tests/deploy)
  - Entrypoint: `src/backend/api.py` defines a FastAPI app with CORS, a `/health` endpoint, and a root redirect to `/dash/`.
  - UI: `src/webapp/app.py` provides `create_dash_app(...)` (Dash + Bootstrap), mounted under `/dash` via `WSGIMiddleware`.
  - Deployment: Render uses `Procfile` and `render.yaml` to run `gunicorn` with Uvicorn workers; health is `/health`.

- Data pipeline (file-based artifacts)
  - Modules under `src/pipeline/` generate small CSV artifacts to `data/raw/` and `data/processed/`. Paths are centralized in `src/pipeline/config.py` and created on demand. External dataset locations are read from environment variables when provided.

- Optional DB-enabled backend (Docker/PostGIS)
  - Service composition: `docker-compose.yml` starts a PostGIS database and a FastAPI service built from `backend/`.
  - API: `backend/app/main.py` assembles the app, includes API routes from `backend/app/api/routes.py`, and mounts a minimal Dash app from `backend/app/dash_app/`.
  - Persistence: SQLAlchemy models in `backend/app/models/tables.py` with a declarative base (`backend/app/models/base.py`). `DATABASE_URL` is read from the environment (defaults to the `db` service). PostGIS types are used for geometry.
  - Migrations: Alembic configured via `backend/alembic.ini` and `backend/alembic/env.py` with autogenerate support (`alembic upgrade head`).

- Tests
  - `tests/test_api.py` exercises the no-DB FastAPI app’s `/health` endpoint using `httpx.AsyncClient`.
  - `tests/test_app.py` validates that the Dash app is constructible with the expected title.
  - `tests/test_models.py` is a placeholder that imports `src.backend.models` (this package is not implemented under `src/` yet).

Key URLs
- Health: `/health`
- Dashboard: `/dash/`
- Non-DB demo API (Render path): `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/config` (GET/POST)
- DB-backed API (Docker): `/areas`, `/energy`, `/traffic`, summaries at `/energy/summary`, `/traffic/summary`

UI notes (Render):
- The dashboard includes a "Data source" toggle (Demo | API). Default is controlled by env var `DEFAULT_DATA_SOURCE` (demo/api). The toggle updates Growth/Energy/Traffic charts by calling local model stubs or the API endpoints.

Examples (non-DB demo responses, truncated):
- `/growth`
  {"items": [{"year": 2025, "predicted_population": 800000}, {"year": 2026, "predicted_population": 824000}]}
- `/energy`
  {"items": [{"hour": 0, "demand_mwh": 5.0}, {"hour": 8, "demand_mwh": 8.0}]}
- `/traffic`
  {"items": [{"hour": 7, "volume": 850}, {"hour": 18, "volume": 900}]}

## Data sources and environment

- Primary APIs and keys
  - OPENWEATHER_API_KEY (default weather provider)
  - OPEN_AQ_API_KEY (OpenAQ air quality)
  - TOMTOM_API_KEY (traffic flow sampling)
- Provider toggles
  - WEATHER_PROVIDER: `openweather` (default) or `open-meteo`
  - TRAFFIC_PROVIDER: `tomtom` (default) or `synthetic`
- Location
  - CITY_LAT / CITY_LON (defaults to Nairobi CBD)
- Raw and processed
  - Ingest writes to `data/raw/`; preprocess writes to `data/processed/`.
  - Growth forecast is precomputed to `data/processed/growth_forecast_city.csv` when census data is available.

## Latest changes (2025-11-10)

- UI: Fixed, dark sidebar flush-left with full-width active highlight; resolved Dash `Div` children error; placeholders render.
- Pipeline: API-first ingestion for weather (OpenWeather), air quality (OpenAQ), traffic (TomTom) with fallbacks to local raw files and then synthetic.
- Urban Growth: Added catalog and features outputs from `data/raw/Urban_Growth`.
- Models/API: Endpoints now prefer processed outputs; added `/energy/summary` and `/traffic/summary`; `/growth` prefers precomputed forecast.
- Config: Removed unused COPERNICUS_PATH, NIGHTLIGHTS_PATH, GHSL_PATH, GOOGLE_MAPS_API_KEY; added WEATHER_PROVIDER and TRAFFIC_PROVIDER.

---

## Environment parity: Local vs Render (processed → DB, identical data)

Overview
- Unified API: `src/backend/api.py` loads `.env` locally and prefers `LOCAL_DATABASE_URL` when `USE_LOCAL_DB=true`. On Render set `USE_DB=1` and provide `DATABASE_URL` for the managed Postgres.
- Schema: Alembic migrations (`backend/alembic`) run in both environments. Render runs them on start (see `render.yaml`).
- Data: Keep the same "raw" under `data/raw/` (local) and in S3 (Render). A bootstrap can pull raw from S3, run ingest+preprocess, then load processed into the DB.

Local workflow (uses `.env` paths + local DB)
1. Generate processed artifacts (from local raw and APIs):
   ```bash
   python -m src.pipeline.ingest
   python -m src.pipeline.preprocess
   ```
2. Load processed into Postgres (today by default):
   ```bash
   # Ensure LOCAL_DATABASE_URL is set in .env and Postgres is running
   $env:DATABASE_URL="postgresql+psycopg2://postgres@localhost:5432/susps_db_local"
   python -m backend.app.etl.load_processed_to_db --date (Get-Date).ToString('yyyy-MM-dd')
   ```
3. Run the unified API + Dash (defaults to API data):
   ```bash
   uvicorn src.backend.api:app --reload
   ```

Render workflow (uses S3 raw + managed Postgres)
- Required env vars: `USE_DB=1`, `DATABASE_URL`, `USE_S3_STORAGE=true`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_BUCKET_NAME`, `AWS_REGION`, `AWS_S3_DATA_PREFIX`.
- First deploy (recommended): set `DB_BOOTSTRAP_ON_START=1` so the service will:
  1) pull raw from S3 → `data/raw/`
  2) run `ingest` → canonical raw CSVs
  3) run `preprocess` → `data/processed/`
  4) load processed into DB (today)
  Then the service starts Gunicorn for the unified API.
- Subsequent deploys: set `DB_BOOTSTRAP_ON_START=0` for faster starts.

S3 parity tools (keep Render in sync with local `data/raw/`)
- Check differences vs S3:
  ```bash
  python -m src.pipeline.s3_sync --check
  ```
- Upload missing/changed files:
  ```bash
  python -m src.pipeline.s3_sync --push
  ```
- Download from S3 (to reproduce Render locally):
  ```bash
  python -m src.pipeline.s3_sync --pull
  ```

API behavior (DB-first with graceful fallbacks)
- When `USE_DB=1` (or `USE_LOCAL_DB=true`) and a `*_DATABASE_URL` is set, the unified API will read from DB for:
  - `/energy`, `/traffic`: recent series (predicted vs actual)
  - `/energy/summary`, `/traffic/summary`: area-level aggregates
  - `/areas`: list of urban areas
- If DB is disabled or empty, endpoints fall back to processed artifacts; if those are missing, they fall back to synthetic demo data.

Dashboard defaults (real data by default)
- The sidebar "Data source" defaults to "API (processed/DB)". Switch to "Demo (fallback)" only for offline demos.
- Charts adapt to the available shape:
  - Energy & Traffic: show predicted vs actual when DB-backed; otherwise 24h profiles from processed.
  - Energy summary: DB → grouped by area (predicted/actual); processed → sector demand.
  - Traffic summary: DB → grouped by area (predicted/actual); processed → hourly averages.

Operational notes
- After changing local `data/raw/`, run `s3_sync --check/--push` to upload diffs, then on Render either temporarily set `DB_BOOTSTRAP_ON_START=1` and redeploy, or run `python -m backend.app.etl.bootstrap_db` in a Render shell to regenerate processed artifacts and refresh the DB.
- Keep secrets (DB and AWS) only in environment variables; `.env` remains uncommitted.
