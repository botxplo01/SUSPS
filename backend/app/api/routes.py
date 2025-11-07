from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.db import get_db
from ..models.tables import UrbanArea, EnergyConsumption, TrafficFlow

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/areas")
def list_areas(db: Session = Depends(get_db)):
    try:
        rows = (
            db.query(UrbanArea.area_id, UrbanArea.name)
            .order_by(UrbanArea.area_id)
            .limit(100)
            .all()
        )
        return {"items": [{"area_id": r[0], "name": r[1]} for r in rows]}
    except Exception as e:
        return {"items": [], "detail": str(e)}


@router.get("/energy")
def list_energy(db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        return {"items": [], "detail": str(e)}


@router.get("/traffic")
def list_traffic(db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        return {"items": [], "detail": str(e)}
