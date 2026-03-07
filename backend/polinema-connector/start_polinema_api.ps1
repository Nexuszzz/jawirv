#!/usr/bin/env pwsh
# Start Polinema API Server
# Usage: .\start_polinema_api.ps1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Polinema API Server..." -ForegroundColor Cyan

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to polinema-connector directory
Set-Location $ScriptDir

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js installed: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not installed!" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check if scraper exists
if (-Not (Test-Path "scraper_enhanced.js")) {
    Write-Host "❌ scraper_enhanced.js not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Scraper found: scraper_enhanced.js" -ForegroundColor Green

# Check if uvicorn is available
try {
    $uvicornVersion = python -m uvicorn --version
    Write-Host "✅ Uvicorn available" -ForegroundColor Green
} catch {
    Write-Host "❌ Uvicorn not installed!" -ForegroundColor Red
    Write-Host "Installing uvicorn..." -ForegroundColor Yellow
    pip install uvicorn
}

# Start the API server
Write-Host ""
Write-Host "📡 Starting API server on http://localhost:8001" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn polinema_api_server:app --host 0.0.0.0 --port 8001 --reload
