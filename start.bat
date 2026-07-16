@echo off
chcp 65001 >nul
title IoT Platform

:: Check prerequisites
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

:: First run: install Python dependencies
if not exist "%~dp0backend\.deps_installed" (
    echo Installing Python dependencies...
    cd /d "%~dp0backend"
    pip install -r requirements.txt -q 2>nul
    type nul > .deps_installed
    cd /d "%~dp0"
)

:: First run: install frontend dependencies
if not exist "%~dp0frontend\node_modules" (
    echo Installing frontend dependencies...
    cd /d "%~dp0frontend"
    call npm install -q 2>nul
    cd /d "%~dp0"
)

:: Start backend
start "IoT-Backend" cmd /c "cd /d "%~dp0backend" && DB_TYPE=sqlite REDIS_ENABLED=false python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

:: Start frontend
start "IoT-Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

:: Wait for servers to start
timeout /t 4 /nobreak >nul

:: Start simulator
start "IoT-Simulator" cmd /c "cd /d "%~dp0" && python simulator.py"

:: Open browser
timeout /t 1 /nobreak >nul
start http://localhost:3000
