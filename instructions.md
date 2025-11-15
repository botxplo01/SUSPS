# SUSPS — Master Development Prompt for Coding Agent

## Smart Urban Simulation and Prediction System

### (Full Specification — Copy & Paste)

---

## 1. System Purpose and Objectives

### General Objective

Develop the **Smart Urban Simulation and Prediction System (SUSPS)**, a full-stack application that integrates demographic, mobility, energy, and environmental datasets to predict:

- Urban growth
- Energy demand
- Traffic flow
- Optimal solutions for sustainable development

All predictions must be based on integrated datasets, API-fetched data, and machine learning model outputs.

### Specific Objectives

- Analyze demographic and population growth using census + geospatial data.
- Forecast future energy demands using population + land use projections.
- Model traffic flow using transportation datasets + mobility APIs.
- Build a working simulation prototype that produces predictive insights.
- Evaluate system effectiveness for sustainable and efficient urban planning.

---

## 2. System Structure & Modules

The system must implement the following modules:

### 2.1 Data Ingestion Module

- Import raw datasets (population, traffic, energy, GIS, etc.).
- Clean, normalize, preprocess all data.
- Integrate Overpass API (OSM), Open-Meteo, and mobility API data.
- Implement fallback logic:
  - If API unavailable → use stored dataset
  - If dataset missing → generate synthetic realistic data
- Save processed data under `/processed/<area_name>/`.

### 2.2 Prediction Engine

The system must:

- Process cleaned datasets.
- Send processed data to selected Hugging Face/IBM models for analysis and forecasting.
- Receive model outputs (JSON or numeric predictions).
- Integrate outputs into the frontend visualizations + insights sections.

**Required model tasks:**

- Urban growth forecasting
- Population density estimation
- Traffic flow prediction
- Energy consumption forecasting
- Optimal scenario analysis
- Anomaly detection

**Use free high-quality models, including:**

- IBM geospatial foundation models (GFM)
- Time-series forecasting models
- Tabular prediction models (AutoGluon, CatBoost, LightGBM, etc.)
- Geospatial segmentation models

### 2.3 Visualization Module

The system must render:

- Labeled bar charts
- Line charts
- Histograms
- 2D maps with overlays
- Hotspot visualizations
- Tables
- Description + Insight text sections

**Charts must NOT contain gridlines.**

**Maps must show:**

- Hotspots (population, traffic, energy)
- Predicted future hotspots
- Optimal scenario overlays

### 2.4 User Interface Module

The UI must:

- Be built in React + Tailwind CSS
- Use modern UI components and interactions
- Be responsive for both desktop and mobile
- Be visually clean and minimalistic with soft shadows and rounded corners
- Include dynamic charts, maps, tables, and text sections
- Provide **Real vs Simulate** mode toggles

**IMPORTANT:**

> The system must NOT implement sign-in or authentication yet.
> Wait for explicit instruction.
>
> However, the backend must include a `users` table in the database schema for future sign-in support.

---

## 3. System Modes

The system must support two fully functional modes:

### 3.1 REAL Mode

**Uses:**

- Raw datasets
- API-fetched data (OSM + Weather + Mobility)
- Model predictions

**Shows:**

- Actual current real-world state of selected area
- Real observed density, traffic, energy, etc.
- Real-state hotspots
- Real-time derived system forecasts

### 3.2 SIMULATE Mode

**Uses:**

- Raw datasets
- API-fetched data
- Optional user inputs
- Model predictions

**Provides:**

- Simulation of hypothetical scenarios
- User-adjusted demographic, traffic, or energy variables
- Uploading optional user data files (CSV, GeoJSON, TIFF, etc.)
- Optimal solution scenarios recommended by system
- Recomputed hotspots and predictions based on user edits

---

## 4. Data Pipeline

Pipeline must be implemented exactly in this order:

```
1. Load raw datasets
2. Fetch API data (OSM + weather + mobility)
    - If unavailable: fallback to stored dataset
    - If missing: generate synthetic realistic data
3. Merge, clean, normalize datasets
4. Save processed dataset under /processed/<area>
5. Display processed data in REAL mode
6. Send processed data to HF/IBM models
7. Receive model outputs
8. Update:
      • Description section
      • Insights section
      • Charts
      • Tables
      • Maps
9. For Simulate Mode:
      • Accept user input
      • Merge user input into datasets
      • Re-run steps 3–8
```

---

## 5. API Integration Requirements

### 5.1 OpenStreetMap (OSM) — Overpass API

Must be used to fetch:

- Road networks
- Buildings
- Land use polygons
- Points of interest
- Traffic-relevant features
- Residential zones
- Industrial areas
- Footpaths and mobility features

**Mandatory Implementation:**

- Query by bounding box
- Query by named area
- Query by polygon
- Parse response as GeoJSON
- Store fetched datasets for reuse
- Integrate into maps, charts, and predictions

### 5.2 Weather — Open-Meteo API

Must fetch:

- Air quality
- Temperature
- Humidity
- Dust & particulate matter
- Weather anomalies

Used to detect:

- Unusual population clustering
- Density heat patterns
- Traffic impact from weather

### 5.3 Mobility / Traffic API (Optional)

If mobility API is not available:

- Use Overpass OSM traffic-relevant tags
- Use stored mobility dataset
- Generate synthetic mobility data

---

## 6. Frontend Requirements

The entire frontend must be implemented using:

- React.js (latest)
- Tailwind CSS (latest)

**Features:**

- Fully responsive design
- Dynamic components
- Smooth transitions
- Minimalistic layout
- Modern UI with rounded corners + soft shadows
- Fast-loading and modular

---

## 7. UI Layout Requirements

### 7.1 Persistent Left Sidebar

Color: `#404040`

Must include:

- Title at top: `SUSPS`
- Search bar with:
  - Real-time suggestions
  - “No results” fallback
  - Click to load area
- Navigation options:
  - Dashboard
  - Urban Growth
  - Energy
  - Traffic
- Active option highlighted in `#fefefe`

### 7.2 Header Section

Includes:

- Page title
- "Sign out" button (visible only; functional redirect)
- Sign-in functionality NOT implemented yet

### 7.3 Page Structure Below Header

- Badge showing current selected area
- Toggle switch (Real ↔ Simulate)
  - Rounded pill switch
  - Active mode highlighted in black
- Description Section
- Tables appropriate to each page
- Charts (bar, line, histogram)
- Maps
  - OSM-based
  - Shows hotspots, overlays, optimal routes/zones
- Insights Section
  - Very detailed interpretation and strategic analysis

### 7.4 Floating Bottom-Left Action Toggle

Must include:

- Predict — show model forecasts
- Optimize — show optimal efficiency scenario
- Simulate — prompt user to input or upload simulation data

This panel appears on:

- Urban Growth
- Energy
- Traffic

---

## 8. Page-Specific Mandatory Requirements

### 8.1 Dashboard

Must include:

- Large visual panels
- Summary of Urban Growth module
- Summary of Energy module
- Summary of Traffic module
- Mini-map and sparkline previews
- Overview: “How the system works”

### 8.2 Urban Growth Page

Show:

- Population growth statistics
- Census data tables
- GIS population raster summary
- Forecasted population density map
- Hotspots of urban pressure
- Weather correlation
- Optimal colony/settlement placement recommendations
- Predict / Optimize / Simulate functionalities

**Data sources:**

- Census datasets
- GeoTIFF or raster population datasets
- OSM land use
- Weather
- User inputs
- Hugging Face/IBM models

### 8.3 Energy Page

Show:

- Current energy usage
- Consumption trends
- Demand spikes
- Forecasted consumption
- Heatmap of energy-stressed areas
- Infrastructure strain predictions
- Optimal distribution network suggestions
- Simulation tools

**Data Sources:**

- Energy baseline datasets
- Population density data
- Predicted growth
- Weather (to detect abnormal consumption)
- HF/IBM forecasting models

### 8.4 Traffic Page

Show:

- Current road network
- Traffic flow
- Congestion hotspots
- Predicted congestion patterns
- Mobile movement simulation
- Emissions impact
- Optimal routing or station positioning
- Simulation features

**Data sources:**

- OSM road network
- Mobility datasets
- Weather
- User inputs
- HF/IBM traffic models

---

## 9. Database Requirements

Database must include:

- `areas` table
- `processed_data` table
- `simulation_inputs` table
- `users` table (for future login)

But no authentication logic yet

Only include schema

---

## 10. Additional Mandatory Rules

- Do NOT implement sign-in yet.
- Implement everything else fully.
- Use modular backend API architecture.
- Use modern UI and scalable components.
- Implement complete data pipeline from ingestion → model → visualization.
- Include support for simulation with user inputs.

---

## 11. What You (Coding Agent) Must Deliver

You must generate the full implementation including:

- Backend architecture
- React frontend
- Tailwind CSS styling
- API integration logic
- Data ingestion + cleaning scripts
- OSM Overpass API client
- Weather API client
- Mobility API client (optional fallback)
- Hugging Face/IBM model interface
- Chart components
- Map components
- Simulation engine
- Database schema
- All pages + sections + components exactly as specified

Do not omit or simplify any detail.
Do not summarize.
Build exactly what is described.
