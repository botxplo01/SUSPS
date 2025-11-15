# SUSPS FILE STRUCTURE

``` graphql:

SWE-Project--SUSPS/
├── data/                              # raw and processed data
│   ├── processed/
│   │   ├── .gitkeep
│   │   ├── energy_features.csv
│   │   ├── environment_features.csv
│   │   ├── fairness_report.csv
│   │   ├── socioeconomic_features.csv
│   │   ├── synthetic_demographics.csv
│   │   ├── traffic_features.csv
│   │   └── worldpop_features.csv
│   └── raw/
│       ├── .gitkeep
│       ├── energy_demand.csv
│       ├── environment_monthly.csv
│       ├── socioeconomic.csv
│       ├── traffic_flows.csv
│       └── worldpop_summary.csv
├── dist/                              # build artifacts
│   └── .gitkeep
├── docs/                              # documentation
│   ├── specification.md
│   └── user_guide.md
├── src/                               # application source
│   ├── backend/                       # FastAPI API
│   │   ├── __init__.py
│   │   ├── api.py
│   │   ├── models/
│   │   │   └── .gitkeep
│   │   └── preprocessing/
│   │       └── .gitkeep
│   ├── desktop/                       # desktop entry point
│   │   ├── __init__.py
│   │   └── main.py
│   ├── frontend/                      # React + Tailwind SPA
│   │   ├── package.json
│   │   └── src/
│   └── pipeline/                      # data pipeline
│       ├── __init__.py
│       ├── ingest.py                  # fetch OSM, GHSL, WorldPop etc.
│       ├── preprocess.py              # build features/targets
│       ├── synthetic.py               # bias-aware synthetic generator
│       ├── fairness.py                # fairness & bias audits
│       └── config.py                  # paths, constants, parameters
├── tests/                             # pytest tests
│   ├── test_api.py
│   ├── test_app.py
│   ├── test_models.py
│   └── test_pipeline.py               # pipeline unit tests
├── .gitignore
├── Procfile                           # process entry for deployment
├── README.md
├── render.yaml                        # Render service config
├── requirements.txt                   # Python dependencies
└── dvc.yaml                           # reproducible pipeline

```
