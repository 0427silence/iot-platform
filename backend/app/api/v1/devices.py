from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.schemas import APIResponse, DeviceCreate, DeviceResponse, DeviceUpdate
from app.services import device_service

router = APIRouter()


@router.get("", response_model=APIResponse)
async def list_devices(db: AsyncSession = Depends(get_db)):
    devices = await device_service.get_all_devices(db)
    return APIResponse(data=[DeviceResponse.model_validate(d).model_dump() for d in devices])


@router.get("/{device_id}", response_model=APIResponse)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    device = await device_service.get_device_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    return APIResponse(data=DeviceResponse.model_validate(device).model_dump())


@router.post("", response_model=APIResponse, status_code=201)
async def create_device(payload: DeviceCreate, db: AsyncSession = Depends(get_db)):
    existing = await device_service.get_device_by_device_id(db, payload.device_id)
    if existing:
        raise HTTPException(status_code=409, detail=f"设备 {payload.device_id} 已存在")
    device = await device_service.create_device(
        db,
        device_id=payload.device_id,
        device_name=payload.device_name,
        device_type=payload.device_type,
        location=payload.location,
        firmware_version=payload.firmware_version,
    )
    return APIResponse(data=DeviceResponse.model_validate(device).model_dump())


@router.put("/{device_id}", response_model=APIResponse)
async def update_device(device_id: str, payload: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    device = await device_service.get_device_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    device = await device_service.update_device(db, device, **payload.model_dump(exclude_none=True))
    return APIResponse(data=DeviceResponse.model_validate(device).model_dump())


@router.delete("/{device_id}", response_model=APIResponse)
async def delete_device(device_id: str, db: AsyncSession = Depends(get_db)):
    device = await device_service.get_device_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"设备 {device_id} 不存在")
    await device_service.delete_device(db, device)
    return APIResponse(message=f"设备 {device_id} 已删除")
