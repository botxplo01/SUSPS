# System Status

This document summarizes the current state of the SUSPS repository: what’s done, what’s next, and the desired end-state for the system.

## Current status (2025-11-10)
- Lint/format/typecheck/tests: green locally (Ruff, Black, Mypy). Pytest: 4 passed, 4 skipped; warnings noted (multipart suggestion, datetime.utcnow deprecation).
- Frontend: Sidebar fixed, dark theme, flush-left with full-width active highlight; extra top spacing; placeholders for maps/tables show on all pages; resolved Dash `Div.__init__` children error.
- Pipeline: API-first ingestion writes to `data/raw/` (OpenWeather default, Open‑Meteo optional; OpenAQ; TomTom). Preprocess writes to `data/processed/` (environment_features, energy_features, traffic_features, air_quality_daily). Census and precomputed growth forecast (`growth_forecast_city.csv`) added. Urban_Growth integrated with catalog and features.
- API: `/growth` now prefers precomputed forecast, then census-based/processed, then synthetic. Added `/energy/summary` and `/traffic/summary`. Energy/traffic endpoints prefer processed data.
- Config: Env alignment with `.env`; removed unused `COPERNICUS_PATH`, `NIGHTLIGHTS_PATH`, `GHSL_PATH`, `GOOGLE_MAPS_API_KEY`. Added `WEATHER_PROVIDER` (default `openweather`), `TRAFFIC_PROVIDER` (default `tomtom`), and `CITY_LAT/LON` defaults for Nairobi.
- Docs: WARP.md and README reflect commands; this status doc updated.

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
- Backend (DONE): `/growth` prefers precomputed forecast; `/energy/summary` and `/traffic/summary` implemented; processed-first behavior across endpoints with graceful fallbacks.
- Pipeline (DONE): API-first ingest (OpenWeather/OpenAQ/TomTom) with fallbacks; preprocess produces environment/energy/traffic/AQ features; census + growth forecast precompute.
- UI (PENDING): add charts for Energy sector summary and hourly Traffic profile; ensure Data Source toggle updates all charts consistently.
- Tests (PENDING): add API route tests for new endpoints; add unit tests for growth forecast generator.
- Docs (PENDING): ensure README/WARP.md examples include new endpoints and provider env guidance.

Milestone M3 — Ward-level and spatial features (Nairobi)
- Add Nairobi ward boundaries; compute zonal stats for WorldPop/land cover → ward-level features.
- Allocate growth forecasts to wards using pop_share; prepare ward choropleth map for UI.
- Derive OSM network metrics (road_km by class, intersection density) to enrich traffic.

Milestone M4 — Reliability and ops
- Add caching and backoff for external API calls; scheduled ingestion (hourly/daily) for weather/AQ/traffic.
- Add basic metrics/logging; keep `/health` stable; document operational playbook.
- Expand fairness checks where applicable (coverage across wards).

Milestone M5 — DB-backed experience and E2E (optional)
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
