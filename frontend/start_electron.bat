@echo off
title JAWIR OS - Frontend Electron App
color 0D

echo ========================================
echo   JAWIR OS - Electron Desktop App
echo ========================================
echo.

set FRONTEND_DIR=%~dp0

REM Check node_modules
if not exist "%FRONTEND_DIR%node_modules" (
    echo [INFO] Installing dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    echo.
)

echo [INFO] Working Dir: %FRONTEND_DIR%
echo [INFO] Mode: Electron + Vite concurrent
echo.

cd /d "%FRONTEND_DIR%"
call npm run dev:electron

echo.
echo [INFO] Electron app stopped.
pause
