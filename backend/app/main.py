from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.database import async_session_factory
from app.core.redis_client import close_redis
from app.services import alarm_rule_service, alarm_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_factory() as db:
        try:
            per_device, global_rules = await alarm_rule_service.load_active_rules(db)
            alarm_service.set_active_rules(per_device, global_rules)
        except Exception:
            pass

    yield

    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
