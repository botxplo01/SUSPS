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
from typing import Iterable

from sqlalchemy.exc import SQLAlchemyError

from src.backend.db.session import SessionLocal
from src.backend.db.tables import UrbanArea, EnergyConsumption, TrafficFlow
from src.pipeline import config as _cfg
from src.models.energy import (
    daily_profile as energy_profile_synthetic,
    daily_profile_from_processed as energy_profile_from_processed,
)
from src.models.traffic import (
    daily_profile as traffic_profile_synthetic,
    daily_profile_from_processed as traffic_profile_from_processed,
)


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
    """Seed traffic_flow with a 24h series if table is empty.

    Returns the number of rows inserted.
    """

    existing = session.query(TrafficFlow).count()
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
            area = _get_or_create_urban_area(session)
            n_energy = _seed_energy_series(session, area)
            n_traffic = _seed_traffic_series(session, area)
        except SQLAlchemyError as e:  # pragma: no cover - defensive
            session.rollback()
            raise

    print(f"Seeded energy_consumption rows: {n_energy}")
    print(f"Seeded traffic_flow rows: {n_traffic}")


if __name__ == "__main__":
    main()
