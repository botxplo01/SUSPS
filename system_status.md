# System Status

This document summarizes the current state of the SUSPS repository: what’s done, what’s next, and the desired end-state for the system.

## Current status (2025-11-15)
- Lint/format/typecheck/tests: green locally (Ruff, Black, Mypy). Pytest suite passes with the new simulation, time-series, and hotspot tests.
- Backend (FastAPI):
  - Core endpoints `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/config` remain in place with DB → processed → synthetic fallbacks.
  - New deterministic features: `/simulate/run` (SIMULATE mode over growth/energy/traffic), `/ts/forecast` (generic time-series forecast), `/hotspots/areas` and `/hotspots/areas/forecast` (static + multi-year hotspot scores), `/areas`, `/processed_data`, `/simulation_inputs` (DB-backed metadata views), plus `/advisory/status`.
  - AI advisory endpoints (`/advisory/{scope}`, `/advisory_batch`) are wired to free Hugging Face models via `HF_API_KEY` with caching and graceful degradation.
- Pipeline and data layout: API-first ingestion writes to `data/<CITY>/raw/` (OpenWeather default, Open‑Meteo optional; OpenAQ; TomTom). Preprocess writes to `data/<CITY>/processed/` (environment_features, energy_features, traffic_features, air_quality_daily, hotspot CSVs). Census and precomputed growth forecast (`growth_forecast_city.csv`) plus Urban_Growth features remain integrated.
- Storage and environments: Local runs with a local PostgreSQL instance plus file-based data under `data/<CITY>/{raw,processed}`; Render runs against managed PostgreSQL and AWS S3 bucket `susps-raw-data` (region `eu-north-1`) holding the same raw datasets. `src/pipeline.s3_sync` keeps local `data/<CITY>/raw/` and S3 in sync so results match between local and Render.
- Frontend (Dash): Sidebar uses an `area-select` dropdown populated from `/areas`; there is no longer a Demo/API data-source toggle. On initial load (no area selected) each page shows descriptive text and placeholder charts only; charts and advisory are populated only once an area is chosen, and the advisory engine now receives the selected area (`zone_id`) so guidance is explicitly scoped.
- Frontend (React + Tailwind, `src/frontend`): Vite+React+TypeScript+Tailwind SPA with Dashboard, Urban Growth, Energy, and Traffic pages; area selection is wired via a fixed left sidebar backed by `/areas` (Montserrat typography, larger nav icons, and a rail-style active highlight with a teal left border), with a mobile hamburger and icon-only collapsed mode on desktop; REAL and SIMULATE modes are wired on the domain pages using `/growth`, `/energy`, `/traffic`, and `/simulate/run`; advisory content is loaded via `/advisory/{scope}` and rendered in frosted-glass "Insights" panels with a galaxy-style icon; an OSM-based hotspot map overlays `/hotspots/areas` and `/hotspots/areas/forecast`, showing dense population, congestion, and inefficient energy usage in soft translucent red and potential optimal zones in soft translucent green when Optimize is active; and the layout includes a sticky blurred page header with gradient titles/icons, a mobile-visible Sign out button, and a persistent slightly darker footer strip describing SUSPS and attribution.
- Docs: WARP.md and README document the local+Render parity story (Postgres + S3), backend capabilities (simulation, time-series, hotspots), and both the legacy Dash and new React area-driven frontends; this status doc reflects that.

## 1) What’s implemented

### Frontend map (pages  endpoints  data flow  advisory)

- Dashboard
  - Endpoints: `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/advisory/dashboard`.
  - Area-driven behavior: Sidebar `area-select` dropdown is populated from `/areas`. Until an area is selected, the page shows descriptive text and placeholder charts only; once selected, the charts call the live API endpoints (which internally prefer DB/processed data with synthetic fallback as needed).
  - Advisory: "Insights" panel is gated on area selection and then calls `/advisory/dashboard` (or batch variant).
- Growth page
  - Endpoints: `/growth`, `/advisory/growth`.
  - Area-driven behavior: shares the same `area-select` gate as the Dashboard; shows only descriptions until an area is selected, then renders the growth series.
  - Advisory: Uses `/advisory/growth` scoped to the selected area's growth context.
- Energy page
  - Endpoints: `/energy`, `/energy/summary`, planned `/energy/sector-summary` (future), `/advisory/energy`.
  - Area-driven behavior: same `area-select` gate; charts are populated from `/energy` and `/energy/summary` only after an area is chosen.
  - Advisory: Uses `/advisory/energy`, summarizing recent energy demand.
- Traffic page
  - Endpoints: `/traffic`, `/traffic/summary`, planned `/traffic/hourly` (future), `/advisory/traffic`.
  - Area-driven behavior: same `area-select` gate; charts are populated from `/traffic` and `/traffic/summary` only after an area is chosen.
  - Advisory: Uses `/advisory/traffic`, summarizing recent traffic flows.
- Hotspot maps (React UI + OSM-based overlays)
  - Endpoints: `/hotspots/areas`, `/hotspots/areas/forecast`.
  - Behavior: React frontend renders an OpenStreetMap-based Leaflet map that overlays hotspot scores as soft translucent red circles; when Optimize is active, improving areas (based on forecast vs current scores) are highlighted in soft translucent green as potential optimal zones, with a small derived "optimal zones" list displayed next to the map. Joining these scores with ward/zone GeoJSON to render choropleth polygons remains a future enhancement; the current implementation uses a simple radial layout around the city center.

|- App structure
  - Unified FastAPI + Dash app for both local and Render: `src/backend/api.py` + `src/webapp/app.py`, with CORS, `/health`, and Dash mounted under `/dash/`.
  - Database support: the unified app can run purely file-based or connect to PostgreSQL (local or Render-managed) when `USE_LOCAL_DB=true` or `USE_DB=1` and a `DATABASE_URL` is provided.
  - Legacy Docker/PostGIS stack under `backend/` is retained for optional DB experiments/E2E tests but is not required for the final-year project.
- Demo/API features (unified app)
  - Endpoints: `/health`, `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/config` (GET/POST), `/areas`, `/processed_data`, `/simulation_inputs`, `/simulate/run`, `/ts/forecast`, `/hotspots/areas`, `/hotspots/areas/forecast`, plus advisory endpoints.
  - UI now uses an area-driven pattern rather than a Demo/API toggle: charts and advisory are gated on `area-select` and always call the real API endpoints, which internally decide between DB/processed/synthetic data.
  - AI Advisory endpoints (`/advisory/{scope}`, `/advisory_batch`, `/advisory/status`) integrated into the frontend, powered by free Hugging Face models with caching and graceful degradation. When `zone_id` is provided (from the selected area), it is included in the advisory prompt and cache key so insights can be area-specific.
- Data pipeline and storage
  - Ingest → preprocess → synthetic → fairness modules under `src/pipeline/` producing CSVs in `data/<CITY>/raw/` and `data/<CITY>/processed/`.
  - Local environment treats `data/<CITY>/{raw,processed}` as canonical and can load processed outputs into a local PostgreSQL instance.
  - Render environment uses the same schema against Render-managed PostgreSQL and stores raw datasets in AWS S3 bucket `susps-raw-data` (region `eu-north-1`), kept in sync with local via `src.pipeline.s3_sync`.
- Tooling and CI
  - Ruff, Black, Mypy (local + CI); pre-commit hooks (Ruff/Black/Mypy).
  - GitHub Actions runs lint, format check, typecheck, and tests with coverage.
  - `pytest.ini` added to set `pythonpath = .` and default asyncio loop scope.
  - Replaced Starlette's deprecated WSGIMiddleware with `a2wsgi.WSGIMiddleware` to remove warnings.
  - WARP.md created and updated with common commands, environment parity, and architecture overview.

## 2) What remains (near-term)

- Frontend: complete React migration and area-driven behavior
  - Polish SIMULATE mode flows in the React UI (e.g., consider surfacing `/ts/forecast` where appropriate and refine parameter controls on the Urban Growth, Energy, and Traffic pages that already call `/simulate/run`).
  - Evolve the React map from the current OSM-based hotspot overlays into proper ward/zone-based choropleths by joining `/hotspots/areas` and `/hotspots/areas/forecast` with GeoJSON geometries.
  - Optionally surface additional summary views on the React Dashboard by aggregating growth/energy/traffic series or using `/energy/summary` and `/traffic/summary` once area filtering is in place.
  - Consider adding an explicit "optimal zones" list next to the hotspot map and refining advisory copy to reference these green optimal zones when Optimize is active.
  - Ensure that when no area is selected in React, each page shows only descriptive content and placeholder visuals, matching the existing Dash behavior.
- Backend/frontend integration
  - Extend core endpoints (`/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`) to accept an `area_id` (or similar) and filter results accordingly.
  - Ensure both Dash and React clients pass the selected area into these endpoints and clearly indicate which area the charts and advisory refer to.
- Models + pipeline integration
  - Growth: continue to rely on processed and census data (`growth_forecast_city.csv` etc.) for `/growth`; optionally surface per-area growth allocations derived from worldpop/socioeconomic features.
  - Energy: optionally expose sector-level summary via an endpoint (e.g., `/energy/sector-summary`) if added, and pair it with a dedicated chart.
  - Traffic: optionally expose an hourly profile endpoint (e.g., `/traffic/hourly`) if needed for more granular visuals.
  - Add or extend unit tests for these model readers and new endpoints.
- DB/E2E workflow
  - Optional CI job: spin up Postgres service, apply schema (`src/backend/db/susps_schema_dump.sql` or migrations), seed minimal data, and run DB-backed endpoint tests.
  - Ensure any seed or bootstrap scripts are referenced in docs and remain up to date.
- Developer experience
  - Keep pre-commit hooks (Ruff, Black, Mypy) enabled and documented.
  - Consider adding `python-multipart` only if file uploads or form parsing are introduced; otherwise keep dependencies minimal.
- Documentation
  - Keep WARP.md, README, and this status document in sync with the area-driven frontend, new endpoints (simulation, time-series, hotspots), and the local↔Render parity workflow.

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

- Frontend (Dash)
  - Treat `src/webapp/app.py` as the single source for the UI; keep it area-driven (no Demo/API toggle) and ensure new charts respect `area-select`.
  - When adding new visualizations (e.g., hotspots, simulation outputs), wire them to the existing FastAPI endpoints and gate them on area selection.
- Backend (FastAPI)
  - Add or refine endpoints under `src/backend/api.py` to support per-area filtering and any additional summaries needed by the UI.
  - Keep all models and external integrations on free tiers (Hugging Face, OpenWeather, Open-Meteo, TomTom, OpenAQ, etc.), with deterministic fallbacks.
- DB-backed features
  - Use local PostgreSQL or Render-managed Postgres with the schema in `src/backend/db/susps_schema_dump.sql` for DB-enabled flows.
  - Add DB tests only where they materially improve confidence (e.g., `/areas`, `/processed_data`, `/simulation_inputs`).
- Models and pipeline
  - Extend or adjust `src/models/*` to consume processed outputs and feed endpoints cleanly.
  - Keep pipeline steps deterministic and documented so that local and Render can be reproduced reliably.

## Roadmap to completion

Milestone M1 — Clean baseline (DONE)
- CI green: Ruff, Black, Mypy, Pytest pass.
- Dash mounting via `a2wsgi.WSGIMiddleware` (no deprecation warnings).
- `pytest.ini` in place; WARP.md/README updated.

Milestone M2 — Backend feature completeness and environment parity (MOSTLY DONE)
- Backend: `/growth` prefers precomputed forecast; `/energy/summary` and `/traffic/summary` implemented; processed-first behavior across endpoints with graceful fallbacks.
- Added SIMULATE (`/simulate/run`), time-series forecasting (`/ts/forecast`), hotspot endpoints (`/hotspots/areas`, `/hotspots/areas/forecast`), and DB metadata endpoints (`/areas`, `/processed_data`, `/simulation_inputs`) backed by a portable schema (`src/backend/db/susps_schema_dump.sql`).
- Pipeline: API-first ingest (OpenWeather/OpenAQ/TomTom) with fallbacks; preprocess produces environment/energy/traffic/AQ features, census-based growth forecasts, and hotspot CSVs.
- Environment parity: local PostgreSQL + `data/<CITY>/{raw,processed}` vs Render PostgreSQL + S3 `susps-raw-data`, kept aligned via `src.pipeline.s3_sync` and documented bootstrap steps.

Milestone M3  Area-driven frontend & hotspot maps (IN PROGRESS)
- Completed:
  - Removed Demo/API toggle from Dash and introduced an `area-select` dropdown gating all charts and advisory.
  - Scaffolded the new React+Tailwind frontend with Dashboard, Urban Growth, Energy, and Traffic pages, and wired area selection via `/areas` plus REAL-mode charts and advisory.
  - Wired REAL vs SIMULATE modes on the React Urban Growth, Energy, and Traffic pages to `/simulate/run`, with basic parameter controls where appropriate.
  - Implemented an OSM-based hotspot map in the React frontend that overlays `/hotspots/areas` and `/hotspots/areas/forecast`, with dense/problematic areas shown in soft translucent red and improving areas highlighted in soft translucent green when Optimize is active.
- Pending:
  - Extend `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary` to accept `area_id` (or equivalent) and filter appropriately.
  - Ensure both Dash and React pass the selected area into these endpoints and reflect the selected area clearly in the UI.
  - Replace the current radial hotspot layout with ward/zone-based choropleths by joining `/hotspots/areas` and `/hotspots/areas/forecast` with GeoJSON geometries in the new React UI (and optionally Dash).
  - Ensure that when no area is selected, each page in both frontends shows only descriptive content and placeholder charts/maps.

Milestone M4  UX polish, simulation & forecasting surfaces
- Refine the SIMULATE UI in React (existing sliders/inputs on Growth, Energy, and Traffic pages calling `/simulate/run`) and ensure results and advisory copy are easy to interpret.
- Optionally expose `/ts/forecast` in charts for extended forecast scenarios.
- Add help tooltips and page descriptions explaining each page's purpose and how area selection affects data.

Milestone M5 — Reliability, tests, and documentation (FINAL)
- Add tests for new endpoints (per-area series, hotspots, simulation/time-series) and, where feasible, basic Dash integration tests.
- Finalize environment-parity checks and document a reproducible path to show local vs Render matching responses for a given city and area.
- Clean up legacy pieces (`/config` + `_DEFAULT_SOURCE`), and optionally remove any remaining demo semantics at the API level if they are no longer desired.
- Keep WARP.md, README, and system_status.md in sync with the final behavior.

Exit criteria (definition of done)
- Render app: `area-select` works; growth/energy/traffic plus hotspot and summary endpoints power charts; docs reflect the area-driven, no-toggle behavior.
- Environment parity: for a given CITY and synced datasets (via `s3_sync`), key API responses (`/growth`, `/energy`, `/traffic`, summaries, hotspots) and advisory outputs are consistent between local and Render within expected tolerances (timestamps, ordering).
- DB app: endpoints and charts display seeded data; optional CI E2E job green.
- Tooling: pre-commit and CI stay green; warnings are either addressed or documented.

## 5) Acceptance criteria (baseline)

- Render app
  - `/health` returns OK; `/dash/` renders pages with the sidebar `area-select` dropdown.
  - With no area selected, pages show descriptive content and placeholder charts only.
  - After selecting an area, `/growth`, `/energy`, `/traffic`, summaries, hotspots, and advisory endpoints return structured data and charts/advisory render without errors.
- Docker/local DB app (if used)
  - Migrations or schema application succeeds; seed scripts (if any) succeed; `/areas` is non-empty; `/energy/summary` and `/traffic/summary` return items where data is present.
- CI
  - All checks pass (Ruff, Black, Mypy with package mode, unit tests).

## 6) Notes

- The `backend/` (DB) and `src/` (no-DB) paths are intentionally decoupled to keep Render simple while supporting richer local DB workflows.
- You can expand the DB-backed app independently without impacting Render deployment.
