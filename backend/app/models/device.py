from datetime import datetime

from sqlalchemy import DateTime, DECIMAL, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID，自增")
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="设备唯一标识符")
    device_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="设备名称")
    device_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="设备类型")
    location: Mapped[str | None] = mapped_column(String(256), default=None, comment="设备安装位置")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="设备状态: 0=离线, 1=在线, 2=故障")
    firmware_version: Mapped[str | None] = mapped_column(String(32), default=None, comment="固件版本号")
    last_online_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="设备最后一次上线时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="记录创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="记录更新时间"
    )

    data_records = relationship("DeviceData", back_populates="device", cascade="all, delete-orphan")


class DeviceData(Base):
    __tablename__ = "device_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID，自增")
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), nullable=False, comment="设备唯一标识符"
    )
    temperature: Mapped[float | None] = mapped_column(DECIMAL(5, 2), default=None, comment="温度读数(℃)")
    humidity: Mapped[float | None] = mapped_column(DECIMAL(5, 2), default=None, comment="湿度读数(%)")
    battery_level: Mapped[float | None] = mapped_column(DECIMAL(5, 2), default=None, comment="电池电量(%)")
    signal_strength: Mapped[int | None] = mapped_column(Integer, default=None, comment="信号强度(dBm)")
    extra_data: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展传感器数据(JSON)")
    reported_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="设备上报数据的时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="服务端接收时间")

    device = relationship("Device", back_populates="data_records")


class AlarmRule(Base):
    __tablename__ = "alarm_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID，自增")
    device_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("devices.device_id"), default=None, comment="设备ID，NULL表示全局规则"
    )
    metric_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="监控指标名称")
    operator: Mapped[str] = mapped_column(String(4), nullable=False, comment="比较运算符")
    threshold_value: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, comment="告警阈值")
    is_active: Mapped[int] = mapped_column(Integer, default=1, comment="是否启用: 0=停用, 1=启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    device = relationship("Device", foreign_keys=[device_id])


class AlarmLog(Base):
    __tablename__ = "alarm_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID，自增")
    device_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("devices.device_id"), nullable=False, comment="设备ID"
    )
    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alarm_rules.id"), nullable=False, comment="触发的规则ID"
    )
    alarm_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="告警类型标识")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="告警消息内容")
    metric_value: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, comment="触发时的实际指标值")
    threshold_value: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, comment="触发时的阈值")
    status: Mapped[int] = mapped_column(Integer, default=0, comment="告警状态: 0=未处理, 1=已恢复")
    triggered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="告警触发时间")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="告警恢复时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="服务端记录时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
