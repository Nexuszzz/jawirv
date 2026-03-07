# Simple Polinema API Test
$NIM = "244101060077"
$PASSWORD = "Fahri080506!"

Write-Host "`n=== POLINEMA API TEST ===" -ForegroundColor Cyan

# Test 1: Basic Auth
Write-Host "`n[1] Testing Basic Auth..." -ForegroundColor Yellow
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${NIM}:${PASSWORD}"))
try {
    $r = Invoke-WebRequest -Uri "https://api.polinema.ac.id/siakad/biodata/mahasiswa?nim=$NIM" `
        -Headers @{"Authorization"="Basic $auth"} -UseBasicParsing
    Write-Host "SUCCESS!" -ForegroundColor Green
    $r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Login Endpoint
Write-Host "`n[2] Testing Login Endpoint..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "https://api.polinema.ac.id/siakad/biodata/login" `
        -Method POST -Body "nim=$NIM&password=$PASSWORD" `
        -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
    Write-Host "SUCCESS!" -ForegroundColor Green
    $r.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Web Login
Write-Host "`n[3] Testing SIAKAD Web..." -ForegroundColor Yellow
try {
    $web = Invoke-WebRequest -Uri "https://siakad.polinema.ac.id/" -SessionVariable s -UseBasicParsing
    $login = Invoke-WebRequest -Uri "https://siakad.polinema.ac.id/auth/login" `
        -Method POST -WebSession $s -Body @{username=$NIM;password=$PASSWORD} -UseBasicParsing
    Write-Host "SUCCESS! Cookies:" -ForegroundColor Green
    $s.Cookies.GetCookies("https://siakad.polinema.ac.id/")
} catch {
    Write-Host "Failed: $($_.Exception.Message)" -ForegroundColor Red
}
