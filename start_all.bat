@echo off
title JAWIR OS - Start All Services
color 0E

echo.
echo  ===================================================
echo  ^|       JAWIR OS - Full Stack Launcher             ^|
echo  ^|  Backend + Frontend + Optional Services           ^|
echo  ===================================================
echo.

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend\
set FRONTEND_DIR=%ROOT_DIR%frontend\
set VENV_PYTHON=%BACKEND_DIR%venv_work\Scripts\python.exe

REM ========== Preflight Checks ==========
echo [CHECK] Verifying environment...

if not exist "%VENV_PYTHON%" (
    echo [FAIL] Python venv not found: %VENV_PYTHON%
    echo        Run: cd backend ^&^& python -m venv venv_work ^&^& venv_work\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
echo   [OK] Python venv: %VENV_PYTHON%

if not exist "%BACKEND_DIR%.env" (
    echo [WARN] backend\.env not found! Copy .env.example to .env
) else (
    echo   [OK] backend\.env found
)

if not exist "%FRONTEND_DIR%node_modules" (
    echo [INFO] Frontend node_modules missing, will install...
) else (
    echo   [OK] frontend\node_modules found
)

echo.
echo ===================================================
echo  Starting services...
echo ===================================================
echo.

REM ========== 1. Backend (port 8000) ==========
echo [1/4] Starting JAWIR Backend (port 8000)...
start "JAWIR Backend" cmd /k "cd /d "%BACKEND_DIR%" && title JAWIR Backend && color 0A && "%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
timeout /t 4 /nobreak >nul

REM ========== 2. Polinema API (port 8001) - optional ==========
if exist "%BACKEND_DIR%polinema-connector\polinema_api_server.py" (
    echo [2/4] Starting Polinema API (port 8001)...
    start "Polinema API" cmd /k "cd /d "%BACKEND_DIR%polinema-connector" && title Polinema API && color 0C && "%VENV_PYTHON%" polinema_api_server.py"
    timeout /t 2 /nobreak >nul
) else (
    echo [2/4] Polinema API - SKIPPED (not found)
)

REM ========== 3. Celus API (port 8002) - optional ==========
set CELUS_DIR=%ROOT_DIR%..\automasicelus\celus-auto\
if exist "%CELUS_DIR%celus_api_server.py" (
    echo [3/4] Starting Celus API (port 8002)...
    start "Celus API" cmd /k "cd /d "%CELUS_DIR%" && title Celus API && color 0D && "%VENV_PYTHON%" celus_api_server.py"
    timeout /t 2 /nobreak >nul
) else (
    echo [3/4] Celus API - SKIPPED (not found)
)

REM ========== 4. Frontend (port 5173) ==========
echo [4/4] Starting Frontend Dev Server (port 5173)...
if not exist "%FRONTEND_DIR%node_modules" (
    start "JAWIR Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && title JAWIR Frontend && color 0B && npm install && npm run dev"
) else (
    start "JAWIR Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && title JAWIR Frontend && color 0B && npm run dev"
)

echo.
echo ===================================================
echo  All services starting!
echo ===================================================
echo.
echo  Services:
echo    Backend:    http://localhost:8000     (API + WebSocket + IoT MQTT)
echo    Frontend:   http://localhost:5173     (Vite Dev)
echo    Polinema:   http://localhost:8001     (optional)
echo    Celus:      http://localhost:8002     (optional)
echo.
echo  Health Check:
echo    curl http://localhost:8000/health
echo    curl http://localhost:8000/health/iot
echo.
echo  Features enabled:
echo    - V2 Function Calling (38 tools)
echo    - IoT MQTT Bridge (HiveMQ Cloud TLS)
echo    - Web Search (Tavily)
echo    - Google Workspace (Gmail/Drive/Calendar/Sheets/Docs/Forms)
echo    - WhatsApp via GoWA (7 tools)
echo    - Desktop Control (3 tools)
echo    - KiCad Schematic Generator
echo    - Python Code Executor
echo    - Polinema SIAKAD ^& LMS
echo    - Celus PCB Automation
echo.
echo  Close this window is safe. Services run in their own windows.
echo  To stop all: close each service window or run stop_all.bat
echo.
pause
