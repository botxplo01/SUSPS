from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import os

from src.models.growth import (
    predict_growth,
    predict_from_processed,
    growth_from_census,
    forecast_from_processed,
)
from src.models.energy import (
    daily_profile as energy_profile,
    daily_profile_from_processed as energy_profile_from_processed,
)
from src.models.traffic import (
    daily_profile as traffic_profile,
    daily_profile_from_processed as traffic_profile_from_processed,
)
from src.webapp.app import create_dash_app

app = FastAPI(title="SUSPS Backend", version="0.1.0")

# CORS (adjust origins as needed for deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return JSONResponse({"status": "ok", "service": "susps", "version": "0.1.0"})


# Simple in-memory config for demo source selection on Render
_DEFAULT_SOURCE = os.getenv("DEFAULT_DATA_SOURCE", "demo")


class ConfigPayload(BaseModel):
    data_source: str


@app.get("/config")
def get_config():
    return {"data_source": _DEFAULT_SOURCE}


@app.post("/config")
def set_config(payload: ConfigPayload):
    global _DEFAULT_SOURCE
    if payload.data_source not in {"demo", "api"}:
        return JSONResponse({"detail": "invalid data_source"}, status_code=400)
    _DEFAULT_SOURCE = payload.data_source
    return {"data_source": _DEFAULT_SOURCE}


@app.get("/growth")
def demo_growth():
    # Prefer precomputed forecast, then census-based, then processed-scaled, then synthetic
    try:
        items = forecast_from_processed()
        if items:
            return {"items": items}
    except Exception:
        pass
    try:
        items = growth_from_census()
        if items:
            return {"items": items}
    except Exception:
        pass
    try:
        items = predict_from_processed()
        if items:
            return {"items": items}
    except Exception:
        pass
    items = predict_growth()
    return {"items": items}


@app.get("/energy")
def demo_energy():
    try:
        items = energy_profile_from_processed()
        if items:
            return {"items": items}
    except Exception:
        pass
    items = energy_profile()
    return {"items": items}


@app.get("/traffic")
def demo_traffic():
    try:
        items = traffic_profile_from_processed()
        if items:
            return {"items": items}
    except Exception:
        pass
    items = traffic_profile()
    return {"items": items}


# Redirect root to dashboard so primary URL works on Render
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/dash/")


# Mount Dash app under /dash
_dash_app = create_dash_app(requests_pathname_prefix="/dash/")
# a2wsgi.WSGIMiddleware is a valid ASGI app; ignore type to satisfy mypy's signature expectations
app.mount("/dash", WSGIMiddleware(_dash_app.server))  # type: ignore[arg-type]


# Optional summaries
@app.get("/energy/summary")
def energy_summary():
    try:
        import pandas as pd
        from src.pipeline import config as _cfg

        f = _cfg.PROCESSED_DIR / "energy_features.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        items = [
            {
                "area_name": "Nairobi",
                "sector": str(r["sector"]),
                "demand_mwh": float(r["demand_mwh"]),
                "pct": float(r.get("pct", 0.0)),
            }
            for _, r in df.iterrows()
        ]
        return {"items": items}
    except Exception:
        return {"items": []}


@app.get("/traffic/summary")
def traffic_summary():
    try:
        import pandas as pd
        from src.pipeline import config as _cfg

        f = _cfg.PROCESSED_DIR / "traffic_features.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        g = df.groupby("hour")["veh_per_hour"].mean().reset_index()
        items = [
            {
                "area_name": "Nairobi",
                "hour": int(r["hour"]),
                "avg_veh_per_hour": float(r["veh_per_hour"]),
            }
            for _, r in g.iterrows()
        ]
        return {"items": items}
    except Exception:
        return {"items": []}
