from datetime import datetime

import pytest


@pytest.mark.anyio
async def test_report_data_unregistered_device(client):
    resp = await client.post("/api/v1/data/report", json={
        "device_id": "no-such-device",
        "temperature": 25.0,
        "humidity": 60.0,
        "reported_at": "2026-07-16T12:00:00",
    })
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_report_data_success(client):
    await client.post("/api/v1/devices", json={
        "device_id": "data-001",
        "device_name": "Data Device",
        "device_type": "multi_sensor",
    })
    resp = await client.post("/api/v1/data/report", json={
        "device_id": "data-001",
        "temperature": 25.5,
        "humidity": 60.0,
        "battery_level": 85.0,
        "signal_strength": -42,
        "reported_at": "2026-07-16T12:00:00",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["device_id"] == "data-001"


@pytest.mark.anyio
async def test_report_data_then_trend(client):
    await client.post("/api/v1/devices", json={
        "device_id": "data-002",
        "device_name": "Trend Device",
        "device_type": "temperature_sensor",
    })
    now = datetime.now().isoformat()
    await client.post("/api/v1/data/report", json={
        "device_id": "data-002",
        "temperature": 30.0,
        "humidity": 55.0,
        "reported_at": now,
    })
    resp = await client.get("/api/v1/dashboard/trend")
    assert resp.status_code == 200
    trend = resp.json()["data"]
    assert len(trend) >= 1
    assert trend[0]["temperature"] == 30.0
