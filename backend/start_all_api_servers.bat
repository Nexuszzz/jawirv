@echo off
echo ========================================
echo Starting All JAWIR API Servers
echo ========================================

REM Get backend directory
set BACKEND_DIR=%~dp0
set VENV_PYTHON=%BACKEND_DIR%venv_fresh\Scripts\python.exe

echo.
echo [1/3] Starting Polinema API Server (port 8001)...
start "Polinema API" cmd /k "cd /d %BACKEND_DIR%polinema-connector && %VENV_PYTHON% polinema_api_server.py"
timeout /t 3

echo.
echo [2/3] Starting Celus API Server (port 8002)...
start "Celus API" cmd /k "cd /d D:\expo\jawirv3\jawirv2\automasicelus\celus-auto && %VENV_PYTHON% celus_api_server.py"
timeout /t 3

echo.
echo [3/3] Starting JAWIR Backend (port 8000)...
start "JAWIR Backend" cmd /k "cd /d %BACKEND_DIR% && %VENV_PYTHON% -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo.
echo ========================================
echo All servers started!
echo ========================================
echo.
echo Servers:
echo   - Polinema API: http://localhost:8001
echo   - Celus API:    http://localhost:8002  
echo   - JAWIR Backend: http://localhost:8000
echo.
echo Press any key to exit (servers will keep running)...
pause >nul
