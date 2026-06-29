from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device


async def get_all_devices(db: AsyncSession) -> list[Device]:
    result = await db.execute(select(Device).order_by(Device.updated_at.desc()))
    return list(result.scalars().all())


async def get_device_by_device_id(db: AsyncSession, device_id: str) -> Device | None:
    result = await db.execute(select(Device).where(Device.device_id == device_id))
    return result.scalar_one_or_none()


async def create_device(db: AsyncSession, device_id: str, device_name: str, device_type: str,
                        location: str | None = None, firmware_version: str | None = None) -> Device:
    device = Device(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        location=location,
        firmware_version=firmware_version,
    )
    db.add(device)
    await db.flush()
    await db.refresh(device)
    return device


async def update_device(db: AsyncSession, device: Device, **kwargs) -> Device:
    for key, value in kwargs.items():
        if value is not None and hasattr(device, key):
            setattr(device, key, value)
    await db.flush()
    await db.refresh(device)
    return device


async def delete_device(db: AsyncSession, device: Device) -> None:
    await db.delete(device)
    await db.flush()


async def get_device_count_by_status(db: AsyncSession) -> dict[str, int]:
    result = await db.execute(
        select(Device.status, func.count(Device.id)).group_by(Device.status)
    )
    counts = {0: 0, 1: 0, 2: 0}
    for status, count in result.all():
        counts[status] = count
    return counts


async def get_total_device_count(db: AsyncSession) -> int:
    result = await db.execute(select(func.count(Device.id)))
    return result.scalar() or 0
