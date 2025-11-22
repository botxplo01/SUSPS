# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

It focuses on day-to-day development workflows: how to set up the environment, run the backend and frontend, work with the data pipeline, and deploy to Render. For a dated snapshot of project progress and roadmap, see `system_status.md`. For thesis-style system documentation, see `docs/documentation.md`.

## Rules (project)
- Keep GitHub tracking issues in sync with roadmap milestones and tasks. Use `gh issue` to view/update when appropriate.
- After modifying code, always run formatting and lint checks locally:
  - `ruff check .` (use `ruff check --fix .` to autofix)
  - `black --check .` (use `black .` to format)
- Run unit tests before pushing when changes affect logic.
- Never commit secrets. Use environment variables locally and in Render.
- Only use high-quality free, free-tier, freemium, and open-source resources/tools. Avoid paid tools or those requiring credit cards.
- Keep comments concise and implementation-focused; avoid AI/meta commentary and other non-essential remarks.
- Treat `documentation.md` as the single source of thesis-style system documentation; when major features, architecture, or data sources change, update this file alongside `system_status.md`.

## Common commands

- Python setup (3.11.x as per `render.yaml`)
  - Create venv and install deps
    - Windows (PowerShell): `py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
    - macOS/Linux: `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

- Run the backend locally (FastAPI API, no DB)
  - Start: `uvicorn src.backend.api:app --reload`
  - Open: http://127.0.0.1:8000/docs (health: http://127.0.0.1:8000/health)

- Run the React frontend (Vite + React + Tailwind)
  - From repo root: `cd src/frontend`
  - Install deps (first time): `npm install`
  - Start dev server: `npm run dev` (defaults to `http://localhost:5173`)

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
  - Backend service (`susps-web`): built and started via `render.yaml` using `pip install -r requirements.txt` and `./scripts/render_start.sh` (which can optionally bootstrap S3 + pipeline + DB, then runs `gunicorn src.backend.api:app -k uvicorn.workers.UvicornWorker --timeout 120`).
  - Health check path: `/health` (see `render.yaml`, `scripts/render_start.sh`).
  - Root path `/` redirects to `/docs` on the backend.
  - Frontend static site: a separate Render Static Site pointing at `src/frontend` with build command `npm install && npm run build`, publish directory `dist`, and env var `VITE_API_BASE_URL` set to the backend URL (e.g. `https://susps-web.onrender.com`).

## Quick start (local full stack)

### Option A – FastAPI API + React SPA (no DB)
- Create and activate a virtualenv and install Python deps (see commands above).
- In one terminal, run `uvicorn src.backend.api:app --reload`.
- In another terminal, from `src/frontend`, run `npm install` (first time) then `npm run dev`.
- Open `http://localhost:5173`, ensure `VITE_API_BASE_URL` points at the backend (default `http://127.0.0.1:8000`), and select "Nairobi" in the sidebar to load data.

### Option B – With local Postgres (DB-backed API)
- Start PostgreSQL and create a local database (e.g. `susps`) and user (e.g. `susps_user`).
  - Example (psql): `CREATE DATABASE susps OWNER susps_user;`
  - Apply the schema dump once to initialize tables: `psql -U susps_user -d susps -f src/backend/db/susps_schema_dump.sql`.
- Set `USE_LOCAL_DB=true` and `LOCAL_DATABASE_URL` in `.env` (e.g. `postgresql+psycopg2://susps_user:password@localhost:5432/susps`).
- Generate processed artifacts and seed the DB:
  ```bash
  python -m src.pipeline.ingest
  python -m src.pipeline.preprocess
  python -m src.backend.db.seed_from_processed
  ```
- Then run the FastAPI backend and React frontend as in Option A.

## Architecture and structure (big picture)

### Repository structure (streamlined)
- src/
  - backend/: unified FastAPI app (primary API for local + Render) and advisory module
  - frontend/: Vite + React + Tailwind SPA (`src/frontend`) providing the SUSPS UI.
  - pipeline/: ingest, preprocess, synthetic, and S3 sync utilities
  - models/: deterministic helpers and lightweight stubs (growth/energy/traffic simulation, time-series, etc.) used by the backend; the UI now relies only on API endpoints rather than local demo stubs.
- backend/: optional DB-focused Docker/PostGIS stack used for experiments and DB-backed E2E tests; not required for the final-year Render deployment path.
- tests/: unit and e2e tests
- data/: city-scoped outputs under `data/<CITY>/{raw,processed}` (default CITY=Nairobi)

Notes
- The `backend/` Docker stack is optional and used for DB-enabled experiments/E2E tests; it reuses the same FastAPI API and does not provide a separate UI.
- Prefer `src/backend/api.py` for local and Render deployments.

### Feature: AI Advisory Engine (Hugging Face)
- Purpose: Turns SUSPS predictions (growth, energy, traffic) into actionable, model-generated insights displayed in the UI.
- How it works:
  - Backend endpoint `/advisory/{scope}` compiles recent predictions (DB → processed → synthetic), optionally scoped by `zone_id` (selected area), builds a compact summary, and queries a Hugging Face model for insights via the free Inference API.
  - The advisory engine now incorporates the selected `zone_id` into its prompt and cache key so guidance can be area-specific while remaining deterministic and cached.
  - Default model: `meta-llama/Meta-Llama-3.1-8B-Instruct` with a lightweight fallback `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (free-tier friendly).
  - The React SPA shows an "AI Analysis & Insights" panel on the Dashboard, Urban Growth, Energy, and Traffic pages that calls the advisory endpoint with the currently selected area (when available) and renders formatted plain-text paragraphs (markdown syntax stripped) via a `FormattedInsights` component, which drops redundant "Insights" headings/underlines and highlights the main title, profile headings (e.g. Energy Profile, Traffic Profile, Growth in Population), and "Recommended Actions" / Short-/Medium-/Long-term sections.
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
  4) Markdown-style insights are rendered inside the page's "AI Analysis & Insights" card with headings/profile sections emphasized by `FormattedInsights`.

SUSPS is organized around a lightweight FastAPI API plus a separate React SPA frontend, with an optional, database-enabled variant for local development with PostGIS.

- Web application (no-DB path used for dev/tests/deploy)
  - Backend: `src/backend/api.py` defines a FastAPI app with CORS, a `/health` endpoint, and a root redirect to `/docs`.
  - Frontend: `src/frontend` contains the Vite+React+Tailwind SPA. Run it with `npm run dev` (from `src/frontend`), pointing `VITE_API_BASE_URL` at the FastAPI backend.
  - Deployment: Render uses `Procfile` and `render.yaml` to run `gunicorn` with Uvicorn workers; health is `/health`.

- Data pipeline (file-based artifacts)
-  - Modules under `src/pipeline/` generate small CSV artifacts to `data/<CITY>/raw/` and `data/<CITY>/processed/`. Paths are centralized in `src/pipeline/config.py` and created on demand. Raw artifacts are grouped into domain-specific subfolders (e.g., `data/Nairobi/raw/Demographics_and_Population/worldpop_summary.csv`, `.../Energy_and_Infrastructure/energy_demand.csv`, `.../Environmental_and_Climate/environment_monthly.csv`, `.../Mobility_and_Transport/traffic_flows.csv`), while processed artifacts remain flat under `data/<CITY>/processed/`. External dataset locations (including GRID3 settlements, MATATUS, OSM, and census CSVs) are read from environment variables when provided.
-  - Daily/Monthly ingest: `src/pipeline/ingest.py` pulls WorldPop/energy CSVs, **live TomTom traffic flows** (when `TOMTOM_API_KEY` and `TRAFFIC_PROVIDER=tomtom` are set), **live weather** (OpenWeather/Open‑Meteo controlled by `WEATHER_PROVIDER`), and **live air quality** (OpenAQ via `OPEN_AQ_API_KEY`, with a fallback to `Air_Quality_Data_2025.csv` under `Environmental_and_Climate`), writing `worldpop_summary.csv`, `energy_demand.csv`, `traffic_flows.csv`, `environment_monthly.csv`, `air_quality_raw.csv` (when available), and `socioeconomic.csv` into their respective domain subfolders beneath `data/<CITY>/raw/`.
-  - Processing: `src/pipeline/preprocess.py` creates `traffic_features.csv` and a MATATUS/OSM-enriched `traffic_enriched_features.csv`, `environment_features.csv` and a fused `environment_aq_features.csv` (weather + AQ + pollution_index), `air_quality_daily.csv`, `worldpop_features.csv`, socio-economic features, deterministic `hotspots_areas.csv` / `hotspots_areas_forecast.csv` used for optimal zones, and additional summary tables that ensure all curated raw datasets are used: `demographic_raster_summary.csv` (population TIFFs under `Demographics_and_Population`), `landcover_raster_summary.csv` (land-cover TIFFs under `Environmental_and_Climate`), `mobility_gis_layers.csv` (layers inside `Mobility_and_Transport/GIS_DATA_2019.zip`), and optional `urban_growth_catalog.csv` / `urban_growth_features.csv` when `GRID3_SETTLEMENTS_PATH` / `SETTLEMENTS_PATH` is configured.
-  - Overpass/OSM integration: `src/pipeline/osm_overpass.py` provides a small Overpass client (bbox, named area, polygon) that returns GeoJSON. `src/pipeline/ingest.py` can optionally call this client and persist an `osm_snapshot.geojson` into `data/<CITY>/raw/` (grouped under the appropriate domain) when `SUSPS_FETCH_OSM=1` (disabled by default so tests and local runs remain offline and deterministic).


- Tests
  - API and advisory: `tests/test_api.py`, `tests/test_simulation_api.py`, `tests/test_ts_forecast_api.py`, `tests/test_hotspots_api.py`, `tests/test_hotspots_forecast_api.py`.
  - Pipeline: `tests/test_pipeline.py` runs ingest → preprocess → synthetic → fairness in a temporary data directory.
  - DB/E2E: `tests/test_db_endpoints.py` (skipped unless `E2E_DOCKER=1`) checks DB-backed `/energy`, `/traffic`, and summary endpoints.
  - Basic package check: `tests/test_models.py` imports `src.backend.models`.

Key URLs
- Health: `/health`
- Backend docs: `/docs` (FastAPI/Swagger UI)
- React frontend (local dev): `http://localhost:5173` (Vite dev server; see `src/frontend`)
- Core data: `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`
- Areas & metadata: `/areas`, `/processed_data`, `/simulation_inputs`
- Simulation & time-series: `/simulate/run`, `/simulation_inputs` (POST), `/ts/forecast`
- Environment & air quality: `/environment/features`, `/air_quality/daily`
- Hotspots: `/hotspots/areas`, `/hotspots/areas/forecast`, `/hotspots/scores`
- Authentication: `/auth/signup`, `/auth/login` (backed by the `users` table defined in `src/backend/db/susps_schema_dump.sql`; used by the React sign-in/sign-up pages and client-side auth context)
- AI Advisory: `/advisory/{scope}` where `scope` ∈ {`dashboard`,`growth`,`energy`,`traffic`} (returns markdown-like insights that the frontend renders as plain paragraphs with key headings bolded). The endpoint accepts `zone_id` and optional `scenario` (e.g. `growth_baseline`, `growth_simulate`, `energy_demand_response`), which are included in the HF prompt and in the cache key so advisory can distinguish between baseline and SIMULATE scenarios for a given area.
- AI Advisory Batch: `/advisory_batch?scopes=dashboard,energy` (returns multiple scopes in one call)

### Frontend map for agents (what each page talks to)

- Dashboard (React route `/dashboard`)
  - Sidebar: `area-select` dropdown populated from `/areas`. No data is loaded into the main charts until an area is selected.
  - Charts: bar chart for urban growth, line chart for energy, and histogram for traffic, plus summary tiles; all use `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary` in REAL mode only (the dashboard does not show Real/Simulate or Action toggles).
  - Behavior: when no area is selected, graphs render placeholder figures with "(select an area)" in the title and the page shows descriptive text only; once an area is selected, charts call the live API endpoints (which internally prefer DB/processed data with synthetic fallback as needed).
  - Advisory: "Insights" panel is gated on area selection and then calls `/advisory/dashboard` (or batch) and renders formatted plain-text paragraphs with only key headings bolded.
- Growth page
  - Shares the same `area-select` gate as the dashboard and uses `/growth` for the current city/area context.
  - Shows only descriptions until an area is selected; then renders the growth series and `/advisory/growth` insights.
  - SIMULATE: header `ModeToggle` (Real/Simulate) and floating `ActionToggle` drive `/simulate/run` with growth-specific parameters such as `population_scale`, `annual_rate_delta_pct`, and optional `shock_year`/`shock_pct`. The UI exposes these as sliders/inputs in a "Simulation parameters" panel.
- Energy page
  - Uses `/energy` and `/energy/summary` for the selected city/area.
  - Same area gating and description-first behavior; advisory via `/advisory/energy`.
  - SIMULATE: `ModeToggle` + `ActionToggle` call `/simulate/run` with energy parameters including `demand_scale`, `peak_hour_shift`, `peak_scale`, `offpeak_scale`, and `flatten_ratio`, controlled via a simulation parameters panel (e.g. demand response or time-of-use tariff scenarios).
- Traffic page
  - Uses `/traffic` and `/traffic/summary` for the selected city/area.
  - Same area gating and description-first behavior; advisory via `/advisory/traffic`.
  - SIMULATE: uses `/simulate/run` with traffic parameters such as `volume_scale`, `peak_hour_shift`, `peak_scale`, `offpeak_scale`, and `flatten_ratio`, controlled by a simulation parameters panel to represent scenarios like remote work adoption or congestion pricing.
- Hotspot maps (React UI + OSM-based overlays)
  - Backend and pipeline are ready: `/hotspots/areas` and `/hotspots/areas/forecast` expose static and multi-year hotspot scores.
  - React frontend renders an OpenStreetMap-based Leaflet map that overlays hotspot scores from `/hotspots/areas` and `/hotspots/areas/forecast` as red circles; when Optimize is active, improving areas (based on forecast vs current scores) are highlighted in green as potential optimal zones. Units in the hotspot lists and optimal-zones panel are ordered alphabetically (e.g., Unit A, Unit B, Unit C), and when no area is selected the map card shows the same "No data available." placeholder text as the other cards.
  - Joining hotspot scores with ward/zone GeoJSON or Overpass geometries to render full choropleth maps remains a future enhancement; the current implementation uses a simple radial layout around the city center.

UI notes (Render):
- The dashboard/sidebar includes an `area-select` dropdown populated from `/areas`. Until an area is selected, pages show descriptive content and placeholder charts only; once selected, the UI calls the real API endpoints for data (no Demo/API toggle in the UI).
- The legacy `/config` endpoint and `DEFAULT_DATA_SOURCE` toggle have been removed; the backend always uses processed/DB data with deterministic fallbacks (no Demo/API switch).

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
-  - Ingest writes canonical raw CSVs into domain-specific subfolders under `data/<CITY>/raw/` (e.g., `Demographics_and_Population/worldpop_summary.csv`, `Energy_and_Infrastructure/energy_demand.csv`, `Environmental_and_Climate/environment_monthly.csv`, `Mobility_and_Transport/traffic_flows.csv`, plus `socioeconomic.csv` in Demographics); preprocess writes all derived artifacts into `data/<CITY>/processed/`.
-  - Growth forecast is precomputed to `data/<CITY>/processed/growth_forecast_city.csv` when census data is available, and summary tables such as `demographic_raster_summary.csv`, `landcover_raster_summary.csv`, `mobility_gis_layers.csv`, and `urban_growth_features.csv` ensure that all curated TIFF/ZIP/GRID3 datasets participate in the pipeline.
- Storage and parity (local + Render)
  - Local: canonical datasets live under `data/<CITY>/{raw,processed}` and feed the local PostgreSQL instance when `USE_LOCAL_DB=true` (or equivalent env).
  - Render: uses managed PostgreSQL plus AWS S3 bucket `susps-raw-data` (region `eu-north-1`) to hold the same raw datasets.
  - Goal: keep local `data/<CITY>/raw/` and S3 `susps-raw-data/<CITY>/raw/` in sync so the frontend behaves identically locally and on Render.
## Status and roadmap

For a dated snapshot of the system’s current state, roadmap, and acceptance criteria, see `system_status.md`. WARP.md focuses on day-to-day development workflows (commands, environment parity, and architecture) and intentionally does not maintain a detailed change log.

---

## Environment parity: Local vs Render (processed → DB, identical data)

Overview
- Unified API: `src/backend/api.py` loads `.env` locally and prefers `LOCAL_DATABASE_URL` when `USE_LOCAL_DB=true`. On Render set `USE_DB=1` and provide `DATABASE_URL` for the managed Postgres.
- Schema: for the final-year project path, initialize each Postgres instance (local or Render) by applying `src/backend/db/susps_schema_dump.sql` once via `psql`; this creates the `users`, `urban_areas`, `energy_consumption`, `traffic_flow`, `environment_features`, `air_quality_daily`, `hotspot_scores`, etc. tables. Legacy Alembic migrations under `backend/` are optional and are not used by the Render deployment.
- Render DB URLs: set `DATABASE_URL` to the exact connection string from the Render Postgres dashboard (usually starting with `postgres://`); the backend automatically normalizes this to `postgresql+psycopg2://` and appends `sslmode=require` for `*.render.com` hosts.
- Data: Keep the same city-scoped raw under `data/<CITY>/raw/` (local) and in S3 bucket `susps-raw-data` (Render, region `eu-north-1`). A bootstrap can pull raw from S3, run ingest+preprocess, then load processed into the DB in both environments.

Local workflow (uses `.env` paths + local DB)
1. Generate processed artifacts (from local raw and APIs):
   ```bash
   python -m src.pipeline.ingest
   python -m src.pipeline.preprocess
   ```
2. Load processed into Postgres:
   ```bash
   # Ensure USE_LOCAL_DB=true and LOCAL_DATABASE_URL are set in .env and Postgres is running
   python -m src.backend.db.seed_from_processed
   ```
3. Run the FastAPI backend:
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
- DB reset (development only):
  - To completely reinitialise the Render Postgres schema, connect with `psql` and run `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` for the `susps` database, then apply `src/backend/db/susps_schema_dump.sql` and rerun the bootstrap (ingest → preprocess → `seed_from_processed`). Alternatively, uncomment the optional `DROP TABLE IF EXISTS` block at the top of `susps_schema_dump.sql` and run it once against the target database.
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
- After changing local `data/<CITY>/raw/`, run `s3_sync --check/--push` to upload diffs, then on Render temporarily set `DB_BOOTSTRAP_ON_START=1` and redeploy so the service reruns ingest, preprocess, and DB seeding.
- Keep secrets (DB and AWS) only in environment variables; `.env` remains uncommitted.
