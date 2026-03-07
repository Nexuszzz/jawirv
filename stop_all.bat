@echo off
title JAWIR OS - Stop All Services
color 0C

echo ========================================
echo   JAWIR OS - Stopping All Services
echo ========================================
echo.

echo [1/4] Stopping Backend (uvicorn)...
taskkill /F /FI "WINDOWTITLE eq JAWIR Backend*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTEN"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo   Done.

echo [2/4] Stopping Polinema API...
taskkill /F /FI "WINDOWTITLE eq Polinema API*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001.*LISTEN"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo   Done.

echo [3/4] Stopping Celus API...
taskkill /F /FI "WINDOWTITLE eq Celus API*" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002.*LISTEN"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo   Done.

echo [4/4] Stopping Frontend (node/vite)...
taskkill /F /FI "WINDOWTITLE eq JAWIR Frontend*" >nul 2>&1
echo   Done.

echo.
echo ========================================
echo   All services stopped.
echo ========================================
pause
