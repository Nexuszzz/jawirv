#!/usr/bin/env pwsh
# JAWIR CLI Starter Script

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "  Starting JAWIR CLI" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

# Change to backend directory
Set-Location D:\expo\jawirv3\jawirv2\jawirv2\backend

Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
try {
    & .\venv_fresh\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to activate venv" -ForegroundColor Red
    exit 1
}

Write-Host "`nStarting JAWIR CLI..." -ForegroundColor Yellow
Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Device: 6287853462867:10@s.whatsapp.net" -ForegroundColor Cyan
Write-Host "`n📱 WhatsApp Tools Available:" -ForegroundColor Yellow
Write-Host "  - whatsapp_check_number" -ForegroundColor White
Write-Host "  - whatsapp_list_contacts" -ForegroundColor White
Write-Host "  - whatsapp_list_groups" -ForegroundColor White
Write-Host "  - whatsapp_list_chats" -ForegroundColor White
Write-Host "  - whatsapp_send_message" -ForegroundColor White
Write-Host "`n" -ForegroundColor White

# Start CLI
python jawir_cli.py
