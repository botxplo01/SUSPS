from __future__ import annotations

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Float,
)

try:  # optional: if geoalchemy2 is available
    from geoalchemy2 import Geometry  # type: ignore
except Exception:  # pragma: no cover
    Geometry = None  # type: ignore

from .base import Base


class UrbanArea(Base):
    __tablename__ = "urban_areas"
    area_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    area_type = Column(Text, nullable=False)
    # geometry column is optional at runtime
    if Geometry is not None:
        geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)


class EnergyConsumption(Base):
    __tablename__ = "energy_consumption"
    energy_id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("urban_areas.area_id"))
    ts = Column(DateTime(timezone=True), nullable=False)
    predicted_demand = Column(Float)
    actual_demand = Column(Float)


class TrafficFlow(Base):
    __tablename__ = "traffic_flow"
    traffic_id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("urban_areas.area_id"))
    ts = Column(DateTime(timezone=True), nullable=False)
    predicted_volume = Column(Integer)
    actual_volume = Column(Integer)
    congestion_level = Column(Text)
