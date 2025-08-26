# SUSPS Specification (Refined)

This document refines and mirrors the draft at `Sand-Box/susps.md`, adapted to the repository. It will be expanded as implementation proceeds.

- Version: 1.1
- Date: August 25, 2025

---

## 1. Project Overview

### 1.1 System Name
Smart Urban Simulation and Prediction System (SUSPS)

### 1.2 Project Goal
The primary goal of SUSPS is to create an AI-driven simulation and prediction tool for an urban center in Zambia (e.g., Lusaka). The system will assist urban planners, policymakers, and utility managers in making data-informed decisions regarding urban development, resource allocation, and infrastructure planning.

### 1.3 Target Users
- Urban Planners at the Lusaka City Council.  
- Policy Makers in government ministries.  
- Resource Managers at utility companies (ZESCO, LWSC).  
- Academic researchers in urban studies.  

---

## 2. Core System Features

### 2.1 Urban Growth Prediction Module
- Function: Predicts physical expansion patterns of the city over 5–10 years.  
- Inputs: Census data, GIS shapefiles, land-use data, satellite imagery.  
- Process: Machine learning models (e.g., Gradient Boosting, Random Forest).  
- Output: Interactive maps with color-coded density indicators.  

### 2.2 Energy Demand Forecasting Module
- Function: Forecasts future electricity and water demand.  
- Inputs: Urban growth outputs, historical utility consumption, seasonal data.  
- Process: Time-series forecasting (e.g., ARIMA, regression).  
- Output: Interactive charts and maps by zone.  

### 2.3 Traffic Flow Simulation Module
- Function: Simulates traffic patterns and predicts congestion points.  
- Inputs: OpenStreetMap road networks, population distribution, POIs.  
- Process: Simulation models analyzing effects of growth and infrastructure.  
- Output: Traffic volume heatmaps and bottleneck predictions.  

### 2.4 Interactive Scenario Analysis Tool
- Function: Allows "what-if" scenarios (e.g., new road, neighborhood, complex).  
- Process: Only re-runs relevant models to save performance.  
- Output: Cascading effects on growth, energy, and traffic visualized in dashboard.  

---

## 3. Technical Architecture & Requirements

### 3.1 Backend Architecture
- Language: Python 3.10+  
- Data Tools: Pandas, GeoPandas, NumPy  
- Machine Learning: Scikit-learn  
- Web Server: Gunicorn  
- Data Sources:  
  - Zambian census and population data (ZamStats)  
  - Lusaka GIS shapefiles (City Council or open sources)  
  - Historical utility data (ZESCO, LWSC)  
  - OpenStreetMap road data  

### 3.2 Web Application (Primary Interface)
- Framework: Dash (Plotly)  
- UI Components: Dash Bootstrap Components  
- Visualization: Plotly Express, Folium / Mapbox  
- Deployment: Git/GitHub + Render (PaaS)  
- Config: `requirements.txt`, `Procfile`  

### 3.3 Native Desktop Application (Optional)
- Strategy: Wrap web app instead of rebuilding.  
- Tech: PyWebView, PyInstaller.  
- Process: Run Dash locally → PyWebView GUI → packaged executable.  

---

## 4. Development Roadmap

- Phase 1 (Sept 2025): Core prediction modules (growth + energy) with maps.  
- Phase 2 (Sept–Oct 2025): Traffic simulation + scenario analysis.  
- Phase 3 (Oct 2025): Optimization, UI polish, optional desktop build.  

---

## 5. Risks & Mitigation

- Data Availability: Use synthetic/public datasets during dev, swap real data when available.  
- Performance: Limit runtime (<30s for datasets under 100MB), implement caching.  
- Feasibility: Modular phases ensure partial success even if some features slip.  

---

## 6. Evaluation & Success Criteria

- Accuracy: Compare predictions with historical test data.  
- Usability: Collect feedback from 2–3 planners/researchers or mock users.  
- Performance: Dashboard loads <5s, supports 10+ concurrent users.  
- Stretch Goal: AI assistant chatbot for querying scenarios (optional).  
