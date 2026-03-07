# WhatsApp Integration TODO List
================================

## ✅ COMPLETED

- [x] Create GoWA client wrapper (`tools/gowa_client.py`)
- [x] Create 5 WhatsApp tools (`agent/tools/whatsapp.py`)
- [x] Update config with GoWA settings (`app/config.py`)
- [x] Register tools in registry (`agent/tools/__init__.py`)
- [x] Add robust error handling and retry logic
- [x] Add device status checking
- [x] Create manual test script (PowerShell)
- [x] Create Python integration test script

## 🔄 IN PROGRESS

### Phase 1: VPS Device Setup (CRITICAL)

- [ ] **1.1 Login Device to WhatsApp** (BLOCKER!)
  - Open browser: http://13.55.23.245:3000
  - Login: admin / jawir2026
  - Click "Login" or "Generate QR Code"
  - Scan QR with WhatsApp mobile
  - Verify device shows "Connected"
  
  **Why critical:** All WhatsApp tools require logged-in device!

- [ ] **1.2 Test Device Connection**
  ```powershell
  .\test_gowa_manual.ps1
  ```
  Expected: "✅ Device Logged In"

## 📋 TODO

### Phase 2: API Endpoint Verification

- [ ] **2.1 Run Manual API Tests**
  ```powershell
  cd D:\expo\jawirv3\jawirv2\jawirv2\backend
  .\test_gowa_manual.ps1
  ```
  
- [ ] **2.2 Verify All Endpoints Working**
  - GET /user/check → Check number registration
  - GET /user/my/contacts → List contacts
  - GET /user/my/groups → List groups  
  - GET /user/my/chats (or /chat/conversations) → List chats
  - POST /send/message → Send text message
  
- [ ] **2.3 Fix Endpoint Issues**
  - If list_chats returns 404, update endpoint in gowa_client.py
  - Check GoWA API docs: http://13.55.23.245:3000/docs
  - Or check openapi.yaml in GoWA repo

### Phase 3: Python Tools Testing

- [ ] **3.1 Run Python Integration Test**
  ```powershell
  cd D:\expo\jawirv3\jawirv2\jawirv2\backend
  python test_whatsapp_tools_robust.py
  ```

- [ ] **3.2 Verify Each Tool**
  - whatsapp_check_number → Should return registration status
  - whatsapp_list_contacts → Should return contact list
  - whatsapp_list_groups → Should return group list
  - whatsapp_list_chats → Should return conversation list
  - whatsapp_send_message → SKIP (test manually later)

- [ ] **3.3 Fix Tool Issues**
  - Update tool implementations if needed
  - Add more error handling if edge cases found
  - Update response formatting for LLM

### Phase 4: JAWIR Backend Integration

- [ ] **4.1 Stop Old Backend Process**
  ```powershell
  Get-Process -Name python | Stop-Process -Force
  ```

- [ ] **4.2 Start Backend with WhatsApp Tools**
  ```powershell
  cd D:\expo\jawirv3\jawirv2\jawirv2\backend
  venv_fresh\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```

- [ ] **4.3 Verify Tools Registered**
  - Check logs for "19 → 24 tools registered"
  - Or check tool count increase

### Phase 5: JAWIR CLI Testing

- [ ] **5.1 Test Check Number**
  ```
  python jawir_cli.py
  > /ask "cek nomor 628123456789 ada WA?"
  ```
  Expected: Agent uses whatsapp_check_number tool

- [ ] **5.2 Test List Contacts**
  ```
  > /ask "list kontak WA saya"
  ```
  Expected: Agent uses whatsapp_list_contacts tool

- [ ] **5.3 Test List Groups**
  ```
  > /ask "list grup WA saya"
  ```
  Expected: Agent uses whatsapp_list_groups tool

- [ ] **5.4 Test List Chats**
  ```
  > /ask "list percakapan WA saya"
  ```
  Expected: Agent uses whatsapp_list_chats tool

- [ ] **5.5 Test Send Message (CAREFUL!)**
  ```
  > /ask "kirim WA ke nomor sendiri: test from JAWIR"
  ```
  Expected: Agent uses whatsapp_send_message tool
  
  **Note:** Test ke nomor sendiri dulu untuk safety!

### Phase 6: Error Handling & Edge Cases

- [ ] **6.1 Test Device Offline Scenario**
  - Logout device di WhatsApp mobile
  - Try using tools
  - Expected: User-friendly error "Device not logged in"

- [ ] **6.2 Test Invalid Phone Number**
  - Try check_number with invalid format
  - Expected: Graceful error message

- [ ] **6.3 Test Rate Limiting**
  - Send multiple messages rapidly
  - Check if WhatsApp blocks/throttles
  - Add rate limiting if needed

- [ ] **6.4 Test Network Errors**
  - Simulate VPS down (edit hosts file temporarily)
  - Expected: Retry logic works, then timeout error

- [ ] **6.5 Test Tool Quota**
  - Check if tool usage tracked in analytics
  - Verify quota system works with WhatsApp tools

### Phase 7: Monitoring & Maintenance

- [ ] **7.1 Add Device Status Monitoring**
  - Create health check endpoint: /api/whatsapp/health
  - Returns: device status, last message time, etc.

- [ ] **7.2 Add Auto-Reconnect Logic**
  - Detect device disconnected
  - Auto-trigger QR code generation
  - Send alert to admin

- [ ] **7.3 Add Usage Logging**
  - Log all WhatsApp tool calls
  - Track: timestamp, tool, params, result
  - Store in database or log file

- [ ] **7.4 Add Performance Metrics**
  - Measure tool execution time
  - Track success/failure rate
  - Alert on high failure rate

### Phase 8: Documentation

- [ ] **8.1 Update Main README**
  - Add WhatsApp tools section
  - List available commands
  - Show usage examples

- [ ] **8.2 Create User Guide**
  - How to use WhatsApp features via JAWIR CLI
  - Best practices (don't spam, rate limits, etc.)
  - Troubleshooting common issues

- [ ] **8.3 Create Admin Guide**
  - VPS maintenance (restart, update, logs)
  - Device re-login procedure
  - Backup/restore device session
  - Update GoWA binary

- [ ] **8.4 Create API Documentation**
  - Document each tool's parameters
  - Show example requests/responses
  - List error codes and meanings

### Phase 9: Optional Enhancements

- [ ] **9.1 Add More Tools** (Future)
  - whatsapp_send_image (with image_url)
  - whatsapp_send_file (with file_url)
  - whatsapp_get_messages (fetch message history)
  - whatsapp_create_group (create new group)
  - whatsapp_add_to_group (add member to group)

- [ ] **9.2 Add Webhook Support** (Future)
  - Receive incoming WhatsApp messages
  - Auto-reply with JAWIR agent
  - Store messages in database

- [ ] **9.3 Add Message Queue** (Future)
  - Queue outgoing messages
  - Retry failed sends
  - Rate limit to avoid ban

- [ ] **9.4 Add Multi-Device Support** (Future)
  - Support multiple WhatsApp accounts
  - User selects device via CLI
  - Each user has own device

## 🚨 CRITICAL PATH (Must Do First)

1. ✅ Code implementation (DONE)
2. **→ Device login** (BLOCKER - do this NOW!)
3. → Manual API test
4. → Python tool test
5. → JAWIR CLI test

## 📊 Success Criteria

- ✅ All 5 tools working without errors
- ✅ Device stays connected (no frequent disconnects)
- ✅ Error messages are user-friendly
- ✅ Tools integrate seamlessly with JAWIR agent
- ✅ Response time < 5 seconds per tool call
- ✅ Documentation complete and clear

## 🔗 Quick Links

- **GoWA Web UI:** http://13.55.23.245:3000
- **GoWA API Docs:** http://13.55.23.245:3000/docs (if available)
- **VPS SSH:** `ssh ubuntu@13.55.23.245`
- **Service Status:** `sudo systemctl status gowa.service`
- **Service Logs:** `sudo journalctl -u gowa.service -f`

## 📝 Notes

- **Auth:** admin / jawir2026 (Basic Auth)
- **Port:** 3000 (opened in UFW)
- **Device JID format:** 628xxx@s.whatsapp.net
- **Phone format:** International without + (e.g., 628123456789)
- **Max groups:** 500 (GoWA API limit)
- **Timeout:** 30s per request (with 3 retries)

## 🎯 Next Action

**RIGHT NOW:** Open http://13.55.23.245:3000 dan login device!

Setelah device logged in, run:
```powershell
cd D:\expo\jawirv3\jawirv2\jawirv2\backend
.\test_gowa_manual.ps1
```

Jika semua test pass, lanjut:
```powershell
python test_whatsapp_tools_robust.py
```
