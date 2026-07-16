# IoT Platform — Open-Source Full-Stack Showcase Design

Date: 2026-07-16
Goal: Transform existing IoT platform into a public GitHub portfolio project targeting internship applications.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend  (React 18 + TypeScript + Vite)           │
│  Tailwind CSS + Recharts + Lucide Icons             │
│  Pages: Dashboard, Devices                          │
└──────────────────┬──────────────────────────────────┘
                   │ REST API (JSON)
┌──────────────────▼──────────────────────────────────┐
│  Backend   (FastAPI + async)                        │
│  /api/v1/devices | /api/v1/data | /api/v1/dashboard │
│  /api/v1/alarms                                     │
│  Services: device, data_ingest, alarm_rule, alarm   │
└──────┬───────────────────────┬──────────────────────┘
       │                       │
  ┌────▼─────┐           ┌─────▼──────┐
  │ MySQL 8  │ (full)    │  SQLite    │ (quick)
  │ Redis 7  │           │  no Redis  │
  └──────────┘           └────────────┘
```

## Two Launch Modes

| Mode   | Command              | Dependencies       | Backend DB    | Redis  |
|--------|----------------------|--------------------|---------------|--------|
| Quick  | `make dev`           | Python 3.11 + Node | SQLite        | off    |
| Full   | `docker compose up`  | Docker             | MySQL 8, Redis | on     |

SQLite backend auto-detects mode via `DB_TYPE` env var. Redis client already has graceful degradation built-in.

## Frontend Design

### Stack
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Recharts (charts — replaces ECharts, smaller bundle, React-native)
- Lucide React (icons)
- React Router (client routing)

### Pages

**Dashboard** (`/`)
- 4 stat cards (total devices, online, alerts triggered, data points today)
- Temperature + humidity trend line chart (Recharts, last 24h)
- Online devices table (5s polling via `usePolling` hook)
- Alert notification badge in header

**Devices** (`/devices`)
- Device table with search/filter by name or type
- Add device modal (form with validation)
- Edit / Delete actions
- Each row links to device detail

### Component Tree
```
App
├── Layout (sidebar nav, header with alert badge)
│   ├── DashboardPage
│   │   ├── StatCard (×4)
│   │   ├── TrendChart (Recharts dual-axis line)
│   │   └── OnlineDevicesTable
│   └── DevicesPage
│       ├── DeviceTable
│       ├── SearchBar
│       └── DeviceFormModal
```

### Data Fetching
- Simple fetch wrapper in `lib/api.ts` with base URL from env
- Custom hooks: `usePolling(url, intervalMs)` for live data, `useApi(url)` for one-shot
- Error states: toast for API errors, skeleton loaders while loading

## Backend Changes

### Keep as-is (polish only)
- All existing REST API endpoints
- Alarm rule engine
- Data ingest pipeline
- Redis degradation logic
- Simulator script

### Add
- `DB_TYPE` env var: `mysql` (default) or `sqlite` — auto-selects async driver
- SQLite connection path: `backend/data/iot.db` (auto-created, gitignored)
- More pytest coverage on services and API routes
- `make dev` target that starts both backend and frontend dev servers

### Remove
- Vercel serverless entrypoint (`api/index.py`) — not needed for this showcase
- Render-specific deployment config — replaced by generic Docker instructions
- Hardcoded production URLs in comments/docs

## Data Flow

```
Simulator (simulator.py)
  → POST /api/v1/data/report  (every 5s per device)
    → data_ingest_service: validate → insert MySQL/SQLite → try cache in Redis
      → alarm_service: check against active rules → generate alarm if threshold crossed

Frontend Dashboard
  → GET /api/v1/dashboard/summary  (poll every 5s)
  → GET /api/v1/dashboard/trend?hours=24
  → GET /api/v1/dashboard/devices/online
```

## README Structure
- English with badges (license, python version, docker)
- Animated GIF of dashboard in action
- Quick start: 3 commands to running
- Architecture diagram (ASCII)
- API reference table
- Technology decisions explained briefly ("Why FastAPI?", "Why SQLite fallback?")

## What This Shows an Interviewer

| Skill | Evidence |
|-------|----------|
| Backend engineering | Layered FastAPI, async SQLAlchemy, Redis caching with degradation |
| Frontend engineering | React + TS component architecture, custom hooks, responsive design |
| Database design | Normalized schema, both MySQL and SQLite support |
| DevOps | Docker Compose, Makefile, env-based configuration |
| Real-time systems | Polling, alarm rule engine, simulator |
| Code quality | Type hints, pytest, clean project structure |

## Non-Goals
- Authentication / user system (out of scope for data showcase)
- CI/CD pipeline (overkill for portfolio project)
- Mobile responsive beyond desktop+tablet
- i18n
