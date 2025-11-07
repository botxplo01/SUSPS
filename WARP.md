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
  - Run type check: `mypy`

- Deployment (Render)
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn src.backend.api:app -k uvicorn.workers.UvicornWorker --timeout 120`
  - Health check path: `/health` (see `render.yaml`, `Procfile`).

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
- DB-backed API (Docker): `/areas`, `/energy`, `/traffic`, summaries at `/energy/summary`, `/traffic/summary`
