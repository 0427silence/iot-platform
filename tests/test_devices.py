import pytest


@pytest.mark.anyio
async def test_create_device(client):
    resp = await client.post("/api/v1/devices", json={
        "device_id": "test-001",
        "device_name": "Sensor A",
        "device_type": "temperature_sensor",
        "location": "Room 101",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["device_id"] == "test-001"


@pytest.mark.anyio
async def test_create_duplicate_device(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-002",
        "device_name": "Sensor B",
        "device_type": "humidity_sensor",
    })
    resp = await client.post("/api/v1/devices", json={
        "device_id": "test-002",
        "device_name": "Sensor B v2",
        "device_type": "humidity_sensor",
    })
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_list_devices(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-003",
        "device_name": "Sensor C",
        "device_type": "multi_sensor",
    })
    resp = await client.get("/api/v1/devices")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1


@pytest.mark.anyio
async def test_get_device_not_found(client):
    resp = await client.get("/api/v1/devices/nonexistent")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_device(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-004",
        "device_name": "Old Name",
        "device_type": "gateway",
    })
    resp = await client.put("/api/v1/devices/test-004", json={
        "device_name": "New Name",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["device_name"] == "New Name"


@pytest.mark.anyio
async def test_delete_device(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-005",
        "device_name": "To Delete",
        "device_type": "gateway",
    })
    resp = await client.delete("/api/v1/devices/test-005")
    assert resp.status_code == 200
    resp = await client.get("/api/v1/devices/test-005")
    assert resp.status_code == 404
