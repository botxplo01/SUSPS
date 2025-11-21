"""API tests for /ts/forecast deterministic fallback behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.api import app


client = TestClient(app)


def test_ts_forecast_growth_deterministic():
    # Simple increasing series; we expect non-empty forecast using fallback.
    payload = {
        "target": "growth",
        "series": [
            {"t": 2025, "value": 800_000},
            {"t": 2026, "value": 824_000},
        ],
        "horizon": 3,
        "use_model": False,
    }
    resp = client.post("/ts/forecast", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["target"] == "growth"
    assert data["used_model"] is False
    items = data["items"]
    assert isinstance(items, list)
    assert len(items) == 3
    # Ensure basic structure
    for i, it in enumerate(items, start=1):
        assert it["step"] == i
        assert "t" in it and "value" in it


def test_ts_forecast_energy_deterministic_constant():
    # Flat series should produce flat forecast with deterministic fallback.
    payload = {
        "target": "energy",
        "series": [
            {"t": 0, "value": 10.0},
        ],
        "horizon": 2,
        "use_model": False,
    }
    resp = client.post("/ts/forecast", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["target"] == "energy"
    items = data["items"]
    assert len(items) == 2
    for it in items:
        assert it["value"] == 10.0
