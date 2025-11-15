# SUSPS: Smart Urban Simulation and Prediction System

SUSPS is an AI-driven system to predict urban growth, forecast energy demand, and simulate traffic flow for Zambian cities.

- Web UI: React + Tailwind CSS SPA in `src/frontend`
- Backend: FastAPI (Python)
- Deployment: Render (Procfile + Gunicorn) for the API; Vite for local frontend dev

Quick start:
- Create a venv and install requirements
- Run backend locally: `uvicorn src.backend.api:app --reload`
- In a separate terminal, start the React dev server from `src/frontend`: `npm install` then `npm run dev`
- Open the React UI at the URL printed by Vite (default http://127.0.0.1:5173)

See `docs/specification.md` for the full spec and `docs/user_guide.md` for usage.

## Demo API (no DB)

These endpoints are available in the Render deployment and local non-DB runs.

- GET `/growth`
- GET `/energy`
- GET `/traffic`

Examples (truncated):

- `/growth`

  ```json
  {"items": [
    {"year": 2025, "predicted_population": 800000},
    {"year": 2026, "predicted_population": 824000}
  ]}
  ```

- `/energy`

  ```json
  {"items": [
    {"hour": 0, "demand_mwh": 5.0},
    {"hour": 8, "demand_mwh": 8.0}
  ]}
  ```

- `/traffic`

  ```json
  {"items": [
    {"hour": 7, "volume": 850},
    {"hour": 18, "volume": 900}
  ]}
  ```

## Data pipeline: regenerate artifacts

This project includes a lightweight data pipeline that produces CSVs under `data/raw/` and `data/processed/`.

- Python modules (no extra tools required):
  - `python -m src.pipeline.ingest`
  - `python -m src.pipeline.preprocess`
  - `python -m src.pipeline.synthetic` (optional)
  - `python -m src.pipeline.fairness` (optional)

- Optional: DVC orchestration (if you use DVC):
  - `dvc repro`

Outputs include:
- `data/raw/`: worldpop_summary.csv, energy_demand.csv, traffic_flows.csv, environment_monthly.csv, socioeconomic.csv
- `data/processed/`: worldpop_features.csv, energy_features.csv, traffic_features.csv, environment_features.csv, socioeconomic_features.csv, synthetic_demographics.csv, fairness_report.csv

## Optional: Database mode (local/Render)

The app can read recent series from PostgreSQL when enabled; otherwise it falls back to processed files, then synthetic data.

Requirements
- PostgreSQL 14+ (or compatible) with PostGIS. In psql you can enable extensions:
  - CREATE EXTENSION postgis;
  - CREATE EXTENSION postgis_topology;

Configure
- Set environment variables (examples):
  - USE_DB=1
  - DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/susps_db_local
- Alternatively for local-only: USE_LOCAL_DB=true and LOCAL_DATABASE_URL=...

Initialize tables (one-time)
- Run this once to create the minimal tables used by the API:
```python path=null start=null
# Create tables in the configured DATABASE_URL
from src.backend.db.base import Base
from src.backend.db.session import engine
import src.backend.db.tables  # ensure models are imported
Base.metadata.create_all(bind=engine)
```

Notes
- If geoalchemy2 is installed, an optional geometry column is available on urban_areas.
- When USE_DB is enabled, the API serves energy/traffic endpoints from the DB first; if empty, processed/synthetic fallbacks are used.

## Deployment (Render)

This repo includes a `Procfile` and a Render blueprint `render.yaml`.

1. Push this repo to GitHub (or GitLab/Bitbucket)
   - Initialize git: `git init`
   - Add files: `git add .`
   - Commit: `git commit -m "chore: initial scaffold"`
   - Create a remote repo and push: `git remote add origin <YOUR_REPO_URL>` then `git push -u origin main`

2. Deploy on Render
   - In Render dashboard: New → Blueprint → point to your repo
   - Confirm service config from `render.yaml`
   - Deploy. Health check path: `/health`

Environment
- Python version is set via `render.yaml` env var `PYTHON_VERSION` (3.11.9)
- Start command uses Gunicorn with Uvicorn worker: `gunicorn src.backend.api:app -k uvicorn.workers.UvicornWorker`

Production URLs
- API health: `https://<your-app>.onrender.com/health`
- Dashboard: `https://<your-app>.onrender.com/dash/`
