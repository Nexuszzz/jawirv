# Test Polinema API Server
# Usage: .\test_polinema_api.ps1

$ErrorActionPreference = "Stop"

$API_URL = "http://localhost:8001"

Write-Host "🧪 Testing Polinema API Server" -ForegroundColor Cyan
Write-Host ""

# Test 1: Health check
Write-Host "1️⃣ Testing /health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/health" -Method GET
    Write-Host "✅ Health check passed" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
    Write-Host "   Scraper: $($response.scraper_exists)" -ForegroundColor Gray
    Write-Host "   Node.js: $($response.node_installed)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Is the server running? Run start_polinema_api.ps1 first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Test 2: Biodata endpoint
Write-Host "2️⃣ Testing /scrape/biodata endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$API_URL/scrape/biodata" -Method POST -ContentType "application/json" -Body "{}"
    if ($response.status -eq "success") {
        Write-Host "✅ Biodata scraping successful" -ForegroundColor Green
        Write-Host $response.data.summary
    } else {
        Write-Host "⚠️ Biodata scraping returned error: $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Biodata test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 3: Akademik endpoint (warning: slow, ~30-40s)
Write-Host "3️⃣ Testing /scrape/akademik endpoint (slow, ~40s)..." -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to skip this test" -ForegroundColor Gray
Start-Sleep -Seconds 2

try {
    $response = Invoke-RestMethod -Uri "$API_URL/scrape/akademik" -Method POST -ContentType "application/json" -Body "{}" -TimeoutSec 120
    if ($response.status -eq "success") {
        Write-Host "✅ Akademik scraping successful" -ForegroundColor Green
        Write-Host $response.data.summary
    } else {
        Write-Host "⚠️ Akademik scraping returned error: $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Akademik test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test 4: LMS endpoint (warning: very slow, ~60-80s)
Write-Host "4️⃣ Testing /scrape/lms endpoint (very slow, ~80s)..." -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to skip this test" -ForegroundColor Gray
Start-Sleep -Seconds 2

try {
    $response = Invoke-RestMethod -Uri "$API_URL/scrape/lms" -Method POST -ContentType "application/json" -Body "{}" -TimeoutSec 180
    if ($response.status -eq "success") {
        Write-Host "✅ LMS scraping successful" -ForegroundColor Green
        Write-Host $response.data.summary
    } else {
        Write-Host "⚠️ LMS scraping returned error: $($response.error)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ LMS test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ All tests completed!" -ForegroundColor Green
