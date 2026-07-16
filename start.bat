@echo off
chcp 65001 >nul
title IoT Platform

:: Only install once - check if node_modules exists
if not exist "%~dp0frontend\node_modules" (
    echo First run: installing frontend dependencies...
    cd /d "%~dp0frontend"
    call npm install -q 2>nul
    cd /d "%~dp0"
)

:: Start backend
start "IoT-Backend" cmd /c "cd /d "%~dp0backend" && DB_TYPE=sqlite REDIS_ENABLED=false python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Start frontend
start "IoT-Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

:: Start simulator after 3s
timeout /t 3 /nobreak >nul
start "IoT-Simulator" cmd /c "cd /d "%~dp0" && python simulator.py"

:: Open browser after 2s
timeout /t 2 /nobreak >nul
start http://localhost:3000
