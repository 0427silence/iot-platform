from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# Device
# ============================================================
class DeviceCreate(BaseModel):
    device_id: str = Field(..., max_length=64, description="设备唯一标识符")
    device_name: str = Field(..., max_length=128, description="设备名称")
    device_type: str = Field(..., max_length=64, description="设备类型")
    location: str | None = Field(None, max_length=256, description="安装位置")
    firmware_version: str | None = Field(None, max_length=32, description="固件版本")


class DeviceUpdate(BaseModel):
    device_name: str | None = Field(None, max_length=128)
    device_type: str | None = Field(None, max_length=64)
    location: str | None = Field(None, max_length=256)
    status: int | None = Field(None, ge=0, le=2, description="0=离线, 1=在线, 2=故障")
    firmware_version: str | None = Field(None, max_length=32)


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_name: str
    device_type: str
    location: str | None
    status: int
    firmware_version: str | None
    last_online_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DeviceStatusResponse(BaseModel):
    """从 Redis 实时读取的设备状态"""
    device_id: str
    device_name: str
    device_type: str
    location: str | None
    status: int
    firmware_version: str | None
    last_report_time: str | None
    temperature: float | None = None
    humidity: float | None = None
    battery: float | None = None
    signal: int | None = None


# ============================================================
# DeviceData
# ============================================================
class DeviceDataReport(BaseModel):
    """设备上报的遥测数据"""
    device_id: str = Field(..., max_length=64, description="设备唯一标识符")
    temperature: float | None = Field(None, description="温度(℃)")
    humidity: float | None = Field(None, description="湿度(%)")
    battery_level: float | None = Field(None, description="电量(%)")
    signal_strength: int | None = Field(None, description="信号强度(dBm)")
    extra_data: dict[str, Any] | None = Field(None, description="扩展传感器数据")
    reported_at: datetime = Field(default_factory=datetime.now, description="上报时间")


class DeviceDataResponse(BaseModel):
    id: int
    device_id: str
    temperature: float | None
    humidity: float | None
    battery_level: float | None
    signal_strength: int | None
    extra_data: dict | None
    reported_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Dashboard
# ============================================================
class DashboardSummary(BaseModel):
    total_devices: int = 0
    online_count: int = 0
    offline_count: int = 0
    fault_count: int = 0
    online_rate: float = 0.0
    avg_temperature: float | None = None
    avg_humidity: float | None = None
    last_updated: str | None = None


# ============================================================
# Common
# ============================================================
class APIResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None
