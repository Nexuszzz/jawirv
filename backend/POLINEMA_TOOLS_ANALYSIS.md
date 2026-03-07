# Analisis JAWIR dan Refactor Polinema Tools

## 📊 ANALISIS SISTEM JAWIR

### **Arsitektur JAWIR (Function Calling Mode)**

```
┌─────────────────────────────────────────────────────────────┐
│                    JAWIR OS Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React)                                            │
│    ↓ WebSocket (/ws/chat)                                   │
│  Backend (FastAPI)                                           │
│    ├── app/main.py (WebSocket handler)                      │
│    ├── app/api/websocket.py (handle_websocket_message)      │
│    └── app/config.py (Settings)                             │
│         ↓                                                     │
│  Agent Layer (LangGraph)                                     │
│    ├── agent/graph.py (get_compiled_graph)                  │
│    ├── agent/nodes/function_calling_agent.py                │
│    └── agent/function_calling_executor.py                   │
│         ↓                                                     │
│  Tools Registry                                              │
│    ├── agent/tools_registry.py (backward compat wrapper)    │
│    └── agent/tools/__init__.py (modular aggregator)         │
│         ├── tools/web.py (Tavily search)                    │
│         ├── tools/kicad.py (KiCad design)                   │
│         ├── tools/python_exec.py (Python executor)          │
│         ├── tools/google.py (Gmail, Drive, Calendar, Sheets)│
│         ├── tools/desktop.py (Open/close apps)              │
│         └── tools/whatsapp.py (WhatsApp integration)        │
│                                                               │
│  Gemini Function Calling                                     │
│    - bind_tools() API                                        │
│    - Auto tool selection                                     │
│    - Max 5 iterations                                        │
│    - API key rotation                                        │
└─────────────────────────────────────────────────────────────┘
```

### **Tool Pattern di JAWIR**

#### 1. **Pydantic Input Schema**
```python
class ToolNameInput(BaseModel):
    """Input schema for tool_name."""
    param1: str = Field(description="Natural language description untuk Gemini")
    param2: int = Field(default=10, description="Optional dengan default")
```

#### 2. **Factory Function**
```python
def create_tool_name_tool() -> StructuredTool:
    """Create tool_name tool."""
    
    async def _tool_name(param1: str, param2: int = 10) -> str:
        """Short description."""
        try:
            # Tool logic
            result = do_something(param1, param2)
            return f"✅ Success: {result}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    return StructuredTool.from_function(
        func=_tool_name,
        coroutine=_tool_name,  # WAJIB async
        name="tool_name",
        description="Deskripsi natural language untuk Gemini decision making",
        args_schema=ToolNameInput,
    )
```

#### 3. **Registration di `agent/tools/__init__.py`**
```python
def get_all_tools() -> list[StructuredTool]:
    tools = []
    try:
        from agent.tools.category import create_tool_name_tool
        tools.append(create_tool_name_tool())
        logger.info("✅ Registered: tool_name")
    except Exception as e:
        logger.warning(f"⚠️ Failed to register tool_name: {e}")
    return tools
```

### **Current Tools (15 registered)**
1. `web_search` - Tavily web search
2. `generate_kicad_schematic` - KiCad design
3. `run_python_code` - Python execution
4. `gmail_search`, `gmail_send` - Gmail ops
5. `drive_search`, `drive_list` - Google Drive
6. `calendar_list_events`, `calendar_create_event` - Calendar
7. `sheets_read`, `sheets_write`, `sheets_create` - Sheets
8. `docs_read`, `docs_create` - Docs
9. `open_app`, `open_url`, `close_app` - Desktop control

---

## 🎯 REFACTOR PLAN: POLINEMA TOOLS

### **Target: 3 New Tools**

1. **`polinema_get_biodata`** - Get mahasiswa biodata
2. **`polinema_get_akademik`** - Get kehadiran, nilai, jadwal, kalender
3. **`polinema_get_lms_assignments`** - Get LMS SPADA assignments

### **Architecture Decision**

**TIDAK** membuat tool `polinema_scrape_all` karena:
- Terlalu broad dan lambat (scrape semua ~60 detik)
- Gemini tidak bisa efisien (harus scrape semua untuk cari 1 info)
- Violates single responsibility principle

**LEBIH BAIK** split menjadi 3 tools spesifik:
- Gemini bisa pilih tool mana yang dibutuhkan
- Faster execution (hanya scrape yang diminta)
- Better error handling per-category
- Scalable (mudah tambah tool baru)

---

## 📦 IMPLEMENTATION PLAN

### **File Structure**
```
backend/
├── agent/
│   └── tools/
│       ├── polinema.py          # NEW: 3 Polinema tools
│       └── __init__.py          # UPDATE: register Polinema tools
├── polinema-connector/
│   ├── scraper_enhanced.js      # EXISTING: Keep as-is
│   ├── polinema_api_server.py   # NEW: Node.js proxy API
│   └── package.json             # EXISTING
└── polinema_tools.py             # DEPRECATED (remove after migration)
```

### **Strategy: Node.js Scraper + Python Proxy**

**WHY?**
- Scraper sudah bekerja sempurna di Node.js + Playwright
- Python `playwright` install complex (requires system deps)
- Lebih mudah: Python call Node.js via subprocess atau HTTP API

**Option 1: HTTP API Proxy** (RECOMMENDED)
```
Python Tool → HTTP Request → Node.js Express Server → Playwright → Return JSON
```

**Option 2: Subprocess** 
```
Python Tool → subprocess.run(['node', 'scraper.js', '--biodata']) → Parse stdout
```

Pilih **Option 1** karena:
- Persistent browser session (faster, no re-login)
- Better error handling
- Can reuse existing Express knowledge
- Scalable for future enhancements

---

## ✅ DELIVERABLES

1. **`backend/polinema-connector/polinema_api_server.py`**
   - FastAPI server wrapping Node.js scraper
   - Endpoints: `/biodata`, `/akademik`, `/lms/assignments`
   - Manages Node.js process lifecycle

2. **`backend/agent/tools/polinema.py`**
   - 3 StructuredTool implementations
   - Calls polinema_api_server endpoints
   - Proper error handling & formatting

3. **`backend/agent/tools/__init__.py`**
   - Updated to import and register Polinema tools

4. **Documentation**
   - Update `TOOLS_INVENTORY.md`
   - Add usage examples

---

## 🚀 NEXT STEPS

1. ✅ Analisis JAWIR architecture - DONE
2. ⬜ Build `polinema_api_server.py` (FastAPI wrapper)
3. ⬜ Build `agent/tools/polinema.py` (3 tools)
4. ⬜ Update `agent/tools/__init__.py`
5. ⬜ Test integration
6. ⬜ Documentation

**User akan integrasikan sendiri** - Kita buat toolsnya siap pakai!
