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
