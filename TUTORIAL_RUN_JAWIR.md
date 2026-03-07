# 📖 JAWIR OS V2 — Tutorial Lengkap: Cara Menjalankan Frontend & Backend

> **Terakhir diupdate**: 8 Februari 2026  
> **Versi**: 0.1.0  
> **Author**: JAWIR OS Team

---

## 📋 Daftar Isi

1. [Prasyarat (Prerequisites)](#1-prasyarat-prerequisites)
2. [Struktur Proyek](#2-struktur-proyek)
3. [Setup Backend](#3-setup-backend)
4. [Setup Frontend](#4-setup-frontend)
5. [Menjalankan Backend](#5-menjalankan-backend)
6. [Menjalankan Frontend](#6-menjalankan-frontend)
7. [Menjalankan dengan Electron (Desktop App)](#7-menjalankan-dengan-electron-desktop-app)
8. [Menjalankan Semua Sekaligus (Quick Start)](#8-menjalankan-semua-sekaligus-quick-start)
9. [Konfigurasi Environment (.env)](#9-konfigurasi-environment-env)
10. [Menjalankan Tests](#10-menjalankan-tests)
11. [Troubleshooting](#11-troubleshooting)
12. [Ports & URLs](#12-ports--urls)

---

## 1. Prasyarat (Prerequisites)

### Software yang HARUS diinstall:

| Software | Versi Minimum | Download |
|----------|---------------|----------|
| **Python** | 3.11+ (rekomendasi 3.12) | https://python.org/downloads |
| **Node.js** | 18+ (rekomendasi 20 LTS) | https://nodejs.org |
| **npm** | 9+ (bundled with Node.js) | — |
| **Git** | 2.40+ | https://git-scm.com |

### Cek versi yang terinstall:

```powershell
python --version    # harus 3.11+
node --version      # harus 18+
npm --version       # harus 9+
git --version       # harus 2.40+
```

### Opsional (untuk fitur tambahan):

| Software | Untuk Fitur | Download |
|----------|-------------|----------|
| **Playwright** | Browser Automation / Deep Research | `pip install playwright && playwright install` |
| **Electron** | Desktop App wrapper | Sudah di devDependencies |

---

## 2. Struktur Proyek

```
jawirv2/
├── backend/                    ← Python FastAPI backend (port 8000)
│   ├── app/                    ← FastAPI app (main.py, config.py, api/)
│   ├── agent/                  ← LangGraph agent (graph, tools, nodes)
│   ├── tools/                  ← External tool implementations
│   ├── tests/                  ← Test files
│   ├── .env                    ← Environment variables (BUAT SENDIRI)
│   ├── .env.example            ← Template environment
│   ├── requirements.txt        ← Python dependencies
│   └── venv_work/              ← Python virtual environment
│
├── frontend/                   ← React + Vite + Electron (port 5173)
│   ├── src/                    ← React source code
│   ├── electron/               ← Electron main process
│   ├── .env                    ← Frontend env vars
│   ├── package.json            ← Node.js dependencies
│   └── node_modules/           ← Installed packages
│
└── google_workspace_mcp/       ← Google Workspace MCP server
```

---

## 3. Setup Backend

### 3.1 Buat Virtual Environment

```powershell
# Masuk ke folder backend
cd D:\jawirv4\jawirv4\jawirv2\backend

# Buat virtual environment baru (sekali saja)
python -m venv venv_work

# Aktifkan virtual environment
.\venv_work\Scripts\activate

# Pastikan pip up-to-date
python -m pip install --upgrade pip
```

### 3.2 Install Dependencies

```powershell
# Pastikan venv aktif (ada (venv_work) di prompt)
pip install -r requirements.txt
```

> **Catatan**: Proses install bisa 5-10 menit tergantung internet.

### 3.3 Setup Environment File

```powershell
# Copy template
copy .env.example .env

# Edit .env dengan notepad/vscode
notepad .env
```

#### Isi `.env` yang WAJIB diisi:

```dotenv
# ═══════════════════════════════════════
# WAJIB - API Keys
# ═══════════════════════════════════════

# Gemini API Key (dari https://aistudio.google.com/apikey)
GOOGLE_API_KEY=your-gemini-api-key-here

# Atau multiple keys (untuk rotation, pisahkan dengan koma):
# GOOGLE_API_KEYS=key1,key2,key3

# Tavily Search API Key (dari https://tavily.com/)
TAVILY_API_KEY=your-tavily-api-key-here

# ═══════════════════════════════════════
# OPSIONAL - Server Config
# ═══════════════════════════════════════
WS_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
GEMINI_MODEL=gemini-2.0-flash

# ═══════════════════════════════════════
# OPSIONAL - Agent Mode
# ═══════════════════════════════════════
# false = V1 ReAct (manual routing, lebih verbose)
# true  = V2 Function Calling (Gemini auto-select tools, lebih cepat)
USE_FUNCTION_CALLING=true

# ═══════════════════════════════════════
# OPSIONAL - WhatsApp Gateway
# ═══════════════════════════════════════
# GOWA_BASE_URL=http://your-server:3000
# GOWA_USERNAME=admin
# GOWA_PASSWORD=your-password

# ═══════════════════════════════════════
# OPSIONAL - IoT (HiveMQ MQTT)
# ═══════════════════════════════════════
# IOT_ENABLED=true
# IOT_MQTT_HOST=your-broker.hivemq.cloud
# IOT_MQTT_PORT=8883
# IOT_MQTT_USER=your-user
# IOT_MQTT_PASS=your-pass
```

### 3.4 Verifikasi Setup

```powershell
# Test import modules
python -c "import fastapi; import langchain; print('Backend deps OK')"
```

---

## 4. Setup Frontend

### 4.1 Install Node.js Dependencies

```powershell
# Masuk ke folder frontend
cd D:\jawirv4\jawirv4\jawirv2\frontend

# Install semua packages
npm install
```

> **Catatan**: Proses install bisa 2-5 menit. Folder `node_modules/` akan dibuat.

### 4.2 Setup Environment File

```powershell
# Copy template (jika belum ada)
copy .env.example .env
```

#### Isi `.env` frontend:

```dotenv
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

> Biasanya default sudah benar, tidak perlu diubah.

### 4.3 Verifikasi Setup

```powershell
# Check TypeScript compilation
npx tsc --noEmit
# Harus keluar tanpa error
```

---

## 5. Menjalankan Backend

### Opsi A: Manual (Rekomendasi untuk Development)

```powershell
# 1. Masuk folder backend
cd D:\jawirv4\jawirv4\jawirv2\backend

# 2. Aktifkan virtual environment
.\venv_work\Scripts\activate

# 3. Jalankan server dengan hot-reload
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Output yang diharapkan:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to stop)
INFO:     Started reloader process
INFO:     MQTT connected to broker
INFO:     Registered 2 IoT devices
```

### Opsi B: Menggunakan BAT File

```powershell
# Double-click atau jalankan:
D:\jawirv4\jawirv4\jawirv2\backend\start_backend.bat
```

### Verifikasi Backend Berjalan:

Buka browser → `http://localhost:8000/health`

Harus muncul:
```json
{
  "status": "healthy",
  "environment": "development",
  "checks": {
    "api": true,
    "gemini_configured": true,
    "tavily_configured": true,
    "iot_enabled": true
  }
}
```

### Endpoint Penting Backend:

| URL | Method | Fungsi |
|-----|--------|--------|
| `http://localhost:8000/health` | GET | Health check utama |
| `http://localhost:8000/health/iot` | GET | Status IoT/MQTT |
| `http://localhost:8000/api/iot/devices` | GET | Daftar device IoT |
| `http://localhost:8000/api/keys/stats` | GET | Status API key rotation |
| `http://localhost:8000/api/config` | GET | Konfigurasi aktif |
| `http://localhost:8000/api/monitoring/health` | GET | Monitoring dashboard |
| `http://localhost:8000/api/monitoring/analytics` | GET | Tool analytics |
| `ws://localhost:8000/ws/chat` | WebSocket | Chat real-time |

---

## 6. Menjalankan Frontend

### Opsi A: Vite Dev Server (Rekomendasi untuk Development)

```powershell
# 1. Masuk folder frontend
cd D:\jawirv4\jawirv4\jawirv2\frontend

# 2. Jalankan dev server
npm run dev
```

Output yang diharapkan:
```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Opsi B: Menggunakan BAT File

```powershell
# Double-click atau jalankan:
D:\jawirv4\jawirv4\jawirv2\frontend\start_frontend.bat
```

### Buka di Browser:

→ **http://localhost:5173**

Kamu akan melihat JAWIR OS UI dengan tema Javanese Gold Coffee:
- Header emas (#dab80b) dengan tulisan "Jawir OS"
- Sidebar kiri (Chat / ReAct / Tools / Dashboard tabs)
- Chat panel di tengah
- Status badge "Connected" (hijau) di header

---

## 7. Menjalankan dengan Electron (Desktop App)

### Mode Development:

```powershell
cd D:\jawirv4\jawirv4\jawirv2\frontend

# Jalankan Vite + Electron bersamaan
npm run dev:electron
```

Atau pakai BAT file:
```powershell
D:\jawirv4\jawirv4\jawirv2\frontend\start_electron.bat
```

> **Catatan**: Electron akan otomatis membuka window desktop 1400×900px dan mengelola backend servers.

### Build Production Electron:

```powershell
npm run build:electron
# Output: dist-electron/ folder
```

---

## 8. Menjalankan Semua Sekaligus (Quick Start)

### Cara Paling Cepat — BAT File:

```powershell
# Jalankan dari root jawirv2:
D:\jawirv4\jawirv4\jawirv2\start_all.bat
```

Ini akan membuka **3 window CMD** terpisah:
1. **JAWIR-BACKEND** — FastAPI di port 8000
2. **JAWIR-POLINEMA** — Polinema API di port 8001 (opsional)
3. **JAWIR-FRONTEND** — Vite dev server di port 5173

### Atau Manual (2 Terminal):

**Terminal 1 — Backend:**
```powershell
cd D:\jawirv4\jawirv4\jawirv2\backend
.\venv_work\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend:**
```powershell
cd D:\jawirv4\jawirv4\jawirv2\frontend
npm run dev
```

### Menghentikan Semua:

```powershell
# Pakai BAT file:
D:\jawirv4\jawirv4\jawirv2\stop_all.bat

# Atau manual: CTRL+C di setiap terminal
```

---

## 9. Konfigurasi Environment (.env)

### Backend `.env` — Variabel Lengkap:

| Variable | Required | Default | Deskripsi |
|----------|----------|---------|-----------|
| `GOOGLE_API_KEY` | ✅ Ya | — | Gemini API key tunggal |
| `GOOGLE_API_KEYS` | Opsional | — | Multiple keys (comma-separated) untuk rotation |
| `TAVILY_API_KEY` | ✅ Ya | — | Tavily web search API |
| `WS_PORT` | Tidak | 8000 | Port WebSocket/API |
| `ENVIRONMENT` | Tidak | development | development / production |
| `LOG_LEVEL` | Tidak | INFO | DEBUG / INFO / WARNING / ERROR |
| `GEMINI_MODEL` | Tidak | gemini-2.0-flash | Model Gemini yang dipakai |
| `USE_FUNCTION_CALLING` | Tidak | false | V1 (ReAct) vs V2 (FC) mode |
| `MAX_RETRY_COUNT` | Tidak | 3 | Max retry agent loop |
| `MAX_CONTEXT_WORDS` | Tidak | 25000 | Max context words |
| `DEEP_RESEARCH_BREADTH` | Tidak | 4 | Deep research breadth |
| `DEEP_RESEARCH_DEPTH` | Tidak | 2 | Deep research depth |
| `GOWA_BASE_URL` | Opsional | — | WhatsApp Gateway URL |
| `GOWA_USERNAME` | Opsional | — | GoWA username |
| `GOWA_PASSWORD` | Opsional | — | GoWA password |
| `IOT_ENABLED` | Opsional | false | Aktifkan IoT MQTT |
| `IOT_MQTT_HOST` | Opsional | — | HiveMQ broker host |
| `IOT_MQTT_PORT` | Opsional | 8883 | MQTT port (TLS) |
| `IOT_MQTT_USER` | Opsional | — | MQTT username |
| `IOT_MQTT_PASS` | Opsional | — | MQTT password |
| `SAFE_MODE` | Opsional | true | Safety guard |
| `ALLOW_DESTRUCTIVE_ACTIONS` | Opsional | false | Allow delete/write ops |

### Frontend `.env`:

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `VITE_API_URL` | http://localhost:8000 | Backend API URL |
| `VITE_WS_URL` | ws://localhost:8000/ws | WebSocket URL |

---

## 10. Menjalankan Tests

### Backend Tests:

```powershell
cd D:\jawirv4\jawirv4\jawirv2\backend
.\venv_work\Scripts\activate

# Full test suite (semua fitur)
python tests\full_feature_test.py

# WebSocket smoke test
python tests\ws_smoke_test.py

# Tool contract test (38 tools)
python tests\tool_contract_test.py

# Function Calling E2E test
python tests\fc_e2e_test.py

# Pytest (unit tests)
python -m pytest tests/ -v
```

### Frontend Tests:

```powershell
cd D:\jawirv4\jawirv4\jawirv2\frontend

# TypeScript type check
npx tsc --noEmit

# Build test (full production build)
npm run build

# Lint
npm run lint
```

### Quick All-in-One Test:

```powershell
D:\jawirv4\jawirv4\jawirv2\test_all.bat
```

---

## 11. Troubleshooting

### ❌ Backend: "Port 8000 already in use"

```powershell
# Cari proses yang pakai port 8000
netstat -ano | findstr :8000

# Kill proses (ganti PID dengan angka dari output di atas)
taskkill /PID <PID> /F

# Atau langsung:
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

### ❌ Backend: "ModuleNotFoundError"

```powershell
# Pastikan venv aktif
.\venv_work\Scripts\activate

# Re-install dependencies
pip install -r requirements.txt
```

### ❌ Backend: "GOOGLE_API_KEY not set"

```powershell
# Pastikan file .env ada dan terisi
type .env | findstr GOOGLE_API_KEY

# Jika kosong, isi:
# GOOGLE_API_KEY=your-key-from-aistudio.google.com
```

### ❌ Frontend: "npm ERR! ENOENT package.json"

```powershell
# Pastikan di folder yang benar
cd D:\jawirv4\jawirv4\jawirv2\frontend
dir package.json
```

### ❌ Frontend: "VITE: Failed to resolve import"

```powershell
# Re-install node_modules
Remove-Item -Recurse -Force node_modules
npm install
```

### ❌ Frontend: "WebSocket connection failed"

- Pastikan backend **sudah jalan** di port 8000
- Cek `http://localhost:8000/health` harus mengembalikan `{"status":"healthy"}`
- Pastikan tidak ada firewall yang block port 8000

### ❌ Voice/PTT tidak bekerja

1. Buka Settings (⚙️) di UI JAWIR OS
2. Masukkan Deepgram API Key
3. Pilih bahasa (Indonesia/English)
4. Tekan tombol mic, **TAHAN** minimal 150ms, bicara, lalu lepas

### ❌ WhatsApp tools error "connection refused"

- GoWA gateway harus running di VPS/server terpisah
- Cek `GOWA_BASE_URL` di `.env` mengarah ke server yang benar
- Test: `curl http://your-server:3000/` harus mengembalikan GoWA response

### ❌ Google Workspace tools error

- Perlu setup OAuth2 di `google_workspace_mcp/`
- Jalankan `python manual_auth.py` di folder tersebut untuk generate token
- Lihat `google_workspace_mcp/SETUP_GUIDE.md` untuk detail

---

## 12. Ports & URLs

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **JAWIR Backend** | 8000 | http://localhost:8000 | Wajib |
| **JAWIR Frontend** | 5173 | http://localhost:5173 | Wajib |
| **Polinema API** | 8001 | http://localhost:8001 | Opsional |
| **GoWA WhatsApp** | 3000 | http://your-vps:3000 | Opsional (VPS) |
| **Google MCP** | — | Via subprocess | Opsional |

---

## ✅ Checklist Quick Start

```
□ Python 3.11+ terinstall
□ Node.js 18+ terinstall
□ Backend venv_work dibuat & dependencies diinstall
□ Backend .env dibuat & API keys diisi (GOOGLE_API_KEY + TAVILY_API_KEY)
□ Frontend npm install selesai
□ Backend dijalankan (python -m uvicorn ...) → http://localhost:8000/health = healthy
□ Frontend dijalankan (npm run dev) → http://localhost:5173 bisa dibuka
□ Chat di UI bisa kirim pesan dan dapat respon dari Gemini
```

---

**Selamat! JAWIR OS siap digunakan 🎉**

Untuk pertanyaan atau masalah, cek file `CONTEXT_FOR_AI.md` di root proyek.
