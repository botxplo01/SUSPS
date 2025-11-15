# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Rules (project)
- Keep GitHub tracking issues in sync with roadmap milestones and tasks. Use `gh issue` to view/update when appropriate.
- After modifying code, always run formatting and lint checks locally:
  - `ruff check .` (use `ruff check --fix .` to autofix)
  - `black --check .` (use `black .` to format)
- Run unit tests before pushing when changes affect logic.
- Never commit secrets. Use environment variables locally and in Render.
- Only use high-quality free, free-tier, freemium, and open-source resources/tools. Avoid paid tools or those requiring credit cards.

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
- Outputs are written to `data/<CITY>/raw/` and `data/<CITY>/processed/` (default CITY=Nairobi; see `README.md`).


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

### Repository structure (streamlined)
- src/
  - backend/: unified FastAPI app (primary API for local + Render) and advisory module
  - webapp/: single Dash UI used by both unified API and Docker backend
  - pipeline/: ingest, preprocess, synthetic, and S3 sync utilities
  - models/: deterministic helpers and lightweight stubs (growth/energy/traffic simulation, time-series, etc.) used by the backend; the Dash UI now relies only on API endpoints rather than local demo stubs.
- backend/: removed (Docker and container-only backend are not used for the final-year project)
- tests/: unit and e2e tests
- data/: city-scoped outputs under `data/<CITY>/{raw,processed}` (default CITY=Nairobi)

Notes
- The Docker backend is maintained for DB-enabled E2E tests but reuses the same Dash UI as the unified API.
- Prefer src/backend/api.py for local and Render deployments.

### Feature: AI Advisory Engine (Hugging Face)
- Purpose: Turns SUSPS predictions (growth, energy, traffic) into actionable, model-generated insights displayed in the UI.
- How it works:
  - Backend endpoint `/advisory/{scope}` compiles recent predictions (DB → processed → synthetic), optionally scoped by `zone_id` (selected area), builds a compact summary, and queries a Hugging Face model for insights via the free Inference API.
  - The advisory engine now incorporates the selected `zone_id` into its prompt and cache key so guidance can be area-specific while remaining deterministic and cached.
  - Default model: `meta-llama/Meta-Llama-3.1-8B-Instruct` with a lightweight fallback `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (free-tier friendly).
  - The Dash UI shows an “Insights” panel on Dashboard, Growth, Energy, and Traffic pages that calls the advisory endpoint with the currently selected area (when available) and renders markdown.
- Configuration:
  - Env vars: `HF_API_KEY` (preferred; see `.env`) or, if needed, `HF_API_TOKEN` / `HUGGINGFACEHUB_API_TOKEN`.
  - Optional: `HF_MODEL_NAME` to override the default advisory/chat model, plus specialized models
    `HF_GROWTH_TS_MODEL`, `HF_ENERGY_TS_MODEL`, `HF_TRAFFIC_TS_MODEL`, and `HF_GEOSPATIAL_MODEL`
    for time-series and geospatial reasoning (all chosen from high-quality free models on Hugging Face).
- Notes:
  - Requests are cached (10 min) to control latency/cost; if the API is unavailable, a deterministic rule-based fallback text is returned.
  - Stable cache key (sha256) avoids cache churn; includes model and timestamp.
  - Small retry with exponential backoff for transient free-tier queueing.
  - Batch endpoint `/advisory_batch` computes multiple scopes concurrently with shared data bundles.
  - Complies with the project rule to use only high-quality free/freemium/open-source resources.
- Example (end-to-end):
  1) Generate predictions (API or DB-backed)
  2) UI/page loads and calls `/advisory/{scope}` (or `/advisory_batch` for multiple scopes)
  3) Backend summarizes recent series and queries Hugging Face model
  4) Markdown insights are rendered under the page's "Insights" section with model and timestamp

SUSPS is organized around a lightweight FastAPI app that mounts a Dash UI, plus an optional, database-enabled variant for local development with PostGIS.

- Web application (no-DB path used for dev/tests/deploy)
  - Entrypoint: `src/backend/api.py` defines a FastAPI app with CORS, a `/health` endpoint, and a root redirect to `/dash/`.
  - UI: `src/webapp/app.py` provides `create_dash_app(...)` (Dash + Bootstrap), mounted under `/dash` via `WSGIMiddleware`.
  - Deployment: Render uses `Procfile` and `render.yaml` to run `gunicorn` with Uvicorn workers; health is `/health`.

- Data pipeline (file-based artifacts)
  - Modules under `src/pipeline/` generate small CSV artifacts to `data/<CITY>/raw/` and `data/<CITY>/processed/`. Paths are centralized in `src/pipeline/config.py` and created on demand. External dataset locations are read from environment variables when provided.


- Tests
  - `tests/test_api.py` exercises the no-DB FastAPI app’s `/health` endpoint using `httpx.AsyncClient`.
  - `tests/test_app.py` validates that the Dash app is constructible with the expected title.
  - `tests/test_models.py` is a placeholder that imports `src.backend.models` (this package is not implemented under `src/` yet).

Key URLs
- Health: `/health`
- Dashboard: `/dash/`
- Core data: `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/config` (GET/POST)
- Areas & metadata: `/areas`, `/processed_data`, `/simulation_inputs`
- Simulation & time-series: `/simulate/run`, `/simulation_inputs` (POST), `/ts/forecast`
- Hotspots: `/hotspots/areas`, `/hotspots/areas/forecast`
- AI Advisory: `/advisory/{scope}` where `scope` ∈ {`dashboard`,`growth`,`energy`,`traffic`} (returns markdown insights)
- AI Advisory Batch: `/advisory_batch?scopes=dashboard,energy` (returns multiple scopes in one call)

### Frontend map for agents (what each page talks to)

- Dashboard (`/dash/` root)
  - Sidebar: `area-select` dropdown populated from `/areas`. No data is loaded into the main charts until an area is selected.
  - Charts: growth, energy, traffic, plus summary tiles; use `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`.
  - Behavior: when no area is selected, graphs render placeholder figures with "(select an area)" in the title and the page shows descriptive text only; once an area is selected, charts call the live API endpoints (which internally prefer DB/processed data with synthetic fallback as needed).
  - Advisory: "Insights" panel is gated on area selection and then calls `/advisory/dashboard` (or batch) and renders markdown.
- Growth page
  - Shares the same `area-select` gate as the dashboard and uses `/growth` for the current city/area context.
  - Shows only descriptions until an area is selected; then renders the growth series and `/advisory/growth` insights.
- Energy page
  - Uses `/energy` and `/energy/summary` for the selected city/area.
  - Same area gating and description-first behavior; advisory via `/advisory/energy`.
- Traffic page
  - Uses `/traffic` and `/traffic/summary` for the selected city/area.
  - Same area gating and description-first behavior; advisory via `/advisory/traffic`.
- Hotspot maps (planned UI)
  - Backend and pipeline are ready: `/hotspots/areas` and `/hotspots/areas/forecast` expose static and multi-year hotspot scores.
  - Frontend will join these scores with ward/zone GeoJSON to render choropleth maps once the map components are implemented.

UI notes (Render):
- The dashboard/sidebar includes an `area-select` dropdown populated from `/areas`. Until an area is selected, pages show descriptive content and placeholder charts only; once selected, the UI calls the real API endpoints for data (no Demo/API toggle in the UI).
- `DEFAULT_DATA_SOURCE` in `.env` is legacy and only affects internal fallback behaviour in `/config`; new features should not depend on it.

Examples (API responses, truncated):
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
- Raw and processed (local canonical layout)
  - Ingest writes to `data/<CITY>/raw/`; preprocess writes to `data/<CITY>/processed/`.
  - Growth forecast is precomputed to `data/<CITY>/processed/growth_forecast_city.csv` when census data is available.
- Storage and parity (local + Render)
  - Local: canonical datasets live under `data/<CITY>/{raw,processed}` and feed the local PostgreSQL instance when `USE_LOCAL_DB=true` (or equivalent env).
  - Render: uses managed PostgreSQL plus AWS S3 bucket `susps-raw-data` (region `eu-north-1`) to hold the same raw datasets.
  - Goal: keep local `data/<CITY>/raw/` and S3 `susps-raw-data/<CITY>/raw/` in sync so the frontend behaves identically locally and on Render.
## Latest changes (2025-11-15)

- Backend
  - Added deterministic SIMULATE engine and `/simulate/run` endpoint over existing growth/energy/traffic outputs.
  - Added generic time-series forecasting endpoint `/ts/forecast` using free Hugging Face models when configured, with deterministic fallbacks.
  - Added hotspot preprocessing in the pipeline (`preprocess_hotspots`, `preprocess_hotspots_forecast`) and endpoints `/hotspots/areas` and `/hotspots/areas/forecast`.
  - Added DB-oriented metadata endpoints `/areas`, `/processed_data`, `/simulation_inputs` and a portable schema dump at `src/backend/db/susps_schema_dump.sql`.

- Frontend (Dash)
  - Reworked layout to use a sidebar `area-select` dropdown populated from `/areas`.
  - Removed the demo vs API data-source toggle; the UI now always calls the real API endpoints and only shows data once an area is selected, otherwise showing descriptive placeholders.
  - Advisory "Insights" panels are now gated on area selection and continue to use the Hugging Face-powered backend.

- Environment parity
  - Confirmed the local vs Render story (local PostgreSQL + `data/<CITY>/{raw,processed}` vs Render PostgreSQL + S3 `susps-raw-data`) and S3 sync tooling as described below.

---

## Environment parity: Local vs Render (processed → DB, identical data)

Overview
- Unified API: `src/backend/api.py` loads `.env` locally and prefers `LOCAL_DATABASE_URL` when `USE_LOCAL_DB=true`. On Render set `USE_DB=1` and provide `DATABASE_URL` for the managed Postgres.
- Schema: Alembic migrations (`backend/alembic`) run in both environments. Render runs them on start (see `render.yaml`).
- Data: Keep the same city-scoped raw under `data/<CITY>/raw/` (local) and in S3 bucket `susps-raw-data` (Render, region `eu-north-1`). A bootstrap can pull raw from S3, run ingest+preprocess, then load processed into the DB in both environments.

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
- Render defaults: `AWS_BUCKET_NAME=susps-raw-data`, `AWS_REGION=eu-north-1` (bucket contains the same city-scoped raw datasets as local `data/<CITY>/raw/`).
- First deploy (recommended): set `DB_BOOTSTRAP_ON_START=1` so the service will:
  1) pull raw from S3 → `data/<CITY>/raw/`
  2) run `ingest` → canonical raw CSVs
  3) run `preprocess` → `data/<CITY>/processed/`
  4) load processed into DB (today)
  Then the service starts Gunicorn for the unified API.
- Subsequent deploys: set `DB_BOOTSTRAP_ON_START=0` for faster starts.

S3 parity tools (keep Render in sync with local `data/<CITY>/raw/`)
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

Dashboard defaults (area-driven)
- The sidebar `area-select` dropdown controls when real data is loaded; with no area selected, the dashboard shows only descriptive content and placeholder charts.
- Charts adapt to the available backend data (DB → processed → synthetic) but this choice is now internal to the API; there is no UI-level Demo/API toggle.
- Energy & Traffic: show predicted vs actual when DB-backed; otherwise 24h profiles from processed.
- Energy summary: DB → grouped by area (predicted/actual); processed → sector demand.
- Traffic summary: DB → grouped by area (predicted/actual); processed → hourly averages.

Operational notes
- After changing local `data/<CITY>/raw/`, run `s3_sync --check/--push` to upload diffs, then on Render either temporarily set `DB_BOOTSTRAP_ON_START=1` and redeploy, or run `python -m backend.app.etl.bootstrap_db` in a Render shell to regenerate processed artifacts and refresh the DB.
- Keep secrets (DB and AWS) only in environment variables; `.env` remains uncommitted.
