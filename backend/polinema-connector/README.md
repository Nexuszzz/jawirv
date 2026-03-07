# Polinema Connector for JAWIR AI

Integration layer untuk mengakses data dari Polinema SIAKAD menggunakan Playwright web scraping.

## 🎯 Fitur

- ✅ **Biodata Mahasiswa** - Data pribadi dan akademik
- ✅ **Kehadiran/Presensi** - Data kehadiran per mata kuliah
- ✅ **Kalender Akademik** - Jadwal kegiatan akademik
- ✅ **Nilai (KHS)** - Nilai dan IPK
- ✅ **Jadwal Kuliah** - Jadwal kelas per semester

## 📦 Setup

### 1. Install Dependencies

```bash
cd polinema-connector
npm install
npx playwright install chromium
```

### 2. Konfigurasi Credentials

Edit file `scraper_enhanced.js` dan update:

```javascript
const CONFIG = {
    nim: 'YOUR_NIM',
    password: 'YOUR_PASSWORD',
    siakad_url: 'https://siakad.polinema.ac.id'
};
```

### 3. Test Scraper

```bash
node scraper_enhanced.js
```

Ini akan:
- Login ke SIAKAD
- Explore semua menu
- Extract data biodata, kehadiran, kalender, nilai, jadwal
- Save ke `polinema_complete_data.json`
- Ambil screenshots di setiap step

### 4. Jalankan API Server

```bash
npm start
```

Server akan berjalan di `http://localhost:3001`

## 🔌 API Endpoints

### POST /api/login
Login ke SIAKAD (otomatis dipanggil saat server start)

```bash
curl -X POST http://localhost:3001/api/login
```

### GET /api/biodata
Get biodata mahasiswa

```bash
curl http://localhost:3001/api/biodata
```

Response:
```json
{
  "success": true,
  "data": {
    "tables": [...],
    "cards": [...]
  }
}
```

### GET /api/kehadiran
Get data kehadiran/presensi

```bash
curl http://localhost:3001/api/kehadiran
```

### GET /api/kalender
Get kalender akademik

```bash
curl http://localhost:3001/api/kalender
```

### GET /api/nilai
Get nilai/KHS

```bash
curl http://localhost:3001/api/nilai
```

### GET /api/jadwal
Get jadwal kuliah

```bash
curl http://localhost:3001/api/jadwal
```

### GET /api/all
Get semua data sekaligus

```bash
curl http://localhost:3001/api/all
```

## 🤖 Integrasi dengan JAWIR AI

### 1. Tool Definition

File `tools_config.json` berisi definisi tools yang bisa digunakan oleh AI:

```json
{
  "tools": [
    {
      "name": "get_biodata_mahasiswa",
      "description": "Get student biodata",
      "endpoint": "/api/biodata"
    },
    ...
  ]
}
```

### 2. Contoh Penggunaan di JAWIR

```python
# Di JAWIR backend
import requests

def get_student_data(tool_name):
    response = requests.get(f"http://localhost:3001/api/{tool_name}")
    return response.json()

# AI bisa memanggil:
biodata = get_student_data("biodata")
kehadiran = get_student_data("kehadiran")
```

### 3. Function Calling (OpenAI/Gemini)

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_kehadiran",
            "description": "Get student attendance data",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# AI akan call function get_kehadiran() saat user bertanya:
# "Berapa kehadiran saya di mata kuliah Basis Data?"
```

## 📊 Data Structure

### Biodata
```json
{
  "tables": [
    {
      "headers": ["Field", "Value"],
      "rows": [
        ["NIM", "244101060077"],
        ["Nama", "MUHAMMAD F.Z"],
        ...
      ]
    }
  ]
}
```

### Kehadiran
```json
{
  "tables": [
    {
      "headers": ["Mata Kuliah", "Hadir", "Izin", "Alpha", "%"],
      "rows": [
        ["Basis Data", "12", "1", "0", "92.3%"],
        ...
      ]
    }
  ]
}
```

## 🔐 Security Notes

- ⚠️ **JANGAN commit credentials** ke Git
- ⚠️ **Gunakan environment variables** untuk production
- ⚠️ **Rate limit** untuk mencegah spam ke SIAKAD
- ⚠️ **Cache** data untuk mengurangi load

## 🛠️ Development

### Debugging

Scraper berjalan dengan `headless: false` by default untuk debugging.
Ubah ke `headless: true` untuk production di `scraper_enhanced.js`:

```javascript
this.browser = await chromium.launch({ 
    headless: true  // Production mode
});
```

### Monitoring

Server log semua API calls dan response API yang ditangkap:

```
📡 API Call: https://siakad.polinema.ac.id/mahasiswa/biodata/get_data
Response: {...}
```

### Screenshots

Setiap step akan generate screenshot untuk debugging:
- `01_after_login.png`
- `02_biodata.png`
- `03_kehadiran.png`
- dll.

## 📝 URL Mapping

Dari hasil scraping, ini URL penting di SIAKAD:

```
Biodata:    /mahasiswa/biodata/index/gm/general
Kalender:   /mahasiswa/kalenderakd/index/gm/akademik
Jadwal:     /mahasiswa/jadwal/index/gm/akademik
Nilai:      /mahasiswa/akademik/index/gm/akademik
Presensi:   /mahasiswa/presensi/index/gm/akademik
```

## 🚀 Production Deployment

### Docker (Recommended)

```dockerfile
FROM node:18
RUN npx playwright install --with-deps chromium
COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]
```

### Environment Variables

```bash
POLINEMA_NIM=244101060077
POLINEMA_PASSWORD=your_password
PORT=3001
HEADLESS=true
```

## 🆘 Troubleshooting

### Login gagal
- Cek credentials di CONFIG
- Cek apakah SIAKAD accessible
- Lihat screenshot `login_error.png`

### Data kosong
- Cek menu structure di SIAKAD (mungkin berubah)
- Lihat console log untuk error
- Review screenshots untuk debug

### Browser crash
- Install Playwright dependencies: `npx playwright install-deps`
- Increase memory limit: `NODE_OPTIONS=--max-old-space-size=4096 npm start`

## 📄 License

MIT

## 🤝 Contributing

PR welcome! Focus areas:
- LMS (Moodle) integration
- API caching layer
- Better error handling
- Session persistence
