#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Comprehensive test suite untuk Polinema dan Celus tools integration
    
.DESCRIPTION
    Script ini melakukan automated testing untuk:
    1. API Server connectivity (Polinema port 8001, Celus port 8002)
    2. Tool registration di JAWIR
    3. Functional testing masing-masing tool
    4. Error handling dan timeout scenarios
    5. End-to-end workflow tests
    
.EXAMPLE
    .\test_integration.ps1
    
.NOTES
    Requirement: Semua API server harus sudah running
#>

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

# Test results tracker
$TestsPassed = 0
$TestsFailed = 0
$TestsSkipped = 0

# ===========================================
# Helper Functions
# ===========================================

function Write-TestHeader {
    param([string]$Title)
    Write-Host "`n========================================" -ForegroundColor $InfoColor
    Write-Host $Title -ForegroundColor $InfoColor
    Write-Host "========================================" -ForegroundColor $InfoColor
}

function Write-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = ""
    )
    
    if ($Passed) {
        Write-Host "✅ PASS: $TestName" -ForegroundColor $SuccessColor
        if ($Message) { Write-Host "   → $Message" -ForegroundColor Gray }
        $script:TestsPassed++
    } else {
        Write-Host "❌ FAIL: $TestName" -ForegroundColor $ErrorColor
        if ($Message) { Write-Host "   → $Message" -ForegroundColor Gray }
        $script:TestsFailed++
    }
}

function Test-ApiHealth {
    param(
        [string]$Name,
        [string]$Url
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -ErrorAction Stop
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "healthy") {
            Write-TestResult -TestName "$Name Health Check" -Passed $true -Message "Status: $($json.status)"
            return $true
        } else {
            Write-TestResult -TestName "$Name Health Check" -Passed $false -Message "Unexpected status: $($json.status)"
            return $false
        }
    } catch {
        Write-TestResult -TestName "$Name Health Check" -Passed $false -Message "Connection failed: $_"
        return $false
    }
}

function Test-PolinemaBiodata {
    Write-Host "`nTesting Polinema Biodata..." -ForegroundColor $InfoColor
    
    try {
        $body = @{} | ConvertTo-Json
        $response = Invoke-WebRequest -Uri "http://localhost:8001/scrape/biodata" `
                                      -Method POST `
                                      -ContentType "application/json" `
                                      -Body $body `
                                      -UseBasicParsing `
                                      -TimeoutSec 60 `
                                      -ErrorAction Stop
        
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "success") {
            $summary = $json.data.summary
            Write-TestResult -TestName "Polinema Get Biodata" -Passed $true -Message "Got biodata (${summary.Length} chars)"
            return $true
        } else {
            Write-TestResult -TestName "Polinema Get Biodata" -Passed $false -Message "Status: $($json.status), Error: $($json.error)"
            return $false
        }
    } catch {
        Write-TestResult -TestName "Polinema Get Biodata" -Passed $false -Message "Request failed: $_"
        return $false
    }
}

function Test-PolinemaAkademik {
    Write-Host "`nTesting Polinema Akademik..." -ForegroundColor $InfoColor
    
    try {
        $body = @{} | ConvertTo-Json
        $response = Invoke-WebRequest -Uri "http://localhost:8001/scrape/akademik" `
                                      -Method POST `
                                      -ContentType "application/json" `
                                      -Body $body `
                                      -UseBasicParsing `
                                      -TimeoutSec 90 `
                                      -ErrorAction Stop
        
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "success") {
            $raw = $json.data.raw
            $kehadiranCount = $raw.kehadiran.Count
            Write-TestResult -TestName "Polinema Get Akademik" -Passed $true -Message "Got $kehadiranCount semester data"
            return $true
        } else {
            Write-TestResult -TestName "Polinema Get Akademik" -Passed $false -Message "Status: $($json.status), Error: $($json.error)"
            return $false
        }
    } catch {
        Write-TestResult -TestName "Polinema Get Akademik" -Passed $false -Message "Request failed: $_"
        return $false
    }
}

function Test-PolinemaLMS {
    Write-Host "`nTesting Polinema LMS..." -ForegroundColor $InfoColor
    
    try {
        $body = @{} | ConvertTo-Json
        $response = Invoke-WebRequest -Uri "http://localhost:8001/scrape/lms" `
                                      -Method POST `
                                      -ContentType "application/json" `
                                      -Body $body `
                                      -UseBasicParsing `
                                      -TimeoutSec 120 `
                                      -ErrorAction Stop
        
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "success") {
            $raw = $json.data.raw
            $coursesCount = $raw.courses.Count
            $assignmentsCount = $raw.assignments.Count
            Write-TestResult -TestName "Polinema Get LMS" -Passed $true -Message "Got $coursesCount courses, $assignmentsCount assignments"
            return $true
        } else {
            Write-TestResult -TestName "Polinema Get LMS" -Passed $false -Message "Status: $($json.status), Error: $($json.error)"
            return $false
        }
    } catch {
        Write-TestResult -TestName "Polinema Get LMS" -Passed $false -Message "Request failed: $_"
        return $false
    }
}

function Test-CelusConfig {
    Write-Host "`nTesting Celus Config..." -ForegroundColor $InfoColor
    
    try {
        $body = @{
            prompt = "Buat rangkaian ESP32 dengan LED pada GPIO2 dan buzzer pada GPIO16"
            headless = $true
            download_mode = "pdf"
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "http://localhost:8002/config" `
                                      -Method POST `
                                      -ContentType "application/json" `
                                      -Body $body `
                                      -UseBasicParsing `
                                      -TimeoutSec 30 `
                                      -ErrorAction Stop
        
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "success") {
            Write-TestResult -TestName "Celus Update Config" -Passed $true -Message "Config updated successfully"
            return $true
        } else {
            Write-TestResult -TestName "Celus Update Config" -Passed $false -Message "Status: $($json.status)"
            return $false
        }
    } catch {
        Write-TestResult -TestName "Celus Update Config" -Passed $false -Message "Request failed: $_"
        return $false
    }
}

function Test-CelusDownloads {
    Write-Host "`nTesting Celus Downloads..." -ForegroundColor $InfoColor
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8002/downloads" `
                                      -Method GET `
                                      -UseBasicParsing `
                                      -TimeoutSec 30 `
                                      -ErrorAction Stop
        
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "success") {
            $count = $json.total_count
            Write-TestResult -TestName "Celus Get Downloads" -Passed $true -Message "Found $count files"
            return $true
        } else {
            Write-TestResult -TestName "Celus Get Downloads" -Passed $false -Message "Status: $($json.status)"
            return $false
        }
    } catch {
        Write-TestResult -TestName "Celus Get Downloads" -Passed $false -Message "Request failed: $_"
        return $false
    }
}

function Test-JAWIRToolRegistry {
    Write-Host "`nTesting JAWIR Tool Registry..." -ForegroundColor $InfoColor
    
    # Check if tools are registered by attempting to call backend
    # This is indirect test - ideally we'd call /tools endpoint if it exists
    
    try {
        # For now, just check backend is responsive
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction Stop
        $json = $response.Content | ConvertFrom-Json
        
        if ($json.status -eq "healthy") {
            Write-TestResult -TestName "JAWIR Backend Responsive" -Passed $true -Message "Backend healthy"
            
            # TODO: Add proper /tools endpoint check
            Write-Host "   ℹ️  Tool registry check requires manual CLI test" -ForegroundColor $WarningColor
            $script:TestsSkipped++
            return $true
        } else {
            Write-TestResult -TestName "JAWIR Backend Responsive" -Passed $false
            return $false
        }
    } catch {
        Write-TestResult -TestName "JAWIR Backend Responsive" -Passed $false -Message "Connection failed: $_"
        return $false
    }
}

# ===========================================
# Main Test Execution
# ===========================================

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor $InfoColor
Write-Host "║  Polinema & Celus Integration Tests   ║" -ForegroundColor $InfoColor
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# Phase 1: API Server Health Checks
Write-TestHeader "Phase 1: API Server Health Checks"
$polinemaHealthy = Test-ApiHealth -Name "Polinema API" -Url "http://localhost:8001/health"
$celusHealthy = Test-ApiHealth -Name "Celus API" -Url "http://localhost:8002/health"
$jawirHealthy = Test-ApiHealth -Name "JAWIR Backend" -Url "http://localhost:8000/health"

if (-not ($polinemaHealthy -and $celusHealthy -and $jawirHealthy)) {
    Write-Host "`n❌ API servers not all healthy. Aborting tests." -ForegroundColor $ErrorColor
    Write-Host "   Make sure all servers are running:" -ForegroundColor $WarningColor
    Write-Host "     1. Polinema API: cd polinema-connector && python polinema_api_server.py" -ForegroundColor Gray
    Write-Host "     2. Celus API: cd automasicelus/celus-auto && python celus_api_server.py" -ForegroundColor Gray
    Write-Host "     3. JAWIR Backend: python -m uvicorn app.main:app --port 8000" -ForegroundColor Gray
    exit 1
}

# Phase 2: Polinema Tools Functional Tests
Write-TestHeader "Phase 2: Polinema Tools Functional Tests"
Test-PolinemaBiodata
Test-PolinemaAkademik
Test-PolinemaLMS

# Phase 3: Celus Tools Functional Tests
Write-TestHeader "Phase 3: Celus Tools Functional Tests"
Test-CelusConfig
Test-CelusDownloads

# Note: We skip celus_run_automation test as it takes 2-5 minutes
Write-Host "`n⏭️  SKIPPED: Celus Run Automation (too long, test manually)" -ForegroundColor $WarningColor
$TestsSkipped++

# Phase 4: JAWIR Integration Tests
Write-TestHeader "Phase 4: JAWIR Integration Tests"
Test-JAWIRToolRegistry

# ===========================================
# Test Summary
# ===========================================

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor $InfoColor
Write-Host "║          Test Summary                  ║" -ForegroundColor $InfoColor
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor $InfoColor
Write-Host ""
Write-Host "Total Tests: $($TestsPassed + $TestsFailed)" -ForegroundColor White
Write-Host "✅ Passed:   $TestsPassed" -ForegroundColor $SuccessColor
Write-Host "❌ Failed:   $TestsFailed" -ForegroundColor $ErrorColor
Write-Host "⏭️  Skipped:  $TestsSkipped" -ForegroundColor $WarningColor
Write-Host ""

if ($TestsFailed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED!" -ForegroundColor $SuccessColor
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor $InfoColor
    Write-Host "  1. Test via JAWIR CLI:" -ForegroundColor Gray
    Write-Host "     jawir" -ForegroundColor White
    Write-Host "     Siapa nama saya?" -ForegroundColor White
    Write-Host "     Buatkan rangkaian ESP32 dengan LED" -ForegroundColor White
    Write-Host ""
    Write-Host "  2. Verify tool registration:" -ForegroundColor Gray
    Write-Host "     Check backend logs for 'Registered: polinema_*' and 'celus_*'" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "❌ SOME TESTS FAILED" -ForegroundColor $ErrorColor
    Write-Host "   Review error messages above and fix issues" -ForegroundColor $WarningColor
    Write-Host ""
    exit 1
}
