from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import os
from typing import Optional

# Load .env in local dev so API picks up LOCAL_DATABASE_URL and local paths
try:  # pragma: no cover - optional
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

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


# --- Optional database wiring (enabled via env) ---

def _truthy(val: Optional[str]) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on"}


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and "+psycopg2://" not in url:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

_DB_ENABLED = False
try:
    _want_db = _truthy(os.getenv("USE_DB")) or _truthy(os.getenv("USE_LOCAL_DB")) or bool(os.getenv("DATABASE_URL"))
    _raw_url = ""
    # Prefer LOCAL_DATABASE_URL when explicitly using local DB
    if _truthy(os.getenv("USE_LOCAL_DB")) and os.getenv("LOCAL_DATABASE_URL"):
        _raw_url = os.getenv("LOCAL_DATABASE_URL", "")
    elif os.getenv("DATABASE_URL"):
        _raw_url = os.getenv("DATABASE_URL", "")

    if _want_db and _raw_url:
        _db_url = _normalize_db_url(_raw_url)
        # ensure backend.app.core.db sees the normalized URL
        os.environ["DATABASE_URL"] = _db_url
        from backend.app.core.db import SessionLocal  # type: ignore
        from backend.app.models.tables import UrbanArea, EnergyConsumption, TrafficFlow  # type: ignore
        from sqlalchemy import text  # type: ignore

        _DB_ENABLED = True
except Exception:
    # If imports fail (libs missing, etc.), stay in no-DB mode
    _DB_ENABLED = False


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
    # DB-first when enabled
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                rows = (
                    db.query(
                        EnergyConsumption.area_id,
                        EnergyConsumption.ts,
                        EnergyConsumption.predicted_demand,
                        EnergyConsumption.actual_demand,
                    )
                    .order_by(EnergyConsumption.ts.desc())
                    .limit(50)
                    .all()
                )
                items = [
                    {
                        "area_id": r[0],
                        "ts": r[1].isoformat() if r[1] else None,
                        "predicted": r[2],
                        "actual": r[3],
                    }
                    for r in rows
                ]
                return {"items": items}
        except Exception:
            pass  # fall back below
    # processed/demo fallback
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
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                rows = (
                    db.query(
                        TrafficFlow.area_id,
                        TrafficFlow.ts,
                        TrafficFlow.predicted_volume,
                        TrafficFlow.actual_volume,
                        TrafficFlow.congestion_level,
                    )
                    .order_by(TrafficFlow.ts.desc())
                    .limit(50)
                    .all()
                )
                items = [
                    {
                        "area_id": r[0],
                        "ts": r[1].isoformat() if r[1] else None,
                        "predicted_volume": r[2],
                        "actual_volume": r[3],
                        "congestion": r[4],
                    }
                    for r in rows
                ]
                return {"items": items}
        except Exception:
            pass
    # processed/demo fallback
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
    # DB-first when enabled
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                rows = (
                    db.query(
                        UrbanArea.area_id,
                        UrbanArea.name,
                        text("AVG(energy_consumption.predicted_demand) as predicted"),
                        text("AVG(energy_consumption.actual_demand) as actual"),
                    )
                    .join(EnergyConsumption, EnergyConsumption.area_id == UrbanArea.area_id)
                    .group_by(UrbanArea.area_id, UrbanArea.name)
                    .order_by(UrbanArea.area_id)
                    .all()
                )
                items = [
                    {
                        "area_id": r[0],
                        "area_name": r[1],
                        "predicted": float(r[2]) if r[2] is not None else None,
                        "actual": float(r[3]) if r[3] is not None else None,
                    }
                    for r in rows
                ]
                return {"items": items}
        except Exception:
            pass
    # processed/demo fallback
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
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                rows = (
                    db.query(
                        UrbanArea.area_id,
                        UrbanArea.name,
                        text("AVG(traffic_flow.predicted_volume) as predicted"),
                        text("AVG(traffic_flow.actual_volume) as actual"),
                    )
                    .join(TrafficFlow, TrafficFlow.area_id == UrbanArea.area_id)
                    .group_by(UrbanArea.area_id, UrbanArea.name)
                    .order_by(UrbanArea.area_id)
                    .all()
                )
                items = [
                    {
                        "area_id": r[0],
                        "area_name": r[1],
                        "predicted_volume": int(r[2]) if r[2] is not None else None,
                        "actual_volume": int(r[3]) if r[3] is not None else None,
                    }
                    for r in rows
                ]
                return {"items": items}
        except Exception:
            pass
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


# Optional: expose areas when DB is enabled
@app.get("/areas")
def list_areas():
    if not _DB_ENABLED:
        return {"items": []}
    try:
        with SessionLocal() as db:  # type: ignore[name-defined]
            rows = (
                db.query(UrbanArea.area_id, UrbanArea.name)
                .order_by(UrbanArea.area_id)
                .limit(100)
                .all()
            )
            return {"items": [{"area_id": r[0], "name": r[1]} for r in rows]}
    except Exception as e:
        return {"items": [], "detail": str(e)}
