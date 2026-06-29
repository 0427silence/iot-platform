from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.schemas import APIResponse, DashboardSummary
from app.services import device_service

router = APIRouter()


@router.get("/summary", response_model=APIResponse)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    total = await device_service.get_total_device_count(db)
    counts = await device_service.get_device_count_by_status(db)

    online = counts.get(1, 0)
    offline = counts.get(0, 0)
    fault = counts.get(2, 0)
    online_rate = round(online / total * 100, 2) if total > 0 else 0.0

    summary = DashboardSummary(
        total_devices=total,
        online_count=online,
        offline_count=offline,
        fault_count=fault,
        online_rate=online_rate,
    )

    return APIResponse(data=summary.model_dump())


@router.get("/devices/online", response_model=APIResponse)
async def get_online_devices(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select as _select
    from app.models.device import Device

    result = await db.execute(
        _select(Device).where(Device.status == 1).order_by(Device.last_online_at.desc())
    )
    devices = list(result.scalars().all())
    return APIResponse(data=[
        {"device_id": d.device_id, "device_name": d.device_name, "last_online_at": d.last_online_at.isoformat() if d.last_online_at else None}
        for d in devices
    ])


@router.get("/devices/{device_id}/latest", response_model=APIResponse)
async def get_device_latest_data(device_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import desc, select as _select
    from app.models.device import DeviceData

    result = await db.execute(
        _select(DeviceData)
        .where(DeviceData.device_id == device_id)
        .order_by(desc(DeviceData.reported_at))
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 暂无数据")
    return APIResponse(data={
        "device_id": record.device_id,
        "temperature": float(record.temperature) if record.temperature else None,
        "humidity": float(record.humidity) if record.humidity else None,
        "battery_level": float(record.battery_level) if record.battery_level else None,
        "signal_strength": record.signal_strength,
        "extra_data": record.extra_data,
        "reported_at": record.reported_at.isoformat() if record.reported_at else None,
    })
