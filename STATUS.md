 # SUSPS Status & Workflows (Consolidated)
 
 This document consolidates:
 
 - `system_status.md` (dated status snapshot, what’s implemented, roadmap, acceptance criteria)
 - `WARP.md` (day-to-day development workflows, commands, environment parity guidance)
 
 It is intended to be a single source of truth for how the repo is structured, how to run it, and what remains.

 ## Table of contents

 - [Current status snapshot](#current-status-snapshot)
 - [Project rules](#project-rules)
 - [Quick start (local full stack)](#quick-start-local-full-stack)
 - [Common commands](#common-commands)
 - [Architecture (big picture)](#architecture-big-picture)
 - [Repository structure](#repository-structure)
 - [Backend API (key URLs)](#backend-api-key-urls)
 - [Frontend behavior (React SPA)](#frontend-behavior-react-spa)
 - [Data pipeline & layout](#data-pipeline--layout)
 - [Environment & configuration](#environment--configuration)
 - [Deployment (Render)](#deployment-render)
 - [Environment parity: Local vs Render (S3 + Postgres)](#environment-parity-local-vs-render-s3--postgres)
 - [What remains (near-term)](#what-remains-near-term)
 - [Roadmap & acceptance criteria (baseline)](#roadmap--acceptance-criteria-baseline)
 - [Notes](#notes)

 ## Changelog

 - **2025-12-28**: Consolidated `system_status.md` + `WARP.md` into `STATUS.md`.
 - **2025-12-30**: Snapshot-based advisory (POST), energy simulation normalization fix, improved TomTom traffic fallback and Live Traffic behavior, and repo-wide comment/author cleanup.
 - **2026-01-05**: Fixed mojibake/encoding artifacts in exports + empty-table placeholders; hardened `/traffic/live` freshness (no-store headers, cache-busting param, richer meta); improved TomTom live sampling (grid + jitter + configurable zoom/radius/max points).
 
 ## Current status snapshot
 
 - Snapshot date: **2025-12-30**
 - Tooling: Ruff/Black/Mypy/Pytest green locally.
 - Backend: FastAPI app in `src/backend/api.py` with deterministic fallbacks and optional Postgres.
 - Frontend: React + Tailwind SPA in `src/frontend`, area-driven (no Demo/API toggle).
 - Pipeline: ingest → preprocess producing canonical raw and processed artifacts under `data/<CITY>/...`.
 - Render: optional bootstrap on start (S3 pull → pipeline → seed DB) controlled by `DB_BOOTSTRAP_ON_START`.

 Recent updates included:

 - **Advisory**: snapshot-aware advisory generation so AI insights reflect the currently displayed series (Real/Predicted/Simulated/Optimal).
 - **Energy simulation**: normalized baseline energy shapes to avoid zero outputs when DB-style rows are used.
 - **Traffic**: TomTom-derived dynamic fallback profile to avoid static charts in deployments without DB history; Live Traffic uses manual refresh with visible freshness metadata.
 - **Exports/UI encoding**: removed mojibake characters (e.g. `â€”`, `Â©`) by replacing hardcoded strings with clean ASCII/Unicode (export footer text and table placeholders).
 - **Live Traffic sampling**: widened TomTom sampling from fixed 5 points to a configurable grid with jitter and zoom controls to avoid repeating identical segments.
 - **Code quality**: repo-wide comment cleanup and standardized author headers.
 
 ---
 
 ## Project rules
 
 - Keep GitHub tracking issues aligned with roadmap milestones/tasks.
 - After modifying code, run formatting/lint checks locally:
   - `ruff check .` (or `ruff check --fix .`)
   - `black --check .` (or `black .`)
 - Run unit tests before pushing when logic changes.
 - Never commit secrets; use `.env` locally and Render env vars in production.
 - Use only high-quality free / free-tier / open-source tools and APIs.
 - Keep comments concise and implementation-focused; avoid AI/meta commentary.
 - Treat `docs/documentation.md` as the thesis-style single source of documentation; keep it in sync with major changes.
 
 ---
 
 ## Quick start (local full stack)
 
 ### Prerequisites
 
 - Python 3.11.x
 - Node.js 18+
 - (Optional) PostgreSQL 14+
 
 ### Option A — FastAPI + React (no DB)
 
 1) Python env + deps
 
 - Windows (PowerShell)
   - `py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
 - macOS/Linux
   - `python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
 
 2) Run the backend
 
 - `uvicorn src.backend.api:app --reload`
 - Swagger UI: `http://127.0.0.1:8000/docs` (health: `http://127.0.0.1:8000/health`)
 
 3) Run the frontend
 
 - `cd src/frontend`
 - First time: `npm install`
 - Start: `npm run dev` (default `http://localhost:5173`)
 - Ensure `VITE_API_BASE_URL` points at the backend (default `http://127.0.0.1:8000`).
 
 4) Prepare data (recommended)
 
 - `python -m src.pipeline.ingest`
 - `python -m src.pipeline.preprocess`
 
 ### Option B — With local Postgres (DB-backed API)
 
 1) Start Postgres and create DB/user (example names)
 
 - DB: `susps`
 - User: `susps_user`
 
 2) Apply schema once
 
 - `psql -U susps_user -d susps -f src/backend/db/susps_schema_dump.sql`
 
 3) Configure `.env`
 
 - `USE_LOCAL_DB=true`
 - `LOCAL_DATABASE_URL=postgresql+psycopg2://susps_user:password@localhost:5432/susps`
 
 4) Generate artifacts and seed DB
 
 - `python -m src.pipeline.ingest`
 - `python -m src.pipeline.preprocess`
 - `python -m src.backend.db.seed_from_processed`
 
 5) Run as in Option A
 
 ---
 
 ## Common commands
 
 ### Tests
 
 - All tests: `pytest -q`
 - Coverage: `pytest --cov=src --cov=backend --cov-report=term-missing -q`
 - Single file: `pytest tests/test_api.py -q`
 - Single test: `pytest tests/test_api.py::test_health -q`
 
 Note: `pytest.ini` sets `pythonpath = .` and `asyncio_default_fixture_loop_scope = function`.
 
 ### Lint / format / typecheck
 
 - Dev tools: `pip install -r requirements-dev.txt`
 - Ruff: `ruff check .` (or `ruff check --fix .`)
 - Black: `black --check .` (or `black .`)
 - Mypy: `mypy -p src -p backend`
 - Pre-commit: `pre-commit run --all-files`
 
 ### Data pipeline
 
 - Ingest: `python -m src.pipeline.ingest`
 - Preprocess: `python -m src.pipeline.preprocess`
 - Synthetic (optional): `python -m src.pipeline.synthetic`
 - Fairness report (optional): `python -m src.pipeline.fairness`
 - S3 parity:
   - Check: `python -m src.pipeline.s3_sync --check`
   - Push: `python -m src.pipeline.s3_sync --push`
   - Pull: `python -m src.pipeline.s3_sync --pull`
 
 ---
 
 ## Architecture (big picture)
 
 SUSPS is organized around a lightweight FastAPI API plus a separate React SPA frontend, with an optional database-enabled variant.
 
 - Backend (FastAPI): `src/backend/api.py`
 - Frontend (React): `src/frontend`
 - Pipeline (Python): `src/pipeline/*`
 - Models: `src/models/*` (growth/energy/traffic helpers used by the backend)
 - Optional DB/E2E stack: `backend/` (not required for the Render deployment path)
 
 ### Data-source behavior (DB-first with graceful fallbacks)
 
 For most endpoints, the backend prefers:
 
 1) **DB** (when enabled and populated)
 2) **Processed artifacts** under `data/<CITY>/processed/`
 3) **Deterministic synthetic fallback** (for offline runs/tests)
 
 The UI does not expose a “Demo/API” toggle; this selection is internal to the API.
 
 ---
 
 ## Repository structure
 
 - `src/backend/`: unified FastAPI app + advisory + simulation + time-series
 - `src/frontend/`: Vite + React + Tailwind SPA
 - `src/pipeline/`: ingest, preprocess, synthetic, fairness, S3 sync
 - `src/models/`: growth/energy/traffic model helpers
 - `tests/`: unit and (optional) DB/E2E tests
 - `data/`: city-scoped outputs under `data/<CITY>/{raw,processed}`
 
 ---
 
 ## Backend API (key URLs)
 
 - Health: `GET /health`
 - Docs: `GET /docs` (via root redirect)
 
 ### Core data
 
 - `GET /growth`
 - `GET /energy` (supports `area_id`)
 - `GET /traffic` (supports `area_id`)
 - `GET /traffic/live` (TomTom provider when configured; includes freshness metadata)
 - `GET /energy/summary` (supports `area_id`)
 - `GET /traffic/summary` (supports `area_id`)
 
 ### Areas & metadata
 
 - `GET /areas`
 - `GET /processed_data`
 - `GET /simulation_inputs`
 - `POST /simulation_inputs`
 
 ### Simulation & forecasting
 
 - `POST /simulate/run` (modules: growth/energy/traffic/all; deterministic helpers)
 - `POST /ts/forecast` (generic time-series forecasting; HF-backed optional)
 
 ### Environment, air quality, hotspots
 
 - `GET /environment/features`
 - `GET /air_quality/daily`
 - `GET /hotspots/areas`
 - `GET /hotspots/areas/forecast`
 - `GET /hotspots/scores`
 
 ### Export
 
 - `POST /export` (pdf/csv/bundle; supports optional chart images from the frontend)
 
 ### Authentication (DB required)
 
 - `POST /auth/signup`
 - `POST /auth/login`
 
 ### AI advisory (Hugging Face, cached, with deterministic fallback)
 
 - `GET /advisory/status`
 - `GET /advisory/{scope}` where `scope ∈ {dashboard,growth,energy,traffic}`
   - Query params: `zone_id` and optional `scenario` (e.g. `growth_baseline`, `growth_simulate`)
 - `POST /advisory/{scope}` (recommended)
   - Accepts a snapshot of the series currently displayed in the UI so insights track REAL/PREDICT/SIMULATE/OPTIMIZE views.
   - Query params: `zone_id` and optional `scenario`
 - `GET /advisory_batch`
 
 ---
 
 ## Frontend behavior (React SPA)
 
 - SPA: Vite + React + TypeScript + Tailwind, Leaflet for maps.
 - Route protection: `/dashboard`, `/urban-growth`, `/energy`, `/traffic` are protected by client-side auth; redirects to `/signin`.
 - Area-driven UX:
   - Sidebar area dropdown is populated from `GET /areas`.
   - With no area selected, pages show descriptive content and placeholder visuals.
   - Once selected, pages call the API endpoints and render charts.
 - Domain pages (Growth/Energy/Traffic):
   - REAL vs SIMULATE mode toggle.
   - Actions: Predict (calls `/ts/forecast`), Simulate (calls `/simulate/run`), Optimize (derived overlay).
   - AI Analysis & Insights use the snapshot-based advisory path so the narrative reflects the currently displayed series.
 - Hotspot map:
   - Uses `/hotspots/areas` and `/hotspots/areas/forecast`.
   - Current implementation uses circle overlays; choropleths via GeoJSON join is a planned enhancement.

 Traffic page specifics:

 - Live Traffic card fetches from `/traffic/live` and exposes freshness/cached metadata.
 - Automatic polling is disabled; refresh is manual to reduce API usage.
 - Backend response includes sampling metadata (e.g. `zoom`, `grid_n`, `radius_deg`, `jitter_deg`, `points_target`) to help verify what was queried.
 
 ---
 
 ## Data pipeline & layout
 
 ### City scoping
 
 - Default city: **Nairobi**.
 - Controlled via environment (`DATA_CITY` or `CITY_NAME`).
 
 ### Output layout
 
 - Raw canonical inputs: `data/<CITY>/raw/<Domain>/...`
 - Processed features: `data/<CITY>/processed/...`
 
 Raw domain folders (created by `src/pipeline/config.py`):
 
 - `Demographics_and_Population/`
 - `Energy_and_Infrastructure/`
 - `Environmental_and_Climate/`
 - `Mobility_and_Transport/`
 - `Urban_Growth/`
 
 Examples of canonical raw outputs:
 
 - `Demographics_and_Population/worldpop_summary.csv`
 - `Demographics_and_Population/socioeconomic.csv`
 - `Energy_and_Infrastructure/energy_demand.csv`
 - `Mobility_and_Transport/traffic_flows.csv`
 - `Environmental_and_Climate/environment_monthly.csv`
 - Air quality ingestion uses OpenAQ when configured, with a fallback to `Air_Quality_Data_2025.csv` under `Environmental_and_Climate/`.
 
 Examples of processed outputs:
 
 - `environment_features.csv`, `environment_aq_features.csv`
 - `energy_features.csv`
 - `traffic_features.csv`, `traffic_enriched_features.csv`
 - `air_quality_daily.csv`
 - Hotspots: `hotspots_areas.csv`, `hotspots_areas_forecast.csv`
 - Summary tables integrating curated datasets: `demographic_raster_summary.csv`, `landcover_raster_summary.csv`, `mobility_gis_layers.csv`, optional `urban_growth_catalog.csv` / `urban_growth_features.csv`.
 
 Optional OSM/Overpass snapshot:
 
 - Enable: `SUSPS_FETCH_OSM=1` (disabled by default for offline determinism)
 - Output: `osm_snapshot.geojson` under `data/<CITY>/raw/`.
 
 ---
 
 ## Environment & configuration
 
 ### Provider API keys
 
 - `OPENWEATHER_API_KEY` (default weather provider)
 - `OPEN_AQ_API_KEY` (air quality)
 - `TOMTOM_API_KEY` (traffic)
 
 ### Provider toggles
 
 - `WEATHER_PROVIDER`: `openweather` (default) or `open-meteo`
 - `TRAFFIC_PROVIDER`: `tomtom` (default) or `synthetic`
 
 ### Location
 
 - `CITY_LAT`, `CITY_LON` (defaults align to Nairobi CBD if not set)
 
 ### DB selection
 
 - Local DB: `USE_LOCAL_DB=true` + `LOCAL_DATABASE_URL=...`
 - Render DB: `USE_DB=1` + `DATABASE_URL=...`
 - Render DB URLs are normalized by the backend (scheme and `sslmode=require` for `*.render.com`).
 
 ### Hugging Face advisory/forecasting
 
 - `HF_API_KEY` preferred; token aliases may also be accepted.
 - Optional overrides: `HF_MODEL_NAME`, plus specialized model env vars.
 - Advisory responses are cached (~10 min) and fall back to deterministic guidance when unavailable.

 Traffic live caching:

 - `TRAFFIC_LIVE_TTL_SECONDS` (default 300s)
 - `TRAFFIC_LIVE_POINTS_TTL_SECONDS` (default 30s)
 - TomTom live sampling (used by `/traffic/live` when `TRAFFIC_PROVIDER=tomtom`):
   - `TRAFFIC_LIVE_ZOOM` (default 14)
   - `TRAFFIC_LIVE_GRID_N` (default 3; grid is `grid_n x grid_n`)
   - `TRAFFIC_LIVE_RADIUS_DEG` (default 0.05)
   - `TRAFFIC_LIVE_JITTER_DEG` (default 0.003)
   - `TRAFFIC_LIVE_MAX_POINTS` (default `grid_n * grid_n`, capped at 49)
 
 ---
 
 ## Deployment (Render)
 
 - Backend service: `susps-web` (Python)
   - Build: `pip install -r requirements.txt`
   - Start: `./scripts/render_start.sh`
   - Health check: `/health`
   - Root `/` redirects to `/docs`
 - Frontend: separate Render Static Site pointing at `src/frontend`
   - Build: `npm install && npm run build`
   - Publish dir: `dist`
   - Env: `VITE_API_BASE_URL=https://<backend-url>`
 
 The free-tier backend may cold-start; the frontend can “wake” the backend by calling it on load.
 
 ---
 
 ## Environment parity: Local vs Render (S3 + Postgres)
 
 Goal: keep `data/<CITY>/raw/` consistent locally and in S3 so local and Render runs match.
 
 Render bootstrap (recommended on first deploy):
 
 - Set env vars:
   - `USE_DB=1`, `DATABASE_URL`
   - `USE_S3_STORAGE=true`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - `AWS_BUCKET_NAME=susps-raw-data`, `AWS_REGION=eu-north-1`, optional `AWS_S3_DATA_PREFIX`
   - `DB_BOOTSTRAP_ON_START=1`
 - On start, the service can:
   1) Pull raw from S3 → `data/<CITY>/raw/`
   2) Run ingest → preprocess
   3) Create schema
   4) Seed DB from processed
 
 Subsequent deploys: set `DB_BOOTSTRAP_ON_START=0` for faster restarts.
 
 ---
 
 ## What remains (near-term)
 
 - Per-area filtering
   - Extend core endpoints (`/growth`, `/energy`, `/traffic`, summaries) to accept and apply `area_id` consistently.
   - Ensure React passes selected area into those endpoints and makes the selection visible.
 - Hotspot maps
   - Replace radial/circle overlays with ward/zone choropleths by joining hotspot outputs to GeoJSON geometries.
 - UX polish
   - Continue refining SIMULATE flows, parameter panels, and Predict/Simulate/Optimize explanations.
 - Reliability/testing
   - Extend tests for per-area behavior and new endpoint paths; optional CI DB-backed E2E job.
 - Documentation
   - Keep this file, `docs/documentation.md`, and the rest of the repo docs in sync with behavior.
 
 ---
 
 ## Roadmap & acceptance criteria (baseline)
 
 Milestones (high level):
 
 - M1 — Clean baseline: CI green (DONE).
 - M2 — Backend feature completeness + parity: simulation, forecasting, hotspots, DB seeding (MOSTLY DONE).
 - M3 — Area-driven frontend + auth + hotspot maps (IN PROGRESS).
 - M4 — UX polish + simulation/forecasting surfaces.
 - M5 — Reliability, tests, documentation (FINAL).
 
 Acceptance criteria (baseline):
 
 - Render
   - `/health` OK; React app loads with sidebar area selection.
   - No area selected → descriptive content + placeholders.
   - Area selected → growth/energy/traffic, summaries, hotspots, advisory render without errors.
 - Local/DB (optional)
   - Schema applies; seed succeeds; `/areas` non-empty when DB is enabled; summaries return data where present.
 - CI
   - Ruff/Black/Mypy/Pytest green.
 
 ---
 
 ## Notes
 
 - For full thesis-style documentation, see `docs/documentation.md`.
