import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

os.environ["DB_TYPE"] = "sqlite"
os.environ["REDIS_ENABLED"] = "false"
os.environ["APP_ENV"] = "testing"

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import Base, async_session_factory, engine
from app.core.db_init import init_db
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
