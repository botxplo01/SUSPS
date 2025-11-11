from __future__ import annotations

import argparse
from datetime import datetime, date, timezone
from typing import Iterable, List, Tuple

import pandas as pd
from sqlalchemy import delete, func

# Ensure DB session and models are available from backend package
from backend.app.core.db import SessionLocal  # type: ignore
from backend.app.models.tables import (
    UrbanArea,
    EnergyConsumption,
    TrafficFlow,
)  # type: ignore

# Reuse processed-data readers so we honor the same logic the API uses
from src.models.energy import daily_profile_from_processed as energy_daily_from_processed
from src.models.energy import daily_profile as energy_daily_synth
from src.models.traffic import (
    daily_profile_from_processed as traffic_daily_from_processed,
)
from src.models.traffic import daily_profile as traffic_daily_synth
from src.pipeline import config as _cfg


def _ensure_areas(db) -> List[int]:
    ids = [row[0] for row in db.query(UrbanArea.area_id).order_by(UrbanArea.area_id).all()]
    if not ids:
        raise RuntimeError("No urban areas found; seed urban areas before loading features.")
    return ids


def _target_day(d: str | None) -> date:
    if d:
        return datetime.fromisoformat(d).date()
    return datetime.now(timezone.utc).date()


def _ts_for(day: date, hour: int) -> datetime:
    # timezone-aware UTC timestamps
    return datetime(day.year, day.month, day.day, hour, 0, 0, tzinfo=timezone.utc)


def _congestion_from_volume(v: int) -> str:
    if v >= 900:
        return "high"
    if v >= 450:
        return "medium"
    return "low"


def load_energy(db, day: date, area_ids: Iterable[int]) -> Tuple[int, int]:
    """Load energy daily profile into energy_consumption for given day and areas.

    Returns: (deleted_rows, inserted_rows)
    """
    # Prefer processed-derived 24h profile; fallback to synthetic
    items = energy_daily_from_processed(_cfg.PROCESSED_DIR)
    if not items:
        items = energy_daily_synth()

    # Delete any existing rows for target day for these areas
    del_stmt = (
        delete(EnergyConsumption)
        .where(func.date(EnergyConsumption.ts) == day)
        .where(EnergyConsumption.area_id.in_(list(area_ids)))
    )
    deleted = db.execute(del_stmt).rowcount or 0

    # If multiple areas, distribute demand evenly across areas as a simple proxy
    area_ids_list = list(area_ids)
    n = max(len(area_ids_list), 1)

    rows = []
    for it in items:
        hour = int(it.get("hour", 0))
        demand = float(it.get("demand_mwh", 0.0)) / n
        ts = _ts_for(day, hour)
        for aid in area_ids_list:
            rows.append(
                EnergyConsumption(
                    area_id=aid,
                    ts=ts,
                    predicted_demand=demand,
                    actual_demand=demand * 0.96,
                )
            )
    for r in rows:
        db.add(r)
    db.commit()
    return deleted, len(rows)


def load_traffic(db, day: date, area_ids: Iterable[int]) -> Tuple[int, int]:
    """Load traffic daily profile into traffic_flow for given day and areas.

    Returns: (deleted_rows, inserted_rows)
    """
    items = traffic_daily_from_processed(_cfg.PROCESSED_DIR)
    if not items:
        items = traffic_daily_synth()

    del_stmt = (
        delete(TrafficFlow)
        .where(func.date(TrafficFlow.ts) == day)
        .where(TrafficFlow.area_id.in_(list(area_ids)))
    )
    deleted = db.execute(del_stmt).rowcount or 0

    area_ids_list = list(area_ids)
    n = max(len(area_ids_list), 1)

    rows = []
    for it in items:
        hour = int(it.get("hour", 0))
        vol = int(it.get("volume", 0)) // n
        ts = _ts_for(day, hour)
        for aid in area_ids_list:
            rows.append(
                TrafficFlow(
                    area_id=aid,
                    ts=ts,
                    predicted_volume=vol,
                    actual_volume=int(vol * 0.95),
                    congestion_level=_congestion_from_volume(vol),
                )
            )
    for r in rows:
        db.add(r)
    db.commit()
    return deleted, len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Load processed features into the database (energy_consumption, traffic_flow). "
            "Deletes existing rows for the target day before inserting."
        )
    )
    parser.add_argument(
        "--date",
        dest="date_str",
        default=None,
        help="Target date (YYYY-MM-DD). Defaults to today (UTC).",
    )
    parser.add_argument(
        "--areas",
        dest="areas",
        default=None,
        help="Comma-separated area IDs to load. Default: all urban areas.",
    )
    args = parser.parse_args()

    tgt_day = _target_day(args.date_str)

    with SessionLocal() as db:  # type: ignore
        # Determine target areas
        if args.areas:
            area_ids = [int(x) for x in args.areas.split(",") if x.strip()]
        else:
            area_ids = _ensure_areas(db)

        e_del, e_ins = load_energy(db, tgt_day, area_ids)
        t_del, t_ins = load_traffic(db, tgt_day, area_ids)

        print(
            f"Energy: deleted {e_del} rows for {tgt_day}, inserted {e_ins}. "
            f"Traffic: deleted {t_del} rows, inserted {t_ins}."
        )


if __name__ == "__main__":
    main()
