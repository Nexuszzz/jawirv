# JAWIR OS + GoWA Integration - Deep Analysis & Plan
=======================================================

## 📊 PART 1: JAWIR Architecture Analysis

### 1.1 Flow Diagram: User → Response

```
┌────────────┐
│ USER INPUT │ "kirim WA ke bos 'meeting jam 10'"
└─────┬──────┘
      │
      v
┌─────────────────┐
│  JAWIR CLI      │  jawir_cli.py
│  - WebSocket    │  ws://localhost:8000/ws/chat
│  - ReAct Track  │  Cumulative step display
│  - Session ID   │  ~/.jawir/session_id
└───────┬─────────┘
        │ JSON message: {"type": "user_message", "data": {...}}
        v
┌─────────────────────────────┐
│  FastAPI Backend (main.py)   │
│  @websocket("/ws/chat")      │
└─────────┬───────────────────┘
          │ handle_websocket_message()
          v
┌──────────────────────────────┐
│  WebSocket Handler           │  app/api/websocket.py
│  - ConnectionManager         │  Manage WS connections
│  - Message routing           │  type: user_message/system/etc
│  - Session management        │  session_id → conversation state
└─────────┬────────────────────┘
          │ Dispatch to ReAct Agent
          v
┌────────────────────────────────────────────────────┐
│  ReActExecutor (react_executor.py)                 │
│  ┌──────────────────────────────────────────┐     │
│  │  ReAct Loop (max 50 iterations)          │     │
│  │  1. THOUGHT   → "Perlu kirim WA"         │     │
│  │  2. ACTION    → whatsapp_send_message()  │     │
│  │  3. OBSERVE   → "✅ Sent"                │     │
│  │  4. EVALUATE  → "Goal achieved"          │     │
│  │  5. LOOP/DONE → Stop or iterate          │     │
│  └──────────────────────────────────────────┘     │
│                                                     │
│  Components:                                        │
│  - ChatGoogleGenerativeAI (Gemini 2.0)            │
│  - .bind_tools(tools) → Native function calling   │
│  - Tool execution: _execute_tool()                │
│  - Error retry: Self-correction logic             │
│  - Streaming: Yield events via SSE                │
└─────────┬───────────────────────────────────────┘
          │ Tool call: whatsapp_send_message
          v
┌────────────────────────────────┐
│  Tool Registry (__init__.py)   │
│  - get_all_tools() → List      │
│  - 19 tools registered:        │
│    ├─ web_search               │
│    ├─ run_python_code          │
│    ├─ gmail_search/send        │
│    ├─ drive_search/list        │
│    ├─ sheets_create/read/write │
│    ├─ forms_create/add         │
│    ├─ open_app/close_app       │
│    └─ (NEW) whatsapp_* x5      │
└─────────┬──────────────────────┘
          │ Execute tool
          v
┌────────────────────────────────┐
│  Tool Implementation           │
│  agent/tools/whatsapp.py       │
│  - Input validation (Pydantic) │
│  - Call GoWAClient wrapper     │
│  - Format response for LLM     │
└─────────┬──────────────────────┘
          │ HTTP REST API call
          v
┌────────────────────────────────┐
│  GoWA Client (gowa_client.py)  │
│  - httpx.BasicAuth()           │
│  - Endpoint wrapper            │
│  - Error handling              │
└─────────┬──────────────────────┘
          │ HTTP Request
          v
┌────────────────────────────────┐
│  VPS GoWA Server               │
│  http://13.55.23.245:3000      │
│  - REST API (Fiber Go)         │
│  - whatsmeow library           │
│  - PostgreSQL/SQLite           │
└─────────┬──────────────────────┘
          │ WhatsApp Protocol
          v
┌────────────────────────────────┐
│  WhatsApp Servers              │
│  - Multi-device protocol       │
│  - End-to-end encrypted        │
└────────────────────────────────┘
```

---

## 📋 PART 2: JAWIR Components Deep Dive

### 2.1 WebSocket Communication (jawir_cli.py)

**Key Features:**
- **Protocol**: WebSocket (bidirectional)
- **Ping/Pong**: 20s interval, 120s timeout (upgraded from 30s)
- **Max size**: 10MB messages
- **Session**: Persistent ID (~/.jawir/session_id)

**Message Flow:**
```python
# Client → Server
{
    "type": "user_message",
    "data": {
        "content": "kirim WA ke 08xxx 'halo'",
        "session_id": "uuid-4",
    }
}

# Server → Client (streaming events)
{"type": "thinking", "data": {"thought": "Perlu kirim WhatsApp..."}}
{"type": "executing_tool", "data": {"tool": "whatsapp_send_message", "args": {...}}}
{"type": "observation", "data": {"result": "✅ Sent"}}
{"type": "final_response", "data": {"text": "Pesan berhasil dikirim!"}}
```

**ReAct Step Display:**
```
━━━ ReAct Loop 1/50 ━━━
[  0.5s] 💭 THINKING: Perlu kirim pesan WhatsApp ke nomor...
[  1.2s] 📋 PLANNING: 2 aksi direncanakan
              ├─ 1. whatsapp_check_number
              ├─ 2. whatsapp_send_message
[  2.1s] 🔧 ACTION [0]: whatsapp_check_number
              └─ params: {'phone': '6281234567890'}
[  3.5s] 👁️ OBSERVE: ✅ Nomor terdaftar di WhatsApp
[  4.0s] 🔧 ACTION [1]: whatsapp_send_message
[  5.2s] 👁️ OBSERVE: ✅ Pesan berhasil dikirim
```

---

### 2.2 ReAct Agent Loop (react_executor.py)

**Pattern:**
```
ITERATION N:
  ├─ THOUGHT:    Agent reasons about goal
  ├─ ACTION:     Execute 1+ tools in parallel
  ├─ OBSERVE:    Collect tool results
  ├─ EVALUATE:   Check if goal achieved
  └─ DECISION:   Done? Or loop again?
```

**Key Variables:**
- `max_iterations = 50` (upgraded from 25)
- `temperature = 0.7`
- `model = gemini-3-pro-preview` (Gemini 2.0 Flash)

**Self-Correction Logic:**
```python
if tool_error:
    memory.add_failure(tool_name, error)
    if retry_count < 3:
        # Try different parameters
        # Or try alternative tool
    else:
        # Explain to user what failed
```

---

### 2.3 Tool Pattern (google.py as reference)

**Current Pattern untuk Google Workspace:**

```python
# 1. Tool Factory Function
def create_gmail_search_tool() -> StructuredTool:
    
    # 2. Async Implementation
    async def _gmail_search(query: str, max_results: int = 5) -> str:
        try:
            # 3. Import MCP subprocess wrapper
            from tools.google_workspace import GoogleWorkspaceMCP
            
            # 4. Call MCP CLI
            gws = GoogleWorkspaceMCP()
            result = gws.search_gmail(query, max_results=max_results)
            
            # 5. Check success
            if not result.get("success"):
                return f"Error: {result.get('error')}"
            
            # 6. Format output for LLM
            output = result.get("output", "")
            return f"Hasil Gmail:\n{output[:3000]}"
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    # 7. Register as StructuredTool
    return StructuredTool.from_function(
        func=_gmail_search,
        coroutine=_gmail_search,
        name="gmail_search",
        description="Search email di Gmail...",
        args_schema=GmailSearchInput,
    )
```

**GoogleWorkspaceMCP Pattern:**
```python
# tools/google_workspace.py

class GoogleWorkspaceMCP:
    def _run_cli_tool(self, tool_name: str, args: dict) -> dict:
        # Build CLI command
        cmd = [
            sys.executable,
            self.mcp_path,
            tool_name,
            json.dumps(args)
        ]
        
        # Execute subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=self._get_env()
        )
        
        # Parse output
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
        }
```

**IMPORTANT:** Google tools use **subprocess MCP CLI** execution, NOT HTTP REST API!

---

## 🔍 PART 3: GoWA Repository Analysis

### 3.1 Project Structure

```
go-whatsapp-web-multidevice/
├── src/
│   ├── main.go              → Entry point (cmd.Execute)
│   ├── cmd/                 → CLI commands (rest, mcp)
│   │   ├── root.go          → Cobra root command
│   │   ├── rest.go          → REST API mode
│   │   └── mcp.go           → MCP server mode
│   ├── domains/             → Business logic
│   │   ├── app/             → Login, logout, device management
│   │   ├── send/            → Send message/media
│   │   ├── user/            → User info, contacts, groups
│   │   ├── message/         → Message operations (revoke, react)
│   │   ├── group/           → Group management
│   │   └── chat/            → Chat conversations
│   ├── infrastructure/      → External services
│   │   ├── database/        → SQLite/Postgres
│   │   ├── whatsmeow/       → WhatsApp client wrapper
│   │   └── fiber/           → HTTP server (REST)
│   ├── pkg/                 → Utilities
│   │   ├── whatsapp/        → WhatsApp helpers
│   │   └── utils/           → General utils
│   ├── validations/         → Request validators
│   ├── config/              → Configuration
│   └── views/               → Web UI templates
├── docs/
│   ├── openapi.yaml         → API documentation (4319 lines!)
│   ├── webhook-payload.md   → Webhook examples
│   └── chatwoot.md          → Chatwoot integration
├── docker/
│   └── golang.Dockerfile    → Docker build
├── docker-compose.yml       → Compose setup
└── readme.md                → Main docs
```

---

### 3.2 GoWA Execution Modes

**Mode 1: REST API (CURRENT VPS)**
```bash
./whatsapp rest \
  -p 3000 \
  -b admin:jawir2026 \
  --db-uri="file:storages/whatsapp.db?_foreign_keys=on"
```

**Characteristics:**
- HTTP REST API (Fiber framework)
- Basic Auth protected
- Multi-device support (v8+)
- Device scoping via `X-Device-Id` header
- Stateless (session in DB)

**Mode 2: MCP Server**
```bash
./whatsapp mcp -p 3001
```

**Characteristics:**
- Server-Sent Events (SSE) for tool discovery
- JSON-RPC 2.0 over stdio
- No HTTP server
- For AI agents (Claude Desktop, etc.)

---

### 3.3 GoWA API Endpoints (REST mode)

**Device Management:**
```
GET  /devices                 → List all devices
POST /devices                 → Create new device slot
GET  /devices/{id}            → Get device info
POST /devices/{id}/login      → QR code login
POST /devices/{id}/logout     → Logout device
```

**User Operations:**
```
GET /user/check?phone=628xxx  → Check if number registered
GET /user/info?phone=628xxx   → Get user profile
GET /user/my/contacts         → List contacts
GET /user/my/groups           → List groups (max 500)
```

**Chat Operations:**
```
GET /chat/conversations            → List chats
GET /chat/{jid}/messages?limit=50  → Get message history
```

**Send Operations:**
```
POST /send/message    → Send text (mentions, reply supported)
POST /send/image      → Send image + caption
POST /send/file       → Send document
POST /send/audio      → Send voice note
POST /send/video      → Send video
POST /send/sticker    → Send sticker (auto WebP convert)
```

**All endpoints require:**
- Basic Auth: `Authorization: Basic base64(admin:jawir2026)`
- Optional header: `X-Device-Id: 628xxx@s.whatsapp.net`

---

### 3.4 VPS Current Status

**Server:**
- IP: `13.55.23.245`
- Port: `3000` (firewall opened ✅)
- Service: `gowa.service` (systemd)
- Binary: `/home/ubuntu/whatsapp`
- User: `ubuntu`

**Configuration:**
```ini
[Service]
ExecStart=/home/ubuntu/whatsapp rest -b admin:jawir2026
Restart=always
RestartSec=5
```

**Status Check:**
```bash
$ systemctl status gowa.service
● gowa.service - GoWhatsApp Web API
     Active: active (running) since Fri 2026-02-06 14:33:39 UTC
   Main PID: 2219009
     Memory: 14.1M
      Tasks: 6
```

**API Test:**
```bash
$ curl -u admin:jawir2026 http://localhost:3000/user/check?phone=628xxx
{"code":"SUCCESS","message":"Success","results":[...]}
```

---

## ⚠️ PART 4: Integration Issues Identified

### Issue 1: Authentication Method Mismatch

**Problem:**
```python
# gowa_client.py (WRONG)
auth = (username, password)  # Tuple
response = client.request(..., auth=self.auth)
```

**Error:**
```
401 Unauthorized
```

**Root Cause:**
- `httpx` tuple auth doesn't automatically become Basic Auth
- Need explicit `httpx.BasicAuth()` wrapper

**Fix Applied:**
```python
auth=httpx.BasicAuth(self.auth[0], self.auth[1])
```

---

### Issue 2: Endpoint 404 - Device Not Logged In

**Problem:**
```
404 Not Found on /chat/conversations
```

**Reason:**
- GoWA v8 is multi-device
- No device logged in yet!
- Must login first via QR code or pairing code

**Fix Required:**
1. Check `/app/devices` → is device logged in?
2. If empty, generate QR: `GET /app/login`
3. Scan QR with WhatsApp mobile
4. Device JID becomes default for single-device setup

---

### Issue 3: Architecture Pattern Mismatch

**Google Workspace:**
```
Tool → GoogleWorkspaceMCP → subprocess → MCP CLI → OAuth → Google API
```

**WhatsApp (current plan):**
```
Tool → GoWAClient → httpx → VPS REST API → WhatsApp Protocol
```

**Difference:**
- Google: Subprocess, local auth, CLI wrapper
- WhatsApp: HTTP client, remote VPS, REST API

**This is OK!** Different services, different patterns. No need to force MCP for WhatsApp.

---

## 📐 PART 5: Proper Integration Plan

### Plan A: REST API Integration (RECOMMENDED)

**Architecture:**
```
┌─────────────────┐
│  JAWIR Backend  │ Windows
│  Python 3.13    │
└────────┬────────┘
         │ httpx.post()
         │ Basic Auth
         │
         v
┌─────────────────┐
│  VPS (AWS)      │ Ubuntu 24.04
│  13.55.23.245   │
│  Port 3000      │
└────────┬────────┘
         │ REST API
         v
┌─────────────────┐
│  GoWA Binary    │ Go 1.22.2
│  /home/ubuntu/  │
│  whatsapp       │
└────────┬────────┘
         │ whatsmeow
         v
┌─────────────────┐
│  WhatsApp Web   │
│  Multi-device   │
│  Protocol       │
└─────────────────┘
```

**Components:**
1. `tools/gowa_client.py` - HTTP wrapper ✅ (created, needs auth fix)
2. `agent/tools/whatsapp.py` - 5 tools ✅ (created)
3. `app/config.py` - VPS config ✅ (updated)
4. `agent/tools/__init__.py` - Registry ✅ (updated)

**Remaining Steps:**
1. Fix `httpx.BasicAuth()` ✅ (done)
2. Check device login status (CRITICAL)
3. If not logged in → generate QR → scan
4. Test 5 tools with real device
5. Add error handling for device offline
6. Document usage in JAWIR CLI

---

### Plan B: MCP Integration (FUTURE)

**Why NOT Now:**
- GoWA MCP mode is v8 feature (still evolving)
- MCP requires stdio communication (more complex)
- REST API is proven, stable, documented
- MCP adds no value for simple HTTP calls

**When to Consider:**
- If we need tool auto-discovery
- If GoWA adds MCP-specific features
- If we integrate with Claude Desktop

---

## 🛠️ PART 6: Implementation Checklist

### Phase 1: Device Setup & Basic Test

- [ ] **1.1** Test VPS GoWA API manually via curl
  ```bash
  curl -u admin:jawir2026 http://13.55.23.245:3000/app/devices
  ```

- [ ] **1.2** Check if device logged in
  - If empty → need to login
  - If exists → get device JID

- [ ] **1.3** If not logged in, generate QR code
  ```bash
  curl -u admin:jawir2026 http://13.55.23.245:3000/app/login
  ```
  
- [ ] **1.4** Scan QR with WhatsApp mobile (user's phone)

- [ ] **1.5** Verify device connected
  ```bash
  curl -u admin:jawir2026 http://13.55.23.245:3000/app/devices
  # Should return: { "jid": "628xxx@s.whatsapp.net", "logged_in": true }
  ```

### Phase 2: Fix Auth & Test Tools

- [x] **2.1** Fix `httpx.BasicAuth()` in `gowa_client.py`

- [ ] **2.2** Add device_id parameter support
  ```python
  # If multi-device, need X-Device-Id header
  headers = {"X-Device-Id": device_jid} if device_jid else {}
  ```

- [ ] **2.3** Test `whatsapp_check_number` with real number

- [ ] **2.4** Test `whatsapp_list_contacts` (requires logged in device)

- [ ] **2.5** Test `whatsapp_list_groups`

- [ ] **2.6** Test `whatsapp_list_chats`

- [ ] **2.7** Test `whatsapp_send_message` to own number (safe test)

### Phase 3: Integration with JAWIR Agent

- [ ] **3.1** Restart JAWIR backend with WhatsApp tools

- [ ] **3.2** Test via CLI: `/ask "cek nomor 08xxx ada WA?"`

- [ ] **3.3** Test via CLI: `/ask "list kontak WA saya"`

- [ ] **3.4** Test via CLI: `/ask "kirim WA ke 08xxx 'test message'"`

- [ ] **3.5** Verify ReAct loop displays correctly

- [ ] **3.6** Check tool quota tracking

- [ ] **3.7** Check tool analytics logging

### Phase 4: Error Handling & Edge Cases

- [ ] **4.1** Handle device offline (reconnect logic)

- [ ] **4.2** Handle rate limiting (WhatsApp ban risk)

- [ ] **4.3** Handle invalid phone numbers

- [ ] **4.4** Handle send failures (network, blocked, etc.)

- [ ] **4.5** Add retry logic for transient errors

- [ ] **4.6** Add user-friendly error messages

### Phase 5: Documentation & UX

- [ ] **5.1** Update README with WhatsApp tools usage

- [ ] **5.2** Add examples to JAWIR CLI help

- [ ] **5.3** Document VPS maintenance (restart, update)

- [ ] **5.4** Create troubleshooting guide

- [ ] **5.5** Add monitoring (device status check)

---

## 🚨 CRITICAL NEXT STEP

**STOP CODING! FIRST:**

1. **Login device ke GoWA di VPS**
   - Buka browser: `http://13.55.23.245:3000`
   - Login: admin / jawir2026
   - Generate QR code
   - Scan dengan WhatsApp mobile
   - Verify device connected

2. **Test API manually dari terminal**
   ```powershell
   $cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:jawir2026"))
   $headers = @{ "Authorization" = "Basic $cred" }
   
   # Test 1: Check devices
   Invoke-RestMethod -Uri "http://13.55.23.245:3000/app/devices" -Headers $headers
   
   # Test 2: List contacts (if device logged in)
   Invoke-RestMethod -Uri "http://13.55.23.245:3000/user/my/contacts" -Headers $headers
   ```

3. **ONLY AFTER device working → fix Python code**

---

## 📊 Summary

| Component | Status | Next Action |
|-----------|--------|-------------|
| JAWIR CLI | ✅ Working | No changes needed |
| React Agent | ✅ Working | No changes needed |
| Backend API | ✅ Working | No changes needed |
| Tool Registry | ✅ Updated | Ready to use |
| gowa_client.py | ⚠️ Auth issue | Fixed, needs test |
| WhatsApp tools | ✅ Created | Needs device login |
| VPS GoWA | ✅ Running | **NEEDS DEVICE LOGIN** |
| Integration | ❌ Not tested | Waiting for device |

**Blocker:** Device not logged in to WhatsApp Web yet!

**Action Required:** User must scan QR code to connect WhatsApp device.

