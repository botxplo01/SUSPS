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


@router.get("/energy/summary")
def energy_summary(db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        return {"items": [], "detail": str(e)}


@router.get("/traffic/summary")
def traffic_summary(db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        return {"items": [], "detail": str(e)}
