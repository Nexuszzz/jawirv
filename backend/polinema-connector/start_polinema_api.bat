@echo off
REM Start Polinema API Server (Windows Batch)
REM Usage: start_polinema_api.bat

echo Starting Polinema API Server...

cd /d "%~dp0"

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not installed!
    echo Please install from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js: OK

REM Check scraper
if not exist "scraper_enhanced.js" (
    echo ERROR: scraper_enhanced.js not found!
    pause
    exit /b 1
)

echo Scraper: OK

REM Start server
echo.
echo Starting API server on http://localhost:8001
echo Press Ctrl+C to stop
echo.

python -m uvicorn polinema_api_server:app --host 0.0.0.0 --port 8001 --reload

pause
