-- SUSPS unified database schema dump (PostgreSQL)
-- Compatible with local PostgreSQL and Render PostgreSQL service
-- Generated from src/backend/db/tables.py and instructions.md

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

BEGIN;

-- Optional reset block for development:
-- Uncomment the DROP TABLE statements below if you want this script to fully
-- reset the SUSPS schema (all data in these tables will be deleted).
DROP TABLE IF EXISTS public.hotspot_scores CASCADE;
DROP TABLE IF EXISTS public.air_quality_daily CASCADE;
DROP TABLE IF EXISTS public.environment_features CASCADE;
DROP TABLE IF EXISTS public.traffic_flow CASCADE;
DROP TABLE IF EXISTS public.energy_consumption CASCADE;
DROP TABLE IF EXISTS public.simulation_inputs CASCADE;
DROP TABLE IF EXISTS public.processed_data CASCADE;
DROP TABLE IF EXISTS public.areas CASCADE;
DROP TABLE IF EXISTS public.urban_areas CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- Users table (future authentication/personalization, no auth logic yet)
CREATE TABLE IF NOT EXISTS public.users (
    id              BIGSERIAL PRIMARY KEY,
    email           VARCHAR(255) NOT NULL UNIQUE,
    full_name       VARCHAR(255),
    hashed_password VARCHAR(255),
    created_at      TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ
);

-- Legacy urban areas (kept for backward compatibility and DB summaries)
CREATE TABLE IF NOT EXISTS public.urban_areas (
    area_id   BIGSERIAL PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    area_type TEXT NOT NULL
    -- geometry column intentionally omitted for portability (PostGIS optional)
);

-- Primary areas table as per SUSPS specification
CREATE TABLE IF NOT EXISTS public.areas (
    id            BIGSERIAL PRIMARY KEY,
    name          VARCHAR(150) NOT NULL,
    area_type     VARCHAR(50) NOT NULL DEFAULT 'city',
    description   TEXT,
    boundary_hint TEXT,
    created_at    TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ
);

-- Processed data registry (REAL/SIMULATE, growth/energy/traffic/environment, etc.)
CREATE TABLE IF NOT EXISTS public.processed_data (
    id           BIGSERIAL PRIMARY KEY,
    area_id      BIGINT NOT NULL REFERENCES public.areas(id) ON DELETE CASCADE,
    mode         VARCHAR(20) NOT NULL DEFAULT 'REAL',
    category     VARCHAR(50) NOT NULL,
    version      VARCHAR(50),
    storage_path TEXT,
    meta         JSONB,
    created_at   TIMESTAMPTZ
);

-- Simulation inputs for SIMULATE mode scenarios
CREATE TABLE IF NOT EXISTS public.simulation_inputs (
    id         BIGSERIAL PRIMARY KEY,
    area_id    BIGINT NOT NULL REFERENCES public.areas(id) ON DELETE CASCADE,
    user_id    BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    name       VARCHAR(150) NOT NULL,
    parameters JSONB,
    file_path  TEXT,
    created_at TIMESTAMPTZ
);

-- Time-series energy consumption (DB-backed variant of /energy and /energy/summary)
CREATE TABLE IF NOT EXISTS public.energy_consumption (
    energy_id        BIGSERIAL PRIMARY KEY,
    area_id          BIGINT REFERENCES public.urban_areas(area_id) ON DELETE CASCADE,
    ts               TIMESTAMPTZ NOT NULL,
    predicted_demand DOUBLE PRECISION,
    actual_demand    DOUBLE PRECISION
);

-- Time-series traffic flow (DB-backed variant of /traffic and /traffic/summary)
CREATE TABLE IF NOT EXISTS public.traffic_flow (
    traffic_id       BIGSERIAL PRIMARY KEY,
    area_id          BIGINT REFERENCES public.urban_areas(area_id) ON DELETE CASCADE,
    ts               TIMESTAMPTZ NOT NULL,
    predicted_volume INTEGER,
    actual_volume    INTEGER,
    congestion_level TEXT
);

-- Monthly environment + air-quality features (mirrors environment_aq_features.csv)
CREATE TABLE IF NOT EXISTS public.environment_features (
    id               BIGSERIAL PRIMARY KEY,
    area_id          BIGINT REFERENCES public.areas(id) ON DELETE SET NULL,
    month            INTEGER NOT NULL,
    temp_c           DOUBLE PRECISION,
    rain_mm          DOUBLE PRECISION,
    cooling_deg      DOUBLE PRECISION,
    wet_month        INTEGER,
    pm25             DOUBLE PRECISION,
    pm10             DOUBLE PRECISION,
    o3               DOUBLE PRECISION,
    pollution_index  DOUBLE PRECISION
);

-- Daily air quality aggregates (mirrors air_quality_daily.csv)
CREATE TABLE IF NOT EXISTS public.air_quality_daily (
    id      BIGSERIAL PRIMARY KEY,
    area_id BIGINT REFERENCES public.areas(id) ON DELETE SET NULL,
    date    DATE NOT NULL,
    pm25    DOUBLE PRECISION,
    pm10    DOUBLE PRECISION,
    o3      DOUBLE PRECISION
);

-- Area-level hotspot / optimal-zone scores (mirrors hotspots_areas*.csv)
CREATE TABLE IF NOT EXISTS public.hotspot_scores (
    id               BIGSERIAL PRIMARY KEY,
    area_id          BIGINT REFERENCES public.areas(id) ON DELETE SET NULL,
    admin_unit       VARCHAR(150),
    year             INTEGER,
    population       DOUBLE PRECISION,
    pop_share        DOUBLE PRECISION,
    income_norm      DOUBLE PRECISION,
    employment_score DOUBLE PRECISION,
    hotspot_score    DOUBLE PRECISION
);

-- Helpful indexes for typical query patterns used in src/backend/api.py

-- processed_data: filter by area/mode/category and list newest first
CREATE INDEX IF NOT EXISTS idx_processed_data_area_mode_category
    ON public.processed_data (area_id, mode, category);

CREATE INDEX IF NOT EXISTS idx_processed_data_created_at
    ON public.processed_data (created_at DESC);

-- simulation_inputs: filter by area and show most recent first
CREATE INDEX IF NOT EXISTS idx_simulation_inputs_area_created_at
    ON public.simulation_inputs (area_id, created_at DESC);

-- energy_consumption: recent series per area
CREATE INDEX IF NOT EXISTS idx_energy_consumption_area_ts
    ON public.energy_consumption (area_id, ts DESC);

-- traffic_flow: recent series per area
CREATE INDEX IF NOT EXISTS idx_traffic_flow_area_ts
    ON public.traffic_flow (area_id, ts DESC);

-- environment_features: fast lookup by area/month
CREATE INDEX IF NOT EXISTS idx_environment_features_area_month
    ON public.environment_features (area_id, month);

-- air_quality_daily: fast lookup by area/date
CREATE INDEX IF NOT EXISTS idx_air_quality_daily_area_date
    ON public.air_quality_daily (area_id, date);

-- hotspot_scores: lookup by area/year and admin_unit
CREATE INDEX IF NOT EXISTS idx_hotspot_scores_area_year
    ON public.hotspot_scores (area_id, year);

CREATE INDEX IF NOT EXISTS idx_hotspot_scores_admin_unit
    ON public.hotspot_scores (admin_unit);

COMMIT;
