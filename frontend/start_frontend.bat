@echo off
title JAWIR OS - Frontend Dev Server (port 5173)
color 0B

echo ========================================
echo   JAWIR OS - Frontend Dev Server
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
echo [INFO] Vite Dev: http://localhost:5173
echo.

cd /d "%FRONTEND_DIR%"
call npm run dev

echo.
echo [INFO] Frontend stopped.
pause
