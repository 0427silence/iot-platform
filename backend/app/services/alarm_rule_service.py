from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import AlarmRule


async def load_active_rules(db: AsyncSession) -> tuple[dict[str, list[AlarmRule]], list[AlarmRule]]:
    result = await db.execute(select(AlarmRule).where(AlarmRule.is_active == 1))
    rows = list(result.scalars().all())

    per_device: dict[str, list[AlarmRule]] = {}
    global_rules: list[AlarmRule] = []

    for rule in rows:
        if rule.device_id is None:
            global_rules.append(rule)
        else:
            per_device.setdefault(rule.device_id, []).append(rule)

    return per_device, global_rules


async def list_alarm_rules(db: AsyncSession) -> list[AlarmRule]:
    result = await db.execute(select(AlarmRule).order_by(AlarmRule.updated_at.desc()))
    return list(result.scalars().all())


async def get_alarm_rule_by_id(db: AsyncSession, rule_id: int) -> AlarmRule | None:
    result = await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
    return result.scalar_one_or_none()


async def create_alarm_rule(db: AsyncSession, **kwargs) -> AlarmRule:
    rule = AlarmRule(**kwargs)
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return rule


async def update_alarm_rule(db: AsyncSession, rule: AlarmRule, **kwargs) -> AlarmRule:
    for key, value in kwargs.items():
        if value is not None and hasattr(rule, key):
            setattr(rule, key, value)
    await db.flush()
    await db.refresh(rule)
    return rule


async def delete_alarm_rule(db: AsyncSession, rule: AlarmRule) -> None:
    await db.delete(rule)
    await db.flush()
