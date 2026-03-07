@echo off
title JAWIR OS - Full Stack Test
color 0E

echo.
echo  ===================================================
echo  ^|  JAWIR OS - Quick Full Stack Test Suite           ^|
echo  ===================================================
echo.

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend\
set FRONTEND_DIR=%ROOT_DIR%frontend\
set VENV_PYTHON=%BACKEND_DIR%venv_work\Scripts\python.exe

REM ===== Check Backend Running =====
echo [CHECK] Backend health...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo   [FAIL] Backend NOT running on port 8000!
    echo   Run start_all.bat first.
    pause
    exit /b 1
)
echo   [PASS] Backend is running

echo.
echo ===================================================
echo  Phase 1: Backend REST Endpoints
echo ===================================================

echo.
echo --- GET /health ---
curl -s http://localhost:8000/health
echo.

echo --- GET /health/iot ---
curl -s http://localhost:8000/health/iot
echo.

echo --- GET /api/iot/devices ---
curl -s http://localhost:8000/api/iot/devices
echo.

echo --- GET /api/iot/events?limit=3 ---
curl -s "http://localhost:8000/api/iot/events?limit=3"
echo.

echo --- GET /api/keys/stats ---
curl -s http://localhost:8000/api/keys/stats
echo.

echo --- GET /api/config ---
curl -s http://localhost:8000/api/config
echo.

echo.
echo ===================================================
echo  Phase 2: Tool Contract Tests (38 tools)
echo ===================================================
echo.

cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" tests\tool_contract_test.py

echo.
echo ===================================================
echo  Phase 3: WebSocket Smoke Test
echo ===================================================
echo.

cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" tests\ws_smoke_test.py

echo.
echo ===================================================
echo  Phase 4: V2 Function Calling E2E
echo ===================================================
echo.

cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" tests\fc_e2e_test.py

echo.
echo ===================================================
echo  Phase 5: Frontend Build Check
echo ===================================================
echo.

cd /d "%FRONTEND_DIR%"
echo --- TypeScript + Vite Build ---
call npm run build
if errorlevel 1 (
    echo   [FAIL] Frontend build failed!
) else (
    echo   [PASS] Frontend build OK
)

echo.
echo ===================================================
echo  Phase 6: IoT Control Test (Fan Speed)
echo ===================================================
echo.

echo --- POST fan-01 speed=high ---
curl -s -X POST http://localhost:8000/api/iot/devices/fan-01/control -H "Content-Type: application/json" -d "{\"action\":\"set_speed\",\"value\":\"high\"}"
echo.

echo --- POST fan-01 speed=off ---
curl -s -X POST http://localhost:8000/api/iot/devices/fan-01/control -H "Content-Type: application/json" -d "{\"action\":\"set_speed\",\"value\":\"off\"}"
echo.

echo --- GET fan-01 state ---
curl -s http://localhost:8000/api/iot/devices/fan-01
echo.

echo.
echo ===================================================
echo  DONE - All Tests Complete
echo ===================================================
echo.
echo  Summary of test files run:
echo    1. REST Health Endpoints   - curl checks
echo    2. Tool Contract (38 tools)- tests\tool_contract_test.py
echo    3. WebSocket Smoke         - tests\ws_smoke_test.py  
echo    4. V2 Function Calling E2E - tests\fc_e2e_test.py
echo    5. Frontend Build          - npm run build (tsc + vite)
echo    6. IoT Fan Control         - curl POST/GET
echo.
pause
