#!/usr/bin/env pwsh
# Quick Integration Test for Polinema & Celus

Write-Host "`n=== Polinema & Celus Integration Tests ===" -ForegroundColor Cyan

# Test counters
$passed = 0
$failed = 0

function Test-API {
    param($name, $url)
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $j = $r.Content | ConvertFrom-Json
        if ($j.status -eq "healthy") {
            Write-Host "[OK] $name" -ForegroundColor Green
            $script:passed++
            return $true
        }
    } catch {
        Write-Host "[FAIL] $name - $_" -ForegroundColor Red
        $script:failed++
    }
    return $false
}

function Test-Endpoint {
    param($name, $url, $method="GET", $body=$null, $timeout=30)
    try {
        $params = @{
            Uri = $url
            Method = $method
            UseBasicParsing = $true
            TimeoutSec = $timeout
            ErrorAction = "Stop"
        }
        if ($body) {
            $params.ContentType = "application/json"
            $params.Body = ($body | ConvertTo-Json)
        }
        
        $r = Invoke-WebRequest @params
        $j = $r.Content | ConvertFrom-Json
        
        if ($j.status -eq "success") {
            Write-Host "[OK] $name" -ForegroundColor Green
            $script:passed++
            return $true
        } else {
            Write-Host "[FAIL] $name - Status: $($j.status)" -ForegroundColor Red
            $script:failed++
        }
    } catch {
        Write-Host "[FAIL] $name - $_" -ForegroundColor Red
        $script:failed++
    }
    return $false
}

# Phase 1: Health Checks
Write-Host "`n--- Health Checks ---"
$p = Test-API "Polinema API (8001)" "http://localhost:8001/health"
$c = Test-API "Celus API (8002)" "http://localhost:8002/health"
$j = Test-API "JAWIR Backend (8000)" "http://localhost:8000/health"

if (-not ($p -and $c -and $j)) {
    Write-Host "`nServers not ready. Run: .\start_all_api_servers.ps1" -ForegroundColor Yellow
    exit 1
}

# Phase 2: Polinema Tests
Write-Host "`n--- Polinema Tests ---"
Test-Endpoint "Biodata" "http://localhost:8001/scrape/biodata" "POST" @{} 60
Test-Endpoint "Akademik" "http://localhost:8001/scrape/akademik" "POST" @{} 90
Test-Endpoint "LMS" "http://localhost:8001/scrape/lms" "POST" @{} 120

# Phase 3: Celus Tests
Write-Host "`n--- Celus Tests ---"
$configBody = @{
    prompt = "Buat rangkaian ESP32 dengan LED pada GPIO2"
    headless = $true
    download_mode = "pdf"
}
Test-Endpoint "Config" "http://localhost:8002/config" "POST" $configBody 30
Test-Endpoint "Downloads" "http://localhost:8002/downloads" "GET" $null 30

# Summary
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })

if ($failed -eq 0) {
    Write-Host "`n SUCCESS! All tests passed." -ForegroundColor Green
    Write-Host "`nNext: Test via CLI with 'jawir'" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "`nSome tests failed. Check errors above." -ForegroundColor Red
    exit 1
}
