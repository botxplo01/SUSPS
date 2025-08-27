# SUSPS: Smart Urban Simulation and Prediction System

SUSPS is an AI-driven system to predict urban growth, forecast energy demand, and simulate traffic flow for Zambian cities.

- Web UI: Dash (Plotly) mounted on FastAPI
- Backend: FastAPI (Python)
- Deployment: Render (Procfile + Gunicorn)

Quick start:
- Create a venv and install requirements
- Run locally: `uvicorn src.backend.api:app --reload`
- Open Dash: http://127.0.0.1:8000/dash/

See `docs/specification.md` for the full spec and `docs/user_guide.md` for usage.

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
