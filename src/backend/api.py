from fastapi import FastAPI
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import os
from typing import Optional, Any, Dict, Literal
import requests

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
from src.backend.advisory import generate_insights_from_scope
from src.backend.advisory.hf_client import HFTextGenerator
from src.backend.simulation import (
    simulate_growth,
    simulate_energy,
    simulate_traffic,
)
from src.backend.ts_forecast import TimeSeriesForecaster

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


class SimulationInputPayload(BaseModel):
    """Payload for creating simulation input records.

    This captures the SIMULATE mode configuration but does not implement
    authentication or file upload logic yet.
    """

    area_id: int
    name: str
    user_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None


class SimulationRunPayload(BaseModel):
    """Payload for running a SIMULATE mode scenario over existing outputs.

    This endpoint uses only free, deterministic helpers on top of the
    existing growth/energy/traffic models. It does not depend on any
    paid APIs or closed-source models.
    """

    module: Literal["growth", "energy", "traffic", "all"] = "all"
    area_id: Optional[int] = None
    name: Optional[str] = None
    user_id: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None


class TSPoint(BaseModel):
    t: float
    value: float


class TimeSeriesForecastPayload(BaseModel):
    target: Literal["growth", "energy", "traffic"]
    series: list[TSPoint]
    horizon: int = 6
    use_model: bool = False


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
    _want_db = (
        _truthy(os.getenv("USE_DB"))
        or _truthy(os.getenv("USE_LOCAL_DB"))
        or bool(os.getenv("DATABASE_URL"))
    )
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
        from src.backend.db.session import SessionLocal  # type: ignore
        from src.backend.db.tables import (
            UrbanArea,
            Area,
            ProcessedData,
            SimulationInput,
            EnergyConsumption,
            TrafficFlow,
        )  # type: ignore
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
def demo_energy(area_id: Optional[int] = Query(None)):
    """Return recent energy series.

    When the database is enabled, this filters by `area_id` when provided and
    otherwise returns the latest records across areas. When the database is
    disabled or no rows are found, it falls back to processed artifacts, then
    to a deterministic synthetic profile.
    """

    # DB-first when enabled
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(
                    EnergyConsumption.area_id,
                    EnergyConsumption.ts,
                    EnergyConsumption.predicted_demand,
                    EnergyConsumption.actual_demand,
                )
                if area_id is not None:
                    q = q.filter(EnergyConsumption.area_id == area_id)
                rows = q.order_by(EnergyConsumption.ts.desc()).limit(50).all()
                items = [
                    {
                        "area_id": r[0],
                        "ts": r[1].isoformat() if r[1] else None,
                        "predicted": r[2],
                        "actual": r[3],
                    }
                    for r in rows
                ]
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
            pass
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
def demo_traffic(area_id: Optional[int] = Query(None)):
    """Return recent traffic series.

    When the database is enabled, this filters by `area_id` when provided; when
    disabled, it falls back to processed artifacts and then to a deterministic
    synthetic profile.
    """

    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(
                    TrafficFlow.area_id,
                    TrafficFlow.ts,
                    TrafficFlow.predicted_volume,
                    TrafficFlow.actual_volume,
                    TrafficFlow.congestion_level,
                )
                if area_id is not None:
                    q = q.filter(TrafficFlow.area_id == area_id)
                rows = q.order_by(TrafficFlow.ts.desc()).limit(50).all()
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
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
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


# Root route: redirect to interactive API docs
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/docs")


# Optional summaries
@app.get("/energy/summary")
def energy_summary(area_id: Optional[int] = Query(None)):
    """Return energy summary aggregates.

    When the database is enabled, this aggregates by area and can be filtered
    to a single `area_id`. When the database is disabled, it falls back to a
    city-level processed summary.
    """

    # DB-first when enabled
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(
                    UrbanArea.area_id,
                    UrbanArea.name,
                    text("AVG(energy_consumption.predicted_demand) as predicted"),
                    text("AVG(energy_consumption.actual_demand) as actual"),
                ).join(
                    EnergyConsumption,
                    EnergyConsumption.area_id == UrbanArea.area_id,
                )
                if area_id is not None:
                    q = q.filter(UrbanArea.area_id == area_id)
                rows = (
                    q.group_by(UrbanArea.area_id, UrbanArea.name)
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
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
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
def traffic_summary(area_id: Optional[int] = Query(None)):
    """Return traffic volume summary aggregates.

    When the database is enabled, this aggregates by area and can be filtered
    to a single `area_id`. When the database is disabled, it falls back to a
    city-level processed hourly summary.
    """

    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(
                    UrbanArea.area_id,
                    UrbanArea.name,
                    text("AVG(traffic_flow.predicted_volume) as predicted"),
                    text("AVG(traffic_flow.actual_volume) as actual"),
                ).join(TrafficFlow, TrafficFlow.area_id == UrbanArea.area_id)
                if area_id is not None:
                    q = q.filter(UrbanArea.area_id == area_id)
                rows = (
                    q.group_by(UrbanArea.area_id, UrbanArea.name)
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
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
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


@app.get("/hotspots/areas")
def hotspots_areas(
    admin_unit: Optional[str] = Query(
        None,
        description="Optional exact admin_unit filter (case-insensitive).",
    ),
    zone_id: Optional[str] = Query(
        None,
        description=(
            "Optional zone/area name filter; matched against admin_unit "
            "case-insensitively, with exact-match preferred over partial."
        ),
    ),
):
    """Return area-level hotspot scores from processed artifacts.

    Reads data/<CITY>/processed/hotspots_areas.csv if present. This file is
    produced by `src.pipeline.preprocess.preprocess_hotspots` and is fully
    deterministic and model-free. The frontend can join the returned
    admin_unit scores with a GeoJSON of wards/neighborhoods to render maps.

    When `admin_unit` or `zone_id` are provided, results are filtered by the
    admin_unit column (case-insensitive), preferring exact matches and
    falling back to substring matches for `zone_id`.
    """

    try:
        import pandas as pd
        from src.pipeline import config as _cfg

        f = _cfg.PROCESSED_DIR / "hotspots_areas.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        if "admin_unit" in df.columns:
            if admin_unit:
                target = admin_unit.strip().lower()
                mask = df["admin_unit"].str.lower() == target
                df = df[mask]
            elif zone_id:
                target = zone_id.strip().lower()
                col = df["admin_unit"].str.lower()
                exact = col == target
                if exact.any():
                    df = df[exact]
                else:
                    partial = col.str.contains(target)
                    if partial.any():
                        df = df[partial]
        items = df.to_dict(orient="records")
        return {"items": items}
    except Exception as e:
        return {"items": [], "detail": str(e)}


@app.get("/hotspots/areas/forecast")
def hotspots_areas_forecast(
    year: Optional[int] = Query(None),
    admin_unit: Optional[str] = Query(
        None,
        description="Optional exact admin_unit filter (case-insensitive).",
    ),
    zone_id: Optional[str] = Query(
        None,
        description=(
            "Optional zone/area name filter; matched against admin_unit "
            "case-insensitively, with exact-match preferred over partial."
        ),
    ),
):
    """Return multi-year area-level hotspot forecasts.

    Reads data/<CITY>/processed/hotspots_areas_forecast.csv if present and
    optionally filters by `year` and admin_unit/zone_id query parameters. This
    file is produced by `preprocess_hotspots_forecast` and remains deterministic
    and model-free.
    """

    try:
        import pandas as pd
        from src.pipeline import config as _cfg

        f = _cfg.PROCESSED_DIR / "hotspots_areas_forecast.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        if year is not None and "year" in df.columns:
            df = df[df["year"] == year]
        if "admin_unit" in df.columns:
            if admin_unit:
                target = admin_unit.strip().lower()
                mask = df["admin_unit"].str.lower() == target
                df = df[mask]
            elif zone_id:
                target = zone_id.strip().lower()
                col = df["admin_unit"].str.lower()
                exact = col == target
                if exact.any():
                    df = df[exact]
                else:
                    partial = col.str.contains(target)
                    if partial.any():
                        df = df[partial]
        items = df.to_dict(orient="records")
        return {"items": items}
    except Exception as e:
        return {"items": [], "detail": str(e)}


# Optional: expose areas when DB is enabled, with a file-based fallback
@app.get("/areas")
def list_areas():
    """List known analysis areas.

    When the database is enabled, this prefers the `areas` table and falls
    back to the legacy `urban_areas` table. When the database is disabled,
    it returns a synthetic single area based on DATA_CITY.
    """

    # No DB: synthetic single-area view derived from pipeline config
    if not _DB_ENABLED:
        try:
            from src.pipeline import config as _cfg  # type: ignore

            city = getattr(_cfg, "DATA_CITY", None) or os.getenv("DATA_CITY", "Nairobi")
        except Exception:
            city = os.getenv("DATA_CITY", "Nairobi")
        return {
            "items": [
                {
                    "id": 1,
                    "area_id": 1,
                    "name": city,
                    "area_type": "city",
                }
            ]
        }

    # DB-enabled: prefer the new Area table, fall back to UrbanArea when needed
    try:
        with SessionLocal() as db:  # type: ignore[name-defined]
            try:
                rows = (
                    db.query(Area.id, Area.name, Area.area_type)
                    .order_by(Area.id)
                    .limit(100)
                    .all()
                )
                if rows:
                    return {
                        "items": [
                            {
                                "id": r[0],
                                "area_id": r[0],
                                "name": r[1],
                                "area_type": r[2],
                            }
                            for r in rows
                        ]
                    }
            except Exception:
                # If the new table is not present or query fails, fall back below
                pass

            rows = (
                db.query(UrbanArea.area_id, UrbanArea.name)
                .order_by(UrbanArea.area_id)
                .limit(100)
                .all()
            )
            return {
                "items": [
                    {
                        "id": r[0],
                        "area_id": r[0],
                        "name": r[1],
                        "area_type": "unknown",
                    }
                    for r in rows
                ]
            }
    except Exception as e:
        return {"items": [], "detail": str(e)}


@app.get("/processed_data")
def list_processed_data(
    area_id: Optional[int] = Query(None),
    mode: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """List processed data records (DB-backed only).

    This endpoint is a thin metadata view over the processed_data table and is
    intended for driving UI selection (e.g., which processed artifacts exist
    for a given area/mode/category).
    """

    if not _DB_ENABLED:
        return {"items": []}

    try:
        with SessionLocal() as db:  # type: ignore[name-defined]
            q = db.query(ProcessedData)
            if area_id is not None:
                q = q.filter(ProcessedData.area_id == area_id)
            if mode:
                q = q.filter(ProcessedData.mode == mode)
            if category:
                q = q.filter(ProcessedData.category == category)

            rows = q.order_by(ProcessedData.id.desc()).limit(limit).all()
            items = [
                {
                    "id": r.id,
                    "area_id": r.area_id,
                    "mode": r.mode,
                    "category": r.category,
                    "version": r.version,
                    "storage_path": r.storage_path,
                    "meta": r.meta,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
            return {"items": items}
    except Exception as e:  # pragma: no cover - defensive
        return {"items": [], "detail": str(e)}


@app.get("/simulation_inputs")
def list_simulation_inputs(
    area_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """List stored simulation scenarios (DB-backed only).

    This is a light metadata view intended for the SIMULATE mode UI.
    """

    if not _DB_ENABLED:
        return {"items": []}

    try:
        with SessionLocal() as db:  # type: ignore[name-defined]
            q = db.query(SimulationInput)
            if area_id is not None:
                q = q.filter(SimulationInput.area_id == area_id)
            rows = q.order_by(SimulationInput.id.desc()).limit(limit).all()
            items = [
                {
                    "id": r.id,
                    "area_id": r.area_id,
                    "user_id": r.user_id,
                    "name": r.name,
                    "parameters": r.parameters,
                    "file_path": r.file_path,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
            return {"items": items}
    except Exception as e:  # pragma: no cover - defensive
        return {"items": [], "detail": str(e)}


@app.post("/simulation_inputs")
def create_simulation_input(payload: SimulationInputPayload):
    """Create a simulation input record.

    This stores SIMULATE mode configuration for later reuse. Authentication and
    file upload handling are intentionally out of scope for now.
    """

    if not _DB_ENABLED:
        return JSONResponse(
            {
                "detail": "Simulation storage requires the database; set USE_DB/USE_LOCAL_DB and DATABASE_URL to enable.",
            },
            status_code=503,
        )

    try:
        from datetime import datetime, timezone

        with SessionLocal() as db:  # type: ignore[name-defined]
            now = datetime.now(timezone.utc)
            obj = SimulationInput(
                area_id=payload.area_id,
                user_id=payload.user_id,
                name=payload.name,
                parameters=payload.parameters,
                file_path=payload.file_path,
                created_at=now,
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)

            return {
                "id": obj.id,
                "area_id": obj.area_id,
                "user_id": obj.user_id,
                "name": obj.name,
                "parameters": obj.parameters,
                "file_path": obj.file_path,
                "created_at": obj.created_at.isoformat() if obj.created_at else None,
            }
    except Exception as e:  # pragma: no cover - defensive
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.post("/simulate/run")
def run_simulation(payload: SimulationRunPayload):
    """Run a SIMULATE scenario for growth/energy/traffic.

    This endpoint:
    - Optionally persists a SimulationInput record when the DB is enabled.
    - Uses current REAL-mode outputs as the base (DB → processed → synthetic).
    - Applies simple, deterministic adjustments via simulation helpers.
    """

    params = payload.parameters or {}

    # Persist simulation input if DB is enabled
    sim_id = None
    if _DB_ENABLED:
        try:
            from datetime import datetime, timezone

            with SessionLocal() as db:  # type: ignore[name-defined]
                now = datetime.now(timezone.utc)
                obj = SimulationInput(
                    area_id=payload.area_id or 1,
                    user_id=payload.user_id,
                    name=payload.name or "Simulation",
                    parameters=params,
                    file_path=payload.file_path,
                    created_at=now,
                )
                db.add(obj)
                db.commit()
                db.refresh(obj)
                sim_id = obj.id
        except Exception:
            # If the database is misconfigured or tables are missing, degrade
            # gracefully and still return simulated results without persistence.
            sim_id = None

    # Base data from existing endpoints (REAL-mode behaviour)
    growth_base = []
    energy_base = []
    traffic_base = []
    try:
        if payload.module in ("growth", "all"):
            growth_base = (demo_growth() or {}).get("items", [])
        if payload.module in ("energy", "all"):
            energy_base = (demo_energy() or {}).get("items", [])
        if payload.module in ("traffic", "all"):
            traffic_base = (demo_traffic() or {}).get("items", [])
    except Exception:
        # Fall back to empty lists; helpers will return [] in that case
        growth_base, energy_base, traffic_base = [], [], []

    results: Dict[str, Any] = {}

    if payload.module in ("growth", "all"):
        results["growth"] = simulate_growth(growth_base, params=params)
    if payload.module in ("energy", "all"):
        results["energy"] = simulate_energy(energy_base, params=params)
    if payload.module in ("traffic", "all"):
        results["traffic"] = simulate_traffic(traffic_base, params=params)

    return {
        "simulation_id": sim_id,
        "module": payload.module,
        "results": results,
    }


@app.post("/ts/forecast")
def ts_forecast(payload: TimeSeriesForecastPayload):
    """Generic time-series forecast endpoint.

    - `target` selects the logical module (growth, energy, traffic).
    - `series` is a list of {"t": number, "value": float}.
    - When `use_model` is True and an HF token is configured, this will attempt
      to call a free Hugging Face model via TimeSeriesForecaster (which uses
      HFTextGenerator under the hood). If no model is configured or the call
      fails, it falls back to a deterministic extrapolation.
    """

    series = [{"t": p.t, "value": p.value} for p in payload.series]
    forecaster = TimeSeriesForecaster(target=payload.target)
    items = forecaster.forecast(
        series=series,
        horizon=payload.horizon,
        use_model=payload.use_model,
    )
    return {
        "target": payload.target,
        "items": items,
        "used_model": bool(payload.use_model and os.getenv("HF_API_KEY")),
    }


# --- AI advisory (Hugging Face) ---
@app.get("/advisory/status")
def advisory_status(probe: bool = Query(False)):
    token_present = bool(
        os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HF_API_TOKEN")
        or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        or os.getenv("HF_API_KEY")
    )
    gen = HFTextGenerator()
    info = {
        "token_present": token_present,
        "model": gen.model,
        "timeout": gen.timeout,
        "client": bool(getattr(gen, "_client", None) is not None),
        "probe_ok": None,
        "task_used": None,
        "error": None,
    }
    if probe:
        try:
            # Prefer Chat Completions for instruct models
            if gen._is_conversational(gen.model):  # type: ignore[attr-defined]
                # If explicitly forced, probe conversational task directly (Inference API)
                if (
                    os.getenv("HF_FORCE_TASK", "").strip(" '\"\t\n\r").lower()
                    == "conversational"
                ):
                    token = getattr(gen, "_token", None)
                    if not token:
                        raise RuntimeError("No HF token available for probe")
                    base_m = gen.model.split(":", 1)[0]
                    r = requests.post(
                        f"https://api-inference.huggingface.co/models/{base_m}",
                        headers={"Authorization": f"Bearer {token}"},
                        json={
                            "inputs": {
                                "past_user_inputs": [],
                                "generated_responses": [],
                                "text": "ping",
                            },
                            "parameters": {"max_new_tokens": 4},
                        },
                        timeout=gen.timeout,
                    )
                    r.raise_for_status()
                    info["probe_ok"] = True
                    info["task_used"] = "conversational"
                else:
                    # Try huggingface_hub Chat Completions first if available (uses HF config/token), then router
                    try:
                        chat = getattr(gen._client, "chat", None)
                        comps = getattr(chat, "completions", None)
                        create = getattr(comps, "create", None)
                        if callable(create):
                            create(
                                model=gen.model,
                                messages=[{"role": "user", "content": "ping"}],
                                max_tokens=4,
                            )
                            info["probe_ok"] = True
                            info["task_used"] = "chat-completions"
                        else:
                            raise AttributeError(
                                "chat.completions.create not available"
                            )
                    except Exception:
                        token = getattr(gen, "_token", None)
                        if not token:
                            raise RuntimeError("No HF token available for probe")
                        m = gen.model.replace(
                            "Meta-Llama-3.1-8B-Instruct", "Llama-3.1-8B-Instruct"
                        )
                        if ":" in m:
                            m = m.split(":", 1)[0]
                        r = requests.post(
                            "https://router.huggingface.co/v1/chat/completions",
                            headers={"Authorization": f"Bearer {token}"},
                            json={
                                "model": m,
                                "messages": [{"role": "user", "content": "ping"}],
                                "max_tokens": 4,
                            },
                            timeout=gen.timeout,
                        )
                        r.raise_for_status()
                        info["probe_ok"] = True
                        info["task_used"] = "chat-completions"
            elif gen._is_text2text(gen.model):  # type: ignore[attr-defined]
                gen._client.post(  # type: ignore[attr-defined]
                    json={"inputs": "ping", "parameters": {"max_new_tokens": 4}},
                    model=gen.model,
                    task="text2text-generation",
                )
                info["probe_ok"] = True
                info["task_used"] = "text2text-generation"
            else:
                gen._client.text_generation(  # type: ignore[attr-defined]
                    "ping", model=gen.model, max_new_tokens=4
                )
                info["probe_ok"] = True
                info["task_used"] = "text-generation"
        except Exception as e:  # pragma: no cover
            info["probe_ok"] = False
            info["error"] = str(e)
    return info


@app.get("/advisory/{scope}")
def advisory(
    scope: str,
    zone_id: Optional[str] = Query(None),
    scenario: Optional[str] = Query(
        None,
        description=(
            "Optional scenario label (e.g. 'baseline', 'remote_work', 'demand_response') "
            "used to tailor advisory text to the current SIMULATE configuration."
        ),
    ),
):
    """
    Return markdown insights for a given scope: dashboard|growth|energy|traffic.
    Uses recent data from existing endpoints (DB → processed → synthetic).
    """
    scope_l = (scope or "dashboard").lower()
    # Preload bundles once
    bundles = {}
    try:
        g = (demo_growth() or {}).get("items", [])
        e = (demo_energy() or {}).get("items", [])
        t = (demo_traffic() or {}).get("items", [])
        if scope_l in ("dashboard", "growth"):
            bundles["growth"] = g
        if scope_l in ("dashboard", "energy"):
            bundles["energy"] = e
        if scope_l in ("dashboard", "traffic"):
            bundles["traffic"] = t
    except Exception:
        bundles.setdefault("growth", [])
        bundles.setdefault("energy", [])
        bundles.setdefault("traffic", [])

    res = generate_insights_from_scope(scope_l, bundles, zone_id=zone_id, scenario=scenario)
    return {
        "scope": scope_l,
        "zone_id": zone_id,
        "scenario": scenario,
        "insights": res.get("text", ""),
        "model": res.get("model"),
        "cached": res.get("cached", False),
        "generated_at": res.get("generated_at"),
        "fallback": res.get("fallback", False),
    }


@app.get("/advisory_batch")
def advisory_batch(
    scopes: str = Query("dashboard,growth,energy,traffic"),
    zone_ids: Optional[str] = Query(
        None,
        description=(
            "Optional comma-separated list of zone_ids to align with scopes. "
            "If a single value is provided, it is used for all scopes."
        ),
    ),
):
    """Batch insights for multiple scopes in one call.

    Example:
        /advisory_batch?scopes=energy,traffic&zone_ids=ward-1,ward-2

    If `zone_ids` contains a single value, it will be used for all scopes.
    """
    wanted = [s.strip().lower() for s in (scopes or "").split(",") if s.strip()]
    valid = {"dashboard", "growth", "energy", "traffic"}
    scopes_list = [s for s in wanted if s in valid] or ["dashboard"]

    # Align zone_ids (if provided) with scopes_list
    zone_id_list: list[Optional[str]] = [None] * len(scopes_list)
    if zone_ids is not None:
        raw = [z.strip() for z in zone_ids.split(",")]
        # Single zone_id: reuse for all scopes
        if len(raw) == 1:
            zid = raw[0] or None
            zone_id_list = [zid] * len(scopes_list)
        else:
            for idx, s in enumerate(scopes_list):
                if idx < len(raw) and raw[idx]:
                    zone_id_list[idx] = raw[idx]

    # Preload bundles once and reuse
    try:
        g = (demo_growth() or {}).get("items", [])
        e = (demo_energy() or {}).get("items", [])
        t = (demo_traffic() or {}).get("items", [])
    except Exception:
        g, e, t = [], [], []

    from concurrent.futures import ThreadPoolExecutor

    def _for_scope(args: tuple[str, Optional[str]]):
        s, zid = args
        b = {}
        if s in ("dashboard", "growth"):
            b["growth"] = g
        if s in ("dashboard", "energy"):
            b["energy"] = e
        if s in ("dashboard", "traffic"):
            b["traffic"] = t
        res = generate_insights_from_scope(s, b, zone_id=zid)
        return s, zid, res

    results: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=min(3, len(scopes_list))) as ex:
        for s, zid, res in ex.map(_for_scope, zip(scopes_list, zone_id_list)):
            results[s] = {
                "zone_id": zid,
                "insights": res.get("text", ""),
                "model": res.get("model"),
                "cached": res.get("cached", False),
                "generated_at": res.get("generated_at"),
                "fallback": res.get("fallback", False),
            }
    return {"results": results}
