@echo off
chcp 65001 >nul
title IoT Platform

echo ============================================
echo   IoT Platform - Device Monitoring Dashboard
echo ============================================
echo.

:: Step 1: Check Python dependencies
echo [1/4] Checking Python dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt -q 2>nul
echo   Backend dependencies OK.

:: Step 2: Start backend
echo [2/4] Starting backend (SQLite mode) on port 8000...
start "IoT-Backend" cmd /c "cd /d "%~dp0backend" && DB_TYPE=sqlite REDIS_ENABLED=false python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo   Backend starting...

:: Step 3: Start frontend
echo [3/4] Starting frontend on port 3000...
cd /d "%~dp0frontend"
call npm install -q 2>nul
start "IoT-Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"
echo   Frontend starting...

:: Step 4: Start simulator
echo [4/4] Starting device simulator...
timeout /t 3 /nobreak >nul
start "IoT-Simulator" cmd /c "cd /d "%~dp0" && python simulator.py"
echo   Simulator started.

:: Open browser
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo ============================================
echo   All services started!
echo   Dashboard: http://localhost:3000
echo   API Docs:  http://localhost:8000/docs
echo.
echo   Close this window or the three console
echo   windows to stop all services.
echo ============================================
pause
