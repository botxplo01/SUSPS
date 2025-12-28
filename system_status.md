# System Status

This document summarizes the current state of the SUSPS repository: what’s done, what’s next, and the desired end-state for the system. It complements `WARP.md` (day-to-day development workflows and commands) and `docs/documentation.md` (thesis-style system and design documentation).

## Current status (2025-11-20)
- Lint/format/typecheck/tests: green locally (Ruff, Black, Mypy). Pytest suite passes with the new simulation, time-series, and hotspot tests.
- Backend (FastAPI):
  - Core endpoints `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary` remain in place with DB  processed  synthetic fallbacks.
  - The legacy `/config` endpoint and `DEFAULT_DATA_SOURCE` toggle have been removed; the backend now always uses processed/DB data with deterministic fallbacks (no Demo/API switch).
  - New deterministic features: `/simulate/run` (SIMULATE mode over growth/energy/traffic), `/ts/forecast` (generic time-series forecast), `/hotspots/areas` and `/hotspots/areas/forecast` (static + multi-year hotspot scores), `/areas`, `/processed_data`, `/simulation_inputs` (DB-backed metadata views), plus `/advisory/status`.
  - AI advisory endpoints (`/advisory/{scope}`, `/advisory_batch`) are wired to free Hugging Face models via `HF_API_KEY` with caching and graceful degradation. Advisory now accepts an optional `scenario` label (e.g. `growth_baseline`, `growth_simulate`, `energy_demand_response`), which is incorporated into the HF prompt and cache key so insights can distinguish between baseline and SIMULATE scenarios for a given area.
- Pipeline and data layout: API-first ingestion writes canonical raw CSVs into domain-specific folders under `data/<CITY>/raw/` (OpenWeather default, Open‑Meteo optional; OpenAQ with fallback to `Air_Quality_Data_2025.csv` under `Environmental_and_Climate`; TomTom), e.g., `Demographics_and_Population/worldpop_summary.csv`, `Energy_and_Infrastructure/energy_demand.csv`, `Mobility_and_Transport/traffic_flows.csv`, `Environmental_and_Climate/environment_monthly.csv`, and `Demographics_and_Population/socioeconomic.csv`. Preprocess writes to `data/<CITY>/processed/` (environment_features, **environment_aq_features**, energy_features, traffic_features, **traffic_enriched_features**, air_quality_daily, hotspot CSVs), and now also emits summary tables that integrate all curated raw datasets: `demographic_raster_summary.csv` (population TIFFs), `landcover_raster_summary.csv` (land-cover TIFFs), `mobility_gis_layers.csv` (layers in `GIS_DATA_2019.zip`), and optional `urban_growth_catalog.csv` / `urban_growth_features.csv` (GRID3 settlements). Census and precomputed growth forecast (`growth_forecast_city.csv`) remain integrated. An optional Overpass/OSM client (`src/pipeline/osm_overpass.py`) can be invoked from `src.pipeline.ingest` when `SUSPS_FETCH_OSM=1` to persist an `osm_snapshot.geojson` under `data/<CITY>/raw/` for later use by the frontend/hotspots (disabled by default so tests/local runs are offline and deterministic).
- Storage and environments: Local runs with a local PostgreSQL instance plus file-based data under `data/<CITY>/{raw,processed}`; Render runs against managed PostgreSQL and AWS S3 bucket `susps-raw-data` (region `eu-north-1`) holding the same raw datasets, with `scripts/render_start.sh` providing an optional `DB_BOOTSTRAP_ON_START` pipeline (S3 pull → ingest → preprocess → seed) on deploy. `src/pipeline.s3_sync` keeps local `data/<CITY>/raw/` and S3 in sync so results match between local and Render, and the backend normalizes Render `DATABASE_URL` values (including `sslmode=require`) so connections succeed reliably.
- Frontend (React + Tailwind, `src/frontend`): Vite+React+TypeScript+Tailwind SPA with Dashboard, Urban Growth, Energy, and Traffic pages; area selection is wired via a fixed left sidebar backed by `/areas` (Montserrat typography, larger nav icons, and a rail-style active highlight with a teal left border), with a mobile hamburger and icon-only collapsed mode on desktop. The sidebar footer now includes **Unload** (red) and **Reset** controls so users can clear the selected area entirely or restore all per-area statistics and charts to their baseline state without changing the area. Domain pages expose REAL vs SIMULATE modes via a header `ModeToggle` (Real/Simulate) and a floating `ActionToggle` (Predict/Optimize/Simulate) whose buttons highlight when selected and include small click animations (scale on press); the Simulate button is hidden in REAL mode and triggers `/simulate/run` when clicked. Each domain page includes a warm-toned `#fffcf3` "Simulation parameters" card exposing per-domain controls: Growth (population scale, annual rate delta, optional shock year/size), Energy (demand scale, peak-hour shift, peak vs off-peak scaling, flattening toward average), and Traffic (volume scale, peak-hour shift, peak vs off-peak scaling, flattening). Charts (`BarChart`, `LineChart`, `Histogram`) now support multiple overlaid series with a legend: REAL (existing per-page accent), Predicted (an advanced forecast overlay in `#de3388` sourced from `/ts/forecast` in REAL mode), Simulated (SIMULATE-mode overlay in `#1b55ce` triggered by Simulate), and Optimal (simple derived overlay in `#08c44d` when Optimize is active).
- Authentication (React + FastAPI): a simple sign-in/sign-up flow is implemented and wired to the `users` table defined in `src/backend/db/susps_schema_dump.sql`. New FastAPI endpoints `/auth/signup` and `/auth/login` hash passwords and create/authenticate users; the React app uses an `AuthProvider` and `RequireAuth` wrapper to protect core routes (`/dashboard`, `/urban-growth`, `/energy`, `/traffic`) and redirect unauthenticated users to `/signin`. Dedicated `/signin` and `/signup` pages provide responsive layouts with a left-side form, right-side frosted-glass info container (desktop/tablet), and a mobile frosted-glass banner using the same black → gray → emerald → green gradient as desktop. Both pages use floating-label inputs whose labels only drop back to the baseline when fields are empty, plus cross-links (Sign in: “Don't have an account? Sign up here”; Sign up: “Already have an account? Sign in here”), and the header's Sign out button now clears the client-side session and routes back to `/signin`. The header also includes a compact Export button that renders as an icon-only control on mobile and expands to a labelled pill button on larger screens.
- Docs: WARP.md and README document the local+Render parity story (Postgres + S3), backend capabilities (simulation, time-series, hotspots), and the React area-driven frontend; this status doc reflects that. WARP.md and the Python/TypeScript code have been updated to remove non-standard or AI-meta comments and to add focused, domain-aware docstrings and comments across backend, frontend, models, pipeline, and tests.

## Quick start (local full stack)
- Python deps: create a virtualenv, install `requirements.txt`, and ensure `.env` at least sets `CITY=Nairobi` (defaults are fine for demo).
- Optional DB: start local PostgreSQL, create a database/user (e.g. `susps` / `susps_user`), and apply the schema dump once: `psql -U susps_user -d susps -f src/backend/db/susps_schema_dump.sql`. Then set `USE_LOCAL_DB=true` and `LOCAL_DATABASE_URL` in `.env`.
- Pipeline: run `python -m src.pipeline.ingest` then `python -m src.pipeline.preprocess` to populate `data/<CITY>/{raw,processed}`.
- If using DB: run `python -m src.backend.db.seed_from_processed` to load processed artifacts into `energy_consumption`, `traffic_flow`, `environment_features`, `air_quality_daily`, and `hotspot_scores`.
- Backend: run `uvicorn src.backend.api:app --reload` (check `/health`, explore `/docs`).
- Frontend: from `src/frontend`, run `npm install` (first time) then `npm run dev` and open `http://localhost:5173` (React SPA calls the FastAPI backend via `VITE_API_BASE_URL`).
- For more detailed setup commands and environment parity workflows, see `WARP.md`.

## 1) What’s implemented

### Frontend map (pages, endpoints, data flow, advisory)

- Dashboard
  - Endpoints: `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/advisory/dashboard`; charts use a bar chart for urban growth, a line chart for energy, and a histogram for traffic (plus summary tiles), all in REAL mode only (no Real/Simulate or Action toggles on the dashboard).
  - Area-driven behavior: Sidebar `area-select` dropdown is populated from `/areas`. Until an area is selected, the page shows descriptive text and placeholder charts only; once selected, the charts call the live API endpoints (which internally prefer DB/processed data with synthetic fallback as needed).
  - Advisory: "AI Analysis & Insights" panel is gated on area selection and then calls `/advisory/dashboard` (or batch variant); advisory text is rendered as plain paragraphs via `FormattedInsights`, which strips markdown/dev markers, hides redundant "Insights" headings/underlines, and emphasizes the main title, profile headings, and Recommended Actions/Short-/Medium-/Long-term sections.
- Growth page
  - Endpoints: `/growth`, `/ts/forecast`, `/advisory/growth`.
  - Area-driven behavior: shares the same `area-select` gate as the Dashboard; shows only descriptions until an area is selected, then renders the growth series.
  - SIMULATE: header `ModeToggle` and `ActionToggle` call `/simulate/run` for module=`growth` with parameters including `population_scale`, `annual_rate_delta_pct`, and optional `shock_year`/`shock_pct`, controlled via a "Simulation parameters" panel. In REAL mode, Predict calls `/ts/forecast` for `target="growth"` to compute an advanced Predicted overlay for the growth series (HF-based when configured, deterministic fallback otherwise) and displays it in the chart and table in `#de3388`; in SIMULATE mode, Simulate overlays simulated growth in `#1b55ce`; when Optimize is active, an Optimal overlay (simple midpoint between REAL and SIMULATE) appears in `#08c44d`.
  - Advisory: Uses `/advisory/growth` scoped to the selected area's growth context, with `scenario` set to `growth_baseline` (REAL) or `growth_simulate` (SIMULATE); text is rendered via `FormattedInsights` (markdown syntax stripped, redundant "Insights" headings removed, main/profile headings and Recommended Actions/Short-/Medium-/Long-term labels bolded).
- Energy page
  - Endpoints: `/energy`, `/energy/summary`, `/ts/forecast`, planned `/energy/sector-summary` (future), `/advisory/energy`.
  - Area-driven behavior: same `area-select` gate; charts are populated from `/energy` and `/energy/summary` only after an area is chosen.
  - SIMULATE: uses `/simulate/run` for module=`energy` with parameters such as `demand_scale`, `peak_hour_shift`, `peak_scale`, `offpeak_scale`, and `flatten_ratio`, controlled via a "Simulation parameters" panel (to model demand-response or time-of-use tariff scenarios). Predict/Simulate/Optimize behave as on the Growth page, with Predict calling `/ts/forecast` for `target="energy"` to generate the Predicted energy demand overlay, and Simulate/Optimize operating as described above.
  - Advisory: Uses `/advisory/energy`, summarizing recent energy demand with `scenario` set to `energy_baseline` or `energy_simulate`, rendered via `FormattedInsights` with the same heading/profile emphasis as on the dashboard.
- Traffic page
  - Endpoints: `/traffic`, `/traffic/summary`, `/ts/forecast`, planned `/traffic/hourly` (future), `/advisory/traffic`.
  - Area-driven behavior: same `area-select` gate; charts are populated from `/traffic` and `/traffic/summary` only after an area is chosen.
  - SIMULATE: uses `/simulate/run` for module=`traffic` with parameters such as `volume_scale`, `peak_hour_shift`, `peak_scale`, `offpeak_scale`, and `flatten_ratio`, controlled by a "Simulation parameters" panel to represent scenarios like remote work adoption or congestion pricing. Predict/Simulate/Optimize overlay Predicted/Simulated/Optimal traffic volumes in the chart (histogram) and as bracketed table values in the same colour scheme, with Predict calling `/ts/forecast` for `target="traffic"` to generate the Predicted traffic overlay.
  - Advisory: Uses `/advisory/traffic`, summarizing recent traffic flows with `scenario` set to `traffic_baseline` or `traffic_simulate`, rendered via `FormattedInsights` with the same heading/profile emphasis as on the dashboard.
- Hotspot maps (React UI + OSM-based overlays)
  - Endpoints: `/hotspots/areas`, `/hotspots/areas/forecast`.
  - Behavior: React frontend renders an OpenStreetMap-based Leaflet map that overlays hotspot scores as soft translucent red circles; when Optimize is active, improving areas (based on forecast vs current scores) are highlighted in soft translucent green as potential optimal zones, with a small derived "optimal zones" list displayed next to the map. Joining these scores with ward/zone GeoJSON to render choropleth polygons remains a future enhancement; the current implementation uses a simple radial layout around the city center.

- App structure
  - FastAPI API for both local and Render: `src/backend/api.py`, with CORS and endpoints such as `/health`, `/growth`, `/energy`, and `/traffic`.
  - Database support: the unified app can run purely file-based or connect to PostgreSQL (local or Render-managed) when `USE_LOCAL_DB=true` or `USE_DB=1` and a `DATABASE_URL` is provided.
  - Legacy Docker/PostGIS stack under `backend/` is retained for optional DB experiments/E2E tests but is not required for the final-year project.
- Demo/API features (unified app)
  - Endpoints: `/health`, `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`, `/areas`, `/processed_data`, `/simulation_inputs`, `/simulate/run`, `/ts/forecast`, `/environment/features`, `/air_quality/daily`, `/hotspots/areas`, `/hotspots/areas/forecast`, `/hotspots/scores`, plus advisory endpoints.
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
  - Removed the legacy Dash WSGI bridge and `a2wsgi` dependency; the FastAPI app now serves API endpoints only, and the React SPA is a separate client.
  - WARP.md created and updated with common commands, environment parity, and architecture overview.

## 2) What remains (near-term)

- Frontend: polish React area-driven behavior and hotspot/optimal-zone UX (Dash has been removed)
  - Polish SIMULATE mode flows in the React UI (e.g., consider surfacing `/ts/forecast` where appropriate and refine parameter controls on the Urban Growth, Energy, and Traffic pages that already call `/simulate/run`).
  - Evolve the React map from the current OSM-based hotspot overlays into proper ward/zone-based choropleths by joining `/hotspots/areas` and `/hotspots/areas/forecast` with GeoJSON geometries.
  - Optionally surface additional summary views on the React Dashboard by aggregating growth/energy/traffic series or using `/energy/summary` and `/traffic/summary` once area filtering is in place.
  - Refine the existing "optimal zones" list next to the hotspot map and advisory copy that references these green optimal zones when Optimize is active.
  - Ensure new pages continue the pattern where, if no area is selected, they show only descriptive content and placeholder visuals.
- Backend/frontend integration
  - Extend core endpoints (`/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary`) to accept an `area_id` (or similar) and filter results accordingly.
  - Ensure the React client passes the selected area into these endpoints and clearly indicates which area the charts and advisory refer to.
- Models + pipeline integration
- Growth: continue to rely on processed and census data (`growth_forecast_city.csv` etc.) for `/growth`; optionally surface per-area growth allocations derived from worldpop/socioeconomic features.
- Energy: optionally expose sector-level summary via an endpoint (e.g., `/energy/sector-summary`) if added, and pair it with a dedicated chart.
- Traffic: the traffic ingest/preprocess path now ensures a realistic 24-hour profile even when raw `traffic_flows.csv` values are nearly constant. `preprocess_traffic` and `src.models.traffic.daily_profile_from_processed` detect degenerate series (e.g., 600 veh/hour for every hour) and fall back to a canonical commuter shape, and `src.backend.db.seed_from_processed` will drop and reseed `traffic_flow` if it finds an all-600 profile in the DB. When `TOMTOM_API_KEY` and `TRAFFIC_PROVIDER=tomtom` are set, real TomTom snapshots can feed the same pipeline; otherwise synthetic flows are used but still produce a varied daily histogram.
- DB integration: `src.backend.db.seed_from_processed` now populates `environment_features`, `air_quality_daily`, and `hotspot_scores` from the processed CSVs so DB-backed flows can query weather, air-quality, and hotspot context directly; read-only API endpoints `/environment/features`, `/air_quality/daily`, and `/hotspots/scores` expose these tables (with CSV fallbacks) for environment/AQ/hotspot analytics and UI features.
- Time-series models: HF-backed time-series models behind `/ts/forecast` are now exercised by the Predict action on the growth, energy, and traffic pages; when HF is not configured, the endpoint falls back to lightweight deterministic heuristics (a full-series trend for growth and other yearly series, and scaled copies of the baseline 24-hour profiles for energy and traffic) so the Predicted overlays remain available but stay realistic.
- Add or extend unit tests for these model readers, new endpoints, and seeding logic.
- DB/E2E workflow
  - Optional CI job: spin up Postgres service, apply schema (`src/backend/db/susps_schema_dump.sql` or migrations), seed minimal data, and run DB-backed endpoint tests.
  - For a clean reset of a dev/Render database, drop and recreate the `public` schema (or manually drop SUSPS tables), then re-run `src/backend/db/susps_schema_dump.sql` and `src.backend.db.seed_from_processed` so the schema and seed data match the current code; the schema file includes an optional commented `DROP TABLE IF EXISTS` block that can be enabled for one-shot resets.
  - Ensure any seed or bootstrap scripts are referenced in docs and remain up to date.
- Developer experience
  - Keep pre-commit hooks (Ruff, Black, Mypy) enabled and documented.
  - Consider adding `python-multipart` only if file uploads or form parsing are introduced; otherwise keep dependencies minimal.
- Documentation
- Keep WARP.md, README, and this status document in sync with the React area-driven frontend, new endpoints (simulation, time-series, hotspots), and the local↔Render parity workflow.
- Maintain a thesis-style documentation file (`documentation.md`) that consolidates system objectives, architecture, implementation, testing, and evaluation for final submission.

## 3) End-state (target architecture)

- Frontend (React)
  - React + Tailwind SPA for demo and API-backed visualizations without DB.
  - Optional Docker/local builds for DB-backed exploration with PostGIS.
  - Clear environment-driven toggles for data sources; ability to run side-by-side.
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

- Frontend (React)
-  - Treat `src/frontend` as the single source for the UI; keep it area-driven (no Demo/API toggle) and ensure new charts respect the selected area.
-  - When adding new visualizations (e.g., hotspots, simulation outputs), wire them to the existing FastAPI endpoints and gate them on area selection.
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
- `pytest.ini` in place; WARP.md/README updated.

Milestone M2 — Backend feature completeness and environment parity (MOSTLY DONE)
- Backend (FastAPI): `/growth` prefers precomputed forecast; `/energy/summary` and `/traffic/summary` implemented; processed-first behavior across endpoints with graceful fallbacks.
- Added SIMULATE (`/simulate/run`), time-series forecasting (`/ts/forecast`), hotspot endpoints (`/hotspots/areas`, `/hotspots/areas/forecast`), and DB metadata endpoints (`/areas`, `/processed_data`, `/simulation_inputs`) backed by a portable schema (`src/backend/db/susps_schema_dump.sql`). New tables `environment_features`, `air_quality_daily`, and `hotspot_scores` have been added to the schema and are now populated by `src.backend.db.seed_from_processed` from processed CSVs, so fused weather/AQ features and area-level hotspot scores are available directly in Postgres.
- Pipeline: API-first ingest (OpenWeather/OpenAQ/TomTom) with fallbacks; preprocess produces environment/energy/traffic/AQ features plus fused `environment_aq_features.csv`, MATATUS/OSM-enriched `traffic_enriched_features.csv`, census-based growth forecasts, and hotspot CSVs.
- Environment parity: local PostgreSQL + `data/<CITY>/{raw,processed}` vs Render PostgreSQL + S3 `susps-raw-data`, kept aligned via `src.pipeline.s3_sync` and documented bootstrap steps.

Milestone M3  Area-driven frontend, authentication & hotspot maps (IN PROGRESS)
- Completed:
  - Removed Demo/API toggle from Dash and introduced an `area-select` dropdown gating all charts and advisory.
  - Scaffolded the new React+Tailwind frontend with Dashboard, Urban Growth, Energy, and Traffic pages, and wired area selection via `/areas` plus REAL-mode charts and advisory.
  - Wired REAL vs SIMULATE modes on the React Urban Growth, Energy, and Traffic pages to `/simulate/run`, with basic parameter controls where appropriate.
  - Implemented an OSM-based hotspot map in the React frontend that overlays `/hotspots/areas` and `/hotspots/areas/forecast`, with dense/problematic areas shown as red circles and improving areas highlighted in green when Optimize is active. Hotspot lists and optimal-zone units are now ordered alphabetically, and when no area is selected the map card shows the same "No data available." placeholder text as the other cards.
  - Refined the generic time-series forecaster behind `/ts/forecast` so that growth predictions use a full-series trend (rather than just the last two points) when falling back to deterministic mode, while energy and traffic predictions reuse scaled versions of the baseline 24-hour profiles; this eliminates flat or slowly drifting predictions (like a constant 0.08 profile on the Energy page) while preserving realistic shapes.
- Pending:
  - Extend `/growth`, `/energy`, `/traffic`, `/energy/summary`, `/traffic/summary` to accept `area_id` (or equivalent) and filter appropriately.
  - Ensure the React UI passes the selected area into these endpoints and reflects the selected area clearly in the UI.
  - Replace the current radial hotspot layout with ward/zone-based choropleths by joining `/hotspots/areas` and `/hotspots/areas/forecast` with GeoJSON geometries in the React UI.
  - Ensure that when no area is selected, each page shows only descriptive content and placeholder charts/maps.
  - Optionally extend authentication in future milestones (e.g., password reset, role-based access) now that the foundational sign-in/sign-up flow and `users` table integration are in place.

Milestone M4  UX polish, simulation & forecasting surfaces
- Refine the SIMULATE UI in React (existing sliders/inputs on Growth, Energy, and Traffic pages calling `/simulate/run`) and ensure results and advisory copy are easy to interpret.
- Predict actions already call `/ts/forecast` for growth, energy, and traffic; further UX polish can clarify when advanced forecasts (HF-backed) are available vs deterministic fallbacks.
- Add help tooltips and page descriptions explaining each page's purpose and how area selection affects data.
- Align chart exports with on-screen visuals by embedding chart images (captured from the React SVG charts) into PDF exports instead of representing charts as coordinate tables.

Milestone M5 — Reliability, tests, and documentation (FINAL)
- Add tests for new endpoints (per-area series, hotspots, simulation/time-series) and, where feasible, React frontend integration or E2E tests.
- Finalize environment-parity checks and document a reproducible path to show local vs Render matching responses for a given city and area.
- Produce a comprehensive thesis-style report in `documentation.md` (to be converted to Word) that follows the university thesis guidelines, explains changes from the initial proposal, and references all major data sources and design decisions.
- Keep legacy demo toggles removed (`/config` and `_DEFAULT_SOURCE` are gone) and optionally remove any remaining demo semantics at the API level if they are no longer desired.
- Keep WARP.md, README, `documentation.md`, and system_status.md in sync with the final behavior.

Exit criteria (definition of done)
- Render app: `area-select` works; growth/energy/traffic plus hotspot and summary endpoints power charts; docs reflect the area-driven, no-toggle behavior.
- Environment parity: for a given CITY and synced datasets (via `s3_sync`), key API responses (`/growth`, `/energy`, `/traffic`, summaries, hotspots) and advisory outputs are consistent between local and Render within expected tolerances (timestamps, ordering).
- DB app: endpoints and charts display seeded data; optional CI E2E job green.
- Tooling: pre-commit and CI stay green; warnings are either addressed or documented.

## 5) Acceptance criteria (baseline)

- Render app
  - `/health` returns OK; the React app renders pages with the sidebar area selection.
  - With no area selected, pages show descriptive content and placeholder charts only.
  - After selecting an area, `/growth`, `/energy`, `/traffic`, summaries, hotspots, and advisory endpoints return structured data and charts/advisory render without errors.
- Docker/local DB app (if used)
  - Migrations or schema application succeeds; seed scripts (if any) succeed; `/areas` is non-empty; `/energy/summary` and `/traffic/summary` return items where data is present.
- CI
  - All checks pass (Ruff, Black, Mypy with package mode, unit tests).

## 6) Notes

- The `backend/` (DB) and `src/` (no-DB) paths are intentionally decoupled to keep Render simple while supporting richer local DB workflows.
- You can expand the DB-backed app independently without impacting Render deployment.
