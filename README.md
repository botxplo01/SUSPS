# SUSPS: Smart Urban Simulation and Prediction System by David Lameck

**SUSPS** is a sophisticated, AI-driven platform designed for urban planning and resource management in the context of rapidly growing cities, with an initial focus on Lusaka, Zambia. The system provides predictive insights into urban growth, energy consumption, and traffic patterns, enabling city planners, policymakers, and researchers to make data-informed decisions.

This project is developed as a Final Year Software Engineering Project, showcasing a modern, full-stack application with a decoupled architecture, a data processing pipeline, and machine learning-powered features.

## System Architecture

The SUSPS platform is built on a decoupled, service-oriented architecture, which allows for independent development, deployment, and scaling of its components. The system comprises three main parts: a React-based frontend, a FastAPI backend, and a data processing pipeline.

``` graphql:
+-----------------+      +-----------------+      +-----------------+
|   Frontend      |      |   Backend       |      |   Data Pipeline |
| (React, Vite)   | <--> | (FastAPI, Python)| <--> | (Python, Pandas)|
+-----------------+      +-----------------+      +-----------------+
        |                      |                      |
        v                      v                      v
+-----------------+      +-----------------+      +-----------------+
|   User          |      |   Database      |      |   Data Sources  |
| (Web Browser)   |      | (PostgreSQL)    |      | (S3, APIs)      |
+-----------------+      +-----------------+      +-----------------+
```

## Features

- **Urban Growth Prediction**: Forecasts population growth and urban expansion using historical data and predictive models.
- **Energy Demand Forecasting**: Predicts energy consumption patterns across different times of the day and seasons.
- **Traffic Flow Simulation**: Simulates traffic flow and congestion patterns to identify potential bottlenecks.
- **AI Advisory Engine**: Provides actionable insights and recommendations based on the analysis of the system's predictions.
- **Interactive Data Visualization**: A rich, map-based user interface to visualize data and simulation results.
- **Scenario Simulation**: Allows users to create and compare different "what-if" scenarios for urban development.
- **Hotspot Analysis**: Identifies areas of interest, such as potential congestion hotspots or areas with high energy demand.

## Technology Stack

### Frontend

- **Framework**: React with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Mapping**: Leaflet
- **Routing**: React Router

### Backend

- **Framework**: FastAPI
- **Language**: Python
- **Database ORM**: SQLAlchemy
- **Geospatial**: GeoAlchemy2
- **API Specification**: OpenAPI (via Swagger UI)

### Data Pipeline & Database

- **Data Processing**: Pandas
- **Database**: PostgreSQL with PostGIS for geospatial capabilities
- **Data Storage**: AWS S3 for raw data storage

## Getting Started

To set up a local development environment, you will need to run the frontend and backend services separately.

### Prerequisites

- Python 3.11
- Node.js 18 or later
- PostgreSQL 14 or later (optional, for database-backed features)

### Backend Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/SUSPS.git
    cd SUSPS
    ```

2. **Create a virtual environment and install dependencies**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3. **Run the backend server**:

    ```bash
    uvicorn src.backend.api:app --reload
    ```

    The API will be available at `http://127.0.0.1:8000`, and the interactive API documentation (Swagger UI) can be accessed at `http://127.0.0.1:8000/docs`.

### Frontend Setup

1. **Navigate to the frontend directory**:

    ```bash
    cd src/frontend
    ```

2. **Install dependencies**:

    ```bash
    npm install
    ```

3. **Run the frontend development server**:

    ```bash
    npm run dev
    ```

    The frontend will be available at `http://localhost:5173`.

### Database Setup (Optional)

For features that require a database, you can set up a local PostgreSQL instance.

1. **Create a PostgreSQL database and user.**

2. **Configure the database connection**:
    Set the `USE_LOCAL_DB` and `LOCAL_DATABASE_URL` environment variables in a `.env` file in the root of the project.

3. **Apply the database schema**:
    The schema is defined in `src/backend/db/susps_schema_dump.sql`.

4. **Seed the database**:
    Run the seeding script to populate the database with processed data:

    ```bash
    python -m src.backend.db.seed_from_processed
    ```

## Deployment

The SUSPS platform is deployed on Render, with the frontend and backend running as separate services.

- **Frontend**: `https://susps-main.onrender.com`
- **Backend**: `https://susps-web.onrender.com`

The backend service is on a free tier and may spin down due to inactivity. The frontend is configured to automatically send a "wake-up" request to the backend upon loading to ensure a seamless user experience.

Please note that due to the use of a free plan, the service experiences longer startup times. After 50 seconds of inactivity, the system is automatically spun down, and it might need to take at least 3-5 minutes to fully startup from a cold start. If starting from a cold start, you are advised to attempt to sign in at least 3-4 times within the 3 minute threshold after the first attempt, making sure you make the second attempt at least after 3 minutes after the first.

## Usage

Access the deployed frontend at `https://susps-main.onrender.com`. From the dashboard, you can navigate to different sections to explore predictions and simulations for urban growth, energy, and traffic.

## Data Pipeline

The data pipeline is a series of Python scripts that ingest, process, and enrich data from various sources. The pipeline is orchestrated to produce clean, analysis-ready datasets that are used by the backend and the machine learning models.

To run the pipeline locally:

```bash
python -m src.pipeline.ingest
python -m src.pipeline.preprocess
```

The pipeline reads raw data and writes processed artifacts to the `data/` directory.

---
*This project is for educational purposes as part of a Final Year Software Engineering degree.*
