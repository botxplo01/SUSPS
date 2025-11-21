"""API tests for forecasted area hotspots endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.api import app
from src.pipeline import config as _cfg


client = TestClient(app)


def test_hotspots_areas_forecast_empty_when_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    resp = client.get("/hotspots/areas/forecast")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


def test_hotspots_areas_forecast_filter_by_year(tmp_path, monkeypatch):
    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    csv_path = tmp_path / "hotspots_areas_forecast.csv"
    csv_path.write_text(
        "year,admin_unit,population,pop_share,hotspot_score\n"
        "2030,WardA,1200,0.3,0.9\n"
        "2031,WardA,1300,0.32,0.95\n",
        encoding="utf-8",
    )
    resp = client.get("/hotspots/areas/forecast", params={"year": 2030})
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert len(items) == 1
    assert items[0]["year"] == 2030
    assert items[0]["admin_unit"] == "WardA"
