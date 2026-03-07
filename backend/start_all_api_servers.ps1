#!/usr/bin/env pwsh

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting All JAWIR API Servers" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get paths
$BackendDir = $PSScriptRoot
$VenvPython = Join-Path $BackendDir "venv_fresh\Scripts\python.exe"
$PolinemaDir = Join-Path $BackendDir "polinema-connector"
$CelusDir = "D:\expo\jawirv3\jawirv2\automasicelus\celus-auto"

# Function to start server in new PowerShell window
function Start-Server {
    param(
        [string]$Name,
        [string]$WorkingDir,
        [string]$Command,
        [int]$Port
    )
    
    Write-Host "[Starting] $Name (port $Port)..." -ForegroundColor Yellow
    
    $scriptBlock = @"
Set-Location '$WorkingDir'
Write-Host '========================================' -ForegroundColor Green
Write-Host '$Name' -ForegroundColor Green  
Write-Host '========================================' -ForegroundColor Green
Write-Host ''
$Command
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $scriptBlock
    Start-Sleep -Seconds 2
}

# Start servers
Start-Server -Name "Polinema API" -WorkingDir $PolinemaDir -Command "& '$VenvPython' polinema_api_server.py" -Port 8001
Start-Server -Name "Celus API" -WorkingDir $CelusDir -Command "& '$VenvPython' celus_api_server.py" -Port 8002
Start-Server -Name "JAWIR Backend" -WorkingDir $BackendDir -Command "& '$VenvPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000" -Port 8000

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All servers started successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Servers:" -ForegroundColor White
Write-Host "  - Polinema API:  http://localhost:8001" -ForegroundColor Cyan
Write-Host "  - Celus API:     http://localhost:8002" -ForegroundColor Cyan
Write-Host "  - JAWIR Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
