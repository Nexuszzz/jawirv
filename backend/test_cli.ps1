#!/usr/bin/env pwsh
# CLI Test Script untuk Polinema & Celus tools

Write-Host "=== Testing JAWIR CLI dengan Polinema & Celus ===" -ForegroundColor Cyan
Write-Host ""

# Get backend dir
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $BackendDir "venv_fresh\Scripts\python.exe"
$CLIScript = Join-Path $BackendDir "jawir_cli.py"

Write-Host "Starting CLI tests..." -ForegroundColor Yellow
Write-Host ""

# Test 1: Polinema Biodata
Write-Host "[Test 1] Polinema Biodata" -ForegroundColor Cyan
$query1 = "Siapa nama saya?"
Write-Host "Query: $query1" -ForegroundColor Gray

$output1 = & $VenvPython $CLIScript $query1 2>&1
if ($output1 -match "MUHAMMAD|NIM|biodata") {
    Write-Host " OK - Got biodata" -ForegroundColor Green
} else {
    Write-Host " FAIL - No biodata" -ForegroundColor Red
    Write-Host $output1 -ForegroundColor Gray
}
Write-Host ""

# Test 2: Celus Config (lightweight test)
Write-Host "[Test 2] Celus Config" -ForegroundColor Cyan
$query2 = "Update config Celus untuk buat rangkaian ESP32 dengan LED pada GPIO2"
Write-Host "Query: $query2" -ForegroundColor Gray

$output2 = & $VenvPython $CLIScript $query2 2>&1
if ($output2 -match "Config|celus|ESP32") {
    Write-Host " OK - Config updated" -ForegroundColor Green
} else {
    Write-Host " FAIL - Config error" -ForegroundColor Red
    Write-Host $output2 -ForegroundColor Gray
}
Write-Host ""

Write-Host "=== Tests Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "For full manual test, run:" -ForegroundColor Yellow
Write-Host "  jawir" -ForegroundColor White
Write-Host ""
