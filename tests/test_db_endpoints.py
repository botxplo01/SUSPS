import os
import pytest
import requests

API_BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
pytestmark = pytest.mark.skipif(os.getenv("E2E_DOCKER") != "1", reason="E2E_DOCKER not enabled")


def test_energy_endpoint_returns_items():
    r = requests.get(f"{API_BASE_URL}/energy", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("items"), list)
    assert len(data["items"]) >= 1


def test_traffic_endpoint_returns_items():
    r = requests.get(f"{API_BASE_URL}/traffic", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("items"), list)
    assert len(data["items"]) >= 1


def test_energy_summary_returns_names():
    r = requests.get(f"{API_BASE_URL}/energy/summary", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("items"), list)
    assert len(data["items"]) >= 1
    assert "area_name" in data["items"][0]


def test_traffic_summary_returns_names():
    r = requests.get(f"{API_BASE_URL}/traffic/summary", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data.get("items"), list)
    assert len(data["items"]) >= 1
    assert "area_name" in data["items"][0]
