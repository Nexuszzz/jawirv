# JAWIR OS - Troubleshooting Function Calling

## Common Issues & Fixes

### 1. Tool Hallucination
**Gejala**: Gemini memanggil tool yang tidak relevan (misal `web_search` untuk "Halo")

**Penyebab**: System prompt kurang strict tentang kapan TIDAK menggunakan tools.

**Fix**:
- Edit `FUNCTION_CALLING_SYSTEM_PROMPT` di `agent/function_calling_executor.py`
- Tambahkan contoh eksplisit: "Untuk sapaan → jawab langsung, JANGAN panggil tool"
- Test dengan: "Halo JAWIR", "Siapa kamu?", "Terima kasih"

### 2. Infinite Tool Loop
**Gejala**: Agent terus memanggil tools tanpa pernah memberi final response.

**Penyebab**: Gemini tidak puas dengan tool results, terus retry.

**Fix**:
- `max_iterations=5` sudah di-set sebagai safety limit
- Jika terjadi, cek logs: apakah tool selalu return error?
- Pastikan tool results informatif (bukan empty string)

### 3. Tool Not Found
**Gejala**: `Tool 'xxx' tidak tersedia`

**Penyebab**: Tool name mismatch antara Gemini dan registry.

**Fix**:
```python
# Cek tools yang terdaftar
from agent.tools_registry import get_tool_names
print(get_tool_names())
# ['web_search', 'generate_kicad_schematic', 'run_python_code', ...]
```

### 4. API Key Rate Limit (429)
**Gejala**: `RESOURCE_EXHAUSTED` atau `429 Too Many Requests`

**Penyebab**: API key quota habis.

**Fix**:
- Executor otomatis rotate ke key lain (`_refresh_llm()`)
- Jika semua keys habis → rollback ke FC=false
- Tambah lebih banyak keys di `.env`:
```
GOOGLE_API_KEYS=key1,key2,key3,key4
```

### 5. PERMISSION_DENIED / Leaked Key
**Gejala**: `PERMISSION_DENIED: API key not valid`

**Penyebab**: API key expired atau terdeteksi sebagai leaked.

**Fix**:
- Generate API key baru di https://aistudio.google.com/apikey
- Update `.env` dengan key baru
- Restart server

### 6. Slow Response (>30 detik)
**Gejala**: Response sangat lambat.

**Penyebab**: Terlalu banyak tool calls per query.

**Diagnosis**:
```
# Cek FC Metrics di log:
📊 FC Metrics: iterations=4, tool_calls=7, tools_used=['web_search', 'gmail_search'], errors=0, time=28.5s
```

**Fix**:
- Tune system prompt: instruksikan gunakan minimal tools
- Set `max_iterations=3` (default 5)
- Implement tool result caching (task 6.1)

### 7. Google Workspace Tool Errors
**Gejala**: `Error Gmail search: Google Workspace MCP not found`

**Penyebab**: MCP server path tidak ditemukan.

**Fix**:
- Pastikan `google_workspace_mcp/` ada di lokasi yang benar
- Cek path di `tools/google_workspace.py` → `_find_mcp_path()`
- Pastikan OAuth credentials sudah di-setup

### 8. Desktop Control Tool Errors (Windows Only)
**Gejala**: `Failed to open chrome`

**Penyebab**: App path tidak ditemukan di Windows.

**Fix**:
- Cek path di `tools/python_interpreter/desktop_control.py` → `APPS` dict
- Update path sesuai instalasi lokal
- Tools ini hanya support Windows (`sys.platform == "win32"`)

## Debug Commands

```python
# Quick verification script
import sys; sys.path.insert(0, '.')

# 1. Check tools
from agent.tools_registry import get_all_tools, get_tool_names
tools = get_all_tools()
print(f"Tools: {len(tools)}")
print(f"Names: {get_tool_names()}")

# 2. Check graph
from agent.graph import build_jawir_graph_v2
graph = build_jawir_graph_v2()
compiled = graph.compile()
print(f"Nodes: {list(compiled.get_graph().nodes.keys())}")

# 3. Check config
from app.config import settings
print(f"FC enabled: {settings.use_function_calling}")
```

## Rollback Procedure

Lihat `ROLLBACK.md` untuk prosedur rollback lengkap.
