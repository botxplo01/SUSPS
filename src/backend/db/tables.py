# @author: David Lameck

from __future__ import annotations

import os

from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    ForeignKey,
    Float,
    JSON,
)

try:  # optional: if geoalchemy2 is available
    from geoalchemy2 import Geometry  # type: ignore
except Exception:  # pragma: no cover
    Geometry = None  # type: ignore

# Geometry columns are optional at runtime. Even when geoalchemy2 is installed,
# some deployments may use a schema where the geometry column was not created.
# To avoid runtime errors like "column urban_areas.geometry does not exist",
# we only map geometry fields when DB_ENABLE_GEOMETRY is explicitly turned on.
_DB_ENABLE_GEOMETRY = (
    os.getenv("DB_ENABLE_GEOMETRY", "").strip().lower() in {"1", "true", "yes", "on"}
)

from .base import Base


def _get_srid_from_env(default: int = 4326) -> int:
    """Resolve SRID for spatial columns based on DB_SPATIAL_CRS.

    Accepts values like 'EPSG:4326' or '4326'; falls back to 4326 on errors.
    """

    crs = os.getenv("DB_SPATIAL_CRS", "") or ""
    if not crs:
        return default
    # Strip common 'EPSG:' prefix or similar
    if ":" in crs:
        crs = crs.split(":", 1)[1]
    try:
        return int(crs)
    except ValueError:
        return default


_SRID = _get_srid_from_env()


class UrbanArea(Base):
    """Legacy urban area table kept for backward compatibility.

    New work should prefer the Area model below, which maps to the areas table
    required by the current SUSPS specification.
    """

    __tablename__ = "urban_areas"
    area_id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    area_type = Column(Text, nullable=False)
    # geometry column is optional at runtime and only mapped when
    # DB_ENABLE_GEOMETRY is explicitly enabled.
    if Geometry is not None and _DB_ENABLE_GEOMETRY:
        geometry = Column(Geometry("MULTIPOLYGON", srid=_SRID), nullable=True)


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
    # Optional geometry; presence depends on geoalchemy2 and DB_ENABLE_GEOMETRY.
    if Geometry is not None and _DB_ENABLE_GEOMETRY:  # type: ignore[truthy-function]
        geometry = Column(Geometry("MULTIPOLYGON", srid=_SRID), nullable=True)  # type: ignore[arg-type]
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


class EnvironmentFeature(Base):
    """Monthly environment + air-quality features per area (optional).

    Rows typically mirror environment_aq_features.csv and may be city-level
    (area_id NULL) or area-specific when such mapping is available.
    """

    __tablename__ = "environment_features"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("areas.id"), nullable=True)
    month = Column(Integer, nullable=False)
    temp_c = Column(Float, nullable=True)
    rain_mm = Column(Float, nullable=True)
    cooling_deg = Column(Float, nullable=True)
    wet_month = Column(Integer, nullable=True)
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    o3 = Column(Float, nullable=True)
    pollution_index = Column(Float, nullable=True)


class AirQualityDaily(Base):
    """Daily air-quality aggregates (pm25/pm10/o3) per area (optional)."""

    __tablename__ = "air_quality_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("areas.id"), nullable=True)
    date = Column(Date, nullable=False)
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    o3 = Column(Float, nullable=True)


class HotspotScore(Base):
    """Hotspot / optimal-zone scores derived from processed pipeline outputs."""

    __tablename__ = "hotspot_scores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    area_id = Column(BigInteger, ForeignKey("areas.id"), nullable=True)
    admin_unit = Column(String(150), nullable=True)
    year = Column(Integer, nullable=True)
    population = Column(Float, nullable=True)
    pop_share = Column(Float, nullable=True)
    income_norm = Column(Float, nullable=True)
    employment_score = Column(Float, nullable=True)
    hotspot_score = Column(Float, nullable=True)
