# @author: Lameck David Musumpuka

"""FastAPI app smoke tests for health and advisory endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from src.backend.api import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "susps"


@pytest.mark.asyncio
async def test_advisory_batch_with_zone_ids():
    """Smoke test for /advisory_batch with per-scope zone_ids.

    This ensures the endpoint accepts zone_ids and returns a structured
    response including zone_id per scope. We do not assert on advisory
    content because it may depend on external HF state.
    """

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/advisory_batch",
            params={
                "scopes": "growth,energy",
                "zone_ids": "ward-1,ward-2",
            },
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    results = data["results"]
    assert "growth" in results and "energy" in results
    growth = results["growth"]
    energy = results["energy"]
    assert growth.get("zone_id") == "ward-1"
    assert energy.get("zone_id") == "ward-2"
    # Basic shape checks
    assert isinstance(growth.get("insights", ""), str)
    assert isinstance(energy.get("insights", ""), str)
