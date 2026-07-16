import pytest


@pytest.mark.anyio
async def test_dashboard_summary_empty(client):
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["total_devices"] == 0


@pytest.mark.anyio
async def test_dashboard_summary_with_devices(client):
    await client.post("/api/v1/devices", json={
        "device_id": "dash-001",
        "device_name": "Device 1",
        "device_type": "sensor",
    })
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["total_devices"] == 1


@pytest.mark.anyio
async def test_trend_empty(client):
    resp = await client.get("/api/v1/dashboard/trend")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.anyio
async def test_online_devices_empty(client):
    resp = await client.get("/api/v1/dashboard/devices/online")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
