# @author: David Lameck

"""API tests for /simulate/run covering all-modules and growth-only modes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.backend.api import app


client = TestClient(app)


def test_simulate_run_all_modules_demo_mode():
    resp = client.post(
        "/simulate/run",
        json={
            "module": "all",
            "parameters": {
                "population_scale": 1.05,
                "annual_rate_delta_pct": 10.0,
                "demand_scale": 1.1,
                "volume_scale": 0.9,
            },
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["module"] == "all"
    results = data["results"]
    # Growth should be present and non-empty
    assert "growth" in results
    assert isinstance(results["growth"], list)
    # Energy should have hourly entries
    assert "energy" in results
    assert isinstance(results["energy"], list)
    # Traffic should have hourly entries
    assert "traffic" in results
    assert isinstance(results["traffic"], list)


def test_simulate_run_growth_only():
    resp = client.post(
        "/simulate/run",
        json={
            "module": "growth",
            "parameters": {"population_scale": 1.1},
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["module"] == "growth"
    results = data["results"]
    assert "growth" in results
    assert "energy" not in results
    assert "traffic" not in results
