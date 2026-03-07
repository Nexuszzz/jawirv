# JAWIR OS - Function Calling Rollback Guide

## Quick Rollback (< 1 menit)

Jika Function Calling (FC) mode bermasalah, rollback ke legacy mode:

### Step 1: Edit `.env`
```bash
# Ubah dari true ke false
USE_FUNCTION_CALLING=false
```

### Step 2: Restart Server
```bash
# Kill server
Ctrl+C

# Restart
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Verify
- Buka Electron app
- Kirim pesan "Halo JAWIR"
- Pastikan response normal (V1 legacy mode)

## Kapan Harus Rollback

| Gejala | Penyebab | Aksi |
|--------|----------|------|
| JAWIR selalu panggil tools untuk greeting | System prompt kurang strict | Rollback + tune prompt |
| Infinite loop (tidak pernah respond) | max_iterations tidak tercapai | Rollback |
| "Tool not found" errors | Tool registry crash | Rollback |
| 429 Rate Limit terus-menerus | API keys habis quota | Rollback + cek API keys |
| Response sangat lambat (>30s) | Too many tool calls | Rollback |

## Arsitektur Dual-Mode

```
USE_FUNCTION_CALLING=true  → V2 Graph: quick_router → fc_agent (Gemini native FC)
USE_FUNCTION_CALLING=false → V1 Graph: supervisor → specialist nodes (manual routing)
```

Kedua mode bisa switch tanpa perubahan kode. Cukup ubah environment variable.

## Files yang Terlibat

| File | Peran |
|------|-------|
| `backend/.env` | Feature flag `USE_FUNCTION_CALLING` |
| `backend/app/config.py` | Settings.use_function_calling |
| `backend/agent/graph.py` | `get_compiled_graph()` branching |
| `backend/agent/tools_registry.py` | 12 tools untuk FC mode |
| `backend/agent/function_calling_executor.py` | FC execution loop |

## Kontak

Jika ada masalah setelah rollback, cek logs di terminal untuk error detail.
