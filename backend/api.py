# @author: David Lameck

"""FastAPI application for the Smart Urban Simulation and Prediction System (SUSPS).

Exposes REST endpoints for growth, energy, traffic, environment, hotspots,
simulation, generic time-series forecasting, exports, advisory, and an
optional authentication and metadata layer backed by PostgreSQL.
"""

from fastapi import FastAPI
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
import os
from typing import Optional, Any, Dict, Literal, List
import io
import csv
import zipfile
from datetime import datetime, timezone
from datetime import timedelta
import hashlib
import secrets
import logging
import requests
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from pathlib import Path
import json

# Load .env in local development so the API can pick up LOCAL_DATABASE_URL and local paths.
try:  # pragma: no cover - optional
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from models.growth import (
    predict_growth,
    predict_from_processed,
    growth_from_census,
    forecast_from_processed,
)
from models.energy import (
    daily_profile as energy_profile,
    daily_profile_from_processed as energy_profile_from_processed,
)
from models.traffic import (
    daily_profile as traffic_profile,
    daily_profile_from_processed as traffic_profile_from_processed,
)
from pipeline.ingest import fetch_traffic as ingest_fetch_traffic
from advisory.engine import (
    generate_insights_from_scope,
    generate_insights_from_snapshot,
)
from advisory.hf_client import HFTextGenerator
from simulation import (
    simulate_growth,
    simulate_energy,
    simulate_traffic,
)
from ts_forecast import TimeSeriesForecaster

logger = logging.getLogger(__name__)

app = FastAPI(title="SUSPS Backend", version="0.1.0")

_TRAFFIC_LIVE_CACHE: Dict[str, Any] = {"at": None, "payload": None}
_TRAFFIC_LIVE_TTL_SECONDS = int(os.getenv("TRAFFIC_LIVE_TTL_SECONDS", "300"))

_TRAFFIC_LIVE_POINTS_CACHE: Dict[str, Any] = {"at": None, "payload": None}
_TRAFFIC_LIVE_POINTS_TTL_SECONDS = int(
    os.getenv("TRAFFIC_LIVE_POINTS_TTL_SECONDS", "30")
)

_TRAFFIC_SNAPSHOTS_DIR = os.getenv("TRAFFIC_SNAPSHOTS_DIR", "traffic_live_snapshots")


def _city_coords() -> tuple[float, float]:
    try:
        lat = float(os.getenv("CITY_LAT", "-1.286389"))
        lon = float(os.getenv("CITY_LON", "36.817223"))
    except Exception:
        lat, lon = -1.286389, 36.817223
    return lat, lon


def _get_tomtom_live_points_payload(force_refresh: bool = False) -> Dict[str, Any]:
    provider = (os.getenv("TRAFFIC_PROVIDER", "tomtom") or "tomtom").lower()
    api_key = os.getenv("TOMTOM_API_KEY")
    if provider != "tomtom" or not api_key:
        return {"points": [], "meta": {"source": "unavailable"}}

    now = datetime.now(timezone.utc)
    cached_at = _TRAFFIC_LIVE_POINTS_CACHE.get("at")
    if not force_refresh and (
        isinstance(cached_at, datetime)
        and (now - cached_at).total_seconds() < _TRAFFIC_LIVE_POINTS_TTL_SECONDS
    ):
        cached_payload = _TRAFFIC_LIVE_POINTS_CACHE.get("payload")
        if isinstance(cached_payload, dict) and cached_payload.get("points"):
            meta = (
                cached_payload.get("meta")
                if isinstance(cached_payload.get("meta"), dict)
                else {}
            )
            age_sec = None
            try:
                if isinstance(cached_at, datetime):
                    age_sec = max(0.0, float((now - cached_at).total_seconds()))
            except Exception:
                age_sec = None
            return {
                **cached_payload,
                "meta": {
                    **(meta or {}),
                    "cached": True,
                    "cache_age_seconds": age_sec,
                    "ttl_seconds": float(_TRAFFIC_LIVE_POINTS_TTL_SECONDS),
                    "request_id": secrets.token_hex(4),
                    "served_at": now.isoformat(),
                },
            }

    lat, lon = _city_coords()
    try:
        zoom = int(os.getenv("TRAFFIC_LIVE_ZOOM", "14"))
    except Exception:
        zoom = 14
    try:
        grid_n = int(os.getenv("TRAFFIC_LIVE_GRID_N", "3"))
    except Exception:
        grid_n = 3
    grid_n = max(1, min(grid_n, 7))
    try:
        radius_deg = float(os.getenv("TRAFFIC_LIVE_RADIUS_DEG", "0.05"))
    except Exception:
        radius_deg = 0.05
    radius_deg = max(0.001, min(radius_deg, 0.25))
    try:
        jitter_deg = float(os.getenv("TRAFFIC_LIVE_JITTER_DEG", "0.003"))
    except Exception:
        jitter_deg = 0.003
    jitter_deg = max(0.0, min(jitter_deg, 0.05))

    def _rand_unit() -> float:
        try:
            return secrets.randbits(32) / float(2**32)
        except Exception:
            return 0.5

    def _jitter() -> float:
        return (2.0 * _rand_unit() - 1.0) * jitter_deg

    try:
        max_points = int(os.getenv("TRAFFIC_LIVE_MAX_POINTS", str(grid_n * grid_n)))
    except Exception:
        max_points = int(grid_n * grid_n)
    max_points = max(1, min(max_points, 49))

    half = (grid_n - 1) / 2.0
    offsets: List[tuple[float, float]] = []
    for i in range(grid_n):
        for j in range(grid_n):
            if grid_n <= 1 or half == 0:
                offsets.append((0.0, 0.0))
            else:
                offsets.append(
                    (
                        ((i - half) / half) * radius_deg,
                        ((j - half) / half) * radius_deg,
                    )
                )
    # Randomize sampling order to reduce the chance of repeatedly snapping to the
    # same road segments when only a subset of points succeed.
    offsets = sorted(offsets, key=lambda _: secrets.randbits(32))

    points: List[Dict[str, Any]] = []
    for idx, (base_dlat, base_dlon) in enumerate(offsets[:max_points], start=1):
        plat = lat + base_dlat + _jitter()
        plon = lon + base_dlon + _jitter()
        try:
            r = requests.get(
                f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/{zoom}/json",
                params={"point": f"{plat},{plon}", "key": api_key},
                timeout=10,
            )
            r.raise_for_status()
            js = r.json().get("flowSegmentData", {})
            has_speed = ("currentSpeed" in js) or ("currentSpeedUncapped" in js)
            has_free = "freeFlowSpeed" in js
            if not js or not has_speed or not has_free:
                continue
            cur = float(js.get("currentSpeed", js.get("currentSpeedUncapped", 0.0)))
            free = float(js.get("freeFlowSpeed", 0.0))
            if cur <= 0 or free <= 0:
                continue
            ratio = min(max(free / max(cur, 1.0), 0.5), 2.5)
            try:
                conf = float(js.get("confidence", 0.0))
            except Exception:
                conf = 0.0
            points.append(
                {
                    "id": idx,
                    "lat": plat,
                    "lon": plon,
                    "current_speed": cur,
                    "free_flow_speed": free,
                    "congestion_ratio": ratio,
                    "confidence": conf,
                    "road_closure": bool(js.get("roadClosure", False)),
                }
            )
        except Exception:
            continue

    avg_ratio = None
    avg_cur = None
    avg_free = None
    if points:
        try:
            avg_ratio = sum(float(p["congestion_ratio"]) for p in points) / len(points)
            avg_cur = sum(float(p["current_speed"]) for p in points) / len(points)
            avg_free = sum(float(p["free_flow_speed"]) for p in points) / len(points)
        except Exception:
            avg_ratio = None

    all_free_flow = None
    try:
        if points:
            all_free_flow = all(
                abs(float(p.get("current_speed", 0.0)) - float(p.get("free_flow_speed", 0.0)))
                < 0.01
                for p in points
            )
    except Exception:
        all_free_flow = None

    payload = {
        "points": points,
        "meta": {
            "source": "tomtom_flow",
            "cached": False,
            "generated_at": now.isoformat(),
            "served_at": now.isoformat(),
            "samples_used": int(len(points)),
            "points_requested": int(grid_n * grid_n),
            "points_target": int(min(max_points, grid_n * grid_n)),
            "zoom": int(zoom),
            "center": {"lat": float(lat), "lon": float(lon)},
            "radius_deg": float(radius_deg),
            "grid_n": int(grid_n),
            "jitter_deg": float(jitter_deg),
            "avg_congestion_ratio": avg_ratio,
            "avg_current_speed": avg_cur,
            "avg_free_flow_speed": avg_free,
            "all_points_free_flow": all_free_flow,
            "cache_age_seconds": 0.0,
            "ttl_seconds": float(_TRAFFIC_LIVE_POINTS_TTL_SECONDS),
            "request_id": secrets.token_hex(4),
        },
    }
    _TRAFFIC_LIVE_POINTS_CACHE["at"] = now
    _TRAFFIC_LIVE_POINTS_CACHE["payload"] = payload
    return payload


def _traffic_snapshots_dir() -> Path:
    from pipeline import config as _cfg

    _cfg.ensure_dirs()
    base = getattr(_cfg, "MOBILITY_RAW_DIR", _cfg.RAW_DIR)
    d = Path(base) / _TRAFFIC_SNAPSHOTS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _append_traffic_snapshot(payload: Dict[str, Any]) -> None:
    try:
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if not isinstance(meta, dict):
            return
        if meta.get("source") != "tomtom_flow":
            return
        if not payload.get("points"):
            return

        # Only persist real fetches, not cache-served responses.
        if meta.get("cached") is True:
            return

        now = datetime.now(timezone.utc)
        out = _traffic_snapshots_dir() / f"{now.date().isoformat()}.jsonl"
        record = {
            "ts": now.isoformat(),
            "meta": meta,
        }
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        return


def _yesterday_profile_from_snapshots(target_date) -> Optional[Dict[str, Any]]:
    try:
        src = _traffic_snapshots_dir() / f"{target_date.isoformat()}.jsonl"
        if not src.exists():
            return None

        hourly: Dict[int, List[float]] = {}
        snapshots_used = 0
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                ts_raw = rec.get("ts")
                meta = rec.get("meta") if isinstance(rec.get("meta"), dict) else {}
                ratio = meta.get("avg_congestion_ratio")
                if ts_raw is None or ratio is None:
                    continue
                ts = datetime.fromisoformat(str(ts_raw))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                try:
                    ratio_f = float(ratio)
                except Exception:
                    continue
                h = int(ts.astimezone(timezone.utc).hour)
                hourly.setdefault(h, []).append(ratio_f)
                snapshots_used += 1
            except Exception:
                continue

        if not hourly:
            return None

        hourly_avg: Dict[int, float] = {
            h: (sum(vals) / float(len(vals))) for h, vals in hourly.items() if vals
        }
        daily_avg = sum(hourly_avg.values()) / float(len(hourly_avg))

        base_items = traffic_profile()
        base_by_hour = {
            int(it.get("hour", 0)): int(it.get("volume", 0)) for it in base_items
        }

        items: List[Dict[str, Any]] = []
        for h in range(24):
            base_v = int(base_by_hour.get(h, 0))
            ratio = hourly_avg.get(h, daily_avg)
            scaling_factor = min(max(float(ratio), 0.5), 1.8)
            items.append({"hour": h, "volume": int(round(base_v * scaling_factor))})

        return {
            "items": items,
            "meta": {
                "source": "tomtom_snapshots",
                "day": "yesterday",
                "date": target_date.isoformat(),
                "snapshots_used": snapshots_used,
                "avg_congestion_ratio": float(daily_avg),
            },
        }
    except Exception:
        return None


def _get_live_traffic_payload(force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    provider = (os.getenv("TRAFFIC_PROVIDER", "tomtom") or "tomtom").lower()
    api_key = os.getenv("TOMTOM_API_KEY")
    if provider != "tomtom" or not api_key:
        return None

    now = datetime.now(timezone.utc)
    cached_at = _TRAFFIC_LIVE_CACHE.get("at")
    if not force_refresh and (
        isinstance(cached_at, datetime)
        and (now - cached_at).total_seconds() < _TRAFFIC_LIVE_TTL_SECONDS
    ):
        cached_payload = _TRAFFIC_LIVE_CACHE.get("payload")
        if isinstance(cached_payload, dict) and cached_payload.get("items"):
            try:
                meta = (
                    cached_payload.get("meta")
                    if isinstance(cached_payload.get("meta"), dict)
                    else {}
                )
                return {
                    **cached_payload,
                    "meta": {**meta, "cached": True, "served_at": now.isoformat()},
                }
            except Exception:
                pass
            return cached_payload

    try:
        df = ingest_fetch_traffic()
        if df is None or getattr(df, "empty", True):
            return None
        if "hour" not in df.columns or "veh_per_hour" not in df.columns:
            return None
        g = df.groupby("hour")["veh_per_hour"].mean().reset_index()
        congestion_ratio = None
        avg_current_speed = None
        avg_free_flow_speed = None
        avg_confidence = None
        any_road_closure = None
        samples_used = None
        try:
            if "congestion_ratio" in df.columns:
                congestion_ratio = float(df["congestion_ratio"].astype(float).mean())
            if "current_speed" in df.columns:
                avg_current_speed = float(df["current_speed"].astype(float).mean())
            if "free_flow_speed" in df.columns:
                avg_free_flow_speed = float(df["free_flow_speed"].astype(float).mean())
            if "confidence" in df.columns:
                avg_confidence = float(df["confidence"].astype(float).mean())
            if "road_closure" in df.columns:
                any_road_closure = bool(df["road_closure"].fillna(False).astype(bool).any())
            if "samples_used" in df.columns:
                samples_used = int(float(df["samples_used"].fillna(0).astype(float).max()))
        except Exception:
            congestion_ratio = None
        items: List[Dict[str, Any]] = [
            {"hour": int(r["hour"]), "volume": int(float(r["veh_per_hour"]))}
            for _, r in g.iterrows()
        ]
        if not items:
            return None
        payload = {
            "items": items,
            "meta": {
                "source": "tomtom_live",
                "cached": False,
                "generated_at": now.isoformat(),
                "congestion_ratio": congestion_ratio,
                "avg_current_speed": avg_current_speed,
                "avg_free_flow_speed": avg_free_flow_speed,
                "avg_confidence": avg_confidence,
                "any_road_closure": any_road_closure,
                "samples_used": samples_used,
            },
        }
        _TRAFFIC_LIVE_CACHE["at"] = now
        _TRAFFIC_LIVE_CACHE["payload"] = payload
        return payload
    except Exception as exc:
        logger.warning("Live traffic fetch failed; falling back. %s", exc)
        return None

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
    """Simple health check used by local development and Render deployments."""

    return JSONResponse({"status": "ok", "service": "susps", "version": "0.1.0"})


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


# --------------------------- auth models ---------------------------


class SignupPayload(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str = Field(min_length=6, max_length=128)


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class AuthUser(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    token: str


class AdvisoryPoint(BaseModel):
    x: float
    y: float


class AdvisorySeries(BaseModel):
    metric: Literal["growth", "energy", "traffic"]
    label: str
    points: list[AdvisoryPoint]


class AdvisorySnapshotPayload(BaseModel):
    active_view: Optional[str] = None
    series: list[AdvisorySeries]


# --------------------------- export models ---------------------------


class ExportChartSeries(BaseModel):
    label: str
    points: list[Dict[str, float]]  # {"x": number, "y": number}


class ExportChart(BaseModel):
    title: str
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    series: list[ExportChartSeries]
    # Optional base64-encoded PNG (or data URL) of the chart as rendered in the
    # frontend. When provided, the PDF export embeds this image directly instead
    # of re-drawing the chart from coordinates.
    image_data: Optional[str] = None


class ExportTable(BaseModel):
    title: str
    columns: list[str]
    rows: list[list[Optional[str]]]


class ExportPage(BaseModel):
    """Represents the data needed to export a single logical page.

    The frontend constructs these from the currently visible charts/tables so the
    export reflects exactly what the user sees (REAL vs SIMULATE, presets, etc.).
    """

    page_name: str
    mode: Literal["REAL", "SIMULATE"]
    area_name: str
    area_id: Optional[int] = None
    description: Optional[str] = None
    insights: Optional[str] = None
    tables: List[ExportTable] = []
    charts: List[ExportChart] = []


class ExportPayload(BaseModel):
    """Payload for exporting one or more pages as PDF/CSV/bundle.

    - When `pages` has a single entry and format is CSV, a single CSV file is
      produced.
    - When `pages` has multiple entries, CSV or bundle exports contain one CSV
      file per page inside a ZIP archive, effectively acting as separate
      "sheets" per page.
    """

    export_format: Literal["pdf", "csv", "bundle"]
    pages: List[ExportPage]
    footer_text: Optional[str] = None


# --- Optional database wiring (enabled via env) ---


def _truthy(val: Optional[str]) -> bool:
    return str(val).lower() in {"1", "true", "yes", "on"}


def _normalize_db_url(url: str) -> str:
    """Normalise DATABASE_URL for SQLAlchemy/psycopg2.

    - Upgrade "postgres://" URLs to "postgresql+psycopg2://".
    - Ensure Render-managed Postgres URLs always include "sslmode=require" so
      connections satisfy the platform's TLS requirement even if the env var is
      missing that query parameter.
    """

    # Normalise scheme for SQLAlchemy's psycopg2 dialect
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2://" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # For Render-managed Postgres (hosts ending with render.com), append
    # sslmode=require when it is not already present. This keeps DATABASE_URL
    # values copy-pasted from the dashboard working even if the parameter is
    # omitted or stripped.
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if host.endswith("render.com"):
            qs_items = parse_qsl(parsed.query, keep_blank_values=True)
            has_sslmode = any(k.lower() == "sslmode" for k, _ in qs_items)
            if not has_sslmode:
                qs_items.append(("sslmode", "require"))
                new_query = urlencode(qs_items)
                url = urlunparse(parsed._replace(query=new_query))
    except Exception:
        # If anything goes wrong during parsing, fall back to the best-effort URL
        return url

    return url


# Global feature flag used to toggle database-backed behaviour. Tests may
# monkeypatch this to False to force file-based fallbacks for specific cases.
_DB_ENABLED = False


def _hash_password(password: str) -> str:
    """Hash a password using a per-user salt and SHA-256.

    This is a lightweight helper for the demo authentication flow. It is not
    intended for production use but keeps credentials non-plain-text in the
    database.
    """

    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def _verify_password(password: str, hashed: str) -> bool:
    try:
        salt, digest = hashed.split("$", 1)
    except ValueError:
        return False
    new_digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(new_digest, digest)


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
        from db.session import SessionLocal  # type: ignore
        from db.tables import (
            UrbanArea,
            Area,
            ProcessedData,
            SimulationInput,
            User,
            EnergyConsumption,
            TrafficFlow,
            EnvironmentFeature,
            AirQualityDaily,
            HotspotScore,
        )  # type: ignore
        from sqlalchemy import text  # type: ignore

        _DB_ENABLED = True
except Exception:
    # If imports fail (libs missing, etc.), stay in no-DB mode
    _DB_ENABLED = False


@app.post("/auth/signup")
def auth_signup(payload: SignupPayload):
    """Create a new user account backed by the users table.

    This endpoint requires the database to be enabled. On success it returns a
    minimal AuthUser payload that the frontend can store for client-side
    sessions.
    """

    if not _DB_ENABLED:
        return JSONResponse(
            {
                "detail": "Authentication requires the database; set USE_DB/USE_LOCAL_DB and DATABASE_URL to enable.",
            },
            status_code=503,
        )

    try:
        with SessionLocal() as db:  # type: ignore[name-defined]
            existing = db.query(User).filter(User.email == payload.email).first()
            if existing is not None:
                return JSONResponse(
                    {"detail": "An account with this email already exists."},
                    status_code=400,
                )

            now = datetime.now(timezone.utc)
            user = User(
                email=str(payload.email),
                full_name=payload.full_name,
                hashed_password=_hash_password(payload.password),
                created_at=now,
                updated_at=now,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            token = f"susps-{user.id}-{secrets.token_hex(8)}"
            return AuthUser(
                id=int(user.id),  # type: ignore[arg-type]
                email=user.email,
                full_name=user.full_name,
                token=token,
            )
    except Exception as exc:  # pragma: no cover - defensive
        return JSONResponse({"detail": str(exc)}, status_code=500)


@app.post("/auth/login")
def auth_login(payload: LoginPayload):
    """Authenticate an existing user by email and password.

    Returns a minimal AuthUser payload on success. This demo implementation
    does not issue real JWTs; the frontend treats the token as a client-side
    session marker.
    """

    if not _DB_ENABLED:
        return JSONResponse(
            {
                "detail": "Authentication requires the database; set USE_DB/USE_LOCAL_DB and DATABASE_URL to enable.",
            },
            status_code=503,
        )

    try:
        with SessionLocal() as db:  # type: ignore[name-defined]
            user = db.query(User).filter(User.email == payload.email).first()
            if user is None or not user.hashed_password:
                return JSONResponse(
                    {"detail": "Invalid email or password."}, status_code=401
                )
            if not _verify_password(payload.password, user.hashed_password):
                return JSONResponse(
                    {"detail": "Invalid email or password."}, status_code=401
                )

            token = f"susps-{user.id}-{secrets.token_hex(8)}"
            return AuthUser(
                id=int(user.id),  # type: ignore[arg-type]
                email=user.email,
                full_name=user.full_name,
                token=token,
            )
    except Exception as exc:  # pragma: no cover - defensive
        return JSONResponse({"detail": str(exc)}, status_code=500)


@app.get("/growth")
def demo_growth():
    """Return urban growth forecast with a deterministic fallback chain.

    Prefers precomputed forecast, then census-based, then processed-derived,
    and finally a purely synthetic growth pattern.
    """

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
def demo_traffic(
    area_id: Optional[int] = Query(None),
    fresh: int = Query(0),
    day: str = Query("yesterday"),
):
    """Return recent traffic series.

    When the database is enabled, this filters by `area_id` when provided; when
    disabled, it falls back to processed artifacts and then to a deterministic
    synthetic profile.
    """

    day_key = (day or "yesterday").strip().lower()
    is_yesterday = day_key in {"yesterday", "prev", "previous"}

    # Default behaviour: show the previous day when possible.
    if is_yesterday:
        now = datetime.now(timezone.utc)
        target_date = (now - timedelta(days=1)).date()
        start = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        if _DB_ENABLED:
            try:
                with SessionLocal() as db:  # type: ignore[name-defined]
                    q = db.query(
                        TrafficFlow.ts,
                        TrafficFlow.predicted_volume,
                        TrafficFlow.actual_volume,
                    ).filter(TrafficFlow.ts >= start, TrafficFlow.ts < end)
                    if area_id is not None:
                        q = q.filter(TrafficFlow.area_id == area_id)
                    rows = q.all()
                    by_hour: Dict[int, List[float]] = {}
                    for ts, pred, actual in rows:
                        if ts is None:
                            continue
                        h = int(ts.astimezone(timezone.utc).hour)
                        v = actual if actual is not None else pred
                        if v is None:
                            continue
                        try:
                            by_hour.setdefault(h, []).append(float(v))
                        except Exception:
                            continue

                    if len(by_hour) >= 18:
                        items = []
                        for h in range(24):
                            vals = by_hour.get(h)
                            if vals:
                                items.append({"hour": h, "volume": int(round(sum(vals) / len(vals)))})
                            else:
                                items.append({"hour": h, "volume": 0})
                        return {
                            "items": items,
                            "meta": {
                                "source": "db",
                                "day": "yesterday",
                                "date": target_date.isoformat(),
                            },
                        }
            except Exception:
                pass

        snap_payload = _yesterday_profile_from_snapshots(target_date)
        if snap_payload and snap_payload.get("items"):
            return snap_payload

        live_payload = _get_live_traffic_payload(force_refresh=(fresh == 1))
        if live_payload and live_payload.get("items"):
            meta = (
                live_payload.get("meta")
                if isinstance(live_payload.get("meta"), dict)
                else {}
            )
            return {
                **live_payload,
                "meta": {
                    **(meta or {}),
                    "day": "yesterday",
                    "fallback_day": "today",
                },
            }

        try:
            items = traffic_profile_from_processed()
            if items:
                return {"items": items, "meta": {"source": "processed", "day": "yesterday"}}
        except Exception:
            pass
        items = traffic_profile()
        return {"items": items, "meta": {"source": "synthetic", "day": "yesterday"}}

    live_payload = _get_live_traffic_payload(force_refresh=(fresh == 1))
    if live_payload and live_payload.get("items"):
        meta = live_payload.get("meta") if isinstance(live_payload.get("meta"), dict) else {}
        return {**live_payload, "meta": {**(meta or {}), "day": "today"}}

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
                    return {"items": items, "meta": {"source": "db"}}
        except Exception:
            # Fall through to processed/demo fallback
            pass
    # processed/demo fallback
    try:
        items = traffic_profile_from_processed()
        if items:
            return {"items": items, "meta": {"source": "processed"}}
    except Exception:
        pass
    items = traffic_profile()
    return {"items": items, "meta": {"source": "synthetic"}}


@app.get("/traffic/live")
def traffic_live(fresh: int = Query(0)):
    provider = (os.getenv("TRAFFIC_PROVIDER", "tomtom") or "tomtom").lower()
    api_key = os.getenv("TOMTOM_API_KEY")
    if provider != "tomtom" or not api_key:
        return JSONResponse(
            {
                "detail": "Live traffic requires TRAFFIC_PROVIDER=tomtom and TOMTOM_API_KEY.",
            },
            status_code=503,
        )

    force_refresh = fresh == 1
    payload = _get_tomtom_live_points_payload(force_refresh=force_refresh)
    try:
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        payload["meta"] = {
            **(meta or {}),
            "force_refresh": bool(force_refresh),
            "served_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        pass
    _append_traffic_snapshot(payload)
    return JSONResponse(
        payload,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/")
def root_redirect():
    """Redirect the root path to FastAPI's interactive API documentation."""

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
        from pipeline import config as _cfg

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
        from pipeline import config as _cfg

        base_dir = _cfg.PROCESSED_DIR
        f = base_dir / "traffic_enriched_features.csv"
        if not f.exists():
            f = base_dir / "traffic_features.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        if "hour" not in df.columns or "veh_per_hour" not in df.columns:
            return {"items": []}
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


@app.get("/environment/features")
def environment_features(area_id: Optional[int] = Query(None)) -> Dict[str, Any]:
    """Return monthly environment + air-quality features.

    When the database is enabled, this reads from the environment_features
    table; otherwise it falls back to environment_aq_features.csv.
    """

    # DB-first when enabled
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(EnvironmentFeature)
                if area_id is not None:
                    q = q.filter(EnvironmentFeature.area_id == area_id)
                rows = q.order_by(EnvironmentFeature.month.asc()).all()
                items = [
                    {
                        "id": r.id,
                        "area_id": r.area_id,
                        "month": r.month,
                        "temp_c": r.temp_c,
                        "rain_mm": r.rain_mm,
                        "cooling_deg": r.cooling_deg,
                        "wet_month": r.wet_month,
                        "pm25": r.pm25,
                        "pm10": r.pm10,
                        "o3": r.o3,
                        "pollution_index": r.pollution_index,
                    }
                    for r in rows
                ]
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
            pass

    # Processed CSV fallback
    try:
        import pandas as pd  # type: ignore
        from pipeline import config as _cfg  # type: ignore

        f = _cfg.PROCESSED_DIR / "environment_aq_features.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        items = []
        for _, r in df.iterrows():
            try:
                month = int(r.get("month", 0))
            except Exception:
                continue
            items.append(
                {
                    "area_id": area_id,
                    "month": month,
                    "temp_c": (
                        float(r.get("temp_c")) if "temp_c" in df.columns else None
                    ),
                    "rain_mm": (
                        float(r.get("rain_mm")) if "rain_mm" in df.columns else None
                    ),
                    "cooling_deg": (
                        float(r.get("cooling_deg"))
                        if "cooling_deg" in df.columns
                        else None
                    ),
                    "wet_month": (
                        int(r.get("wet_month")) if "wet_month" in df.columns else None
                    ),
                    "pm25": float(r.get("pm25")) if "pm25" in df.columns else None,
                    "pm10": float(r.get("pm10")) if "pm10" in df.columns else None,
                    "o3": float(r.get("o3")) if "o3" in df.columns else None,
                    "pollution_index": (
                        float(r.get("pollution_index"))
                        if "pollution_index" in df.columns
                        else None
                    ),
                }
            )
        return {"items": items}
    except Exception:
        return {"items": []}


@app.get("/air_quality/daily")
def air_quality_daily(
    area_id: Optional[int] = Query(None),
    limit: int = Query(365, ge=1, le=3650),
) -> Dict[str, Any]:
    """Return daily air-quality aggregates (pm25/pm10/o3).

    When the database is enabled, this reads from the air_quality_daily table;
    otherwise it falls back to air_quality_daily.csv.
    """

    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(AirQualityDaily)
                if area_id is not None:
                    q = q.filter(AirQualityDaily.area_id == area_id)
                rows = q.order_by(AirQualityDaily.date.desc()).limit(limit).all()
                items = [
                    {
                        "id": r.id,
                        "area_id": r.area_id,
                        "date": r.date.isoformat() if r.date else None,
                        "pm25": r.pm25,
                        "pm10": r.pm10,
                        "o3": r.o3,
                    }
                    for r in rows
                ]
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
            pass

    try:
        import pandas as pd  # type: ignore
        from pipeline import config as _cfg  # type: ignore

        f = _cfg.PROCESSED_DIR / "air_quality_daily.csv"
        if not f.exists():
            return {"items": []}
        df = pd.read_csv(f)
        if "date" not in df.columns:
            return {"items": []}
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        df = df.dropna(subset=["date"]).sort_values("date", ascending=False).head(limit)
        items = []
        for _, r in df.iterrows():
            d = r["date"]
            items.append(
                {
                    "area_id": area_id,
                    "date": d.isoformat() if d else None,
                    "pm25": float(r.get("pm25")) if "pm25" in df.columns else None,
                    "pm10": float(r.get("pm10")) if "pm10" in df.columns else None,
                    "o3": float(r.get("o3")) if "o3" in df.columns else None,
                }
            )
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
) -> Dict[str, Any]:
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
        from pipeline import config as _cfg

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
) -> Dict[str, Any]:
    """Return multi-year area-level hotspot forecasts.

    Reads data/<CITY>/processed/hotspots_areas_forecast.csv if present and
    optionally filters by `year` and admin_unit/zone_id query parameters. This
    file is produced by `preprocess_hotspots_forecast` and remains deterministic
    and model-free.
    """

    try:
        import pandas as pd
        from pipeline import config as _cfg

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


@app.get("/hotspots/scores")
def hotspots_scores(
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
) -> Dict[str, Any]:
    """Return hotspot scores from DB or processed CSVs.

    When the database is enabled, this reads from the hotspot_scores table.
    Otherwise it falls back to hotspots_areas.csv and hotspots_areas_forecast.csv
    and returns a unified view.
    """

    def _filter_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not items:
            return []
        if admin_unit:
            target = admin_unit.strip().lower()
            return [
                it for it in items if str(it.get("admin_unit", "")).lower() == target
            ]
        if zone_id:
            target = zone_id.strip().lower()
            names = [str(it.get("admin_unit", "")).lower() for it in items]
            exact = [it for it, name in zip(items, names) if name == target]
            if exact:
                return exact
            partial = [it for it, name in zip(items, names) if target in name]
            if partial:
                return partial
        return items

    # DB-first when enabled
    if _DB_ENABLED:
        try:
            with SessionLocal() as db:  # type: ignore[name-defined]
                q = db.query(HotspotScore)
                if year is not None:
                    q = q.filter(HotspotScore.year == year)
                rows = q.order_by(
                    HotspotScore.admin_unit.asc(), HotspotScore.year.asc()
                ).all()
                items = [
                    {
                        "id": r.id,
                        "area_id": r.area_id,
                        "admin_unit": r.admin_unit,
                        "year": r.year,
                        "population": r.population,
                        "pop_share": r.pop_share,
                        "income_norm": r.income_norm,
                        "employment_score": r.employment_score,
                        "hotspot_score": r.hotspot_score,
                    }
                    for r in rows
                ]
                items = _filter_items(items)
                if items:
                    return {"items": items}
        except Exception:
            # Fall through to processed/demo fallback
            pass

    # CSV fallback
    try:
        import pandas as pd  # type: ignore
        from pipeline import config as _cfg  # type: ignore

        items: list[dict[str, Any]] = []

        base_path = _cfg.PROCESSED_DIR / "hotspots_areas.csv"
        if base_path.exists():
            df = pd.read_csv(base_path)
            for _, r in df.iterrows():
                # Baseline rows have year=None and are only included when no
                # explicit year filter is provided.
                if year is not None:
                    continue
                items.append(
                    {
                        "area_id": None,
                        "admin_unit": r.get("admin_unit"),
                        "year": None,
                        "population": r.get("population"),
                        "pop_share": r.get("pop_share"),
                        "income_norm": r.get("income_norm"),
                        "employment_score": r.get("employment_score"),
                        "hotspot_score": r.get("hotspot_score"),
                    }
                )

        forecast_path = _cfg.PROCESSED_DIR / "hotspots_areas_forecast.csv"
        if forecast_path.exists():
            df = pd.read_csv(forecast_path)
            for _, r in df.iterrows():
                yr = None
                if "year" in df.columns:
                    try:
                        yr = int(r.get("year"))
                    except Exception:
                        yr = None
                if year is not None and yr != year:
                    continue
                items.append(
                    {
                        "area_id": None,
                        "admin_unit": r.get("admin_unit"),
                        "year": yr,
                        "population": r.get("population"),
                        "pop_share": r.get("pop_share"),
                        "income_norm": r.get("income_norm"),
                        "employment_score": r.get("employment_score"),
                        "hotspot_score": r.get("hotspot_score"),
                    }
                )

        items = _filter_items(items)
        return {"items": items}
    except Exception as e:
        return {"items": [], "detail": str(e)}


# Optional: expose areas when DB is enabled, with a file-based fallback
@app.get("/areas")
def list_areas():
    """List known analysis areas.

    When the database is enabled, this prefers the `areas` table and falls
    back to the legacy `urban_areas` table. When the database is disabled or
    no rows are found, it returns a synthetic single area based on the
    configured city (DATA_CITY / CITY env) so that the UI always has at least
    one selectable area such as "Nairobi".
    """

    def _fallback_single_area() -> Dict[str, Any]:
        """Return a synthetic single-area view derived from pipeline config/env.

        This keeps the UI usable even when the database is disabled, empty, or
        misconfigured by exposing a city-level area (e.g. Nairobi) that matches
        the current DATA_CITY/CITY configuration.
        """

        try:
            from pipeline import config as _cfg  # type: ignore

            city = (
                getattr(_cfg, "DATA_CITY", None)
                or os.getenv("DATA_CITY")
                or getattr(_cfg, "_CITY", None)
                or os.getenv("CITY", "Nairobi")
            )
        except Exception:
            city = os.getenv("DATA_CITY") or os.getenv("CITY", "Nairobi")

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

    # No DB: synthetic single-area view
    if not _DB_ENABLED:
        return _fallback_single_area()

    # DB-enabled: prefer the new Area table, fall back to UrbanArea when needed,
    # and finally fall back to a synthetic city area when no rows exist.
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
            if rows:
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

        # DB enabled but no rows in either table: fall back to synthetic city
        return _fallback_single_area()
    except Exception:
        # On any DB error, degrade gracefully to a synthetic city area so the
        # search UI still exposes e.g. "Nairobi" as a selectable area.
        return _fallback_single_area()


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
    - Uses current REAL-mode outputs as the base (DB â†’ processed â†’ synthetic).
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
            energy_base = (demo_energy(area_id=payload.area_id) or {}).get("items", [])
        if payload.module in ("traffic", "all"):
            traffic_base = (
                demo_traffic(area_id=payload.area_id, day="yesterday") or {}
            ).get("items", [])
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

    # For energy, enforce a minimum average relative difference between the
    # forecast and the input series; otherwise fall back to the deterministic
    # forecast.
    if payload.target == "energy" and items:
        base_vals = [float(p.value) for p in payload.series][: len(items)]
        pred_vals = [float(it.get("value", 0.0)) for it in items[: len(base_vals)]]
        diffs: List[float] = []
        for b, v in zip(base_vals, pred_vals):
            denom = abs(b) if abs(b) > 1e-6 else 1.0
            diffs.append(abs(v - b) / denom)
        avg_diff = sum(diffs) / len(diffs) if diffs else 0.0
        if avg_diff < 0.05:
            items = forecaster._forecast_deterministic(
                series=series,
                horizon=payload.horizon,
            )

    return {
        "target": payload.target,
        "items": items,
        "used_model": bool(payload.use_model and os.getenv("HF_API_KEY")),
    }


def _build_csv_for_page(page: ExportPage) -> bytes:
    """Build a single CSV file for the given page.

    The CSV is structured as:
    - Area and page metadata at the top
    - One block per table (with its title)
    - One block per chart, rendered as a wide table (x plus one column per
      series label)
    """

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow([f"Area: {page.area_name}"])
    writer.writerow([f"Page: {page.page_name}"])
    writer.writerow([f"Mode: {page.mode}"])
    writer.writerow([])

    # Tables
    for table in page.tables:
        writer.writerow([f"Table: {table.title}"])
        writer.writerow(table.columns)
        for row in table.rows:
            writer.writerow(["" if v is None else str(v) for v in row])
        writer.writerow([])

    # Charts as tables
    for chart in page.charts:
        writer.writerow([f"Chart: {chart.title}"])
        # Collect all distinct x-values in order of appearance
        x_values: List[Any] = []
        for series in chart.series:
            for pt in series.points:
                x_val = pt.get("x")
                if x_val not in x_values:
                    x_values.append(x_val)
        header = ["x"] + [s.label for s in chart.series]
        writer.writerow(header)
        for x_val in x_values:
            row: List[str] = [str(x_val)]
            for series in chart.series:
                # find point with this x (if any)
                val = None
                for pt in series.points:
                    if pt.get("x") == x_val:
                        val = pt.get("y")
                        break
                row.append("" if val is None else str(val))
            writer.writerow(row)
        writer.writerow([])

    return buf.getvalue().encode("utf-8")


def _build_pdf(payload: ExportPayload) -> bytes:
    """Build a multi-page PDF for the given export payload.

    Uses reportlab if available. If reportlab is not installed, raises
    ImportError with a helpful message.
    """

    try:
        from reportlab.lib.pagesizes import A4  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
        from reportlab.platypus import (  # type: ignore
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table as RLTable,
            TableStyle,
            Image as RLImage,
            ListFlowable,
            ListItem,
        )
        from reportlab.lib import colors  # type: ignore
        from reportlab.graphics.shapes import Drawing, Line as RLLine  # type: ignore
        from reportlab.graphics.shapes import PolyLine as RLPolyLine  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "PDF export requires the 'reportlab' package. Install it with 'pip install reportlab'."
        ) from exc

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=48, bottomMargin=48
    )
    styles = getSampleStyleSheet()
    story: List[Any] = []

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    for idx, page in enumerate(payload.pages):
        if idx > 0:
            story.append(Spacer(1, 18))

        title_text = "Smart Urban Simulation and Prediction System (SUSPS)"
        story.append(Paragraph(title_text, styles["Title"]))
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                f"Page: {page.page_name} | Area: {page.area_name} | Mode: {page.mode}",
                styles["Normal"],
            )
        )
        story.append(Paragraph(f"Exported at: {now}", styles["Normal"]))
        if page.description:
            story.append(Spacer(1, 6))
            story.append(Paragraph(page.description, styles["BodyText"]))
        story.append(Spacer(1, 10))

        # Helper to render AI Analysis & Insights in a clean, markdown-aware layout
        def _render_insights(text: str) -> None:
            """Render advisory markdown-like text into PDF primitives.

            Keeps the PDF output aligned with the frontend renderer by
            normalizing headings/lists and stripping redundant boilerplate.
            """

            import re

            if not text or not text.strip():
                return

            # Normalise newlines and gently split markdown-style headings and list
            # items so layout is closer to the on-screen view.
            normalised = text.replace("\r\n", "\n")
            normalised = re.sub(r"\s*###\s+", "\n### ", normalised)
            normalised = re.sub(
                r"\s*\*\*\s*Insights\s*\*\*", "\nInsights\n", normalised, flags=re.I
            )
            normalised = re.sub(r"(\S)\s+(\d+\.\s)", r"\1\n\2", normalised)
            normalised = re.sub(r"(\S)\s+(\*\s+)", r"\1\n\2", normalised)

            lines = normalised.split("\n")

            pending_ordered: list[str] = []
            pending_bullets: list[str] = []

            def _flush_lists() -> None:
                if pending_ordered:
                    items = [
                        Paragraph(it, styles["BodyText"]) for it in pending_ordered
                    ]
                    story.append(
                        ListFlowable(
                            [ListItem(i) for i in items],
                            bulletType="1",
                            start="1",
                            leftIndent=18,
                        )
                    )
                    pending_ordered.clear()
                if pending_bullets:
                    items = [
                        Paragraph(it, styles["BodyText"]) for it in pending_bullets
                    ]
                    story.append(
                        ListFlowable(
                            [ListItem(i) for i in items],
                            bulletType="bullet",
                            leftIndent=18,
                        )
                    )
                    pending_bullets.clear()

            for raw in lines:
                line = raw.strip()
                if not line:
                    continue

                # Drop embedded SUSPS footer and the default "Insights" heading.
                if "Smart Urban Simulation and Prediction System (SUSPS)" in line:
                    continue
                lower = line.lower()
                if lower == "insights" or lower.startswith("### insights"):
                    continue
                if re.fullmatch(r"[=_-]+", line):
                    continue

                # Remove dev markers and inline (bold) hints
                if "(remove this)" in lower:
                    continue
                line = re.sub(r"\(bold\)", "", line, flags=re.I).strip()
                if not line:
                    continue

                # Ordered list item: "1. text"
                m_ord = re.match(r"^(\d+)\.\s+(.*)$", line)
                if m_ord:
                    item = re.sub(r"\*\*", "", m_ord.group(2)).strip()
                    if item:
                        pending_ordered.append(item)
                    continue

                # Unordered bullet item: "- text" or "* text"
                m_bul = re.match(r"^[-*]\s+(.*)$", line)
                if m_bul:
                    item = re.sub(r"\*\*", "", m_bul.group(1)).strip()
                    if item:
                        pending_bullets.append(item)
                    continue

                # Non-list content: flush any accumulated lists first.
                _flush_lists()

                # Strip remaining markdown markers (heading hashes, bold markers).
                line = re.sub(r"^#{1,6}\s*", "", line)
                line = line.replace("**", "")
                if not line:
                    continue

                # Main title lines like "Urban Analytics Insights for Nairobi".
                if re.match(r"^Urban Analytics Insights for ", line, flags=re.I):
                    story.append(Paragraph(line, styles["Heading4"]))
                    story.append(Spacer(1, 4))
                    continue

                # Section headings such as "Recommended Actions", "Energy Profile Analysis",
                # "Trend Analysis", "Traffic Analysis for Nairobi", etc.
                if (
                    re.match(
                        r"^(Recommended Actions?|Energy Profile|.*Profile Analysis|.*Analysis for .+|Population Growth|Traffic Enriched|Urban Hotspots?)",
                        line,
                        flags=re.I,
                    )
                    and len(line) <= 100
                ):
                    story.append(Paragraph(line, styles["Heading4"]))
                    story.append(Spacer(1, 3))
                    continue

                # Sub-headings: Short-term / Medium-term / Long-term.
                if (
                    re.match(r"^Short-term\b", line, flags=re.I)
                    or re.match(r"^Medium-term\b", line, flags=re.I)
                    or re.match(r"^Long-term\b", line, flags=re.I)
                ):
                    base, _, suffix = line.partition(" ")
                    story.append(
                        Paragraph(f"<b>{base}</b>{suffix}", styles["BodyText"])
                    )
                    story.append(Spacer(1, 2))
                    continue

                # Default: paragraph text.
                story.append(Paragraph(line, styles["BodyText"]))
                story.append(Spacer(1, 2))

            _flush_lists()
            story.append(Spacer(1, 8))

        # Show AI Analysis & Insights immediately after the metadata for the
        # first page only, so it appears once at the top of the document.
        if idx == 0 and page.insights:
            story.append(Paragraph("AI Analysis & Insights", styles["Heading3"]))
            _render_insights(page.insights)

        # Tables
        for table in page.tables:
            story.append(Paragraph(table.title, styles["Heading3"]))
            data: List[List[Any]] = [table.columns]
            for row in table.rows:
                data.append(["" if v is None else str(v) for v in row])
            rl_table = RLTable(data, hAlign="LEFT")
            rl_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                    ]
                )
            )
            story.append(rl_table)
            story.append(Spacer(1, 12))

        # Charts rendered as images when provided, with a vector fallback
        for chart in page.charts:
            story.append(Paragraph(chart.title, styles["Heading3"]))

            # If the frontend provided a PNG (or data URL) of the chart, embed it
            # directly so the PDF matches the on-screen visualization as closely
            # as possible.
            img_data = getattr(chart, "image_data", None)
            if img_data:
                try:
                    import base64

                    # Avoid shadowing the outer ExportPayload so footer_text and
                    # other metadata remain accessible after this block.
                    data_url = img_data
                    # Support data URLs like "data:image/png;base64,...".
                    if "," in data_url:
                        _, data_url = data_url.split(",", 1)
                    raw = base64.b64decode(data_url)
                    img_buf = io.BytesIO(raw)
                    img = RLImage(img_buf, width=420, height=220)
                    story.append(img)
                    story.append(Spacer(1, 12))
                    continue
                except Exception:
                    # Fall back to vector rendering below if anything goes wrong.
                    pass

            # Flatten all points to determine global x/y ranges
            all_points: List[Dict[str, Any]] = []
            for series in chart.series:
                for pt in series.points:
                    # Defensive: ensure required keys exist
                    if "x" in pt and "y" in pt:
                        all_points.append(pt)
            if not all_points:
                continue

            xs = [float(p.get("x", 0.0)) for p in all_points]
            ys = [float(p.get("y", 0.0)) for p in all_points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            if max_x == min_x:
                max_x = min_x + 1.0
            if max_y == min_y:
                max_y = min_y + 1.0

            def _nx(v: float) -> float:
                return (v - min_x) / (max_x - min_x) if max_x != min_x else 0.0

            def _ny(v: float) -> float:
                return (v - min_y) / (max_y - min_y) if max_y != min_y else 0.0

            # Drawing area
            width, height = 420, 220
            left_margin, bottom_margin = 40, 30
            plot_width = width - left_margin - 10
            plot_height = height - bottom_margin - 20

            d = Drawing(width, height)
            # Axes
            d.add(
                RLLine(
                    left_margin,
                    bottom_margin,
                    left_margin,
                    bottom_margin + plot_height,
                    strokeColor=colors.grey,
                    strokeWidth=0.5,
                )
            )
            d.add(
                RLLine(
                    left_margin,
                    bottom_margin,
                    left_margin + plot_width,
                    bottom_margin,
                    strokeColor=colors.grey,
                    strokeWidth=0.5,
                )
            )

            # Plot each series as a polyline; use a basic colour cycle
            palette = [
                colors.HexColor("#1f77b4"),
                colors.HexColor("#ff7f0e"),
                colors.HexColor("#2ca02c"),
                colors.HexColor("#d62728"),
            ]
            for idx_s, series in enumerate(chart.series):
                pts: List[tuple[float, float]] = []
                for pt in series.points:
                    try:
                        x_val = float(pt.get("x", 0.0))
                        y_val = float(pt.get("y", 0.0))
                    except Exception:
                        continue
                    px = left_margin + _nx(x_val) * plot_width
                    py = bottom_margin + _ny(y_val) * plot_height
                    pts.append((px, py))
                if len(pts) < 2:
                    continue
                color = palette[idx_s % len(palette)]
                d.add(
                    RLPolyLine(
                        pts,
                        strokeColor=color,
                        strokeWidth=1.2,
                    )
                )

            story.append(d)
            story.append(Spacer(1, 12))

    footer_text = (
        payload.footer_text
        or "Smart Urban Simulation and Prediction System (SUSPS) - (c) 2025 Developed by David Lameck."
    )

    def _footer(canvas, doc):  # type: ignore[override]
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColorRGB(0.3, 0.3, 0.3)
        text_y = 20
        canvas.drawString(36, text_y, footer_text)
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


@app.post("/export")
def export_documents(payload: ExportPayload):
    """Export one or more pages as PDF, CSV, or a bundled ZIP.

    The frontend is responsible for sending the exact data currently visible in
    the UI so that REAL vs SIMULATE, presets, and advisory text are faithfully
    captured.
    """

    if not payload.pages:
        return JSONResponse(
            {"detail": "No pages provided for export."}, status_code=400
        )

    # Normalise page names for filenames
    def _slug(name: str) -> str:
        return " ".join(name.split())

    if payload.export_format == "pdf":
        try:
            pdf_bytes = _build_pdf(payload)
        except ImportError as exc:
            return JSONResponse({"detail": str(exc)}, status_code=503)
        filename = (
            f"susps_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if payload.export_format == "csv":
        if len(payload.pages) == 1:
            page = payload.pages[0]
            csv_bytes = _build_csv_for_page(page)
            filename = f"SUSPS - {_slug(page.page_name)}.csv"
            return Response(
                content=csv_bytes,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        # Multiple pages: return a ZIP archive, one CSV per page
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for page in payload.pages:
                csv_bytes = _build_csv_for_page(page)
                name = f"SUSPS - {_slug(page.page_name)}.csv"
                zf.writestr(name, csv_bytes)
        filename = f"susps_export_csv_bundle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
        return Response(
            content=buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # Bundle: ZIP containing PDF plus per-page CSVs
    try:
        pdf_bytes = _build_pdf(payload)
    except ImportError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=503)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("susps_export.pdf", pdf_bytes)
        for page in payload.pages:
            csv_bytes = _build_csv_for_page(page)
            name = f"SUSPS - {_slug(page.page_name)}.csv"
            zf.writestr(name, csv_bytes)
    filename = f"susps_export_bundle_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


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
    Uses recent data from existing endpoints (DB â†’ processed â†’ synthetic).
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

    res = generate_insights_from_scope(
        scope_l, bundles, zone_id=zone_id, scenario=scenario
    )
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


@app.post("/advisory/{scope}")
def advisory_from_snapshot(
    scope: str,
    payload: AdvisorySnapshotPayload,
    zone_id: Optional[str] = Query(None),
    scenario: Optional[str] = Query(
        None,
        description=(
            "Optional scenario label (e.g. 'baseline', 'remote_work', 'demand_response') "
            "used to tailor advisory text to the current SIMULATE configuration."
        ),
    ),
):
    """Return markdown insights based on the series currently displayed in the UI.

    The frontend provides the active chart series (Real/Predicted/Simulated/Optimal)
    so the advisory engine can generate insights that match what the user is
    looking at right now.
    """

    scope_l = (scope or "dashboard").lower()
    snapshot_dict = payload.model_dump()
    res = generate_insights_from_snapshot(
        scope_l, snapshot_dict, zone_id=zone_id, scenario=scenario
    )
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

