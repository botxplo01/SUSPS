# Gemini Code Assistant Context

This document provides instructional context about the SUSPS project for the Gemini Code Assistant.

## Project Overview

SUSPS (Smart Urban Simulation and Prediction System) is an AI-driven platform to predict urban growth, forecast energy demand, and simulate traffic flow for Zambian cities. The project aims to provide decision-makers with actionable insights for sustainable urban planning in Zambia. For the demonstration phase, Nairobi data is being used due to current data limitations in Zambia.

- **Backend**: Python with [FastAPI](https://fastapi.tiangolo.com/).
- **Frontend**: [Dash](https://dash.plotly.com/) (by Plotly) for the interactive web UI.
- **Data Pipeline**: A series of Python scripts orchestrated with [DVC](https://dvc.org/) for data ingestion, preprocessing, and generation.
- **Deployment**: Deployed on [Render](https://render.com/) via a `Procfile` and `render.yaml`.

The application is served from a single FastAPI backend, which mounts the Dash application at the `/dash/` endpoint.

## System Architecture

The proposed system architecture consists of the following modules:

-   **Data Ingestion Module**: Imports, cleans, and integrates demographic, transport, and energy datasets.
-   **Prediction Engine**: Runs simulation models for population, traffic, and energy demand.
-   **Visualization Module**: Provides dashboards, maps, and charts for planners.
-   **User Interface**: Interactive web-based system for policymakers and stakeholders.

The system is designed to be modular, with each module communicating through defined APIs. While the current implementation is file-based, the long-term vision includes a `PostgreSQL` database with `PostGIS` for spatial data.

## Development Roadmap

The project is being developed in phases:

-   **Phase 1 (Sept 2025)**: Core prediction modules (growth + energy) with maps.
-   **Phase 2 (Sept–Oct 2025)**: Traffic simulation + scenario analysis.
-   **Phase 3 (Oct 2025)**: Optimization, UI polish, optional desktop build.

## Building and Running

### 1. Setup

1.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 2. Data Pipeline

The project includes a data pipeline to generate the data used by the application.

-   **Run the full pipeline (if DVC is installed)**:
    ```bash
    dvc repro
    ```
-   **Run individual pipeline steps**:
    ```bash
    python -m src.pipeline.ingest
    python -m src.pipeline.preprocess
    python -m src.pipeline.synthetic
    python -m src.pipeline.fairness
    ```

### 3. Running the Web Application

-   **Run locally with auto-reload**:
    ```bash
    uvicorn src.backend.api:app --reload
    ```
-   **Access the application**:
    -   **API Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
    -   **Dash UI**: [http://127.0.0.1:8000/dash/](http://127.0.0.1:8000/dash/)

## Testing

The project uses `pytest` for testing.

-   **Run all tests**:
    ```bash
    pytest
    ```

## Deployment

The application is configured for deployment on Render.

-   **Build Command**: `pip install -r requirements.txt`
-   **Start Command**: `gunicorn src.backend.api:app -k uvicorn.workers.UvicornWorker --timeout 120`

The `render.yaml` file contains the service configuration, and the `Procfile` defines the web process.

## Development Conventions

-   **Code Style**: The code follows standard Python conventions (PEP 8).
-   **Data**: Raw data is stored in `data/raw` and processed data in `data/processed`. The pipeline scripts in `src/pipeline` are responsible for this transformation.
-   **Configuration**: The `src/pipeline/config.py` file contains configuration for the data pipeline.
-   **API**: The main FastAPI application is in `src/backend/api.py`.
-   **Web App**: The Dash application is created in `src/webapp/app.py`.
-   **Database**: The initial proposal includes a `PostgreSQL` database with `PostGIS` for data storage, though the current implementation is file-based.