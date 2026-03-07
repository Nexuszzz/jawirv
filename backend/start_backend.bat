@echo off
title JAWIR OS - Backend Server (port 8000)
color 0A

echo ========================================
echo   JAWIR OS - Backend Server
echo ========================================
echo.

REM Auto-detect directory (wherever this bat is)
set BACKEND_DIR=%~dp0
set VENV_PYTHON=%BACKEND_DIR%venv_work\Scripts\python.exe

REM Check python exists
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Python venv not found at: %VENV_PYTHON%
    echo Coba jalankan: python -m venv venv_work
    pause
    exit /b 1
)

REM Check .env exists
if not exist "%BACKEND_DIR%.env" (
    echo [WARNING] .env not found! Copy .env.example to .env dan isi konfigurasi.
)

echo [INFO] Python: %VENV_PYTHON%
echo [INFO] Working Dir: %BACKEND_DIR%
echo [INFO] Port: 8000
echo [INFO] Mode: USE_FUNCTION_CALLING=true, IOT_ENABLED=true
echo.

cd /d "%BACKEND_DIR%"
"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo [INFO] Server stopped.
pause
