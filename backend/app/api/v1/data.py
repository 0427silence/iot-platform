from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
from app.models.device import Device
from app.models.schemas import APIResponse, DeviceDataReport, DeviceDataResponse
from app.services import data_ingest_service
from sqlalchemy import select

router = APIRouter()


@router.post("/report", response_model=APIResponse)
async def report_device_data(payload: DeviceDataReport, db: AsyncSession = Depends(get_db)):
    # 验证设备是否存在
    result = await db.execute(select(Device).where(Device.device_id == payload.device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {payload.device_id} 未注册，请先注册设备")

    redis = await get_redis()
    record = await data_ingest_service.ingest_device_data(
        db=db,
        redis=redis,
        device_id=payload.device_id,
        temperature=payload.temperature,
        humidity=payload.humidity,
        battery_level=payload.battery_level,
        signal_strength=payload.signal_strength,
        extra_data=payload.extra_data,
        reported_at=payload.reported_at,
    )

    return APIResponse(
        message="数据上报成功",
        data={
            "id": record.id,
            "device_id": record.device_id,
            "reported_at": record.reported_at.isoformat() if record.reported_at else None,
        },
    )
