# Integrasi Polinema SIAKAD untuk JAWIR

## 🎯 Overview

Sistem scraping dan API untuk mengakses data SIAKAD Polinema menggunakan Python Playwright, terintegrasi dengan JAWIR AI Assistant.

## 📦 Komponen

1. **polinema_scraper.py** - Core scraper menggunakan Playwright
2. **polinema_api_server.py** - FastAPI REST API server
3. **polinema_tools.py** - Tools untuk AI function calling

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements_polinema.txt
playwright install chromium
```

### 2. Test Scraper

```bash
python polinema_scraper.py
```

Output: `polinema_data.json` dengan semua data

### 3. Start API Server

```bash
python polinema_api_server.py
```

Server berjalan di: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 4. Test API

```bash
# Health check
curl http://localhost:8000/health

# Get biodata
curl http://localhost:8000/api/biodata

# Get presensi
curl http://localhost:8000/api/presensi

# Get all data
curl http://localhost:8000/api/all
```

## 🔌 Integrasi dengan JAWIR

### Method 1: Direct Import

```python
from polinema_tools import PolinemaTools

tools = PolinemaTools()

# Gunakan di JAWIR
biodata = tools.get_biodata_mahasiswa()
presensi = tools.get_presensi()
jadwal = tools.get_jadwal_kuliah()
```

### Method 2: Function Calling (OpenAI/Gemini)

```python
from polinema_tools import TOOL_DEFINITIONS, PolinemaTools

tools = PolinemaTools()

# Register tools dengan AI
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Berapa kehadiran saya?"}],
    tools=TOOL_DEFINITIONS
)

# Execute tool call
if response.choices[0].message.tool_calls:
    tool_name = response.choices[0].message.tool_calls[0].function.name
    
    if tool_name == "get_presensi":
        result = tools.get_presensi()
```

### Method 3: HTTP API

```python
import requests

def get_student_data(endpoint):
    response = requests.get(f"http://localhost:8000/api/{endpoint}")
    return response.json()

# Panggil dari JAWIR
biodata = get_student_data("biodata")
```

## 📊 Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/biodata` | GET | Biodata mahasiswa |
| `/api/presensi` | GET | Data kehadiran |
| `/api/kalender` | GET | Kalender akademik |
| `/api/jadwal` | GET | Jadwal kuliah |
| `/api/nilai` | GET | Nilai/KHS |
| `/api/all` | GET | Semua data |

## 📝 Data Structure

### Biodata
```json
{
  "success": true,
  "biodata": {
    "NIM": "244101060077",
    "Nama": "MUHAMMAD F.Z",
    "Program Studi": "D4 Teknik Informatika",
    "Jurusan": "Teknologi Informasi"
  }
}
```

### Presensi
```json
{
  "success": true,
  "matakuliah": [
    {
      "mata_kuliah": "Basis Data",
      "hadir": "12",
      "izin": "1",
      "alpha": "0",
      "persentase": "92.3%"
    }
  ]
}
```

### Jadwal
```json
{
  "success": true,
  "jadwal": [
    {
      "hari": "Senin",
      "jam": "08:00-10:00",
      "kode_mk": "RTI024001",
      "mata_kuliah": "Pendidikan Pancasila",
      "dosen": "...",
      "ruangan": "..."
    }
  ]
}
```

## 🔐 Security

### Environment Variables

```bash
# .env
POLINEMA_NIM=244101060077
POLINEMA_PASSWORD=your_password
```

Load di code:
```python
import os
NIM = os.getenv("POLINEMA_NIM")
PASSWORD = os.getenv("POLINEMA_PASSWORD")
```

### Production Settings

Edit `polinema_scraper.py`:
```python
# Change headless to True
scraper = PolinemaScraper(NIM, PASSWORD, headless=True)
```

## 🛠️ Troubleshooting

### Browser not found
```bash
playwright install chromium
```

### Permission denied
```bash
# Windows: Run as Administrator
# Linux: Check permissions
```

### Data kosong
- Cek apakah login berhasil
- Lihat screenshot yang dihasilkan
- Review struktur HTML di SIAKAD (mungkin berubah)

## 📈 Performance

- **Cold start**: ~10 detik (browser launch + login)
- **Cached**: ~2-3 detik per endpoint
- **Memory**: ~200MB (browser overhead)

## 🔄 Auto-Refresh

Untuk data real-time, gunakan scheduler:

```python
import schedule
import time

def refresh_data():
    with PolinemaScraper(NIM, PASSWORD) as scraper:
        scraper.login()
        data = scraper.get_all_data()
        # Save or update cache

schedule.every(30).minutes.do(refresh_data)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## 🎨 UI Integration

JAWIR bisa menampilkan data dengan format yang lebih baik:

```python
def format_presensi_response(data):
    if not data.get("success"):
        return "Gagal mengambil data presensi"
    
    response = "📊 **Data Presensi Anda:**\n\n"
    
    for mk in data["matakuliah"]:
        response += f"**{mk['mata_kuliah']}**\n"
        response += f"  • Hadir: {mk['hadir']}\n"
        response += f"  • Alpha: {mk['alpha']}\n"
        response += f"  • Persentase: {mk['persentase']}\n\n"
    
    return response
```

## 📚 Next Steps

1. ✅ Basic scraping - DONE
2. ✅ API server - DONE
3. ✅ Tools integration - DONE
4. ⏳ LMS (Moodle) integration
5. ⏳ Caching layer
6. ⏳ WebSocket for real-time updates

## 🤝 Contributing

Perbaikan bisa dilakukan di:
- Error handling
- Data parsing
- API caching
- Rate limiting
- Session management
