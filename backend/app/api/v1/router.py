from fastapi import APIRouter

from app.api.v1 import dashboard, data, devices

router = APIRouter(prefix="/api/v1")
router.include_router(devices.router, prefix="/devices", tags=["devices"])
router.include_router(data.router, prefix="/data", tags=["data"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
