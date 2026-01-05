# @author: David Lameck

"""API tests for baseline area hotspots endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.api import app
from src.pipeline import config as _cfg


client = TestClient(app)


def test_hotspots_areas_empty_when_missing_file(tmp_path, monkeypatch):
    # Point PROCESSED_DIR to a temporary directory with no hotspots file
    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    resp = client.get("/hotspots/areas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


def test_hotspots_areas_returns_items(tmp_path, monkeypatch):
    # Create a temporary hotspots_areas.csv and ensure the endpoint returns it
    monkeypatch.setattr(_cfg, "PROCESSED_DIR", tmp_path)
    csv_path = tmp_path / "hotspots_areas.csv"
    csv_path.write_text(
        "admin_unit,population,pop_share,income_norm,employment_score,hotspot_score\n"
        "WardA,1000,0.3,0.4,60,0.8\n"
        "WardB,500,0.2,0.6,70,0.5\n",
        encoding="utf-8",
    )
    resp = client.get("/hotspots/areas")
    assert resp.status_code == 200
    data = resp.json()
    items = data["items"]
    assert len(items) == 2
    assert items[0]["admin_unit"] == "WardA"
    assert items[0]["hotspot_score"] == 0.8
