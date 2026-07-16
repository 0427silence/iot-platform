# IoT Platform Open-Source Showcase — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform existing IoT platform into a polished GitHub portfolio project with SQLite zero-dependency mode, React+TS+Vite frontend, English README, and test coverage.

**Architecture:** FastAPI backend with dual-database support (MySQL+Redis via Docker, or SQLite standalone). React 18 + TypeScript + Vite frontend with Tailwind CSS, Recharts, and Lucide icons. Two launch paths: `make dev` (SQLite, no Docker) and `docker compose up` (full stack).

**Tech Stack:** Python 3.11+, FastAPI 0.115, SQLAlchemy 2.0 async, aiomysql, aiosqlite, Redis 5.2, React 18, TypeScript 5, Vite 5, Tailwind CSS 3, Recharts 2, Lucide React

## Global Constraints

- Python >= 3.11, Node >= 18
- Backend dependencies in `backend/requirements.txt`
- Frontend dependencies via npm (Vite project)
- Two launch modes: `make dev` (SQLite) and `docker compose up` (MySQL+Redis)
- All backend API paths unchanged (`/api/v1/*`)
- No authentication system
- English README with badges
- Deep color theme for frontend (preserved from current design)

---

### Task 1: Add SQLite support to backend

**Files:**
- Modify: `backend/app/core/config.py:4-60`
- Modify: `backend/app/core/database.py:1-38`
- Create: `backend/app/core/db_init.py`

**Interfaces:**
- Consumes: `settings` from `config.py`
- Produces: `DB_TYPE: str`, `database_url` returning MySQL or SQLite URL, `engine` and `async_session_factory` unchanged signatures, `init_db()` async function

- [ ] **Step 1: Add DB_TYPE config field**

Edit `backend/app/core/config.py`, add after `DB_ECHO`:

```python
    # --- Database type: "mysql" | "sqlite" ---
    DB_TYPE: str = "mysql"
```

- [ ] **Step 2: Update database_url property to support SQLite**

Edit `backend/app/core/config.py`, replace the `database_url` property:

```python
    @property
    def database_url(self) -> str:
        if self.DB_TYPE == "sqlite":
            return "sqlite+aiosqlite:///./data/iot.db"
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )
```

- [ ] **Step 3: Update database.py to handle SQLite engine args**

Edit `backend/app/core/database.py`, replace the engine creation block:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

if settings.DB_TYPE == "sqlite":
    _engine_kwargs: dict = {"echo": settings.DB_ECHO}
else:
    _engine_kwargs: dict = {
        "echo": settings.DB_ECHO,
        "pool_size": settings.DB_POOL_SIZE,
        "pool_recycle": settings.DB_POOL_RECYCLE,
    }
    if settings.DB_SSL:
        _engine_kwargs["connect_args"] = {"ssl": True}

engine = create_async_engine(settings.database_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- [ ] **Step 4: Create db_init.py for SQLite auto-table creation**

Create `backend/app/core/db_init.py`:

```python
"""Auto-create tables for SQLite mode on startup."""
from app.core.config import settings
from app.core.database import Base, engine


async def init_db() -> None:
    if settings.DB_TYPE != "sqlite":
        return
    import os
    os.makedirs("data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 5: Wire init_db into lifespan**

Edit `backend/app/main.py`, add import and call:

```python
from app.core.db_init import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    async with async_session_factory() as db:
        try:
            per_device, global_rules = await alarm_rule_service.load_active_rules(db)
            alarm_service.set_active_rules(per_device, global_rules)
        except Exception:
            pass

    yield

    await close_redis()
```

- [ ] **Step 6: Add aiosqlite to requirements**

Edit `backend/requirements.txt`, add after `aiomysql`:

```
aiosqlite==0.20.0
```

- [ ] **Step 7: Test SQLite mode**

```bash
cd backend && pip install aiosqlite && DB_TYPE=sqlite uvicorn app.main:app --port 8000 &
sleep 3
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"IoT-Platform"}
curl http://localhost:8000/api/v1/devices
# Expected: {"code":0,"message":"ok","data":[]}
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/config.py backend/app/core/database.py backend/app/core/db_init.py backend/app/main.py backend/requirements.txt
git commit -m "feat: add SQLite support for zero-dependency quick start mode"
```

---

### Task 2: Make Redis optional (graceful disable)

**Files:**
- Modify: `backend/app/core/redis_client.py:1-29`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/api/v1/data.py:13-42`
- Modify: `backend/app/api/v1/alarms.py`

**Interfaces:**
- Consumes: `settings` from config
- Produces: `get_redis()` may return None; `close_redis()` is a no-op when disabled; `RedisDisabledError` exception class

- [ ] **Step 1: Add REDIS_ENABLED to config**

Edit `backend/app/core/config.py`, add after `REDIS_SSL`:

```python
    REDIS_ENABLED: bool = True
```

- [ ] **Step 2: Update redis_client.py to return None when disabled**

Edit `backend/app/core/redis_client.py`:

```python
import redis.asyncio as aioredis

from app.core.config import settings

_redis: aioredis.Redis | None = None
_redis_disabled = False


async def get_redis() -> aioredis.Redis | None:
    global _redis, _redis_disabled
    if not settings.REDIS_ENABLED:
        _redis_disabled = True
        return None
    if _redis is None and not _redis_disabled:
        try:
            _redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                db=settings.REDIS_DB,
                ssl=settings.REDIS_SSL,
                ssl_cert_reqs=None if settings.REDIS_SSL else "required",
                max_connections=settings.REDIS_POOL_MAX_CONNECTIONS,
                decode_responses=True,
            )
        except Exception:
            _redis_disabled = True
            return None
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.close()
        _redis = None
```

- [ ] **Step 3: Update data.py endpoint to handle None redis**

Edit `backend/app/api/v1/data.py`, change line 21 from `redis = await get_redis()`:

```python
    redis = await get_redis()
    if redis is None:
        raise HTTPException(status_code=503, detail="Redis unavailable, data ingest requires Redis")
```

Wait — actually, looking at the ingest service, Redis is used for caching and alarms. The MySQL fallback works for most things. But the Redis Lua script is core to the caching layer. Let me reconsider...

Actually, the data_ingest_service already wraps Redis operations in try/except. So if Redis is None, we can pass None and let the service handle it — but the service calls `redis.eval(...)` which will raise AttributeError on None.

Better approach: wrap the Redis calls in data_ingest_service so they check `if redis is None: return/continue`. The service already has try/except for Redis errors, but passing None will cause AttributeError on `redis.eval(...)` not a connection error.

Let me update the approach. Instead of modifying the endpoint, I'll update the service.

Edit `backend/app/services/data_ingest_service.py`, wrap the Redis block:

At line 106, change the try block to skip if redis is None:

```python
    # Step 3: Redis atomic update (skip if Redis disabled)
    if redis is not None:
        try:
            status_key = f"device:status:{device_id}"
            latest_key = f"device:latest:{device_id}"
            # ... existing code unchanged ...
        except Exception:
            pass
```

And in alarm_service.py, all redis calls are already in try/except. But we need to handle `redis.hget(...)` when redis is None. Let me update the calls there too.

Actually, the simplest approach: in `alarm_service.py`, add a check at the start of `evaluate_rules`:

```python
async def evaluate_rules(db, redis, device_id, ...):
    # ... existing code ...
    # Skip Redis-dependent dedup if redis is None
    _redis_available = redis is not None
```

Then change each `try: await redis.X(...)` block to also check `_redis_available`.

This is getting complex. Let me simplify with a different approach: make a null Redis wrapper or just add `if redis is None: return` guards at each try block.

OK let me keep this task simpler. I'll update the plan to:
1. Make redis_client return None when disabled
2. In data_ingest_service, wrap the Redis block with `if redis is not None`
3. In alarm_service, the existing try/except already handles connection errors, but we need AttributeError too. Add `except (Exception, AttributeError)` or check `if redis is None`.

Let me rewrite this task more cleanly.

Actually, let me just add `if redis is None: return` at the relevant points. Or better: in data_ingest, where we pass redis to evaluate_rules, just skip the Redis parts if redis is None. The evaluate_rules function uses Redis only for dedup and feed - if redis is None, it should still create alarm logs in MySQL.

Let me simplify. The cleanest fix:

In `data_ingest_service.py`:
```python
    # Step 3: Redis atomic update
    if redis is not None:
        try:
            # ...existing redis code...
        except Exception:
            pass
```

In `alarm_service.py` `evaluate_rules`:
For each `try: await redis.X(...)` block, add `if redis is None: continue/pass` before it.

Actually, the simplest and most robust approach: make all redis calls in alarm_service check for None first. Let me just update the except clauses to catch AttributeError too.

OK this is getting too complex for the plan. Let me write it more simply:

- [ ] **Step 3: Update data_ingest_service to skip Redis when None**

Edit `backend/app/services/data_ingest_service.py`, indent the existing Redis code block inside `if redis is not None:`:

Find at line 106:
```python
    # Step 3: Redis 原子更新（Redis 不可用时静默降级）
    try:
```

Replace the entire Step 3 block (lines 106-132) with:
```python
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
                "1",
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
```

- [ ] **Step 4: Update alarm_service to handle None redis**

Edit `backend/app/services/alarm_service.py`.

In `evaluate_rules`, for each `try: await redis.X(...)` block, wrap with `if redis is not None:`.

The two blocks are:
- Lines 115-160: the triggered alarm dedup + feed block
- Lines 164-206: the resolved alarm block

Change line 115 from:
```python
            try:
                existing = await redis.hget(alarm_key, "status")
            except Exception:
                existing = None
```
To:
```python
            if redis is not None:
                try:
                    existing = await redis.hget(alarm_key, "status")
                except Exception:
                    existing = None
            else:
                existing = None
```

Similarly, change the Redis writes block (lines 140-160) from:
```python
            try:
                await redis.hset(alarm_key, mapping={...})
```
To:
```python
            if redis is not None:
                try:
                    await redis.hset(alarm_key, mapping={...})
                    ...
                except Exception:
                    pass
```

And the resolution block (lines 164-206) — add `if redis is not None:` around the redis calls.

- [ ] **Step 5: Update alarms API endpoints to handle None redis**

Edit `backend/app/api/v1/alarms.py`.

In `get_active_alarms` (line 64), change:
```python
    redis = await get_redis()
    alarms = await alarm_service.get_active_alarms(redis)
    if alarms:
        return APIResponse(data=alarms)
    # Redis 不可用或无数据 → MySQL 降级
```
To:
```python
    redis = await get_redis()
    if redis is not None:
        alarms = await alarm_service.get_active_alarms(redis)
        if alarms:
            return APIResponse(data=alarms)
    # Redis 不可用或无数据 → MySQL/SQLite 降级
```

Same pattern for `get_alarm_feed` (line 97).

Also update `get_redis` dependency in `deps.py` to handle `None`:
```python
async def get_redis() -> aioredis.Redis | None:
    return await _get_redis()
```

And update `data.py` endpoint (line 21) to pass None redis to ingest:

```python
    redis = await get_redis()
    record = await data_ingest_service.ingest_device_data(
        db=db,
        redis=redis,
        ...
    )
```

The redis parameter already has `aioredis.Redis` type hint. Change to `aioredis.Redis | None`.

- [ ] **Step 6: Test Redis-disabled mode**

```bash
DB_TYPE=sqlite REDIS_ENABLED=false uvicorn app.main:app --port 8000 &
sleep 3
curl http://localhost:8000/health
# register a device
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-001","device_name":"Test","device_type":"sensor"}'
# report data
curl -X POST http://localhost:8000/api/v1/data/report \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test-001","temperature":25.5,"humidity":60.0,"reported_at":"2026-07-16T12:00:00"}'
# Expected: {"code":0,"message":"数据上报成功",...}
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/redis_client.py backend/app/core/config.py backend/app/services/data_ingest_service.py backend/app/services/alarm_service.py backend/app/api/v1/alarms.py backend/app/api/v1/data.py backend/app/api/deps.py
git commit -m "feat: make Redis optional with graceful degradation"
```

---

### Task 3: Clean up Vercel/Render artifacts

**Files:**
- Remove: `api/index.py`
- Remove: `vercel.json`
- Remove: `frontend/vercel.json`
- Modify: `Makefile`

- [ ] **Step 1: Remove Vercel serverless entrypoint**

```bash
rm api/index.py
# If api/ is now empty:
rmdir api
```

- [ ] **Step 2: Remove vercel configs**

```bash
rm vercel.json
rm -f frontend/vercel.json
```

- [ ] **Step 3: Remove Vercel from .gitignore if present**

Check `backend/.gitignore` is already clean — `.vercel` was in root `.gitignore` which is correct.

- [ ] **Step 4: Update Makefile — add dev-simple target and clean up**

Rewrite `Makefile`:

```makefile
.PHONY: help dev dev-full install db-init db-test lint clean

help:  ## Show all commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:  ## Install Python dependencies
	cd backend && pip install -r requirements.txt

dev:  ## Start backend (SQLite, no Docker needed) + frontend dev server
	@echo "Starting backend (SQLite mode)..."
	cd backend && DB_TYPE=sqlite REDIS_ENABLED=false uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev

dev-full:  ## Start with Docker (MySQL + Redis + backend)
	docker compose up --build

db-init:  ## Initialize MySQL tables
	@mysql -u root -p < db/init.sql

db-test:  ## Test database connection
	python scripts/test_db.py

lint:  ## Run code checks
	ruff check backend/ scripts/

clean:  ## Clean temp files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned."
```

- [ ] **Step 5: Add backend/data/ to .gitignore**

Append to `.gitignore`:
```
backend/data/
```

- [ ] **Step 6: Commit**

```bash
git rm api/index.py vercel.json frontend/vercel.json 2>/dev/null
git add Makefile .gitignore
git commit -m "chore: remove Vercel/Render artifacts, add SQLite quick-start mode"
```

---

### Task 4: Add backend tests

**Files:**
- Create: `tests/test_devices.py`
- Create: `tests/test_dashboard.py`
- Create: `tests/test_data.py`
- Create: `tests/conftest_sqlite.py`

- [ ] **Step 1: Create SQLite test fixture**

Create `tests/conftest_sqlite.py`:

```python
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
```

- [ ] **Step 2: Write device API tests**

Create `tests/test_devices.py`:

```python
import pytest


@pytest.mark.anyio
async def test_create_device(client):
    resp = await client.post("/api/v1/devices", json={
        "device_id": "test-001",
        "device_name": "Sensor A",
        "device_type": "temperature_sensor",
        "location": "Room 101",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["device_id"] == "test-001"


@pytest.mark.anyio
async def test_create_duplicate_device(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-002",
        "device_name": "Sensor B",
        "device_type": "humidity_sensor",
    })
    resp = await client.post("/api/v1/devices", json={
        "device_id": "test-002",
        "device_name": "Sensor B v2",
        "device_type": "humidity_sensor",
    })
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_list_devices(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-003",
        "device_name": "Sensor C",
        "device_type": "multi_sensor",
    })
    resp = await client.get("/api/v1/devices")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) >= 1


@pytest.mark.anyio
async def test_get_device_not_found(client):
    resp = await client.get("/api/v1/devices/nonexistent")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_update_device(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-004",
        "device_name": "Old Name",
        "device_type": "gateway",
    })
    resp = await client.put("/api/v1/devices/test-004", json={
        "device_name": "New Name",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["device_name"] == "New Name"


@pytest.mark.anyio
async def test_delete_device(client):
    await client.post("/api/v1/devices", json={
        "device_id": "test-005",
        "device_name": "To Delete",
        "device_type": "gateway",
    })
    resp = await client.delete("/api/v1/devices/test-005")
    assert resp.status_code == 200
    resp = await client.get("/api/v1/devices/test-005")
    assert resp.status_code == 404
```

- [ ] **Step 3: Write dashboard tests**

Create `tests/test_dashboard.py`:

```python
import pytest


@pytest.mark.anyio
async def test_dashboard_summary_empty(client):
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert data["data"]["total_devices"] == 0


@pytest.mark.anyio
async def test_dashboard_summary_with_devices(client):
    await client.post("/api/v1/devices", json={
        "device_id": "dash-001",
        "device_name": "Device 1",
        "device_type": "sensor",
    })
    resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["total_devices"] == 1


@pytest.mark.anyio
async def test_trend_empty(client):
    resp = await client.get("/api/v1/dashboard/trend")
    assert resp.status_code == 200
    assert resp.json()["data"] == []
```

- [ ] **Step 4: Add pytest and httpx to requirements**

Add to `backend/requirements.txt`:
```
pytest==8.3.4
pytest-asyncio==0.24.0
httpx==0.28.1
```

(httpx is already there, so just add pytest ones.)

- [ ] **Step 5: Run tests**

```bash
cd backend && pip install pytest pytest-asyncio && cd ..
pytest tests/ -v
# Expected: all tests pass
```

- [ ] **Step 6: Commit**

```bash
git add tests/ backend/requirements.txt
git commit -m "test: add API tests with SQLite backend"
```

---

### Task 5: Scaffold React + TypeScript + Vite frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/vite-env.d.ts`

- [ ] **Step 1: Create package.json**

Create `frontend/package.json`:

```json
{
  "name": "iot-platform-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "lucide-react": "^0.454.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0",
    "recharts": "^2.13.3"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.15",
    "typescript": "~5.6.2",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

Create `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 3: Create tsconfig files**

Create `frontend/tsconfig.json`:

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

Create `frontend/tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["src"]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create Tailwind config**

Create `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        darkBg: '#0b0f19',
        cardBg: '#161b26',
        borderBg: '#232d3f',
      },
    },
  },
  plugins: [],
}
```

Create `frontend/postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 5: Create index.html entry**

Create `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>IoT Platform — Device Monitoring Dashboard</title>
  </head>
  <body class="bg-darkBg text-gray-100">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create CSS entry**

Create `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.glass-card {
  background: rgba(22, 27, 38, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(35, 45, 63, 0.5);
}
```

- [ ] **Step 7: Create React entry point**

Create `frontend/src/main.tsx`:

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

Create `frontend/src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />
```

- [ ] **Step 8: Create App shell**

Create `frontend/src/App.tsx`:

```tsx
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Devices from './pages/Devices'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/devices" element={<Devices />} />
      </Route>
    </Routes>
  )
}
```

- [ ] **Step 9: Create Layout component**

Create `frontend/src/components/Layout.tsx`:

```tsx
import { Outlet, NavLink } from 'react-router-dom'
import { Cpu, LayoutDashboard, Smartphone } from 'lucide-react'

export default function Layout() {
  return (
    <div className="min-h-screen bg-darkBg">
      <header className="border-b border-borderBg bg-cardBg/50 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <NavLink to="/" className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600/20 text-blue-500 rounded-lg">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider text-white">IoT Platform</h1>
            <p className="text-xs text-gray-400">Device Monitoring Dashboard</p>
          </div>
        </NavLink>
        <nav className="flex items-center space-x-4">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white'
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/devices"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white'
              }`
            }
          >
            <Smartphone className="w-4 h-4" />
            <span>Devices</span>
          </NavLink>
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
```

- [ ] **Step 10: Install dependencies and verify**

```bash
cd frontend && npm install && npm run dev
# Expected: Vite dev server starts on port 3000
```

- [ ] **Step 11: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React + TypeScript + Vite frontend"
```

---

### Task 6: Build frontend API layer and hooks

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/hooks/usePolling.ts`
- Create: `frontend/src/hooks/useApi.ts`

- [ ] **Step 1: Create API client**

Create `frontend/src/lib/api.ts`:

```typescript
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `HTTP ${res.status}`)
  }
  const json: ApiResponse<T> = await res.json()
  if (json.code !== 0) {
    throw new Error(json.message)
  }
  return json.data
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

// Types
export interface Device {
  id: number
  device_id: string
  device_name: string
  device_type: string
  location: string | null
  status: number
  firmware_version: string | null
  last_online_at: string | null
  created_at: string
  updated_at: string
}

export interface DashboardSummary {
  total_devices: number
  online_count: number
  offline_count: number
  fault_count: number
  online_rate: number
  avg_temperature: number | null
  avg_humidity: number | null
  last_updated: string | null
}

export interface TrendPoint {
  device_id: string
  temperature: number | null
  humidity: number | null
  reported_at: string
}

export interface OnlineDevice {
  device_id: string
  device_name: string
  last_online_at: string | null
}

export interface AlarmEntry {
  device_id: string
  alarm_type: string
  message: string
  metric_value: number
  threshold_value: number
  triggered_at: string
}
```

- [ ] **Step 2: Create usePolling hook**

Create `frontend/src/hooks/usePolling.ts`:

```typescript
import { useEffect, useRef, useCallback, useState } from 'react'

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
): { data: T | null; error: string | null; loading: boolean } {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const mounted = useRef(true)

  const tick = useCallback(async () => {
    try {
      const result = await fetcher()
      if (mounted.current) {
        setData(result)
        setError(null)
      }
    } catch (e) {
      if (mounted.current) {
        setError(e instanceof Error ? e.message : 'Unknown error')
      }
    } finally {
      if (mounted.current) {
        setLoading(false)
      }
    }
  }, [fetcher])

  useEffect(() => {
    mounted.current = true
    tick()
    const id = setInterval(tick, intervalMs)
    return () => {
      mounted.current = false
      clearInterval(id)
    }
  }, [tick, intervalMs])

  return { data, error, loading }
}
```

- [ ] **Step 3: Create useApi hook (one-shot fetch)**

Create `frontend/src/hooks/useApi.ts`:

```typescript
import { useEffect, useState } from 'react'

export function useApi<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result)
          setError(null)
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Unknown error')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [fetcher])

  return { data, error, loading }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/ frontend/src/hooks/
git commit -m "feat: add API client and data hooks"
```

---

### Task 7: Build Dashboard page with components

**Files:**
- Create: `frontend/src/components/StatCard.tsx`
- Create: `frontend/src/components/TrendChart.tsx`
- Create: `frontend/src/components/LoadingSkeleton.tsx`
- Create: `frontend/src/components/AlarmBadge.tsx`
- Create: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Create StatCard**

Create `frontend/src/components/StatCard.tsx`:

```tsx
import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: 'up' | 'down'
}

export default function StatCard({ title, value, subtitle, icon: Icon, trend }: StatCardProps) {
  return (
    <div className="glass-card rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold mt-1 text-white">{value}</p>
          {subtitle && (
            <p className={`text-xs mt-1 ${trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-rose-400' : 'text-gray-500'}`}>
              {subtitle}
            </p>
          )}
        </div>
        <div className="p-2 bg-blue-600/10 rounded-lg">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create TrendChart**

Create `frontend/src/components/TrendChart.tsx`:

```tsx
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts'
import type { TrendPoint } from '../lib/api'

interface TrendChartProps {
  data: TrendPoint[]
}

export default function TrendChart({ data }: TrendChartProps) {
  if (data.length === 0) {
    return (
      <div className="glass-card rounded-xl p-6 text-center text-gray-500">
        No trend data yet — start the simulator to see charts
      </div>
    )
  }

  const chartData = data.map((d) => ({
    time: new Date(d.reported_at).toLocaleTimeString(),
    temperature: d.temperature,
    humidity: d.humidity,
  }))

  return (
    <div className="glass-card rounded-xl p-6">
      <h3 className="text-sm font-semibold text-gray-400 mb-4">Temperature & Humidity (24h)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#232d3f" />
          <XAxis dataKey="time" stroke="#4b5563" tick={{ fontSize: 12 }} />
          <YAxis yAxisId="temp" stroke="#60a5fa" tick={{ fontSize: 12 }} unit="°C" />
          <YAxis yAxisId="humid" orientation="right" stroke="#34d399" tick={{ fontSize: 12 }} unit="%" />
          <Tooltip
            contentStyle={{ background: '#161b26', border: '1px solid #232d3f', borderRadius: '8px' }}
            labelStyle={{ color: '#9ca3af' }}
          />
          <Legend />
          <Line yAxisId="temp" type="monotone" dataKey="temperature" stroke="#60a5fa" dot={false} name="Temperature °C" />
          <Line yAxisId="humid" type="monotone" dataKey="humidity" stroke="#34d399" dot={false} name="Humidity %" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
```

- [ ] **Step 3: Create LoadingSkeleton**

Create `frontend/src/components/LoadingSkeleton.tsx`:

```tsx
export default function LoadingSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-card rounded-xl p-5 animate-pulse">
          <div className="h-4 bg-gray-700 rounded w-1/2 mb-3" />
          <div className="h-8 bg-gray-700 rounded w-1/3" />
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 4: Create AlarmBadge**

Create `frontend/src/components/AlarmBadge.tsx`:

```tsx
import { Bell } from 'lucide-react'

interface AlarmBadgeProps {
  count: number
  onClick: () => void
}

export default function AlarmBadge({ count, onClick }: AlarmBadgeProps) {
  if (count === 0) return null

  return (
    <button
      onClick={onClick}
      className="relative flex items-center space-x-2 bg-rose-500/10 border border-rose-500/20 px-3 py-1.5 rounded-full text-rose-400 text-xs cursor-pointer"
    >
      <span className="absolute -top-0.5 -right-0.5 flex h-3 w-3">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-500 opacity-75" />
        <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500" />
      </span>
      <Bell className="w-3.5 h-3.5" />
      <span>{count} alarm{count > 1 ? 's' : ''}</span>
    </button>
  )
}
```

- [ ] **Step 5: Create Dashboard page**

Create `frontend/src/pages/Dashboard.tsx`:

```tsx
import { useCallback, useState } from 'react'
import { Wifi, WifiOff, AlertTriangle, Activity } from 'lucide-react'
import { api, type DashboardSummary, type TrendPoint, type OnlineDevice, type AlarmEntry } from '../lib/api'
import { usePolling } from '../hooks/usePolling'
import StatCard from '../components/StatCard'
import TrendChart from '../components/TrendChart'
import LoadingSkeleton from '../components/LoadingSkeleton'
import AlarmBadge from '../components/AlarmBadge'

export default function Dashboard() {
  const [showAlarms, setShowAlarms] = useState(false)

  const fetchSummary = useCallback(() => api.get<DashboardSummary>('/dashboard/summary'), [])
  const fetchTrend = useCallback(() => api.get<TrendPoint[]>('/dashboard/trend?limit=30'), [])
  const fetchOnline = useCallback(() => api.get<OnlineDevice[]>('/dashboard/devices/online'), [])
  const fetchAlarms = useCallback(() => api.get<AlarmEntry[]>('/alarms/active'), [])

  const summary = usePolling(fetchSummary, 5000)
  const trend = usePolling(fetchTrend, 5000)
  const online = usePolling(fetchOnline, 5000)
  const alarms = usePolling(fetchAlarms, 10000)

  if (summary.loading) {
    return <LoadingSkeleton />
  }

  const s = summary.data
  const activeAlarms = alarms.data || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Dashboard</h2>
        <AlarmBadge count={activeAlarms.length} onClick={() => setShowAlarms(!showAlarms)} />
      </div>

      {showAlarms && activeAlarms.length > 0 && (
        <div className="glass-card rounded-xl p-4 border-rose-500/30">
          <h3 className="text-sm font-semibold text-rose-400 mb-3">Active Alarms</h3>
          <div className="space-y-2">
            {activeAlarms.map((a, i) => (
              <div key={i} className="flex items-center justify-between text-sm bg-rose-500/5 rounded-lg p-3">
                <span className="text-gray-300">{a.message}</span>
                <span className="text-gray-500 text-xs">
                  {new Date(a.triggered_at).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Devices" value={s?.total_devices ?? 0} icon={Activity} />
        <StatCard title="Online" value={s?.online_count ?? 0} icon={Wifi} trend="up" />
        <StatCard title="Offline" value={s?.offline_count ?? 0} icon={WifiOff} trend="down" />
        <StatCard title="Alerts" value={activeAlarms.length} icon={AlertTriangle} trend={activeAlarms.length > 0 ? 'down' : undefined} />
      </div>

      <TrendChart data={trend.data || []} />

      <div className="glass-card rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-400 mb-4">Online Devices</h3>
        {online.data && online.data.length > 0 ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-500 border-b border-borderBg">
                <th className="text-left py-2">Device</th>
                <th className="text-left py-2">Last Seen</th>
              </tr>
            </thead>
            <tbody>
              {online.data.map((d) => (
                <tr key={d.device_id} className="border-b border-borderBg/50">
                  <td className="py-2 text-white">{d.device_name}</td>
                  <td className="py-2 text-gray-400">
                    {d.last_online_at ? new Date(d.last_online_at).toLocaleTimeString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-gray-500 text-center py-4">No devices online — start the simulator</p>
        )}
      </div>

      {summary.error && (
        <div className="glass-card rounded-xl p-4 border-rose-500/30 text-rose-400 text-sm">
          Backend error: {summary.error}. Make sure the API server is running on port 8000.
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ frontend/src/pages/
git commit -m "feat: add Dashboard page with stat cards, trend chart, and alarm badge"
```

---

### Task 8: Build Devices page

**Files:**
- Create: `frontend/src/pages/Devices.tsx`
- Create: `frontend/src/components/DeviceFormModal.tsx`

- [ ] **Step 1: Create DeviceFormModal**

Create `frontend/src/components/DeviceFormModal.tsx`:

```tsx
import { useState } from 'react'
import { X } from 'lucide-react'
import type { Device } from '../lib/api'

interface DeviceFormModalProps {
  device?: Device | null
  onClose: () => void
  onSubmit: (data: { device_id: string; device_name: string; device_type: string; location: string }) => Promise<void>
}

export default function DeviceFormModal({ device, onClose, onSubmit }: DeviceFormModalProps) {
  const [deviceId, setDeviceId] = useState(device?.device_id || '')
  const [name, setName] = useState(device?.device_name || '')
  const [type, setType] = useState(device?.device_type || 'temperature_sensor')
  const [location, setLocation] = useState(device?.location || '')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await onSubmit({ device_id: deviceId, device_name: name, device_type: type, location })
      onClose()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-cardBg border border-borderBg rounded-xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">{device ? 'Edit Device' : 'Add Device'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Device ID</label>
            <input
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              disabled={!!device}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Type</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="temperature_sensor">Temperature Sensor</option>
              <option value="humidity_sensor">Humidity Sensor</option>
              <option value="multi_sensor">Multi Sensor</option>
              <option value="gateway">Gateway</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Location</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-darkBg border border-borderBg rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : device ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create Devices page**

Create `frontend/src/pages/Devices.tsx`:

```tsx
import { useCallback, useState } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { api, type Device } from '../lib/api'
import { usePolling } from '../hooks/usePolling'
import DeviceFormModal from '../components/DeviceFormModal'
import LoadingSkeleton from '../components/LoadingSkeleton'

export default function Devices() {
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState<Device | null>(null)
  const [search, setSearch] = useState('')

  const fetchDevices = useCallback(() => api.get<Device[]>('/devices'), [])
  const { data: devices, error, loading } = usePolling(fetchDevices, 5000)

  const handleCreate = async (payload: { device_id: string; device_name: string; device_type: string; location: string }) => {
    await api.post('/devices', payload)
  }

  const handleUpdate = async (payload: { device_id: string; device_name: string; device_type: string; location: string }) => {
    if (!editing) return
    await api.put(`/devices/${editing.device_id}`, {
      device_name: payload.device_name,
      device_type: payload.device_type,
      location: payload.location,
    })
  }

  const handleDelete = async (deviceId: string) => {
    if (!confirm(`Delete device ${deviceId}?`)) return
    await api.del(`/devices/${deviceId}`)
  }

  const filtered = (devices || []).filter(
    (d) =>
      d.device_name.toLowerCase().includes(search.toLowerCase()) ||
      d.device_id.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) return <LoadingSkeleton />

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-white">Devices</h2>
        <button
          onClick={() => { setEditing(null); setShowModal(true) }}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          <span>Add Device</span>
        </button>
      </div>

      <input
        type="text"
        placeholder="Search devices..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full max-w-sm bg-cardBg border border-borderBg rounded-lg px-4 py-2 text-sm text-white focus:border-blue-500 focus:outline-none"
      />

      <div className="glass-card rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b border-borderBg">
              <th className="text-left py-3 px-4">Name</th>
              <th className="text-left py-3 px-4">ID</th>
              <th className="text-left py-3 px-4">Type</th>
              <th className="text-left py-3 px-4">Status</th>
              <th className="text-left py-3 px-4">Location</th>
              <th className="text-right py-3 px-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.id} className="border-b border-borderBg/50 hover:bg-white/5">
                <td className="py-3 px-4 text-white">{d.device_name}</td>
                <td className="py-3 px-4 text-gray-400 font-mono text-xs">{d.device_id}</td>
                <td className="py-3 px-4 text-gray-400">{d.device_type}</td>
                <td className="py-3 px-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                    d.status === 1 ? 'bg-emerald-500/10 text-emerald-400' :
                    d.status === 2 ? 'bg-rose-500/10 text-rose-400' :
                    'bg-gray-500/10 text-gray-400'
                  }`}>
                    {d.status === 1 ? 'Online' : d.status === 2 ? 'Fault' : 'Offline'}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-500">{d.location || '—'}</td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => { setEditing(d); setShowModal(true) }}
                    className="p-1.5 text-gray-400 hover:text-white mr-1"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(d.device_id)}
                    className="p-1.5 text-gray-400 hover:text-rose-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-500">
                  No devices found. Add one or start the simulator.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <DeviceFormModal
          device={editing}
          onClose={() => setShowModal(false)}
          onSubmit={editing ? handleUpdate : handleCreate}
        />
      )}

      {error && (
        <div className="glass-card rounded-xl p-4 border-rose-500/30 text-rose-400 text-sm">
          Error: {error}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Devices.tsx frontend/src/components/DeviceFormModal.tsx
git commit -m "feat: add Devices page with CRUD and search"
```

---

### Task 9: Update simulator and add demo seed data

**Files:**
- Modify: `simulator.py`
- Modify: `frontend/.gitignore`

- [ ] **Step 1: Make simulator API_BASE env-configurable**

Edit `simulator.py`, change line 22:

```python
API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")
```

Add `import os` at top after `import logging`.

- [ ] **Step 2: Create frontend .gitignore**

Create `frontend/.gitignore`:

```
node_modules/
dist/
.vite/
```

- [ ] **Step 3: Verify end-to-end flow**

```bash
# Terminal 1: Start backend
cd backend && DB_TYPE=sqlite REDIS_ENABLED=false uvicorn app.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Start simulator
python simulator.py

# Browser: open http://localhost:3000
# Expected: Dashboard shows 5 devices, live data streaming, trend chart updating
```

- [ ] **Step 4: Commit**

```bash
git add simulator.py frontend/.gitignore
git commit -m "feat: make simulator API_BASE env-configurable"
```

---

### Task 10: Rewrite README in English

**Files:**
- Rewrite: `README.md`

- [ ] **Step 1: Create English README**

Rewrite `README.md`:

```markdown
# IoT Platform — Full-Stack Device Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6.svg)](https://www.typescriptlang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A full-stack IoT device management and real-time monitoring dashboard. Register devices, ingest telemetry data, visualize trends, and configure alarm rules — all with a clean dark-themed UI.

## Quick Start (No Docker Required)

```bash
# 1. Install backend dependencies
cd backend && pip install -r requirements.txt

# 2. Start backend (SQLite mode)
DB_TYPE=sqlite REDIS_ENABLED=false uvicorn app.main:app --reload --port 8000

# 3. Start frontend (new terminal)
cd frontend && npm install && npm run dev

# 4. Start device simulator (new terminal)
python simulator.py
```

Open **http://localhost:3000** to see the dashboard with live data.

## Full Stack with Docker

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your own passwords
docker compose up --build
```

This starts MySQL 8, Redis 7, and the FastAPI backend. Open `frontend/index.html` or start the Vite dev server for the new React frontend.

## Architecture

```
simulator.py ──→ POST /api/v1/data/report ──→ FastAPI ──→ MySQL/SQLite
                                                    ──→ Redis (optional)
Frontend ←── GET /api/v1/dashboard/* ──────────────┘
(React+TS)   GET /api/v1/devices/*
```

## Features

- **Device CRUD** — Register, update, delete IoT devices
- **Real-time Data Ingestion** — Async telemetry pipeline with batch simulator
- **Live Dashboard** — Stat cards, trend charts (Recharts), online device table
- **Alarm Engine** — Threshold-based rules with per-device or global scope
- **Dual Database** — MySQL (production) or SQLite (zero-config dev)
- **Redis Caching** — Atomic Lua scripts for device status, auto-degrades if unavailable

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/devices` | List all devices |
| `POST` | `/api/v1/devices` | Register a device |
| `GET` | `/api/v1/devices/{id}` | Get device details |
| `PUT` | `/api/v1/devices/{id}` | Update device |
| `DELETE` | `/api/v1/devices/{id}` | Delete device |
| `POST` | `/api/v1/data/report` | Ingest telemetry data |
| `GET` | `/api/v1/dashboard/summary` | Dashboard stats |
| `GET` | `/api/v1/dashboard/trend` | Temperature/humidity trend |
| `GET` | `/api/v1/dashboard/devices/online` | Online devices |
| `GET` | `/api/v1/dashboard/devices/{id}/latest` | Latest device data |
| `GET` | `/api/v1/alarms/rules` | List alarm rules |
| `POST` | `/api/v1/alarms/rules` | Create alarm rule |
| `GET` | `/api/v1/alarms/active` | Active alarms |
| `GET` | `/api/v1/alarms/feed` | Alarm event feed |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async) |
| Database | MySQL 8 or SQLite |
| Cache | Redis 7 (optional) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| Simulator | Python asyncio + httpx |
| DevOps | Docker Compose, Makefile |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── core/                # Config, database, Redis, db init
│   │   ├── models/              # SQLAlchemy ORM + Pydantic schemas
│   │   ├── api/v1/              # REST endpoints
│   │   └── services/            # Business logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # StatCard, TrendChart, DeviceFormModal
│   │   ├── pages/               # Dashboard, Devices
│   │   ├── hooks/               # usePolling, useApi
│   │   └── lib/                 # API client
│   └── package.json
├── db/init.sql                  # MySQL schema
├── simulator.py                 # Multi-device data simulator
├── docker-compose.yml           # Full-stack Docker deployment
├── Makefile                     # dev, dev-full, db-init, test
└── README.md
```

## Running Tests

```bash
cd backend && pip install pytest pytest-asyncio httpx
pytest ../tests/ -v
```

Tests use SQLite in-memory — no external services needed.

## License

MIT
```

- [ ] **Step 2: Create blank LICENSE file**

```bash
# MIT License - placeholder, let the user fill in their name
```

Create a basic MIT LICENSE file (the user can update their name):

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Commit**

```bash
git add README.md LICENSE
git commit -m "docs: English README with badges, quick start, and API reference"
```

---

### Task 11: Final integration test and polish

- [ ] **Step 1: Full clean-room test**

```bash
# Fresh clone test
cd /tmp
git clone <repo-url> iot-test && cd iot-test

# Quick mode
cd backend && pip install -r requirements.txt
DB_TYPE=sqlite REDIS_ENABLED=false uvicorn app.main:app --port 8000 &
sleep 3

# Test health
curl http://localhost:8000/health

# Test devices API
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","device_name":"Test","device_type":"sensor"}'
curl http://localhost:8000/api/v1/devices

# Test data report
curl -X POST http://localhost:8000/api/v1/data/report \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test","temperature":25.0,"humidity":60,"reported_at":"2026-07-16T12:00:00"}'

# Test dashboard
curl http://localhost:8000/api/v1/dashboard/summary

# Run tests
pytest tests/ -v
```

- [ ] **Step 2: Run linter**

```bash
cd backend && pip install ruff && ruff check .
# Expected: no errors (or fix any found)
```

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final polish and cleanup"
```

- [ ] **Step 4: Force push to GitHub**

```bash
git push --force github master
```
