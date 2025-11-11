from fastapi import FastAPI
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from a2wsgi import WSGIMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from pydantic import BaseModel
import os
from typing import Optional
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
from src.webapp.app import create_dash_app
from src.backend.advisory import generate_insights_from_scope
from src.backend.advisory.hf_client import HFTextGenerator

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
                    .join(
                        EnergyConsumption,
                        EnergyConsumption.area_id == UrbanArea.area_id,
                    )
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
                # Try huggingface_hub Chat Completions first
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
                        raise AttributeError("chat.completions.create not available")
                except Exception:
                    # Raw HTTP to router as fallback
                    token = (
                        os.getenv("HUGGINGFACE_API_KEY")
                        or os.getenv("HF_API_TOKEN")
                        or os.getenv("HUGGINGFACEHUB_API_TOKEN")
                        or os.getenv("HF_API_KEY")
                    )
                    if token:
                        r = requests.post(
                            "https://router.huggingface.co/v1/chat/completions",
                            headers={"Authorization": f"Bearer {token}"},
                            json={
                                "model": gen.model,
                                "messages": [{"role": "user", "content": "ping"}],
                                "max_tokens": 4,
                            },
                            timeout=gen.timeout,
                        )
                        r.raise_for_status()
                        info["probe_ok"] = True
                        info["task_used"] = "chat-completions"
                    else:
                        raise RuntimeError("No HF token available for probe")
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
def advisory(scope: str, zone_id: Optional[str] = Query(None)):
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

    res = generate_insights_from_scope(scope_l, bundles)
    return {
        "scope": scope_l,
        "insights": res.get("text", ""),
        "model": res.get("model"),
        "cached": res.get("cached", False),
        "generated_at": res.get("generated_at"),
        "fallback": res.get("fallback", False),
    }


@app.get("/advisory_batch")
def advisory_batch(scopes: str = Query("dashboard,growth,energy,traffic")):
    """
    Batch insights for multiple scopes in one call. Example: /advisory_batch?scopes=energy,traffic
    """
    wanted = [s.strip().lower() for s in (scopes or "").split(",") if s.strip()]
    valid = {"dashboard", "growth", "energy", "traffic"}
    scopes_list = [s for s in wanted if s in valid] or ["dashboard"]

    # Preload bundles once and reuse
    try:
        g = (demo_growth() or {}).get("items", [])
        e = (demo_energy() or {}).get("items", [])
        t = (demo_traffic() or {}).get("items", [])
    except Exception:
        g, e, t = [], [], []

    from concurrent.futures import ThreadPoolExecutor

    def _for_scope(s: str):
        b = {}
        if s in ("dashboard", "growth"):
            b["growth"] = g
        if s in ("dashboard", "energy"):
            b["energy"] = e
        if s in ("dashboard", "traffic"):
            b["traffic"] = t
        return s, generate_insights_from_scope(s, b)

    results = {}
    with ThreadPoolExecutor(max_workers=min(3, len(scopes_list))) as ex:
        for s, res in ex.map(_for_scope, scopes_list):
            results[s] = {
                "insights": res.get("text", ""),
                "model": res.get("model"),
                "cached": res.get("cached", False),
                "generated_at": res.get("generated_at"),
                "fallback": res.get("fallback", False),
            }
    return {"results": results}
