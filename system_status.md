# System Status

This document summarizes the current state of the SUSPS repository: what’s done, what’s next, and the desired end-state for the system.

## Current status (2025-11-08)
- Lint/format/typecheck/tests: all green locally (Ruff, Black, Mypy). Pytest: 4 passed, 4 skipped, 1 warning (Starlette suggests installing `python-multipart`; harmless unless form parsing is used).
- Dash mounting migrated to `a2wsgi.WSGIMiddleware` (Starlette WSGI deprecation removed).
- `pytest.ini` added to set `pythonpath = .` and default asyncio loop scope to function.
- WARP.md updated with these changes and commands.

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

- Data/UI integration
  - Decide UI strategy: keep Render (no-DB) and Docker (DB) dashboards separate (recommended) or add a third "DB" toggle in Render.
  - If adding DB toggle: wire charts to `/energy/summary` and `/traffic/summary` when available; fallback to demo/API gracefully.
  - Confirm `DEFAULT_DATA_SOURCE` docs and behavior; add simple tests for `/config` GET/POST.
- Models + pipeline integration
  - Growth: implement `predict_from_processed` usage in API when artifacts exist; calibrate base population/rates from `data/processed/worldpop_features.csv`.
  - Energy: expose `summary_from_processed` via an endpoint (e.g., `/energy/sector-summary`) and add a matching chart.
  - Traffic: expose `daily_profile_from_processed` via an endpoint (e.g., `/traffic/hourly`) and add a matching chart.
  - Add unit tests for these model readers against temp processed artifacts.
- DB/E2E workflow
  - Optional CI job: spin up Postgres service, run migrations/seed, and run the DB summary tests.
  - Ensure seed scripts are referenced in docs (already present) and remain up to date.
- Developer experience
  - Starlette warning: optionally add `python-multipart` to requirements if form parsing or file uploads are planned; otherwise, suppress the warning in tests.
  - Keep pre-commit hooks (Ruff, Black, Mypy) enabled and documented.
- Documentation
  - Keep WARP.md and README in sync with UI toggle behavior, new endpoints, and any CI/E2E changes.

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

## Roadmap to completion

Milestone M1 — Clean baseline (DONE)
- CI green: Ruff, Black, Mypy, Pytest pass.
- Dash mounting via `a2wsgi.WSGIMiddleware` (no deprecation warnings).
- `pytest.ini` in place; WARP.md/README updated.

Milestone M2 — Demo/API feature completeness (no-DB path)
- Endpoints: add `/energy/sector-summary` and `/traffic/hourly` backed by `src/models.energy.summary_from_processed` and `src.models.traffic.daily_profile_from_processed` with graceful fallback to synthetic when artifacts absent.
- UI: add charts for sector energy and hourly traffic; ensure the Data Source toggle (Demo | API) updates all charts.
- Tests: unit tests for the model readers against temporary processed artifacts; API route tests for new endpoints.
- Docs: update WARP.md/README with new endpoints and toggle behavior.

Milestone M3 — DB-backed experience and E2E (optional but recommended)
- Ensure `docker compose up --build` + seed scripts produce data; DB-backed `/energy/summary` and `/traffic/summary` reflect seeded content.
- UI (DB dashboard under `backend/`): verify charts render and document usage.
- CI (optional separate job): service container Postgres, run migrations/seed, then run DB summary tests.

Milestone M4 — Reliability and ops
- Add structured logging and error handling for API endpoints; timeouts on outbound calls used by UI when source=API.
- Define health/readiness endpoints if needed; keep `/health` stable.
- Security baseline: CORS review, basic rate-limiting notes (if required), minimal headers.
- Coverage target: add/adjust tests to meet an agreed baseline (e.g., 70–80%).

Milestone M5 — Data store alignment (optional, per preference)
- Evaluate TiDB compatibility for transactional workloads while keeping geospatial via PostGIS or an external geoservice; confirm open-source path without credit card signups.
- Define an abstraction layer for DB access to allow incremental migration or dual support.
- Produce a migration plan (scoped; only if adoption is desired).

Exit criteria (definition of done)
- Render app: toggle works; growth/energy/traffic plus new sector/hourly endpoints power charts; docs reflect behavior.
- DB app: endpoints and charts display seeded data; optional CI E2E job green.
- Tooling: pre-commit and CI stay green; warnings are either addressed or documented.

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
