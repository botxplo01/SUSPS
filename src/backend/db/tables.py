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
    JSON,
)

try:  # optional: if geoalchemy2 is available
    from geoalchemy2 import Geometry  # type: ignore
except Exception:  # pragma: no cover
    Geometry = None  # type: ignore

from .base import Base


class UrbanArea(Base):
    """Legacy urban area table kept for backward compatibility.

    New work should prefer the Area model below, which maps to the areas table
    required by the current SUSPS specification.
    """

    __tablename__ = "urban_areas"
    area_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    area_type = Column(Text, nullable=False)
    # geometry column is optional at runtime
    if Geometry is not None:
        geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)


class Area(Base):
    """Primary areas table as per SUSPS database specification.

    Represents a logical analysis area (city, ward, neighborhood, corridor, etc.)
    and is used as the anchor for processed data and simulations.
    """

    __tablename__ = "areas"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    area_type = Column(String(50), nullable=False, default="city")
    description = Column(Text, nullable=True)
    # Optional geometry; presence depends on geoalchemy2
    if Geometry is not None:  # type: ignore[truthy-function]
        geometry = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)  # type: ignore[arg-type]
    boundary_hint = Column(
        Text, nullable=True
    )  # e.g., bounding box or GeoJSON reference
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class ProcessedData(Base):
    """Stores references and metadata for processed datasets.

    This table links processed artifacts under data/<CITY>/processed or S3
    prefixes back to a logical area and data category (growth, energy, traffic,
    environment, etc.).
    """

    __tablename__ = "processed_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("areas.id"), nullable=False)
    # REAL vs SIMULATE; kept as free-text to avoid enum migrations
    mode = Column(String(20), nullable=False, default="REAL")
    # e.g. "urban_growth", "energy", "traffic", "environment"
    category = Column(String(50), nullable=False)
    # versioning or run identifier
    version = Column(String(50), nullable=True)
    # path to CSV/GeoJSON/GeoTIFF under processed/ or S3 key
    storage_path = Column(Text, nullable=True)
    # arbitrary JSON metadata about schema, columns, summary stats, etc.
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class SimulationInput(Base):
    """Captures user-provided simulation configurations and uploads.

    These records allow re-running SIMULATE mode scenarios and auditing the
    impact of user-edited parameters or uploaded files.
    """

    __tablename__ = "simulation_inputs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("areas.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    # free-text label for the scenario (e.g. "High Growth 2035")
    name = Column(String(150), nullable=False)
    # JSON payload with structured parameters (sliders, toggles, etc.)
    parameters = Column(JSON, nullable=True)
    # optional reference to uploaded file on disk or S3
    file_path = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class User(Base):
    """Users table for future authentication and personalization.

    Authentication and authorization are intentionally not implemented yet.
    """

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    # Optional hashed password field for future sign-in support
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


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
