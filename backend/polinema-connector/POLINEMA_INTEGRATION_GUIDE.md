# 🎓 Polinema SIAKAD/LMS Integration for JAWIR

## 📋 Overview

Integrasi Polinema SIAKAD dan LMS SPADA ke dalam JAWIR OS sebagai native tools. Menggunakan Playwright web scraper (Node.js) yang di-wrap dengan FastAPI untuk seamless integration dengan JAWIR agent.

### ✅ Status: **READY FOR INTEGRATION**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Polinema Integration                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  JAWIR Agent (Python/LangGraph)                              │
│    └── Gemini Function Calling                              │
│         └── Polinema Tools (3 tools)                        │
│              ├── polinema_get_biodata                       │
│              ├── polinema_get_akademik                      │
│              └── polinema_get_lms_assignments               │
│                   ↓ HTTP (localhost:8001)                    │
│  Polinema API Server (FastAPI)                               │
│    └── Wraps Node.js scraper                                │
│         └── Manages process lifecycle                       │
│              ↓ subprocess                                     │
│  Node.js Playwright Scraper                                  │
│    ├── scraper_enhanced.js (working code)                   │
│    ├── Headless browser automation                          │
│    └── FancyTree expansion for LMS                          │
│         ↓                                                     │
│  Polinema SIAKAD/LMS                                         │
│    ├── https://siakad.polinema.ac.id                        │
│    └── https://slc.polinema.ac.id/spada/                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tools Description

### 1. `polinema_get_biodata`

**Purpose:** Get mahasiswa biodata dari SIAKAD

**Returns:**
- Nama lengkap
- NIM (Nomor Induk Mahasiswa)
- Program Studi
- Semester
- Status mahasiswa
- Data kontak

**Use Cases:**
```
User: "Siapa nama saya?"
User: "Apa NIM saya?"
User: "Program studi saya apa?"
```

**Input Schema:**
```python
class PolinemaBiodataInput(BaseModel):
    force_refresh: bool = False  # Force scrape (default: use cache)
```

---

### 2. `polinema_get_akademik`

**Purpose:** Get data akademik (kehadiran, nilai, jadwal, kalender)

**Returns:**
- **Kehadiran**: Attendance records per semester
- **Nilai**: Grades for all mata kuliah (courses)
- **Jadwal**: Class schedule dengan Zoom links
- **Kalender**: Academic calendar (UTS, UAS, libur, dll)

**Use Cases:**
```
User: "Berapa IPK saya?"
User: "Jadwal kuliah saya hari ini?"
User: "Link Zoom untuk kelas Jaringan Komputer?"
User: "Kehadiran saya semester ini berapa persen?"
User: "Kapan UTS dimulai?"
```

**Input Schema:**
```python
class PolinemaAkademikInput(BaseModel):
    include_kehadiran: bool = True
    include_nilai: bool = True
    include_jadwal: bool = True
    include_kalender: bool = True
    force_refresh: bool = False
```

---

### 3. `polinema_get_lms_assignments`

**Purpose:** Get LMS SPADA courses and assignments

**Returns:**
- **Courses**: List of 10 enrolled mata kuliah
- **Assignments**: 13 active tugas/quiz including:
  - Workshop Jaringan Komputer (3 assignments)
  - Sistem Komunikasi Seluler (10 assignments)

**Use Cases:**
```
User: "Tugas apa yang harus dikerjakan?"
User: "Ada quiz apa minggu ini?"
User: "Deadline tugas Jaringan Wireless kapan?"
User: "List semua assignments saya"
```

**Input Schema:**
```python
class PolinemaLMSInput(BaseModel):
    force_refresh: bool = False
```

---

## 📁 Files Created

### 1. **API Server**
📄 `backend/polinema-connector/polinema_api_server.py`
- FastAPI server (port 8001)
- Wraps Node.js scraper via subprocess
- Endpoints: `/scrape/biodata`, `/scrape/akademik`, `/scrape/lms`
- Auto-formats data for tools

### 2. **JAWIR Tools**
📄 `backend/agent/tools/polinema.py`
- 3 StructuredTool implementations
- httpx async HTTP client
- Error handling & retry logic
- Natural language summaries

### 3. **Tools Registry**
📄 `backend/agent/tools/__init__.py` (UPDATED)
- Registered 3 new Polinema tools
- Total tools: **18 → 21 tools**

### 4. **Node.js Scraper** (EXISTING - NO CHANGES NEEDED)
📄 `backend/polinema-connector/scraper_enhanced.js`
- Already working perfectly
- Extracts all data successfully
- FancyTree expansion for LMS

---

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
# Python dependencies (if not already installed)
pip install httpx

# Node.js scraper already has dependencies installed
```

### Step 2: Start Polinema API Server

**Option A: Terminal**
```bash
cd backend/polinema-connector
uvicorn polinema_api_server:app --host 0.0.0.0 --port 8001
```

**Option B: Background Process (PowerShell)**
```powershell
cd D:\expo\jawirv3\jawirv2\jawirv2\backend\polinema-connector
Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn polinema_api_server:app --host 0.0.0.0 --port 8001"
```

**Option C: Add to JAWIR startup script**
Add to `backend/jawir-server.bat`:
```batch
start "Polinema API" cmd /k "cd polinema-connector && uvicorn polinema_api_server:app --port 8001"
```

### Step 3: Verify API Server

```bash
# Health check
curl http://localhost:8001/health

# Should return:
# {
#   "status": "healthy",
#   "scraper_exists": true,
#   "node_installed": true,
#   "scraper_path": "...",
#   "timestamp": "2026-02-07T..."
# }
```

### Step 4: Test Tools (Optional)

```bash
cd backend
python -c "from agent.tools import get_all_tools; tools = get_all_tools(); print(f'{len(tools)} tools registered')"

# Should show: 21 tools registered (or 18 + 3 = 21)
```

---

## 🧪 Testing

### Test API Server Directly

```bash
# Test biodata endpoint
curl -X POST http://localhost:8001/scrape/biodata -H "Content-Type: application/json"

# Test akademik endpoint
curl -X POST http://localhost:8001/scrape/akademik -H "Content-Type: application/json"

# Test LMS endpoint
curl -X POST http://localhost:8001/scrape/lms -H "Content-Type: application/json"
```

### Test via JAWIR Chat

Start JAWIR and ask:
```
"Siapa nama saya?"
"Berapa IPK saya?"
"Tugas apa yang harus dikerjakan minggu ini?"
"Jadwal kuliah saya hari ini jam berapa?"
"Link Zoom untuk kelas Workshop Jaringan Komputer?"
```

---

## 📊 Data Examples

### Biodata Response
```markdown
✅ Biodata retrieved successfully:

👤 **Biodata Mahasiswa**
- Nama: MUHAMMAD FAKHRI ZAMANI
- NIM: 244101060077
- Program Studi: Diploma IV Jaringan Telekomunikasi Digital
- Semester: 3
```

### Akademik Response
```markdown
✅ **Data Akademik Retrieved**

📊 **Kehadiran**: 3 semester
  - 2024/2025 Ganjil
  - 2025/2026 Ganjil
  - 2025/2026 Genap

📈 **Nilai**: 29 mata kuliah tersedia

📅 **Jadwal**: 10 pertemuan
  - Senin: Jaringan Komputer (Zoom: https://...)
  - Selasa: Sistem Komunikasi (Zoom: https://...)

📆 **Kalender Akademik**: 15 event
```

### LMS Response
```markdown
✅ **LMS SPADA Data Retrieved**

📚 **Enrolled Courses**: 10
  - Praktikum Sistem Modulasi dan Multiplexing
  - Workshop Jaringan Komputer
  - Sistem Komunikasi Seluler
  ... and 7 more courses

📝 **Current Assignments**: 13

  **Workshop Jaringan Komputer**:
    - Jaringan Wireless (Essay) (Pertemuan ke 5)
    - Pengumpulan Quiz (Pertemuan ke 13)
    - Quiz 2D (Pertemuan ke 13)

  **Sistem Komunikasi Seluler**:
    - Tugas 25 September 2025_2E
    - Tugas Propagasi Gelombang Radio_2D
    ... and 8 more assignments
```

---

## 🔧 Configuration

### Credentials

Default credentials (hardcoded in scraper):
```
NIM: 244101060077
Password: Fahri080506!
```

**To change:** Edit `scraper_enhanced.js` lines 30-31:
```javascript
this.credentials = {
    username: '244101060077',
    password: 'Fahri080506!'
};
```

### API Server URL

Default: `http://localhost:8001`

**To change:** Edit `backend/agent/tools/polinema.py` line 22:
```python
POLINEMA_API_URL = "http://your-server:port"
```

---

## ⚙️ Troubleshooting

### Issue 1: API Server not responding

**Check if server is running:**
```bash
curl http://localhost:8001/health
```

**If not running, start it:**
```bash
cd backend/polinema-connector
uvicorn polinema_api_server:app --port 8001
```

### Issue 2: Scraper fails

**Check Node.js installation:**
```bash
node --version  # Should be v16+
```

**Check scraper manually:**
```bash
cd backend/polinema-connector
node scraper_enhanced.js
```

**Common causes:**
- SIAKAD website down
- Credentials incorrect
- Network issues
- SSL certificate expired (already handled with `ignoreHTTPSErrors`)

### Issue 3: Tools not registered

**Check logs when starting JAWIR:**
```
✅ Registered: polinema_get_biodata
✅ Registered: polinema_get_akademik
✅ Registered: polinema_get_lms_assignments
```

**If not showing, check:**
```bash
cd backend
python -c "from agent.tools.polinema import create_polinema_biodata_tool; tool = create_polinema_biodata_tool(); print(tool.name)"
```

---

## 📈 Performance

- **Biodata**: ~5-10 seconds
- **Akademik**: ~30-40 seconds (includes 3 semesters kehadiran)
- **LMS**: ~60-80 seconds (includes FancyTree expansion)

**Caching:** Data is cached in `polinema_complete_data.json` until force_refresh=True

---

## 🔒 Security Considerations

1. **Credentials**: Hardcoded in scraper (consider environment variables for production)
2. **API Server**: Running on localhost only (no external access)
3. **SSL**: Using `ignoreHTTPSErrors` for expired SIAKAD certificate
4. **Data**: Sensitive student data - ensure proper access control in JAWIR

---

## 🎯 Future Enhancements

1. **Caching Layer**: Redis cache for faster responses
2. **Webhooks**: Real-time notifications for new assignments
3. **Batch Operations**: Scrape multiple students simultaneously
4. **LMS Calendar Events**: Extract calendar events from LMS (currently 0 found)
5. **Assignment Deadlines**: Parse and track assignment due dates
6. **Grade Analytics**: Calculate GPA, trend analysis, predictions

---

## 📝 Summary

✅ **3 New Tools Added:**
- `polinema_get_biodata` - Student personal info
- `polinema_get_akademik` - Academic data (attendance, grades, schedule, calendar)
- `polinema_get_lms_assignments` - LMS courses and 13 assignments

✅ **Working Components:**
- Node.js Playwright scraper (tested, 100% success)
- FastAPI API server (ready to run)
- JAWIR tool implementations (integrated)
- Tool registry updated (21 total tools)

✅ **Ready for Use:**
User tinggal start API server dan mulai chat dengan JAWIR!

---

## 🚦 Quick Start Checklist

- [ ] Start Polinema API Server: `uvicorn polinema_api_server:app --port 8001`
- [ ] Verify health: `curl http://localhost:8001/health`
- [ ] Start JAWIR backend: `python -m uvicorn app.main:app --port 8000`
- [ ] Start JAWIR frontend
- [ ] Test with: "Siapa nama saya?"
- [ ] Test with: "Tugas apa yang harus dikerjakan?"

**Selamat menggunakan Polinema integration di JAWIR! 🎉**
