# Test WhatsApp Integration via JAWIR CLI
# 5 Scenarios Campuran dengan Tools Lain

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  JAWIR CLI WhatsApp Integration Test" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check backend
Write-Host "[0/5] Checking Backend Status..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET -ErrorAction Stop
    Write-Host "  ✅ Backend: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Backend not running!" -ForegroundColor Red
    Write-Host "  Please start: python -m uvicorn app.main:app" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Starting 5 test scenarios..." -ForegroundColor Cyan
Write-Host "Each scenario akan ditest via JAWIR CLI interactively" -ForegroundColor Gray
Write-Host ""

# Test Scenarios
$scenarios = @(
    @{
        num = 1
        title = "Cek Nomor WA + Web Search Info"
        prompt = "Tolong cek apakah nomor 6287853462867 terdaftar di WhatsApp. Kalau terdaftar, cari info tentang kode area 6287853 itu dari mana."
        expected = @("whatsapp_check_number", "web_search")
    },
    @{
        num = 2
        title = "List Kontak WA + Hitung Python"
        prompt = "Tampilkan list kontak WhatsApp saya (cukup 5 kontak pertama saja), lalu hitung ada berapa total kontak."
        expected = @("whatsapp_list_contacts")
    },
    @{
        num = 3
        title = "Cek Nomor WA Simple"
        prompt = "Cek nomor 6287853462867 apakah terdaftar di WhatsApp atau tidak?"
        expected = @("whatsapp_check_number")
    },
    @{
        num = 4
        title = "List Percakapan WA"
        prompt = "Tampilkan list percakapan WhatsApp saya. Berapa jumlah total chat yang saya punya?"
        expected = @("whatsapp_list_chats")
    },
    @{
        num = 5
        title = "List Grup WA"
        prompt = "List semua grup WhatsApp yang saya ikuti. Berapa total grup yang ada?"
        expected = @("whatsapp_list_groups")
    }
)

Write-Host "Test scenarios prepared. Cara test:" -ForegroundColor Yellow
Write-Host ""

foreach ($scenario in $scenarios) {
    Write-Host "[$($scenario.num)/5] $($scenario.title)" -ForegroundColor Cyan
    Write-Host "    Expected tools: $($scenario.expected -join ', ')" -ForegroundColor Gray
    Write-Host "    Prompt:" -ForegroundColor Gray
    Write-Host "    `"$($scenario.prompt)`"" -ForegroundColor White
    Write-Host ""
}

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Manual Test Instructions" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run JAWIR CLI in another terminal:" -ForegroundColor Yellow
Write-Host "  cd D:\expo\jawirv3\jawirv2\jawirv2\backend" -ForegroundColor White
Write-Host "  python jawir_cli.py" -ForegroundColor White
Write-Host ""
Write-Host "Then paste each prompt above, one by one." -ForegroundColor Yellow
Write-Host "Watch for:" -ForegroundColor Yellow
Write-Host "  🔧 ACTION - Tool being called" -ForegroundColor Gray
Write-Host "  👁️ OBSERVE - Tool result" -ForegroundColor Gray
Write-Host "  ✅ Final response" -ForegroundColor Gray
Write-Host ""

# Alternative: Create quick test file
Write-Host "Or use quick test (automated):" -ForegroundColor Yellow
Write-Host "  .\test_whatsapp_quick.ps1" -ForegroundColor White
Write-Host ""

# Save prompts to file for easy copy-paste
$promptFile = "whatsapp_test_prompts.txt"
"JAWIR CLI WhatsApp Test Prompts" | Out-File $promptFile
"=" * 50 | Out-File $promptFile -Append
"" | Out-File $promptFile -Append

foreach ($scenario in $scenarios) {
    "[$($scenario.num)/5] $($scenario.title)" | Out-File $promptFile -Append
    "Expected: $($scenario.expected -join ',')" | Out-File $promptFile -Append
    "" | Out-File $promptFile -Append
    $scenario.prompt | Out-File $promptFile -Append
    "" | Out-File $promptFile -Append
    "---" | Out-File $promptFile -Append
    "" | Out-File $promptFile -Append
}

Write-Host "✅ Test prompts saved to: $promptFile" -ForegroundColor Green
Write-Host "   You can copy-paste from this file into JAWIR CLI" -ForegroundColor Gray
Write-Host ""
