# 🧪 Quick Test Guide - JAWIR CLI WhatsApp Integration

## ✅ Setup Status
- **Backend:** Running at http://127.0.0.1:8000 (healthy)
- **Device:** Logged in (6287853462867:10@s.whatsapp.net)
- **Tools:** 24 total (19 existing + 5 WhatsApp)

## 📝 5 Test Scenarios

### Scenario 1: Cek Nomor WA + Web Search 🌐
```
Tolong cek apakah nomor 6287853462867 terdaftar di WhatsApp. Kalau terdaftar, cari info tentang kode area 6287853 itu dari mana.
```
**Expected Tools:** `whatsapp_check_number`, `web_search`

---

### Scenario 2: List Kontak WA + Hitung 📊
```
Tampilkan list kontak WhatsApp saya (cukup 5 kontak pertama saja), lalu hitung ada berapa total kontak.
```
**Expected Tools:** `whatsapp_list_contacts`

---

### Scenario 3: Cek Nomor WA Simple ✅
```
Cek nomor 6287853462867 apakah terdaftar di WhatsApp atau tidak?
```
**Expected Tools:** `whatsapp_check_number`

---

### Scenario 4: List Percakapan WA 💬
```
Tampilkan list percakapan WhatsApp saya. Berapa jumlah total chat yang saya punya?
```
**Expected Tools:** `whatsapp_list_chats`

---

### Scenario 5: List Grup WA 👥
```
List semua grup WhatsApp yang saya ikuti. Berapa total grup yang ada?
```
**Expected Tools:** `whatsapp_list_groups`

---

## 🚀 How to Run Test

### Option 1: Manual CLI Test (Recommended)
```powershell
# Terminal 1: Backend already running ✅
# Terminal 2: Open JAWIR CLI
cd D:\expo\jawirv3\jawirv2\jawirv2\backend
python jawir_cli.py

# Paste each prompt above, one by one
# Watch the ReAct loop output
```

### Option 2: Direct API Test (Advanced)
```powershell
# Use WebSocket directly
python test_whatsapp_cli_scenarios.py
```

---

## 👀 What to Watch For

During test, observe these phases in CLI output:

### 1. **💭 THINKING Phase**
```
💭 THINKING: Perlu cek nomor WhatsApp dulu...
```
Agent reasoning about what to do

### 2. **📋 PLANNING Phase**
```
📋 PLANNING: 2 aksi direncanakan
   ├─ 1. whatsapp_check_number
   └─ 2. web_search
```
Agent planning which tools to use

### 3. **🔧 ACTION Phase**
```
🔧 ACTION [0]: whatsapp_check_number
   └─ params: {'phone': '6287853462867'}
```
**✅ THIS IS KEY!** - Verify correct tool is called

### 4. **👁️ OBSERVE Phase**
```
👁️ OBSERVE: ✅ Nomor 6287853462867 terdaftar di WhatsApp
             📱 Status: Aktif
```
Tool execution result

### 5. **✅ FINAL RESPONSE**
```
✅ Final: Nomor 6287853462867 terdaftar di WhatsApp, Lur! 
         Kode area 6287853 adalah dari Sulawesi...
```
Agent's final answer to user

---

## ✅ Success Criteria

For each scenario, verify:

- [ ] **Correct Tool Called** - Expected WhatsApp tool appears in ACTION phase
- [ ] **No Errors** - No "DEVICE_NOT_LOGGED_IN" or connection errors
- [ ] **Data Returned** - OBSERVE shows actual data (contacts, chats, etc.)
- [ ] **Formatted Response** - Final response is readable with emojis
- [ ] **Context Aware** - Agent combines tools appropriately (Scenario 1)

---

## 🐛 Troubleshooting

### If tool not called:
- Agent might not understand prompt → rephrase more explicitly
- Check agent thinks it doesn't need tool → add "gunakan tool WhatsApp"

### If "DEVICE_NOT_LOGGED_IN" error:
```powershell
# Check device status from VPS
ssh ubuntu@13.55.23.245
curl -u admin:jawir2026 http://localhost:3000/app/devices | jq
```

### If connection timeout:
```powershell
# Restart backend
Get-Process python | Stop-Process -Force
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### If wrong response format:
- Check `agent/tools/whatsapp.py` - response parsing might need adjustment
- GoWA API response format bisa berubah per version

---

## 📊 Expected Results Summary

| Scenario | Tools | Pass Criteria |
|----------|-------|---------------|
| 1 | check_number + web_search | Both tools called, combined response |
| 2 | list_contacts | Contact list shown, count calculated |
| 3 | check_number | Quick yes/no answer |
| 4 | list_chats | Chat list shown with count |
| 5 | list_groups | Group list shown with count |

---

## 📝 Logging

All test results will show in CLI output. For debugging:

1. **Agent logs:** Check THINKING/PLANNING/ACTION phases
2. **Tool logs:** Check OBSERVE phase for tool output
3. **Backend logs:** Check terminal running uvicorn
4. **VPS logs:** `ssh ubuntu@13.55.23.245 "sudo journalctl -u gowa.service -f"`

---

## 🎯 Next Steps After Test

Once all 5 scenarios pass:

1. ✅ Mark "Test via JAWIR CLI E2E" as completed
2. 📄 Update documentation (README, usage examples)
3. 🚀 Ready for production use!

---

**Test File:** `whatsapp_test_prompts.txt` (detailed prompts)
**Backend:** http://127.0.0.1:8000/health
**VPS GoWA:** http://13.55.23.245:3000 (admin/jawir2026)
