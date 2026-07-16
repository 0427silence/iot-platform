"""
IoT 设备数据模拟器 — 独立脚本

模拟 5 台 IoT 设备定时上报传感器数据到 FastAPI 后端。
启动前请确保后端服务已在 localhost:8000 运行。

用法:
    python simulator.py
"""

import asyncio
import logging
import os
import random
import sys
from datetime import datetime

import httpx

# ============================================================
# 配置常量
# ============================================================
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")
REPORT_INTERVAL = 5  # 上报间隔（秒）
REQUEST_TIMEOUT = 10  # HTTP 请求超时（秒）

# 模拟设备列表
DEVICES = [
    {
        "device_id": "sensor-temp-001",
        "device_name": "温湿度计01",
        "device_type": "temperature_sensor",
        "location": "办公楼3层A区",
        "firmware_version": "v2.1.0",
        "temp_range": (25, 40),   # 温度偏高型
        "humid_range": (40, 65),
        "has_sensors": True,
    },
    {
        "device_id": "sensor-humid-002",
        "device_name": "湿度监测仪02",
        "device_type": "humidity_sensor",
        "location": "地下仓库B区",
        "firmware_version": "v1.8.3",
        "temp_range": (20, 30),
        "humid_range": (50, 80),   # 湿度偏高型
        "has_sensors": True,
    },
    {
        "device_id": "sensor-env-003",
        "device_name": "环境监测仪03",
        "device_type": "multi_sensor",
        "location": "室外气象站",
        "firmware_version": "v3.0.1",
        "temp_range": (20, 38),    # 均衡型
        "humid_range": (40, 75),
        "has_sensors": True,
    },
    {
        "device_id": "sensor-indoor-004",
        "device_name": "室内传感器04",
        "device_type": "multi_sensor",
        "location": "会议室C-301",
        "firmware_version": "v2.0.4",
        "temp_range": (20, 28),    # 温和型
        "humid_range": (45, 65),
        "has_sensors": True,
    },
    {
        "device_id": "sensor-gateway-005",
        "device_name": "网关设备05",
        "device_type": "gateway",
        "location": "数据中心机房",
        "firmware_version": "v4.2.0",
        "temp_range": None,         # 无传感器
        "humid_range": None,
        "has_sensors": False,
    },
]

# ============================================================
# 日志配置
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("simulator")


# ============================================================
# DeviceSimulator — 单设备模拟器
# ============================================================
class DeviceSimulator:
    def __init__(self, client: httpx.AsyncClient, config: dict):
        self.client = client
        self.config = config
        self.device_id = config["device_id"]
        self.device_name = config["device_name"]
        self.battery = 100.0  # 初始满电

    async def register(self) -> bool:
        """向平台注册设备。设备已存在则跳过（409）"""
        payload = {
            "device_id": self.config["device_id"],
            "device_name": self.config["device_name"],
            "device_type": self.config["device_type"],
            "location": self.config["location"],
            "firmware_version": self.config["firmware_version"],
        }
        try:
            resp = await self.client.post(
                f"{API_BASE}/devices", json=payload, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 201:
                logger.info("[%s] 设备注册成功", self.device_name)
                return True
            elif resp.status_code == 409:
                logger.info("[%s] 设备已注册，跳过", self.device_name)
                return True
            else:
                body = resp.json()
                logger.warning(
                    "[%s] 设备注册失败 HTTP %s: %s",
                    self.device_name, resp.status_code, body.get("detail", resp.text),
                )
                return False
        except httpx.RequestError as e:
            logger.error("[%s] 注册请求异常: %s", self.device_name, e)
            return False

    def _update_battery(self):
        """模拟电池消耗与更换"""
        self.battery -= random.uniform(0.01, 0.05)
        if self.battery < 15 and random.random() < 0.3:  # 30%概率更换电池
            self.battery = random.uniform(90, 100)
        self.battery = max(0, min(100, round(self.battery, 2)))

    def generate_data(self) -> dict:
        """生成随机传感器读数"""
        self._update_battery()
        signal = random.randint(-75, -30)

        payload: dict = {
            "device_id": self.device_id,
            "battery_level": self.battery,
            "signal_strength": signal,
            "reported_at": datetime.now().isoformat(),
        }

        if self.config["has_sensors"]:
            t_min, t_max = self.config["temp_range"]
            h_min, h_max = self.config["humid_range"]
            payload["temperature"] = round(random.uniform(t_min, t_max), 1)
            payload["humidity"] = round(random.uniform(h_min, h_max), 1)

        return payload

    async def report(self) -> bool:
        """上报一轮数据到后端"""
        data = self.generate_data()
        try:
            resp = await self.client.post(
                f"{API_BASE}/data/report", json=data, timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                body = resp.json()
                if body.get("code") == 0:
                    parts = []
                    if "temperature" in data:
                        parts.append(f"温度: {data['temperature']}℃")
                    if "humidity" in data:
                        parts.append(f"湿度: {data['humidity']}%")
                    parts.append(f"电量: {data['battery_level']}%")
                    parts.append(f"信号: {data['signal_strength']}dBm")
                    logger.info("[%s] ✓ 上报成功 | %s", self.device_name, " | ".join(parts))
                    return True
                else:
                    logger.warning(
                        "[%s] ✗ 上报失败: %s", self.device_name, body.get("message", body)
                    )
            else:
                logger.warning("[%s] ✗ HTTP %s", self.device_name, resp.status_code)
        except httpx.RequestError as e:
            logger.error("[%s] ✗ 网络异常: %s", self.device_name, e)
        return False

    async def run(self):
        """主循环：启动时注册 -> 循环上报"""
        ok = await self.register()
        if not ok:
            logger.warning("[%s] 注册未完成，仍尝试上报数据", self.device_name)

        while True:
            await self.report()
            await asyncio.sleep(REPORT_INTERVAL)


# ============================================================
# 入口
# ============================================================
async def main():
    logger.info("=" * 60)
    logger.info("IoT 设备模拟器启动中...")
    logger.info("后端地址: %s", API_BASE)
    logger.info("设备数量: %d", len(DEVICES))
    logger.info("上报间隔: %ds", REPORT_INTERVAL)
    logger.info("=" * 60)

    async with httpx.AsyncClient() as client:
        simulators = [DeviceSimulator(client, cfg) for cfg in DEVICES]
        await asyncio.gather(*(sim.run() for sim in simulators))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("模拟器已停止")
