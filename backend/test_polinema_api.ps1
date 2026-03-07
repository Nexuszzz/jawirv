# Polinema API Testing Script
$NIM = "244101060077"
$PASSWORD = "Fahri080506!"
$API_BASE = "https://api.polinema.ac.id"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "POLINEMA API TESTING" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
}

# Test 1: Basic Auth with NIM:Password
Write-Host "`n### TEST 1: HTTP Basic Authentication ###" -ForegroundColor Magenta
$basicAuth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${NIM}:${PASSWORD}"))
$headers = @{
    "Authorization" = "Basic $basicAuth"
    "Accept" = "application/json"
}

$result1 = Test-Endpoint -Url "$API_BASE/siakad/biodata/mahasiswa?nim=$NIM" `
    -Headers $headers `
    -Description "Biodata Mahasiswa with Basic Auth (NIM:Password)"

# Test 2: POST Login Endpoint (no auth)
Write-Host "`n`n### TEST 2: POST Login Endpoint (No Basic Auth) ###" -ForegroundColor Magenta
$loginBody = "nim=$NIM&password=$PASSWORD&showresponse=true"
$result2 = Test-Endpoint -Url "$API_BASE/siakad/biodata/login" `
    -Method "POST" `
    -Body $loginBody `
    -Description "Login with POST"

# Test 3: Login with username instead of nim
Write-Host "`n`n### TEST 3: POST Login with 'username' parameter ###" -ForegroundColor Magenta
$loginBody2 = "username=$NIM&password=$PASSWORD"
$result3 = Test-Endpoint -Url "$API_BASE/siakad/biodata/login" `
    -Method "POST" `
    -Body $loginBody2 `
    -Description "Login with username parameter"

# Test 4: Try different endpoints without auth to see error messages
Write-Host "`n`n### TEST 4: Testing Various Endpoints (No Auth) ###" -ForegroundColor Magenta

$endpoints = @(
    "/siakad/master/semester",
    "/siakad/master/kalender",
    "/siakad/master/jurusan",
    "/siakad/master/prodi"
)

foreach ($endpoint in $endpoints) {
    Test-Endpoint -Url "$API_BASE$endpoint" `
        -Description "Testing: $endpoint"
    Start-Sleep -Milliseconds 500
}

# Test 5: SIAKAD Web Login
Write-Host "`n`n### TEST 5: SIAKAD Web Login ###" -ForegroundColor Magenta

try {
    # First, get the login page
    Write-Host "`nGetting login page..." -ForegroundColor Yellow
    $loginPage = Invoke-WebRequest -Uri "https://siakad.polinema.ac.id/" `
        -SessionVariable 'siakadSession' `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "✓ Login page loaded" -ForegroundColor Green
    Write-Host "Cookies: $($siakadSession.Cookies.GetCookies('https://siakad.polinema.ac.id/').Name)"
    
    # Try to find login endpoint
    Write-Host "`nAttempting login..." -ForegroundColor Yellow
    $loginUrl = "https://siakad.polinema.ac.id/auth/login"
    
    $loginResult = Invoke-WebRequest -Uri $loginUrl `
        -Method POST `
        -WebSession $siakadSession `
        -Body @{
            username = $NIM
            password = $PASSWORD
        } `
        -UseBasicParsing `
        -ErrorAction Stop
    
    Write-Host "✓ Login response received" -ForegroundColor Green
    Write-Host "Status: $($loginResult.StatusCode)"
    Write-Host "Redirected to: $($loginResult.BaseResponse.ResponseUri)"
    
} catch {
    Write-Host "✗ Web login error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n`n========================================" -ForegroundColor Cyan
Write-Host "TESTING COMPLETE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "1. Check DevTools Network tab in browser while logged into SIAKAD"
Write-Host "2. Look for XHR/Fetch requests to find internal JSON endpoints"
Write-Host "3. Copy cookies from browser and test with those"
Write-Host "4. Consider Playwright if no JSON endpoints exist"
