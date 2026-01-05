# SUSPS User Guide

_**@author: David Lameck**_

## Introduction

Welcome to the Smart Urban Simulation and Prediction System (SUSPS). This guide will walk you through the features of the SUSPS platform and how to use them to gain insights into urban dynamics. SUSPS is designed to help urban planners, researchers, and policymakers make data-driven decisions by providing predictive analytics and simulation tools for urban growth, energy consumption, and traffic flow.

## Getting Started

To get started with SUSPS, simply open the web application in your browser.

- **URL**: [https://susps-main.onrender.com](https://susps-main.onrender.com)

Please note that, since the app is hosted on free-tier services, some features, or even the entire system, may be limited or unavailable if traffic exceeds the free tier's resource limits. If you'd like to run the system on your own machine for free, you can easily obtain your credentials by checking the [prerequisites section](#prerequisites).

## Running the Application Locally

For developers or users who wish to run the application on their local machine, follow the steps below.

### Prerequisites

- Raw data files (view `docs/data_sources.md` for details)
- Python 3.11
- Node.js 18+
- PostgreSQL 14+ (required)
- OpenAQ API key (can be obtained for free: <https://docs.openaq.org/docs>); or optionally AirQo API key (can be obtained for free: <https://airqo.net/products/api>)
- HuggingFace API key and 'meta-llama/Llama-3.1-8B-Instruct' license accepted (can be obtained for free: <https://huggingface.co/>)
- TomTom API key (can be obtained for free: <https://developer.tomtom.com/documentation>)
- Openweather API key (can be obtained for free: <https://openweathermap.org/api>)

### BACKEND SETUP

1. **Create a virtual environment and install dependencies**:

    ```bash
    > python -m venv .venv
    > .venv\scripts\activate  # On Unix-like systems, use `.venv/bin/activate`
    > pip install -r requirements.txt
    ```

2. **Setup the database (required)**
   1. **Create a PostgreSQL user and a database.**

   2. **Configure the database connection**:
       Set the `USE_LOCAL_DB` and `LOCAL_DATABASE_URL` environment variables in a `.env` file in the root of the project.

   3. **Apply the database schema**:
       The schema is defined in `src/backend/db/susps_schema_dump.sql`. It can be created by running `scripts/create_schema.py` as a script:

       ``` bash
       > python -m scripts/create_schema.py
       ```

3. **Run the pipeline locally:**

    ```bash
    > python -m src.pipeline.ingest
    > python -m src.pipeline.preprocess
    ```

4. **Seed the database**:
       Run the seeding script to populate the database with processed data:

    ```bash
    > python -m src.backend.db.seed_from_processed
    ```

5. **Run the backend server**:

    ```bash
    > uvicorn src.backend.api:app --reload
    ```

    The API will be available at `http://127.0.0.1:8000`, and the interactive API documentation (Swagger UI) can be accessed at `http://127.0.0.1:8000/docs`.

### FRONTEND SETUP

1. **Navigate to the frontend directory**:

    ```bash
    > cd src/frontend
    ```

2. **Install dependencies**:

    ```bash
    > npm install
    ```

3. **Run the frontend development server**:

    ```bash
    > npm run dev
    ```

    The frontend will be available at `http://localhost:5173`.

## Navigating the Dashboard

The SUSPS dashboard is your central hub for accessing all the features of the platform.

- **Sidebar**: On the left side of the screen, you will find the main navigation sidebar. This is where you can select the urban area you wish to analyze.
- **Main Content Area**: The main area of the dashboard displays key metrics and visualizations for the selected area.

### Selecting an Area

To begin, you must select an urban area from the dropdown menu in the sidebar. Once you select an area, the dashboard will populate with data and insights for that specific location.

## Core Features

SUSPS offers a range of features to explore and analyze urban data.

### Urban Growth

The Urban Growth section provides predictions on population growth and urban expansion.

1. **Navigate to Urban Growth**: Select "Urban Growth" from the sidebar.
2. **View Predictions**: The chart displays the predicted population growth over time for the selected area.
3. **Simulate Scenarios**: Use the simulation controls to model different growth scenarios, such as changes in the annual growth rate.

### Energy Demand

This section provides forecasts of energy consumption.

1. **Navigate to Energy**: Select "Energy" from the sidebar.
2. **Analyze Demand**: The chart shows the forecasted energy demand (in MWh) over a 24-hour period.
3. **Simulate Scenarios**: Use the simulation panel to create scenarios like demand response events or shifts in peak consumption hours.

### Traffic Flow

The Traffic Flow section allows you to simulate and analyze traffic patterns.

1. **Navigate to Traffic**: Select "Traffic" from the sidebar.
2. **Examine Traffic Volume**: The histogram displays the simulated traffic volume throughout the day.
3. **Live Traffic**: The Live Traffic card displays current live traffic statistics. It can be updated by clicking the _Refesh_ button.
4. **Simulate Scenarios**: Use the simulation controls to model the impact of events like road closures or the introduction of public transport.

### Hotspot Analysis

SUSPS can identify and visualize urban hotspots, such as areas with high traffic congestion or rapid growth.

1. **View Hotspot Map**: On the dashboard, you can view a map with hotspot overlays.
2. **Interpret the Map**: Red circles indicate areas of concern, while green circles highlight areas of improvement or "optimal zones".

### AI Advisory Engine

The AI Advisory Engine provides plain-language insights and recommendations based on the data.

- **Insights Panel**: On each page (Dashboard, Urban Growth, etc.), you will find an "AI Analysis & Insights" panel.
- **Actionable Advice**: This panel contains an AI summary of the key findings and suggests potential actions or areas for further investigation.

### Simulation Mode

The simulation mode is a powerful feature that allows you to explore "what-if" scenarios.

1. **Activate Simulation Mode**: On the Urban Growth, Energy, or Traffic pages, toggle the mode from "Real" to "Simulate".
2. **Adjust Parameters**: A "Simulation parameters" card will appear, allowing you to adjust variables such as population scale, demand scale, and peak hour shifts.
3. **Observe Results**: The charts will update in real-time to reflect the impact of your changes, with the simulated data overlaid on the baseline predictions.

---
