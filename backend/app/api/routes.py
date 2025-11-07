from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.db import get_db
from ..models.tables import UrbanArea

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
