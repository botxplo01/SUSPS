
SUSPS — Smart Urban Simulation and Prediction System

Author: Lameck David Musumpuka


1) Overview

  SUSPS is a full-stack decision-support system for urban planning and resource
  management in rapidly growing cities. It combines:

  - A React frontend for interactive visualization (maps + charts)
  - A FastAPI backend providing REST APIs for growth, energy, traffic, hotspots,
    forecasting, simulation, exports, and an advisory engine
  - A Python data pipeline (ingest → preprocess) that produces canonical raw and
    processed artifacts under data/<CITY>/

  PostgreSQL is required for the system to work. The backend expects a database
  connection for core features, and the recommended local workflow is:

  - Apply schema
  - Run ingest → preprocess
  - Seed the database
  - Start backend + frontend


2) What the system does

   Core capabilities:

    - Urban growth: population forecasting and trends
    - Energy: profiles and forecasting (and simulation overlays)
    - Traffic: profiles, forecasting, and live traffic integration (TomTom)
    - Hotspots: identify areas of interest (e.g., congestion / demand / risk)
    - Simulation: run scenario simulations across growth/energy/traffic
    - Advisory engine: generates narrative insights + recommended actions
      - Cached responses with deterministic fallback
      - Snapshot-based advisory supported so the narrative matches what the user is
        currently viewing in the UI (Real/Predicted/Simulated/Optimal)


3) High-level architecture

Frontend (React/Vite)  <---->  Backend (FastAPI)  <---->  Pipeline (Pandas)
        |                              |                     |
        v                              v                     v
   Web Browser                    Optional DB            Data sources
                                  (Postgres)            (S3/APIs/files)


4) Project directory layout (important paths)

    - src/backend/api.py --------------------------------------- # FastAPI app entrypoint
    - src/backend/advisory/engine.py --------------------------- # Advisory prompt building + caching
    - src/backend/advisory/hf_client.py ------------------------ # Hugging Face wrapper with fallbacks
    - src/pipeline/ingest.py ----------------------------------- # Raw data ingestion (provider + fallbacks)
    - src/pipeline/preprocess.py ------------------------------- # Feature engineering → processed outputs
    - src/backend/db/ ------------------------------------------ # Schema + seed utilities
    - src/frontend/ -------------------------------------------- # React SPA
    - data/<CITY>/raw/ and data/<CITY>/processed/ -------------- # Data, data directories, and domains


5) Running locally: Prerequisites (all resources used are free):

    - Python 3.11
    - Node.js 18+
    - PostgreSQL 14+ (required)
    - OpenAQ API key (can be obtained for free: https://docs.openaq.org/docs)
    - HuggingFace API key and 'meta-llama/Llama-3.1-8B-Instruct' license accepted (can be obtained for free: https://huggingface.co/)
    - TomTom API key (can be obtained for free: https://developer.tomtom.com/documentation)
    - Openweather API key (can be obtained for free: https://openweathermap.org/api)


6) Running locally: Local setup (PostgreSQL required):

    Backend + database:

      1) Create a Postgres database and user (example names)
          - DB: susps
          - User: susps_user (default user `postgres` is recommended)

      2) Apply schema (one-time)
          a) Option 1: use the schema dump directly:
                       > psql -U susps_user -d susps -f src/backend/db/susps_schema_dump.sql

          b) Option 2: run the schema creation script
                       > python -m scripts/create_schema.py

      3) Configure `.env` at project directory root (example):

          USE_LOCAL_DB=true
          LOCAL_DATABASE_URL=postgresql://susps_user:password@localhost:5432/susps

      4) Create a virtual environment and install dependencies:
          > cd SUSPS-System
          > .venv\scripts\activate                # On Unix-like systems, use `.venv/bin/activate`
          > pip install -r requirements.txt

      5) Generate artifacts and seed DB
          > python -m src.pipeline.ingest
          > python -m src.pipeline.preprocess
          > python -m src.backend.db.seed_from_processed

      6) Start the backend as usual
          > uvicorn src.backend.api:app --reload

         API URLs:
          - http://127.0.0.1:8000/health
          - http://127.0.0.1:8000/docs

    Frontend:

      1) From the project root, go to the frontend folder
          > cd src/frontend

      2) Install dependencies and start dev server
          > npm install
          > npm run dev

    Frontend URL:
      - http://localhost:5173

    Ensure the frontend points to the backend. If needed, set VITE_API_BASE_URL to
    http://127.0.0.1:8000.


7) Key environment variables

  City scoping:
    - DATA_CITY or CITY_NAME (default: Nairobi)
    - CITY_LAT, CITY_LON (default aligns to Nairobi CBD)

  Traffic providers:
    - TRAFFIC_PROVIDER=tomtom|synthetic
    - TOMTOM_API_KEY

  Traffic live caching:
    - TRAFFIC_LIVE_TTL_SECONDS (default 300)
    - TRAFFIC_LIVE_POINTS_TTL_SECONDS (default 30)

  Weather/Air quality:
    - WEATHER_PROVIDER=openweather | optionally open-meteo
    - OPENWEATHER_API_KEY
    - OPEN_AQ_API_KEY

  Hugging Face (Advisory: required for AI Analysis and Insights features):
    - HF_API_KEY
    - HF_MODEL_NAME

8) Useful endpoints (backend)

    Core:
    - GET /growth
    - GET /energy
    - GET /traffic
    - GET /energy/summary
    - GET /traffic/summary

    Live traffic:
    - GET /traffic/live

    Advisory:
    - GET  /advisory/status
    - GET  /advisory/{scope}
    - POST /advisory/{scope}   (snapshot-based; recommended)

    Simulation + forecasting:
    - POST /simulate/run
    - POST /ts/forecast

    Hotspots/environment:
    - GET /hotspots/areas
    - GET /hotspots/areas/forecast
    - GET /environment/features
    - GET /air_quality/daily


8) Deployment

  The system is deployed to Render, and can be accessed through the links below if you do not have the credentials for 
  some environment variables (HuggingFace, TomTom, OpenAQ, AWS) that require them in order for the system's features to be accessible.

  - Backend: `https://susps-web.onrender.com` (you can start with this link if you want to observe the service startup before accessing the system using the frontend link)
  - Frontend: `https://susps-main.onrender.com` (use this link to access the system, but you will have to wait atleast 4 minutes to attempt the second sign in)

  **NOTE: - All services (backend, frontend, and Render-managed PostgreSQL database) are 
            on a free tier and may spin down due to inactivity. The frontend is configured to 
            automatically send a "wake-up" request to the backend upon loading to ensure a seamless 
            user experience. Note that it may take 3 - 8 minutes for the system to fully startup.
    
          - After 50 seconds of inactivity, the system is automatically spun down, and it might take at least 
            5-8 minutes to fully startup from a cold start. If starting from a cold start. You are advised to 
            attempt to sign in at least 3-4 times after the 5-8 minute threshold after the first attempt, making 
            sure you make the second attempt at least after 4 minutes after the first.
