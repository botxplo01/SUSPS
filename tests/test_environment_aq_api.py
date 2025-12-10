# @author: Lameck David Musumpuka

"""API tests for environment and air-quality feature endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.api import app
from src.pipeline import config as _cfg


client = TestClient(app)


def test_environment_features_empty_when_missing_file(tmp_path, monkeypatch):
    """When no environment_aq_features.csv is present, return an empty list."""

    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    # Force API into file-based mode for this test, even if a DB is configured.
    monkeypatch.setattr("src.backend.api._DB_ENABLED", False, raising=False)
    resp = client.get("/environment/features")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


def test_environment_features_returns_items(tmp_path, monkeypatch):
    """environment/features should surface rows from environment_aq_features.csv."""

    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr("src.backend.api._DB_ENABLED", False, raising=False)
    csv_path = tmp_path / "environment_aq_features.csv"
    csv_path.write_text(
        "month,temp_c,rain_mm,cooling_deg,wet_month,pm25,pm10,o3,pollution_index\n"
        "1,25.0,100.0,5.0,1,35.0,50.0,10.0,0.6\n"
        "2,24.0,80.0,4.0,0,30.0,40.0,9.0,0.5\n",
        encoding="utf-8",
    )

    resp = client.get("/environment/features")
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert isinstance(items, list)
    assert len(items) == 2
    assert items[0]["month"] == 1
    assert items[0]["temp_c"] == 25.0
    assert items[0]["pollution_index"] == 0.6


def test_air_quality_daily_empty_when_missing_file(tmp_path, monkeypatch):
    """When no air_quality_daily.csv is present, return an empty list."""

    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr("src.backend.api._DB_ENABLED", False, raising=False)
    resp = client.get("/air_quality/daily")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


def test_air_quality_daily_returns_items(tmp_path, monkeypatch):
    """air_quality/daily should surface rows from air_quality_daily.csv."""

    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr("src.backend.api._DB_ENABLED", False, raising=False)
    csv_path = tmp_path / "air_quality_daily.csv"
    csv_path.write_text(
        "date,pm25,pm10,o3\n"
        "2025-01-01,35.0,50.0,10.0\n"
        "2025-01-02,30.0,45.0,9.5\n",
        encoding="utf-8",
    )

    resp = client.get("/air_quality/daily", params={"limit": 1})
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert isinstance(items, list)
    assert len(items) == 1
    # Sorted descending by date, so the most recent row should be returned first.
    assert items[0]["date"] == "2025-01-02"
    assert items[0]["pm25"] == 30.0


def test_hotspots_scores_empty_when_missing_files(tmp_path, monkeypatch):
    """When no hotspot CSVs are present, /hotspots/scores returns an empty list."""

    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr("src.backend.api._DB_ENABLED", False, raising=False)
    resp = client.get("/hotspots/scores")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


def test_hotspots_scores_merges_baseline_and_forecast(tmp_path, monkeypatch):
    """/hotspots/scores should merge baseline and forecast hotspot CSVs."""

    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    monkeypatch.setattr("src.backend.api._DB_ENABLED", False, raising=False)

    base = tmp_path / "hotspots_areas.csv"
    base.write_text(
        "admin_unit,population,pop_share,income_norm,employment_score,hotspot_score\n"
        "WardA,1000,0.3,0.4,60,0.8\n",
        encoding="utf-8",
    )

    forecast = tmp_path / "hotspots_areas_forecast.csv"
    forecast.write_text(
        "admin_unit,year,population,pop_share,income_norm,employment_score,hotspot_score\n"
        "WardA,2030,1200,0.32,0.45,65,0.85\n",
        encoding="utf-8",
    )

    # Without year filter, we expect both baseline and forecast rows.
    resp = client.get("/hotspots/scores")
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert isinstance(items, list)
    assert len(items) == 2

    baseline = [it for it in items if it["year"] is None][0]
    forecast_row = [it for it in items if it["year"] == 2030][0]
    assert baseline["admin_unit"] == "WardA"
    assert baseline["hotspot_score"] == 0.8
    assert forecast_row["hotspot_score"] == 0.85

    # With a year filter, only the matching forecast row should be returned.
    resp_year = client.get("/hotspots/scores", params={"year": 2030})
    assert resp_year.status_code == 200
    items_year = resp_year.json()["items"]
    assert len(items_year) == 1
    assert items_year[0]["year"] == 2030
