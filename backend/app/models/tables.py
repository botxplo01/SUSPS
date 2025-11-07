from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Float,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from .base import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UrbanArea(Base):
    __tablename__ = "urban_areas"
    area_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    area_type = Column(Text, nullable=False)
    geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=False)


class Demographics(Base):
    __tablename__ = "demographics"
    demo_id = Column(BigInteger, primary_key=True, autoincrement=True)
    region_name = Column(String(100), nullable=False)
    population = Column(Integer, nullable=False)
    age_distribution = Column(JSONB)
    gender_distribution = Column(JSONB)
    census_year = Column(Integer, nullable=False)
    area_id = Column(BigInteger, ForeignKey("urban_areas.area_id"))


class MobilityTransport(Base):
    __tablename__ = "mobility_transport"
    transport_id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("urban_areas.area_id"))
    mode = Column(Text, nullable=False)
    route_info = Column(JSONB)
    average_speed_kmh = Column(Float)
    capacity = Column(Integer)


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


class UrbanGrowthPrediction(Base):
    __tablename__ = "urban_growth_predictions"
    growth_id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("urban_areas.area_id"))
    prediction_date = Column(Date, nullable=False)
    predicted_population = Column(Integer)
    predicted_land_use = Column(JSONB)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    simulation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    run_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    parameters = Column(JSONB)
    results = Column(JSONB)
    area_ids = Column(JSONB)


class SystemLog(Base):
    __tablename__ = "system_logs"
    log_id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    action = Column(Text)
    severity = Column(Text, nullable=False, server_default="info")
