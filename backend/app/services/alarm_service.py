import json
import operator as _op
from datetime import datetime

import redis.asyncio as aioredis
from sqlalchemy import desc, select as _select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import AlarmLog, AlarmRule

_OPERATOR_MAP = {
    ">": _op.gt,
    "<": _op.lt,
    ">=": _op.ge,
    "<=": _op.le,
    "==": _op.eq,
}

# 内存规则缓存
_active_rules: dict[str, list[AlarmRule]] = {}
_global_rules: list[AlarmRule] = []


_rules_loaded = False


def set_active_rules(per_device: dict[str, list[AlarmRule]], global_rules: list[AlarmRule]) -> None:
    global _active_rules, _global_rules, _rules_loaded
    _active_rules = per_device
    _global_rules = global_rules
    _rules_loaded = True


async def _ensure_rules_loaded(db: AsyncSession) -> None:
    global _rules_loaded
    if not _rules_loaded:
        from app.services import alarm_rule_service
        per_device, global_rules = await alarm_rule_service.load_active_rules(db)
        set_active_rules(per_device, global_rules)


def _evaluate_rule(metric_value: float | int | None, operator_str: str, threshold: float) -> bool:
    if metric_value is None:
        return False
    cmp_fn = _OPERATOR_MAP.get(operator_str)
    if cmp_fn is None:
        return False
    return cmp_fn(metric_value, threshold)


def _build_alarm_type(rule: AlarmRule) -> str:
    return f"{rule.metric_name}_{rule.operator}{rule.threshold_value}"


def _build_message(device_id: str, rule: AlarmRule, metric_value: float | int) -> str:
    unit_map = {
        "temperature": "℃",
        "humidity": "%",
        "battery_level": "%",
        "signal_strength": "dBm",
    }
    unit = unit_map.get(rule.metric_name, "")
    return (
        f"设备 {device_id} 指标 {rule.metric_name} 当前值 {metric_value}{unit}，"
        f"超出阈值 {rule.operator}{rule.threshold_value}{unit}"
    )


def _build_resolve_message(device_id: str, rule: AlarmRule, metric_value: float | int) -> str:
    unit_map = {
        "temperature": "℃",
        "humidity": "%",
        "battery_level": "%",
        "signal_strength": "dBm",
    }
    unit = unit_map.get(rule.metric_name, "")
    return (
        f"设备 {device_id} 指标 {rule.metric_name} 已恢复正常，"
        f"当前值 {metric_value}{unit}，阈值 {rule.operator}{rule.threshold_value}{unit}"
    )


async def evaluate_rules(
    db: AsyncSession,
    redis: aioredis.Redis,
    device_id: str,
    temperature: float | None,
    humidity: float | None,
    battery_level: float | None,
    signal_strength: int | None,
) -> None:
    await _ensure_rules_loaded(db)

    metrics = {
        "temperature": temperature,
        "humidity": humidity,
        "battery_level": battery_level,
        "signal_strength": signal_strength,
    }

    rules_to_check = list(_active_rules.get(device_id, [])) + list(_global_rules)
    if not rules_to_check:
        return

    for rule in rules_to_check:
        metric_value = metrics.get(rule.metric_name)
        if metric_value is None:
            continue

        alarm_key = f"alarms:state:{device_id}:{rule.id}"
        triggered = _evaluate_rule(metric_value, rule.operator, rule.threshold_value)

        if triggered:
            # 检查去重
            try:
                existing = await redis.hget(alarm_key, "status")
            except Exception:
                existing = None

            if existing == b"active" or existing == "active":
                continue

            now = datetime.now()
            alarm_type = _build_alarm_type(rule)
            message = _build_message(device_id, rule, metric_value)

            alarm_log = AlarmLog(
                device_id=device_id,
                rule_id=rule.id,
                alarm_type=alarm_type,
                message=message,
                metric_value=float(metric_value),
                threshold_value=rule.threshold_value,
                status=0,
                triggered_at=now,
            )
            db.add(alarm_log)
            await db.flush()

            try:
                await redis.hset(alarm_key, mapping={
                    "status": "active",
                    "triggered_at": now.isoformat(),
                })
                await redis.expire(alarm_key, 86400)

                feed_entry = {
                    "device_id": device_id,
                    "alarm_type": alarm_type,
                    "message": message,
                    "metric_value": float(metric_value),
                    "threshold_value": rule.threshold_value,
                    "triggered_at": now.isoformat(),
                }
                feed_json = json.dumps(feed_entry, ensure_ascii=False)
                await redis.lpush("alarms:feed", feed_json)
                await redis.ltrim("alarms:feed", 0, 49)
                await redis.hset("alarms:active", device_id, feed_json)
            except Exception:
                pass

        else:
            # 检查是否有活跃告警需要自动恢复
            try:
                existing = await redis.hget(alarm_key, "status")
            except Exception:
                existing = None

            if existing == b"active" or existing == "active":
                now = datetime.now()

                result = await db.execute(
                    _select(AlarmLog)
                    .where(
                        AlarmLog.device_id == device_id,
                        AlarmLog.rule_id == rule.id,
                        AlarmLog.status == 0,
                    )
                    .order_by(desc(AlarmLog.triggered_at))
                    .limit(1)
                )
                log_record = result.scalar_one_or_none()
                if log_record:
                    log_record.status = 1
                    log_record.resolved_at = now

                try:
                    await redis.hset(alarm_key, mapping={
                        "status": "resolved",
                        "resolved_at": now.isoformat(),
                    })
                    await redis.hdel("alarms:active", device_id)

                    resolve_entry = {
                        "device_id": device_id,
                        "alarm_type": f"{rule.metric_name}_resolved",
                        "message": _build_resolve_message(device_id, rule, metric_value),
                        "metric_value": float(metric_value),
                        "threshold_value": rule.threshold_value,
                        "triggered_at": now.isoformat(),
                    }
                    resolve_json = json.dumps(resolve_entry, ensure_ascii=False)
                    await redis.lpush("alarms:feed", resolve_json)
                    await redis.ltrim("alarms:feed", 0, 49)
                except Exception:
                    pass


async def get_active_alarms(redis: aioredis.Redis) -> list[dict]:
    try:
        data = await redis.hgetall("alarms:active")
    except Exception:
        return []
    result = []
    for raw in data.values():
        try:
            result.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            pass
    return result


async def get_alarm_feed(redis: aioredis.Redis, limit: int = 20) -> list[dict]:
    try:
        items = await redis.lrange("alarms:feed", 0, limit - 1)
    except Exception:
        return []
    result = []
    for raw in items:
        try:
            result.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            pass
    return result


async def get_alarm_logs(
    db: AsyncSession,
    device_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[AlarmLog]:
    stmt = _select(AlarmLog).order_by(desc(AlarmLog.triggered_at))
    if device_id:
        stmt = stmt.where(AlarmLog.device_id == device_id)
    stmt = stmt.limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())
