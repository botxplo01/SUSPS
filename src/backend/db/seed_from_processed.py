# @author: David Lameck

from __future__ import annotations

"""Seed the SUSPS database from processed pipeline outputs.

This script is intentionally small and deterministic. It:
- Ensures there is at least one urban area (for DB-backed series).
- Inserts a recent energy time-series into energy_consumption using
  src.models.energy.daily_profile_from_processed / daily_profile.
- Inserts a recent traffic time-series into traffic_flow using
  src.models.traffic.daily_profile_from_processed / daily_profile.

It is designed to make the DB-backed `/energy`, `/traffic`,
`/energy/summary`, and `/traffic/summary` endpoints return non-empty
results that align with the processed pipeline outputs.

It does *not* attempt to load every processed artifact into the
`processed_data` table; that can be extended later if needed.
"""

from datetime import datetime, time, timezone

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import pandas as pd

from src.backend.db.session import SessionLocal
from src.backend.db.tables import (
    UrbanArea,
    Area,
    EnergyConsumption,
    TrafficFlow,
    EnvironmentFeature,
    AirQualityDaily,
    HotspotScore,
)
from src.pipeline import config as _cfg
from src.models.energy import (
    daily_profile as energy_profile_synthetic,
    daily_profile_from_processed as energy_profile_from_processed,
)
from src.models.traffic import (
    daily_profile as traffic_profile_synthetic,
    daily_profile_from_processed as traffic_profile_from_processed,
)


def _ensure_urban_geometry_nullable(session: SessionLocal) -> None:
    """Relax legacy constraints on urban_areas for compatibility.

    Some earlier PostGIS-oriented schemas added a non-null geometry column on
    urban_areas and a strict check constraint on area_type. The current SUSPS
    schema treats geometry as optional and area_type as a free-text descriptor.
    To keep seeding portable against such databases, we:

    - Drop NOT NULL from geometry when that column exists.
    - Drop the ck_area_type constraint when present.
    """

    try:
        changed = False

        # Check whether a geometry column exists and is marked NOT NULL.
        res = session.execute(
            text(
                """
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'urban_areas'
                    AND column_name = 'geometry'
                """
            )
        ).scalar()
        if res == "NO":
            session.execute(
                text(
                    "ALTER TABLE public.urban_areas "
                    "ALTER COLUMN geometry DROP NOT NULL"
                )
            )
            changed = True

        # Drop any legacy check constraint that restricts area_type values.
        session.execute(
            text(
                "ALTER TABLE public.urban_areas "
                "DROP CONSTRAINT IF EXISTS ck_area_type"
            )
        )
        changed = True

        if changed:
            session.commit()
    except Exception:
        # If this helper fails (e.g. lack of privileges or the table does not
        # exist yet), we swallow the error and let the normal seeding flow run.
        session.rollback()


def _get_or_create_urban_area(session: SessionLocal) -> UrbanArea:
    """Return a canonical UrbanArea row, creating it if needed.

    For now we create a single city-level area using DATA_CITY
    (default Nairobi). This keeps the area_id used by DB-backed
    endpoints consistent with the `/areas` fallback when the
    `areas` table is empty.
    """

    city = getattr(_cfg, "_CITY", None) or getattr(_cfg, "DATA_CITY", None) or "Nairobi"

    ua = (
        session.query(UrbanArea)
        .filter(UrbanArea.name == city)
        .order_by(UrbanArea.area_id.asc())
        .first()
    )
    if ua is not None:
        return ua

    ua = UrbanArea(name=city, area_type="city")
    session.add(ua)
    session.commit()
    session.refresh(ua)
    return ua


def _get_or_create_area(session: SessionLocal) -> Area:
    """Return a canonical Area row, creating it if needed.

    This is similar to _get_or_create_urban_area but targets the new `areas`
    table, which is used by environment_features/air_quality_daily/hotspot_scores.
    """

    city = getattr(_cfg, "_CITY", None) or getattr(_cfg, "DATA_CITY", None) or "Nairobi"

    ar = (
        session.query(Area)
        .filter(Area.name == city)
        .order_by(Area.id.asc())
        .first()
    )
    if ar is not None:
        return ar

    ar = Area(name=city, area_type="city")
    session.add(ar)
    session.commit()
    session.refresh(ar)
    return ar


def _seed_energy_series(session: SessionLocal, area: UrbanArea) -> int:
    """Seed energy_consumption with a 24h series if table is empty.

    Returns the number of rows inserted.
    """

    existing = session.query(EnergyConsumption).count()
    if existing > 0:
        return 0

    # Try to derive from processed energy_features.csv; fall back to synthetic.
    series = energy_profile_from_processed() or energy_profile_synthetic()

    # Use a fixed reference day (today in UTC) to keep timestamps recent.
    today = datetime.now(timezone.utc).date()
    rows: list[EnergyConsumption] = []

    for item in series:
        try:
            hour = int(item.get("hour", 0))
        except Exception:
            hour = 0
        try:
            demand = float(item.get("demand_mwh", 0.0))
        except Exception:
            demand = 0.0

        ts = datetime.combine(today, time(hour=hour), tzinfo=timezone.utc)
        # For now, let actual ~= predicted with a small deterministic adjustment.
        predicted = demand
        actual = demand * 0.97 if demand else None

        rows.append(
            EnergyConsumption(
                area_id=area.area_id,
                ts=ts,
                predicted_demand=predicted,
                actual_demand=actual,
            )
        )

    for row in rows:
        session.add(row)
    session.commit()
    return len(rows)


def _congestion_label(volume: int) -> str:
    if volume >= 900:
        return "high"
    if volume >= 500:
        return "medium"
    return "low"


def _seed_traffic_series(session: SessionLocal, area: UrbanArea) -> int:
    """Seed traffic_flow with a 24h series when empty or obviously degenerate.

    Returns the number of rows inserted. If the table already contains rows but
    the predicted_volume values are essentially flat (e.g. all ~600 veh/h), the
    existing data is cleared and reseeded using the same processed/synthetic
    logic so REAL-mode charts display a realistic 24h profile.
    """

    existing = session.query(TrafficFlow).count()
    if existing > 0:
        try:
            # Sample a subset of existing volumes to detect degenerate cases.
            vals = [
                int(v[0])
                for v in session.query(TrafficFlow.predicted_volume)
                .order_by(TrafficFlow.ts.desc())
                .limit(100)
                .all()
                if v[0] is not None
            ]
            if vals:
                unique = set(vals)
                spread = max(vals) - min(vals)
                # Treat as degenerate when there are very few distinct levels
                # and they are tightly clustered (e.g. 590-610 only).
                if len(unique) <= 3 and spread < 100:
                    session.query(TrafficFlow).delete()
                    session.commit()
                    existing = 0
        except Exception:
            # On any error, keep existing data and skip reseed.
            return 0

    if existing > 0:
        return 0

    series = traffic_profile_from_processed() or traffic_profile_synthetic()
    today = datetime.now(timezone.utc).date()
    rows: list[TrafficFlow] = []

    for item in series:
        try:
            hour = int(item.get("hour", 0))
        except Exception:
            hour = 0
        try:
            vol = int(item.get("volume", 0))
        except Exception:
            vol = 0

        ts = datetime.combine(today, time(hour=hour), tzinfo=timezone.utc)
        predicted = vol
        # Slight deterministic difference between predicted and actual
        actual = max(int(vol * 0.9), 0)

        rows.append(
            TrafficFlow(
                area_id=area.area_id,
                ts=ts,
                predicted_volume=predicted,
                actual_volume=actual,
                congestion_level=_congestion_label(vol),
            )
        )

    for row in rows:
        session.add(row)
    session.commit()
    return len(rows)


def _seed_environment_features(session: SessionLocal, area: Area) -> int:
    """Seed environment_features from environment_aq_features.csv if empty.

    This maps each row in environment_aq_features to EnvironmentFeature with
    the given area_id. If the table already has rows, it does nothing.
    """

    existing = session.query(EnvironmentFeature).count()
    if existing > 0:
        return 0

    env_path = _cfg.PROCESSED_DIR / "environment_aq_features.csv"
    if not env_path.exists():
        return 0

    df = pd.read_csv(env_path)
    if "month" not in df.columns:
        return 0

    rows: list[EnvironmentFeature] = []
    for _, r in df.iterrows():
        try:
            month = int(r.get("month", 0))
        except Exception:
            continue
        ef = EnvironmentFeature(
            area_id=area.id,
            month=month,
            temp_c=float(r.get("temp_c")) if "temp_c" in df.columns else None,
            rain_mm=float(r.get("rain_mm")) if "rain_mm" in df.columns else None,
            cooling_deg=float(r.get("cooling_deg")) if "cooling_deg" in df.columns else None,
            wet_month=int(r.get("wet_month")) if "wet_month" in df.columns else None,
            pm25=float(r.get("pm25")) if "pm25" in df.columns else None,
            pm10=float(r.get("pm10")) if "pm10" in df.columns else None,
            o3=float(r.get("o3")) if "o3" in df.columns else None,
            pollution_index=float(r.get("pollution_index")) if "pollution_index" in df.columns else None,
        )
        rows.append(ef)

    if not rows:
        return 0

    for row in rows:
        session.add(row)
    session.commit()
    return len(rows)


def _seed_air_quality_daily(session: SessionLocal, area: Area) -> int:
    """Seed air_quality_daily from air_quality_daily.csv if empty."""

    existing = session.query(AirQualityDaily).count()
    if existing > 0:
        return 0

    aq_path = _cfg.PROCESSED_DIR / "air_quality_daily.csv"
    if not aq_path.exists():
        return 0

    df = pd.read_csv(aq_path)
    if "date" not in df.columns:
        return 0

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    rows: list[AirQualityDaily] = []
    for _, r in df.iterrows():
        if not r["date"]:
            continue
        aq = AirQualityDaily(
            area_id=area.id,
            date=r["date"],
            pm25=float(r.get("pm25")) if "pm25" in df.columns else None,
            pm10=float(r.get("pm10")) if "pm10" in df.columns else None,
            o3=float(r.get("o3")) if "o3" in df.columns else None,
        )
        rows.append(aq)

    if not rows:
        return 0

    for row in rows:
        session.add(row)
    session.commit()
    return len(rows)


def _seed_hotspot_scores(session: SessionLocal, area: Area) -> int:
    """Seed hotspot_scores from hotspots_areas.csv and hotspots_areas_forecast.csv.

    This creates one HotspotScore per row in hotspots_areas (base year) and
    hotspots_areas_forecast (future years), using the given area as a logical
    anchor while preserving the admin_unit field.
    """

    existing = session.query(HotspotScore).count()
    if existing > 0:
        return 0

    total_inserted = 0

    # Base hotspots (no year column)
    base_path = _cfg.PROCESSED_DIR / "hotspots_areas.csv"
    if base_path.exists():
        df = pd.read_csv(base_path)
        for _, r in df.iterrows():
            hs = HotspotScore(
                area_id=area.id,
                admin_unit=str(r.get("admin_unit")) if "admin_unit" in df.columns else None,
                year=None,
                population=float(r.get("population")) if "population" in df.columns else None,
                pop_share=float(r.get("pop_share")) if "pop_share" in df.columns else None,
                income_norm=float(r.get("income_norm")) if "income_norm" in df.columns else None,
                employment_score=float(r.get("employment_score")) if "employment_score" in df.columns else None,
                hotspot_score=float(r.get("hotspot_score")) if "hotspot_score" in df.columns else None,
            )
            session.add(hs)
            total_inserted += 1

    # Forecast hotspots (with year)
    forecast_path = _cfg.PROCESSED_DIR / "hotspots_areas_forecast.csv"
    if forecast_path.exists():
        df = pd.read_csv(forecast_path)
        for _, r in df.iterrows():
            try:
                year = int(r.get("year")) if "year" in df.columns else None
            except Exception:
                year = None
            hs = HotspotScore(
                area_id=area.id,
                admin_unit=str(r.get("admin_unit")) if "admin_unit" in df.columns else None,
                year=year,
                population=float(r.get("population")) if "population" in df.columns else None,
                pop_share=float(r.get("pop_share")) if "pop_share" in df.columns else None,
                income_norm=float(r.get("income_norm")) if "income_norm" in df.columns else None,
                employment_score=float(r.get("employment_score")) if "employment_score" in df.columns else None,
                hotspot_score=float(r.get("hotspot_score")) if "hotspot_score" in df.columns else None,
            )
            session.add(hs)
            total_inserted += 1

    if total_inserted == 0:
        return 0

    session.commit()
    return total_inserted


def main() -> None:
    """Entry point used as a script.

    Assumes the following have already run successfully:
    - `python -m src.pipeline.ingest`
    - `python -m src.pipeline.preprocess`

    and that DATABASE_URL / USE_LOCAL_DB / LOCAL_DATABASE_URL are
    configured to point at the target Postgres instance.
    """

    with SessionLocal() as session:  # type: ignore[call-arg]
        try:
            # Ensure legacy urban_areas geometry (when present) is nullable so
            # that we can create a simple city-level row without requiring
            # PostGIS data.
            _ensure_urban_geometry_nullable(session)

            # Legacy urban_areas-backed time series
            urban_area = _get_or_create_urban_area(session)
            n_energy = _seed_energy_series(session, urban_area)
            n_traffic = _seed_traffic_series(session, urban_area)

            # New areas-backed environment/AQ/hotspot tables
            area = _get_or_create_area(session)
            n_env = _seed_environment_features(session, area)
            n_aq = _seed_air_quality_daily(session, area)
            n_hs = _seed_hotspot_scores(session, area)
        except SQLAlchemyError:  # pragma: no cover - defensive
            session.rollback()
            raise

    print(f"Seeded energy_consumption rows: {n_energy}")
    print(f"Seeded traffic_flow rows: {n_traffic}")
    print(f"Seeded environment_features rows: {n_env}")
    print(f"Seeded air_quality_daily rows: {n_aq}")
    print(f"Seeded hotspot_scores rows: {n_hs}")


if __name__ == "__main__":
    main()

