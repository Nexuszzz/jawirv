# 🚀 Polinema Tools - Quick Reference

## ⚡ TLDR - Start in 30 Seconds

```powershell
# Terminal 1: Start Polinema API
cd D:\expo\jawirv3\jawirv2\jawirv2\backend\polinema-connector
.\start_polinema_api.ps1

# Terminal 2: Start JAWIR (wait for API to be ready)
cd D:\expo\jawirv3\jawirv2\jawirv2\backend
python -m uvicorn app.main:app --port 8000

# Done! Chat dengan JAWIR:
# "Siapa nama saya?"
# "Tugas apa yang harus dikerjakan?"
```

---

## 📋 Files Created

```
backend/
├── agent/tools/
│   ├── polinema.py                     ✅ NEW (3 tools)
│   └── __init__.py                     ✅ UPDATED (register tools)
│
└── polinema-connector/
    ├── polinema_api_server.py          ✅ NEW (FastAPI server)
    ├── start_polinema_api.ps1          ✅ NEW (startup script)
    ├── start_polinema_api.bat          ✅ NEW (startup batch)
    ├── test_polinema_api.ps1           ✅ NEW (test script)
    ├── POLINEMA_INTEGRATION_GUIDE.md   ✅ NEW (full docs)
    ├── POLINEMA_TOOLS_READY.md         ✅ NEW (summary)
    ├── QUICK_REFERENCE.md              ✅ NEW (this file)
    └── scraper_enhanced.js             ✅ EXISTING (working)
```

---

## 🎯 Tools Overview

| Tool Name | Purpose | Time | Status |
|-----------|---------|------|--------|
| `polinema_get_biodata` | Get biodata (nama, NIM, prodi) | 5-10s | ✅ Ready |
| `polinema_get_akademik` | Get kehadiran, nilai, jadwal | 30-40s | ✅ Ready |
| `polinema_get_lms_assignments` | Get LMS courses + 13 tugas | 60-80s | ✅ Ready |

---

## 💬 Example Conversations

```
User: Siapa nama saya?
JAWIR: [polinema_get_biodata]
       Nama lengkap kamu adalah MUHAMMAD FAKHRI ZAMANI

User: Jadwal kuliah saya hari ini?
JAWIR: [polinema_get_akademik]
       Jadwal hari ini:
       - 08:00 Workshop Jaringan Komputer
       - 13:00 Sistem Komunikasi Seluler

User: Ada tugas apa?
JAWIR: [polinema_get_lms_assignments]
       Ada 13 tugas aktif:
       - Jaringan Wireless (Essay)
       - Quiz 2D
       ... (11 more)
```

---

## 🧪 Testing

```powershell
# Test API server
cd backend/polinema-connector
.\test_polinema_api.ps1

# Test tools from Python
cd backend
python -c "from agent.tools import get_all_tools; print(f'{len(get_all_tools())} tools')"
# Should output: 21 tools
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Start API server: `.\start_polinema_api.ps1` |
| Node not found | Install Node.js from nodejs.org |
| Tools not registered | Check logs: "✅ Registered: polinema_*" |
| Scraper fails | Check credentials in `scraper_enhanced.js` |

---

## 📖 Full Documentation

- **Integration Guide:** [POLINEMA_INTEGRATION_GUIDE.md](./POLINEMA_INTEGRATION_GUIDE.md)
- **Architecture Analysis:** [../POLINEMA_TOOLS_ANALYSIS.md](../POLINEMA_TOOLS_ANALYSIS.md)
- **Complete Summary:** [POLINEMA_TOOLS_READY.md](./POLINEMA_TOOLS_READY.md)

---

## ✅ Checklist

- [ ] API server started and healthy
- [ ] JAWIR backend running
- [ ] Tools showing in logs (21 total)
- [ ] Test query: "Siapa nama saya?"
- [ ] Test query: "Ada tugas apa?"

**All ready? Start chatting! 🎉**
