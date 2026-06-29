from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_redis
from app.models.schemas import (
    APIResponse,
    AlarmLogResponse,
    AlarmRuleCreate,
    AlarmRuleResponse,
    AlarmRuleUpdate,
)
from app.services import alarm_rule_service, alarm_service

router = APIRouter()


# ==================== 告警规则 CRUD ====================

@router.get("/rules", response_model=APIResponse)
async def list_rules(db: AsyncSession = Depends(get_db)):
    rules = await alarm_rule_service.list_alarm_rules(db)
    return APIResponse(data=[AlarmRuleResponse.model_validate(r).model_dump() for r in rules])


@router.post("/rules", response_model=APIResponse, status_code=201)
async def create_rule(payload: AlarmRuleCreate, db: AsyncSession = Depends(get_db)):
    rule = await alarm_rule_service.create_alarm_rule(
        db, **payload.model_dump(exclude_none=True)
    )
    # 刷新内存缓存
    per_device, global_rules = await alarm_rule_service.load_active_rules(db)
    alarm_service.set_active_rules(per_device, global_rules)
    return APIResponse(data=AlarmRuleResponse.model_validate(rule).model_dump())


@router.put("/rules/{rule_id}", response_model=APIResponse)
async def update_rule(rule_id: int, payload: AlarmRuleUpdate, db: AsyncSession = Depends(get_db)):
    rule = await alarm_rule_service.get_alarm_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"告警规则 {rule_id} 不存在")
    rule = await alarm_rule_service.update_alarm_rule(
        db, rule, **payload.model_dump(exclude_none=True)
    )
    # 刷新内存缓存
    per_device, global_rules = await alarm_rule_service.load_active_rules(db)
    alarm_service.set_active_rules(per_device, global_rules)
    return APIResponse(data=AlarmRuleResponse.model_validate(rule).model_dump())


@router.delete("/rules/{rule_id}", response_model=APIResponse)
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    rule = await alarm_rule_service.get_alarm_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"告警规则 {rule_id} 不存在")
    await alarm_rule_service.delete_alarm_rule(db, rule)
    # 刷新内存缓存
    per_device, global_rules = await alarm_rule_service.load_active_rules(db)
    alarm_service.set_active_rules(per_device, global_rules)
    return APIResponse(message=f"告警规则 {rule_id} 已删除")


# ==================== 告警查询 ====================

@router.get("/active", response_model=APIResponse)
async def get_active_alarms(db: AsyncSession = Depends(get_db)):
    redis = await get_redis()
    alarms = await alarm_service.get_active_alarms(redis)
    if alarms:
        return APIResponse(data=alarms)
    # Redis 不可用或无数据 → MySQL 降级
    logs = await alarm_service.get_alarm_logs(db, limit=50, offset=0)
    return APIResponse(data=[
        {
            "device_id": log.device_id,
            "alarm_type": log.alarm_type,
            "message": log.message,
            "metric_value": log.metric_value,
            "threshold_value": log.threshold_value,
            "triggered_at": log.triggered_at.isoformat(),
        }
        for log in logs
        if log.status == 0
    ])


@router.get("/logs", response_model=APIResponse)
async def get_alarm_logs(
    device_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    logs = await alarm_service.get_alarm_logs(db, device_id=device_id, limit=limit, offset=offset)
    return APIResponse(data=[AlarmLogResponse.model_validate(log).model_dump() for log in logs])


@router.get("/feed", response_model=APIResponse)
async def get_alarm_feed(limit: int = Query(20, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    redis = await get_redis()
    feed = await alarm_service.get_alarm_feed(redis, limit=limit)
    if feed:
        return APIResponse(data=feed)
    # Redis 不可用或无数据 → MySQL 降级
    logs = await alarm_service.get_alarm_logs(db, limit=limit, offset=0)
    return APIResponse(data=[
        {
            "device_id": log.device_id,
            "alarm_type": log.alarm_type if log.status == 0 else f"{log.alarm_type}_resolved",
            "message": log.message if log.status == 0 else log.message.replace("超出阈值", "已恢复正常，曾超出阈值"),
            "metric_value": log.metric_value,
            "threshold_value": log.threshold_value,
            "triggered_at": log.triggered_at.isoformat(),
        }
        for log in logs
    ])
