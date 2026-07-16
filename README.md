# IoT Platform — Full-Stack Device Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6.svg)](https://www.typescriptlang.org)

A full-stack IoT device management and real-time monitoring dashboard. Register devices, ingest telemetry data, visualize trends, and configure alarm rules — all with a clean dark-themed UI.

## Quick Start (No Docker Required)

**Prerequisites:** Python 3.11+ and Node.js 18+

**Windows:** double-click `start.bat`

**macOS / Linux:**

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

This starts MySQL 8, Redis 7, and the FastAPI backend.

## Usage Guide

### 1. Add a Device

**Via Web UI:** Click **Devices** in the top nav → **+ Add Device** → fill in the form.

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "stm32-sensor-001",
    "device_name": "STM32 Temperature Sensor",
    "device_type": "temperature_sensor",
    "location": "Lab Room 302"
  }'
```

**Device types:** `temperature_sensor`, `humidity_sensor`, `multi_sensor`, `gateway`

### 2. Report Data

**Via simulator (auto):** `python simulator.py` — simulates 5 devices with random telemetry every 5 seconds.

**Via API (for real hardware like STM32 / ESP32 / Raspberry Pi):**

```bash
curl -X POST http://localhost:8000/api/v1/data/report \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "stm32-sensor-001",
    "temperature": 26.5,
    "humidity": 62.3,
    "battery_level": 85.0,
    "signal_strength": -42,
    "reported_at": "2026-07-16T15:30:00"
  }'
```

The device must be registered first, otherwise the server returns `404`. Only `device_id` and `reported_at` are required — all sensor fields are optional.

**STM32 / Arduino example (pseudocode):**

```cpp
// ESP8266 / ESP32 — POST sensor data every 5 seconds
String json = "{\"device_id\":\"stm32-sensor-001\",\"temperature\":" +
              String(temp) + ",\"humidity\":" + String(humid) +
              ",\"reported_at\":\"" + getISO8601Time() + "\"}";

http.begin("http://192.168.1.100:8000/api/v1/data/report");
http.addHeader("Content-Type", "application/json");
int code = http.POST(json);
```

> Replace `192.168.1.100` with the IP of the machine running the backend.

### 3. Set Up Alarm Rules

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/alarms/rules \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "stm32-sensor-001",
    "metric_name": "temperature",
    "operator": ">",
    "threshold_value": 35.0
  }'
```

This triggers an alarm when the device reports temperature above 35°C. Use `"device_id": null` to create a global rule that applies to all devices.

**Supported metrics:** `temperature`, `humidity`, `battery_level`, `signal_strength`
**Operators:** `>`, `<`, `>=`, `<=`, `==`

### 4. View the Dashboard

Open **http://localhost:3000**. The dashboard shows:

- **Stat cards** — total devices, online/offline counts, active alarms
- **Trend chart** — temperature & humidity over time (Recharts)
- **Online devices table** — which devices are currently sending data
- **Alarm badge** — red dot in the top-right corner when alarms are active

Alarms auto-resolve when the metric returns within the threshold on the next data report.

---

## Architecture

```
simulator.py ──→ POST /api/v1/data/report ──→ FastAPI ──→ MySQL / SQLite
                                                    ──→ Redis (optional)
Frontend ←── GET /api/v1/dashboard/* ──────────────┘
(React+TS)   GET /api/v1/devices/*
             GET /api/v1/alarms/*
```

## Features

- **Device CRUD** — Register, update, delete IoT devices
- **Real-time Data Ingestion** — Async telemetry pipeline with batch simulator
- **Live Dashboard** — Stat cards, trend charts (Recharts), online device table
- **Alarm Engine** — Threshold-based rules with per-device or global scope, auto-resolve
- **Dual Database** — MySQL (production) or SQLite (zero-config dev)
- **Redis Caching** — Atomic Lua scripts for device status, auto-degrades if unavailable
- **Dark Theme UI** — React 18 + TypeScript + Tailwind CSS + Lucide icons

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
| `PUT` | `/api/v1/alarms/rules/{id}` | Update alarm rule |
| `DELETE` | `/api/v1/alarms/rules/{id}` | Delete alarm rule |
| `GET` | `/api/v1/alarms/active` | Active alarms |
| `GET` | `/api/v1/alarms/feed` | Alarm event feed |
| `GET` | `/api/v1/alarms/logs` | Alarm log history |

## Simulated Devices

| Device ID | Name | Type | Location | Characteristics |
|-----------|------|------|----------|----------------|
| `sensor-temp-001` | TempSensor-01 | Temperature | Office 3F Zone A | High temp range (25-40°C) |
| `sensor-humid-002` | HumidSensor-02 | Humidity | Warehouse B1 | High humidity (50-80%) |
| `sensor-env-003` | EnviroSensor-03 | Multi | Outdoor Station | Balanced range |
| `sensor-indoor-004` | IndoorSensor-04 | Multi | Meeting Room C-301 | Mild range (20-28°C) |
| `sensor-gateway-005` | Gateway-05 | Gateway | Data Center | Signal + battery only |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async) |
| Database | MySQL 8 or SQLite |
| Cache | Redis 7 (optional) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide |
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
├── tests/                       # Backend API tests (SQLite)
├── db/init.sql                  # MySQL schema
├── simulator.py                 # Multi-device data simulator
├── docker-compose.yml           # Full-stack Docker deployment
├── Makefile                     # dev, dev-full, db-init, test
└── README.md
```

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Tests use SQLite in-memory — no external services needed.

