from datetime import datetime

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import Device, DeviceData
from app.services import alarm_service


LUA_INGEST_SCRIPT = """
local status_key = KEYS[1]
local latest_key = KEYS[2]
local online_set = KEYS[3]
local fault_set = KEYS[4]
local summary_key = KEYS[5]

local device_id = ARGV[1]
local status = tonumber(ARGV[2])
local device_name = ARGV[3]
local device_type = ARGV[4]
local location = ARGV[5]
local firmware_version = ARGV[6]
local temperature = ARGV[7]
local humidity = ARGV[8]
local battery = ARGV[9]
local signal = ARGV[10]
local last_report_time = ARGV[11]

-- 更新设备状态 Hash（元信息字段）
redis.call('HSET', status_key,
    'status', ARGV[2],
    'device_name', device_name,
    'device_type', device_type,
    'location', location,
    'firmware_version', firmware_version,
    'last_report_time', last_report_time)
redis.call('EXPIRE', status_key, 300)

-- 更新设备最新数据 Hash（传感器值）
redis.call('HSET', latest_key,
    'temperature', temperature,
    'humidity', humidity,
    'battery', battery,
    'signal', signal,
    'last_report_time', last_report_time)
redis.call('EXPIRE', latest_key, 300)

-- 管理在线/故障集合
if status == 1 then
    redis.call('SADD', online_set, device_id)
    redis.call('SREM', fault_set, device_id)
elseif status == 2 then
    redis.call('SREM', online_set, device_id)
    redis.call('SADD', fault_set, device_id)
else
    redis.call('SREM', online_set, device_id)
    redis.call('SREM', fault_set, device_id)
end

-- 更新汇总时间戳
redis.call('HSET', summary_key, 'last_updated', last_report_time)

return 'OK'
"""


async def ingest_device_data(
    db: AsyncSession,
    redis: aioredis.Redis,
    device_id: str,
    temperature: float | None,
    humidity: float | None,
    battery_level: float | None,
    signal_strength: int | None,
    extra_data: dict | None,
    reported_at: datetime,
) -> DeviceData:
    # Step 1: 写入 MySQL 历史表
    record = DeviceData(
        device_id=device_id,
        temperature=temperature,
        humidity=humidity,
        battery_level=battery_level,
        signal_strength=signal_strength,
        extra_data=extra_data,
        reported_at=reported_at,
    )
    db.add(record)

    # Step 2: 更新设备主表状态
    from sqlalchemy import select as _select
    result = await db.execute(_select(Device).where(Device.device_id == device_id))
    device = result.scalar_one_or_none()
    device_name = device.device_name if device else ""
    device_type = device.device_type if device else ""
    location = device.location or ""
    firmware_version = device.firmware_version or ""

    if device:
        device.status = 1  # 在线
        device.last_online_at = datetime.now()

    await db.flush()

    # Step 3: Redis 原子更新（Redis 不可用时静默降级）
    if redis is not None:
        try:
            status_key = f"device:status:{device_id}"
            latest_key = f"device:latest:{device_id}"
            report_time_str = reported_at.strftime("%Y-%m-%dT%H:%M:%S")

            await redis.eval(
                LUA_INGEST_SCRIPT,
                5,
                status_key,
                latest_key,
                "devices:online",
                "devices:fault",
                "dashboard:summary",
                device_id,
                "1",  # status = online
                device_name,
                device_type,
                location,
                firmware_version,
                str(temperature) if temperature is not None else "",
                str(humidity) if humidity is not None else "",
                str(battery_level) if battery_level is not None else "",
                str(signal_strength) if signal_strength is not None else "",
                report_time_str,
            )
        except Exception:
            pass

    # Step 4: 评估告警规则
    await alarm_service.evaluate_rules(
        db=db,
        redis=redis,
        device_id=device_id,
        temperature=temperature,
        humidity=humidity,
        battery_level=battery_level,
        signal_strength=signal_strength,
    )

    return record
