# Manual Test Script untuk GoWA API
# Run: .\test_gowa_manual.ps1

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "   GoWA API Manual Test Suite" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$baseUrl = "http://13.55.23.245:3000"
$username = "admin"
$password = "jawir2026"

# Create Basic Auth header
$credentials = "${username}:${password}"
$encodedCreds = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($credentials))
$headers = @{
    "Authorization" = "Basic $encodedCreds"
    "Content-Type" = "application/json"
}

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Base URL: $baseUrl"
Write-Host "  Username: $username"
Write-Host "  Password: $([String]::new('*', $password.Length))"
Write-Host ""

# Test 1: Health Check
Write-Host "[1/6] Testing Connection..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/user/check?phone=628" -Headers $headers -Method GET
    Write-Host "  ✅ Connection OK" -ForegroundColor Green
    Write-Host "  Response: $($response.message)" -ForegroundColor Gray
} catch {
    Write-Host "  ❌ Connection FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Kemungkinan masalah:" -ForegroundColor Yellow
    Write-Host "  1. VPS GoWA service tidak running: sudo systemctl status gowa.service"
    Write-Host "  2. Firewall block port 3000: sudo ufw status"
    Write-Host "  3. Username/password salah"
    exit 1
}
Write-Host ""

# Test 2: Get Devices
Write-Host "[2/6] Checking Device Status..." -ForegroundColor Cyan
try {
    $devices = Invoke-RestMethod -Uri "$baseUrl/app/devices" -Headers $headers -Method GET
    
    if ($devices.results -and $devices.results.Count -gt 0) {
        Write-Host "  ✅ Device Logged In" -ForegroundColor Green
        foreach ($device in $devices.results) {
            Write-Host "    Device JID: $($device.device)" -ForegroundColor Gray
            Write-Host "    Name: $($device.name)" -ForegroundColor Gray
            Write-Host "    Status: $($device.status)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  ⚠️  No Device Logged In" -ForegroundColor Yellow
        Write-Host "  Action required: Scan QR code at $baseUrl" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Steps to login:" -ForegroundColor Cyan
        Write-Host "  1. Buka browser: $baseUrl"
        Write-Host "  2. Login: $username / $password"
        Write-Host "  3. Klik 'Generate QR Code' atau 'Get Pairing Code'"
        Write-Host "  4. Scan QR dengan WhatsApp mobile"
        Write-Host "  5. Re-run test ini setelah device connected"
        Write-Host ""
        
        # Still continue tests to check endpoints
    }
} catch {
    Write-Host "  ❌ Device check FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 3: Check Number (example with safe number)
Write-Host "[3/6] Testing Check Number..." -ForegroundColor Cyan
$testPhone = "628123456789"  # Example number
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/user/check?phone=$testPhone" -Headers $headers -Method GET
    
    if ($response.code -eq "SUCCESS") {
        Write-Host "  ✅ Check Number API OK" -ForegroundColor Green
        if ($response.results -and $response.results.Count -gt 0) {
            $exists = $response.results[0].exists
            if ($exists) {
                Write-Host "    Number $testPhone terdaftar di WhatsApp" -ForegroundColor Gray
            } else {
                Write-Host "    Number $testPhone tidak terdaftar" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  ⚠️  API responded with: $($response.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Check number FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 4: List Contacts
Write-Host "[4/6] Testing List Contacts..." -ForegroundColor Cyan
try {
    $contacts = Invoke-RestMethod -Uri "$baseUrl/user/my/contacts" -Headers $headers -Method GET
    
    if ($contacts.code -eq "SUCCESS") {
        Write-Host "  ✅ List Contacts API OK" -ForegroundColor Green
        if ($contacts.results) {
            $count = $contacts.results.Count
            Write-Host "    Total contacts: $count" -ForegroundColor Gray
            if ($count -gt 0) {
                Write-Host "    First 3 contacts:" -ForegroundColor Gray
                $contacts.results[0..2] | ForEach-Object {
                    Write-Host "      - $($_.name): $($_.phone)" -ForegroundColor DarkGray
                }
            }
        }
    } else {
        Write-Host "  ⚠️  API responded with: $($contacts.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  List contacts FAILED (device might not be logged in)" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 5: List Groups
Write-Host "[5/6] Testing List Groups..." -ForegroundColor Cyan
try {
    $groups = Invoke-RestMethod -Uri "$baseUrl/user/my/groups" -Headers $headers -Method GET
    
    if ($groups.code -eq "SUCCESS") {
        Write-Host "  ✅ List Groups API OK" -ForegroundColor Green
        if ($groups.results) {
            $count = $groups.results.Count
            Write-Host "    Total groups: $count" -ForegroundColor Gray
            if ($count -gt 0) {
                Write-Host "    First 3 groups:" -ForegroundColor Gray
                $groups.results[0..2] | ForEach-Object {
                    Write-Host "      - $($_.name) ($($_.participants) members)" -ForegroundColor DarkGray
                }
            }
        }
    } else {
        Write-Host "  ⚠️  API responded with: $($groups.message)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  List groups FAILED (device might not be logged in)" -ForegroundColor Yellow
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Test 6: List Chats (try multiple endpoints)
Write-Host "[6/6] Testing List Chats..." -ForegroundColor Cyan
$chatEndpoints = @("/user/my/chats", "/chat/conversations", "/user/chats")
$chatSuccess = $false

foreach ($endpoint in $chatEndpoints) {
    try {
        Write-Host "  Trying endpoint: $endpoint" -ForegroundColor Gray
        $chats = Invoke-RestMethod -Uri "$baseUrl$endpoint" -Headers $headers -Method GET
        
        if ($chats.code -eq "SUCCESS") {
            Write-Host "  ✅ List Chats API OK (endpoint: $endpoint)" -ForegroundColor Green
            if ($chats.results) {
                $count = $chats.results.Count
                Write-Host "    Total chats: $count" -ForegroundColor Gray
            }
            $chatSuccess = $true
            break
        }
    } catch {
        # Try next endpoint
        continue
    }
}

if (-not $chatSuccess) {
    Write-Host "  ⚠️  List chats FAILED on all endpoints (device might not be logged in)" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "         Test Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. If device not logged in, scan QR at: $baseUrl" -ForegroundColor White
Write-Host "  2. After device connected, run: python test_whatsapp_tools.py" -ForegroundColor White
Write-Host "  3. Then test via JAWIR CLI: /ask 'cek nomor 08xxx ada WA?'" -ForegroundColor White
Write-Host ""
