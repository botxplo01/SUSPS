# SUSPS User Guide

## Introduction

Welcome to the Smart Urban Simulation and Prediction System (SUSPS). This guide will walk you through the features of the SUSPS platform and how to use them to gain insights into urban dynamics. SUSPS is designed to help urban planners, researchers, and policymakers make data-driven decisions by providing predictive analytics and simulation tools for urban growth, energy consumption, and traffic flow.

## Getting Started

To get started with SUSPS, simply open the web application in your browser.

-   **URL**: [https://susps-main.onrender.com](https://susps-main.onrender.com)

The application is designed to be intuitive and easy to use. Upon your first visit, you will be greeted by the sign in page, where you can then sin in or sign up to access the main dashboard.

## Running the Application Locally

For developers or users who wish to run the application on their local machine, follow the steps below.

### Prerequisites

-   Python 3.11
-   Node.js 18 or later
-   Git

### Backend Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/SUSPS.git
    cd SUSPS
    ```

2.  **Create a virtual environment and install dependencies**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Run the backend server**:
    ```bash
    uvicorn src.backend.api:app --reload
    ```
    The backend API will now be running at `http://127.0.0.1:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory**:
    In a new terminal window, from the root of the project, navigate to the frontend directory:
    ```bash
    cd src/frontend
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

3.  **Run the frontend development server**:
    ```bash
    npm run dev
    ```
    The frontend application will be available at `http://localhost:5173`. You can now access the application in your web browser.


## Navigating the Dashboard

The SUSPS dashboard is your central hub for accessing all the features of the platform.

-   **Sidebar**: On the left side of the screen, you will find the main navigation sidebar. This is where you can select the urban area you wish to analyze.
-   **Main Content Area**: The main area of the dashboard displays key metrics and visualizations for the selected area.

### Selecting an Area

To begin, you must select an urban area from the dropdown menu in the sidebar. Once you select an area, the dashboard will populate with data and insights for that specific location.

`[Screenshot of the area selection dropdown in the sidebar]`

## Core Features

SUSPS offers a range of features to explore and analyze urban data.

### Urban Growth

The Urban Growth section provides predictions on population growth and urban expansion.

1.  **Navigate to Urban Growth**: Select "Urban Growth" from the sidebar.
2.  **View Predictions**: The chart displays the predicted population growth over time for the selected area.
3.  **Simulation**: Use the simulation controls to model different growth scenarios, such as changes in the annual growth rate.

`[Screenshot of the Urban Growth page with a growth projection chart]`

### Energy Demand

This section provides forecasts of energy consumption.

1.  **Navigate to Energy**: Select "Energy" from the sidebar.
2.  **Analyze Demand**: The chart shows the forecasted energy demand (in MWh) over a 24-hour period.
3.  **Simulate Scenarios**: Use the simulation panel to create scenarios like demand response events or shifts in peak consumption hours.

`[Screenshot of the Energy page with a daily energy demand curve]`

### Traffic Flow

The Traffic Flow section allows you to simulate and analyze traffic patterns.

1.  **Navigate to Traffic**: Select "Traffic" from the sidebar.
2.  **Examine Traffic Volume**: The histogram displays the simulated traffic volume throughout the day.
3.  **Model Scenarios**: Use the simulation controls to model the impact of events like road closures or the introduction of public transport.

`[Screenshot of the Traffic page with a traffic volume histogram]`

### Hotspot Analysis

SUSPS can identify and visualize urban hotspots, such as areas with high traffic congestion or rapid growth.

1.  **View Hotspot Map**: On the dashboard, you can view a map with hotspot overlays.
2.  **Interpret the Map**: Red circles indicate areas of concern, while green circles highlight areas of improvement or "optimal zones".

`[Screenshot of the hotspot map with red and green overlays]`

### AI Advisory Engine

The AI Advisory Engine provides plain-language insights and recommendations based on the data.

-   **Insights Panel**: On each page (Dashboard, Urban Growth, etc.), you will find an "AI Analysis & Insights" panel.
-   **Actionable Advice**: This panel contains a summary of the key findings and suggests potential actions or areas for further investigation.

`[Screenshot of the AI Analysis & Insights panel]`

### Simulation Mode

The simulation mode is a powerful feature that allows you to explore "what-if" scenarios.

1.  **Activate Simulation Mode**: On the Urban Growth, Energy, or Traffic pages, toggle the mode from "Real" to "Simulate".
2.  **Adjust Parameters**: A "Simulation parameters" card will appear, allowing you to adjust variables such as population scale, demand scale, and peak hour shifts.
3.  **Observe Results**: The charts will update in real-time to reflect the impact of your changes, with the simulated data overlaid on the baseline predictions.

`[Screenshot of the simulation parameter controls and the updated chart with simulated data]`

---
We hope this guide helps you get the most out of the SUSPS platform. As the project evolves, this guide will be updated to reflect new features and enhancements.