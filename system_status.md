# System Status

This document summarizes the current state of the SUSPS repository: what’s done, what’s next, and the desired end-state for the system.

## 1) What’s implemented

- App structure
  - FastAPI + Dash (Render path, no DB): `src/backend/api.py` + `src/webapp/app.py`
  - Optional DB-backed stack (Docker/PostGIS): `backend/` service with Alembic migrations and minimal Dash
- Demo features (Render)
  - Endpoints: `/health`, `/growth`, `/energy`, `/traffic`, `/config` (GET/POST)
  - Dashboard charts for Growth, Energy, Traffic with a “Data source” toggle (Demo | API)
  - Model stubs in `src/models/` generating synthetic data; can be extended to use pipeline outputs
- DB-backed features (Docker)
  - DB models and migrations (PostGIS geometry via GeoAlchemy)
  - Seed scripts and demo data for `urban_areas`, `energy_consumption`, `traffic_flow`
  - API endpoints: `/areas`, `/energy`, `/traffic`, summaries at `/energy/summary`, `/traffic/summary`
  - Minimal DB-backed Dash with charts
- Data pipeline
  - Ingest → preprocess → synthetic → fairness modules under `src/pipeline/`
  - Produces CSVs in `data/raw/` and `data/processed/`
- Tooling and CI
  - Ruff, Black, Mypy (local + CI); pre-commit hooks (Ruff/Black/Mypy)
  - GitHub Actions runs lint, format check, typecheck, and tests with coverage
  - `pytest.ini` added to set `pythonpath = .` and default asyncio loop scope
  - Replaced Starlette's deprecated WSGIMiddleware with `a2wsgi.WSGIMiddleware` to remove warnings
  - WARP.md created and updated with common commands and architecture overview

## 2) What remains (near-term)

- Unify the UI modes (optional)
  - Option A (recommended): Keep Render (no-DB) and Docker (DB) dashboards separate to minimize coupling
  - Option B: Add a third toggle state (DB) to the Render dashboard for local Docker development; fetch from `/energy/summary`, `/traffic/summary` when available
- Model integration with pipeline outputs
  - Growth: add functions that read processed artifacts to drive projections (e.g., calibrate base pop/rates)
  - Energy: add endpoints/logic to surface sector summaries and time-of-day profiles from processed data
  - Traffic: aggregate per-hour volumes by corridor into dashboard-ready curves
- Testing expansion
  - Add unit tests for `src/models/*` functions reading processed data
  - Add optional Docker E2E tests for DB-backed summaries and seeds
- Documentation
  - Add developer notes for toggling `DEFAULT_DATA_SOURCE` (Render) and how to run DB and non-DB paths in parallel

## 3) End-state (target architecture)

- Frontend (Dash)
  - Render dashboard for demo and API-backed visualizations without DB
  - Docker-local dashboard for DB-backed exploration with PostGIS
  - Clear environment-driven toggles for data sources; ability to run side-by-side
- API (FastAPI)
  - Render: stateless demo endpoints, lightweight transformation endpoints
  - Docker: CRUD + analytics endpoints backed by Postgres/PostGIS; Alembic-managed schema
- Models layer
  - Predictive modules (growth, energy, traffic) encapsulated in `src/models/`
  - Each module supports both synthetic/demo data and real data via pipeline outputs
- Data pipeline
  - Reproducible steps generating normalized artifacts consumable by models
  - Optional orchestration (DVC) or simple documented scripts
- Ops/Tooling
  - CI: lint, format, typecheck, tests; optional E2E job against a test DB service
  - Pre-commit hooks ensure consistent style locally
  - Clear developer docs (README, WARP.md, this status doc)

## 4) How to proceed

- For Render-only features
  - Implement new endpoints in `src/backend/api.py` and corresponding charts in `src/webapp/app.py`
  - Use `DEFAULT_DATA_SOURCE` to set initial data source
- For DB-backed features
  - Use `docker compose up --build` and `scripts/seed-db.*` to prepare data
  - Implement analytics endpoints under `backend/app/api/routes.py`
  - Update DB-backed Dash charts under `backend/app/dash_app/app.py`
- For model and pipeline integration
  - Extend `src/models/*` to parse `data/processed/*` outputs
  - Add new endpoints or reuse existing ones to expose model outputs to the UI

## 5) Acceptance criteria (baseline)

- Render app
  - `/health` returns OK; `/dash/` renders charts with toggle functioning
  - `/growth`, `/energy`, `/traffic` return structured demo data
- Docker app
  - Migrations apply; seed scripts succeed; `/areas` non-empty; `/energy/summary` and `/traffic/summary` return items
- CI
  - All checks pass (Ruff, Black, Mypy with package mode, unit tests)

## 6) Notes

- The `backend/` (DB) and `src/` (no-DB) paths are intentionally decoupled to keep Render simple while supporting richer local DB workflows.
- You can expand the DB-backed app independently without impacting Render deployment.
