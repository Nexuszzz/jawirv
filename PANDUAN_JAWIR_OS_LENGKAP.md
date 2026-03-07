# 📚 PANDUAN LENGKAP JAWIR OS

> **Just Another Wise Intelligent Resource**  
> Desktop AI Agent dengan kemampuan True Agentic Workflow, Deep Research, Desktop Control & Google Workspace Integration

---

## 📋 DAFTAR ISI

1. [Overview](#-overview)
2. [Instalasi & Setup](#-instalasi--setup)
3. [Fitur Utama](#-fitur-utama-jawir-os)
4. [Tools Reference](#-tools-reference)
5. [Panduan Desktop Control](#-panduan-desktop-control)
6. [Panduan Spotify](#-panduan-spotify)
7. [Panduan YouTube](#-panduan-youtube)
8. [Panduan Python Interpreter](#-panduan-python-interpreter)
9. [Panduan File Generation](#-panduan-file-generation)
10. [Panduan KiCad Tool](#-panduan-kicad-tool)
11. [Panduan Web Search Tool](#-panduan-web-search-tool)
12. [Panduan Deep Research Tool](#-panduan-deep-research-tool)
13. [Panduan Google Workspace](#-panduan-google-workspace)
14. [ReAct Agent Deep Dive](#-react-agent-deep-dive)
15. [CLI Commands Reference](#-cli-commands-reference)
16. [Architecture](#-architecture)
17. [Troubleshooting](#-troubleshooting)
18. [Function Calling V2](#-function-calling-v2-new)

---

## 🎯 OVERVIEW

JAWIR OS adalah AI Assistant "Jawa Terkuat" yang dibangun dengan arsitektur **Hybrid Stack**:

| Layer | Technology | Fungsi |
|-------|------------|--------|
| **Backend** | Python + FastAPI | Otak AI (LangGraph + Gemini) |
| **Agent** | LangGraph | ReAct Loop Pattern |
| **LLM** | Gemini 2.0 Flash | Natural Language Processing |
| **Search** | Tavily API | Web Search & Research |
| **Workspace** | Google MCP | Gmail, Drive, Calendar, Sheets, Forms |
| **Electronics** | KiCad Generator | Schematic Design |
| **Desktop** | Python ctypes + subprocess | App Control, Media Keys |
| **Media** | Spotify + YouTube | Music & Video Playback |

---

## 🚀 INSTALASI & SETUP

### Prerequisites

```bash
# Python 3.11+
python --version

# Install dependencies
pip install langchain-core langchain-google-genai tavily-python
pip install youtube-search-python python-docx fpdf openpyxl
```

### Environment Variables

Buat file `.env` di `backend/`:

```env
# LLM API Keys (Gemini)
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_API_KEY_2=backup_api_key  # Optional, untuk rotation

# Web Search
TAVILY_API_KEY=your_tavily_api_key

# Google Workspace (Optional)
USER_GOOGLE_EMAIL=your_email@gmail.com
```

### Quick Start

```bash
# Navigate ke folder tools
cd D:\jawirv2\jawirv2\backend\tools\kicad

# Run interactive mode
python kicad_cli.py -i
```

---

## ⭐ FITUR UTAMA JAWIR OS

### 🎵 1. Media Control (Spotify & YouTube)
Kontrol musik dan video langsung dari natural language.

**Spotify:**
- Buka/tutup Spotify
- Search dan play musik
- Kontrol playback (play, pause, next, prev, stop)
- Play via Spotify URI

**YouTube:**
- Search dan play video (autoplay!)
- Cari hasil video
- Buka halaman pencarian

### 🖥️ 2. Desktop Control
Kontrol aplikasi desktop dari perintah natural language.

**Kemampuan:**
- Buka/tutup aplikasi (Chrome, VS Code, Notepad, dll)
- Screenshot layar
- Browse website
- Search Google

### 🐍 3. Python Interpreter
Eksekusi kode Python langsung dari chat.

**Kemampuan:**
- Run code inline atau subprocess
- Install pip packages
- Multi-session execution
- Error handling

### 📄 4. File Generation
Generate berbagai format dokumen.

**Format:**
- Word (.docx)
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
- JSON (.json)
- Excel (.xlsx)

### 🔧 5. KiCad Schematic Generator
Generate skematik elektronika dari natural language.

**Kemampuan:**
- Generate ESP32, Arduino, Raspberry Pi projects
- Sensor integration (DHT11, BME280, Ultrasonic, PIR, dll)
- Auto wiring dengan validasi koneksi
- Power distribution management
- Template-based generation

**Contoh:**
```
"Buat ESP32 dengan sensor DHT11 dan LED"
"Rangkaian Arduino dengan 4 relay dan LCD 16x2"
"IoT weather station dengan BME280 dan OLED display"
```

### 🔍 6. Web Search (Tavily)
Pencarian web dengan AI-powered relevance ranking.

**Kemampuan:**
- Search komponen elektronika
- Cari datasheet dan pinout
- Tutorial dan reference
- Auto-filtering domain terpercaya

**Supported Domains:**
- sparkfun.com, adafruit.com
- arduino.cc, espressif.com
- randomnerdtutorials.com
- electronicshub.org
- circuitdigest.com

### 🔬 7. Deep Research
Riset mendalam otomatis dengan breadth-first + depth exploration.

**Kemampuan:**
- Multi-layer research (breadth × depth)
- Context trimming (max 25K words)
- Follow-up questions generation
- Source aggregation & validation

**Settings:**
| Parameter | Default | Deskripsi |
|-----------|---------|-----------|
| Breadth | 4 | Concurrent search threads |
| Depth | 2 | Recursive depth levels |
| Max Context | 25000 | Max words for LLM |

### 🧠 8. True Agent (ReAct Loop)
Pattern "berpikir-bertindak-mengamati" berulang sampai target tercapai.

**Flow:**
```
Thought → Action → Observation → Loop
   ↑                              ↓
   └──────────────────────────────┘
```

**Karakteristik:**
- **Reasoning**: Chain of Thought analysis
- **Acting**: Tool selection & execution
- **Observation**: Result evaluation
- **Self-correction**: Max 3 retry dengan strategi berbeda

### 9. 📧 Google Workspace Integration
Akses penuh ke Google Workspace services.

**Services Aktif:**
| Service | Status | Fungsi |
|---------|--------|--------|
| 📧 Gmail | ✅ Enabled | Email management |
| 📁 Drive | ✅ Enabled | File storage |
| 📅 Calendar | ✅ Enabled | Event scheduling |
| 📊 Sheets | ✅ Enabled | Spreadsheet ops |
| 📝 Forms | ✅ Enabled | Form creation |

---

## 🛠️ TOOLS REFERENCE

### Tool Categories

| Category | Tools | Purpose |
|----------|-------|---------|
| **Media** | Spotify, YouTube | Music & video playback |
| **Desktop** | App Control, Screenshot | Desktop automation |
| **Python** | Code Executor | Run Python code |
| **Files** | Document Generator | Create Word, PDF, Excel |
| **Electronics** | KiCad Generator | Schematic design |
| **Search** | Tavily Search | Web information |
| **Research** | Deep Research | In-depth analysis |
| **Productivity** | Google Workspace | Email, Drive, Calendar |

### Complete Tools List

| Tool | Action | Deskripsi |
|------|--------|-----------|
| `finish(answer)` | General | Selesaikan task dengan jawaban |
| `respond(message)` | General | Balas user tanpa selesai |
| `web_search(query)` | Search | Cari informasi di web |
| `search_component(name)` | Search | Cari info komponen elektronik |
| `open_app(name)` | Desktop | Buka aplikasi |
| `close_app(name)` | Desktop | Tutup aplikasi |
| `screenshot()` | Desktop | Ambil screenshot |
| `play_youtube(query)` | YouTube | Cari & putar video |
| `search_youtube(query)` | YouTube | Buka halaman hasil search |
| `youtube_results(query)` | YouTube | Dapatkan list video |
| `open_spotify()` | Spotify | Buka Spotify |
| `play_spotify(query)` | Spotify | Search & play musik |
| `spotify_control(action)` | Spotify | Play/pause/next/prev/stop |
| `close_spotify()` | Spotify | Tutup Spotify |
| `play_spotify_uri(uri)` | Spotify | Play via URI |
| `browse(url)` | Browser | Buka website |
| `search_google(query)` | Browser | Search di Google |
| `run_python(code)` | Python | Eksekusi kode Python |
| `install_package(pkg)` | Python | Install pip package |
| `create_word(content)` | File | Buat dokumen Word |
| `create_pdf(content)` | File | Buat dokumen PDF |
| `create_txt(content)` | File | Buat file teks |
| `create_markdown(content)` | File | Buat file Markdown |
| `create_json(data)` | File | Buat file JSON |
| `create_excel(data)` | File | Buat file Excel |
| `generate_schematic(spec)` | KiCad | Generate skematik |

---

## 🖥️ PANDUAN DESKTOP CONTROL

### Buka Aplikasi

**Supported Apps:**

| App Name | Aliases | Deskripsi |
|----------|---------|-----------|
| `chrome` | `google chrome` | Google Chrome browser |
| `firefox` | `mozilla` | Firefox browser |
| `edge` | `microsoft edge` | Microsoft Edge |
| `spotify` | - | Spotify music player |
| `vscode` | `visual studio code`, `code` | VS Code editor |
| `notepad` | - | Windows Notepad |
| `notepad++` | `npp` | Notepad++ editor |
| `explorer` | `file explorer` | Windows Explorer |
| `cmd` | `command prompt` | Command Prompt |
| `powershell` | `ps` | PowerShell |
| `calc` | `calculator` | Windows Calculator |
| `paint` | - | MS Paint |
| `word` | `microsoft word` | MS Word |
| `excel` | `microsoft excel` | MS Excel |
| `powerpoint` | `ppt` | MS PowerPoint |
| `discord` | - | Discord |
| `slack` | - | Slack |
| `telegram` | - | Telegram Desktop |
| `whatsapp` | - | WhatsApp Desktop |

**Contoh Natural Language:**

```
✅ "buka chrome"
✅ "buka visual studio code"
✅ "buka notepad"
✅ "buka file explorer"
✅ "tutup chrome"
✅ "tutup spotify"
```

### Screenshot

```
✅ "ambil screenshot"
✅ "screenshot layar"
✅ "capture screen"
```

Screenshot akan disimpan di folder output dengan format: `screenshot_YYYYMMDD_HHMMSS.png`

### Browse Website

```
✅ "buka website google.com"
✅ "browse ke github.com"
✅ "akses youtube.com"
```

### Search Google

```
✅ "cari di google tentang python tutorial"
✅ "search google machine learning"
```

---

## 🎵 PANDUAN SPOTIFY

### Membuka Spotify

```
✅ "buka spotify"
✅ "jalankan spotify"
✅ "open spotify"
```

### Play Musik

**Search dan Play:**

```
✅ "putar musik jazz di spotify"
✅ "play lagu rock di spotify"
✅ "nyalakan musik pop"
✅ "putar lagu sheila on 7"
✅ "play album coldplay"
✅ "putar playlist workout"
```

**Play via URI (Advanced):**

```
✅ "play spotify:track:4iV5W9uYEdYUVa79Axb7Rh"
✅ "putar spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
```

### Kontrol Playback

| Command Natural | Action |
|-----------------|--------|
| "pause musiknya" | Pause |
| "stop musik" | Stop |
| "lanjutkan musik" | Play/Resume |
| "play lagi" | Play/Resume |
| "next song" | Skip ke lagu berikutnya |
| "skip lagu" | Skip ke lagu berikutnya |
| "lagu sebelumnya" | Previous track |
| "previous track" | Previous track |

**Contoh:**

```
✅ "pause musiknya"
✅ "skip ke lagu berikutnya"
✅ "next song"
✅ "lagu sebelumnya"
✅ "stop musik"
✅ "play lagi"
```

### Menutup Spotify

```
✅ "tutup spotify"
✅ "close spotify"
```

### Workflow Lengkap

```
User: "buka spotify dan putar musik jazz"
JAWIR: 
  1. Thought: User mau buka Spotify dan putar jazz
  2. Action: open_spotify()
  3. Observation: ✅ Spotify opened!
  4. Thought: Sekarang putar musik jazz
  5. Action: play_spotify(jazz relaxing music)
  6. Observation: ✅ Now playing on Spotify: jazz relaxing music
  7. finish(Spotify sudah dibuka dan musik jazz sedang diputar!)
```

---

## 🎬 PANDUAN YOUTUBE

### Search dan Play Video (Autoplay!)

```
✅ "putar video tutorial python di youtube"
✅ "play jazz music di youtube"
✅ "putarkan video cooking di youtube"
✅ "nyalakan video lo-fi di youtube"
```

**Fitur Autoplay:**
- Video langsung diputar tanpa perlu klik manual
- Menggunakan parameter `autoplay=1`

### Search YouTube (Buka Halaman Hasil)

```
✅ "cari di youtube tutorial arduino"
✅ "search youtube review laptop"
```

### Dapatkan List Hasil

```
✅ "cari hasil video python tutorial"
✅ "list video tentang machine learning"
```

Output:
```
[1] Python Tutorial for Beginners - freeCodeCamp
[2] Learn Python - Full Course - Mosh
[3] Python Crash Course - Traversy Media
...
```

### Contoh Penggunaan

```
# Play langsung dengan autoplay
User: "putarkan musik jazz di youtube"
JAWIR: ✅ Now playing: Jazz Music Relaxing
       🔗 https://youtube.com/watch?v=xxxxx&autoplay=1

# Cari tanpa play
User: "cari video tutorial react di youtube"
JAWIR: ✅ YouTube search opened for: tutorial react
```

---

## 🐍 PANDUAN PYTHON INTERPRETER

### Eksekusi Kode Sederhana

```
✅ "hitung faktorial 10"
✅ "buat program hello world"
✅ "jalankan python: print('Hello JAWIR!')"
✅ "eksekusi kode: import math; print(math.pi)"
```

### Contoh Penggunaan

**Matematika:**
```
User: "hitung 2 pangkat 10"
JAWIR: 
  Action: run_python(print(2 ** 10))
  Output: 1024

User: "hitung faktorial 15"
JAWIR:
  Action: run_python(import math; print(f"15! = {math.factorial(15)}"))
  Output: 15! = 1307674368000
```

**String Processing:**
```
User: "balik string 'hello world'"
JAWIR:
  Action: run_python(s = 'hello world'; print(s[::-1]))
  Output: dlrow olleh
```

**Data Processing:**
```
User: "hitung rata-rata dari [10, 20, 30, 40, 50]"
JAWIR:
  Action: run_python(data = [10, 20, 30, 40, 50]; print(f"Rata-rata: {sum(data)/len(data)}"))
  Output: Rata-rata: 30.0
```

**Generate Data:**
```
User: "buat list bilangan prima dari 1-50"
JAWIR:
  Action: run_python(
    def is_prime(n):
        if n < 2: return False
        for i in range(2, int(n**0.5)+1):
            if n % i == 0: return False
        return True
    primes = [x for x in range(1, 51) if is_prime(x)]
    print(f"Bilangan prima 1-50: {primes}")
  )
  Output: Bilangan prima 1-50: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
```

### Install Package

```
✅ "install package requests"
✅ "install numpy"
✅ "install pandas matplotlib"
```

### Tips

1. **Kode inline** - untuk snippet pendek
2. **Subprocess** - untuk kode yang perlu isolasi
3. **Multi-line** - gunakan semicolon (;) atau \\n

---

## 📄 PANDUAN FILE GENERATION

### Buat Dokumen Word

```
✅ "buatkan dokumen word tentang IoT"
✅ "buat laporan word tentang machine learning"
```

**Output:** `output/document_TIMESTAMP.docx`

### Buat PDF

```
✅ "buatkan PDF tentang tutorial python"
✅ "buat dokumen PDF laporan proyek"
```

**Output:** `output/document_TIMESTAMP.pdf`

### Buat Text File

```
✅ "simpan catatan ini ke file txt"
✅ "buat file text dengan isi hello world"
```

**Output:** `output/document_TIMESTAMP.txt`

### Buat Markdown

```
✅ "buatkan dokumentasi markdown untuk API"
✅ "buat readme markdown untuk project"
```

**Output:** `output/document_TIMESTAMP.md`

### Buat JSON

```
✅ "buat file JSON dengan data produk"
✅ "simpan konfigurasi ke JSON"
```

**Output:** `output/data_TIMESTAMP.json`

### Buat Excel

```
✅ "buatkan spreadsheet excel untuk data penjualan"
✅ "buat excel dengan data karyawan"
```

**Output:** `output/workbook_TIMESTAMP.xlsx`

### Contoh Lengkap

```
User: "buatkan laporan word tentang Internet of Things"

JAWIR:
  1. Thought: User mau laporan tentang IoT. Cari info dulu.
  2. Action: web_search(Internet of Things penjelasan lengkap aplikasi)
  3. Observation: [hasil search tentang IoT...]
  4. Thought: Info cukup. Buat dokumen Word.
  5. Action: create_word(
       # Laporan Internet of Things
       
       ## Pendahuluan
       Internet of Things (IoT) adalah konsep...
       
       ## Komponen Utama
       1. Sensor dan Aktuator
       2. Konektivitas
       3. Cloud Computing
       ...
     )
  6. Observation: ✅ Word document created: output/document_20260203.docx
  7. finish(Laporan IoT berhasil dibuat di output/document_20260203.docx)
```

---

## 🔧 PANDUAN KICAD TOOL

### Basic Usage

```bash
# Interactive mode
python kicad_cli.py -i

# Direct generation
python kicad_cli.py "Buat ESP32 dengan LED"

# Research + Generate
python kicad_cli.py -r "IoT weather station dengan BME280"
```

### Supported Components

| Category | Components |
|----------|------------|
| **MCU** | ESP32, Arduino Uno, Arduino Nano, Raspberry Pi Pico |
| **Sensors** | DHT11, BME280, BMP280, HC-SR04, PIR, LDR |
| **Display** | OLED 128x64, LCD 16x2, 7-Segment |
| **Output** | LED, Relay, Buzzer, Motor |
| **Communication** | HC-05 Bluetooth, nRF24L01, RF 433MHz |
| **Power** | Voltage Regulator, Battery, USB |

### Wiring Rules

⚠️ **ATURAN KRITIS:**
```
✅ VCC sensor → 3V3/VCC pin (bukan GPIO!)
✅ GND sensor → GND pin (bukan GPIO!)
✅ DATA sensor → GPIO yang sesuai
```

### ESP32 Pin Reference
```
pin1  = GND (Ground)
pin2  = 3V3 (Power 3.3V)
pin10-14, pin24-37 = GPIO (Data pins)
```

### Example Commands

```bash
# Simple LED blink
"Buat ESP32 dengan LED di GPIO4"

# Multiple sensors
"ESP32 dengan DHT11 dan HC-SR04 ultrasonic"

# IoT project
"Weather station dengan ESP32, BME280, dan OLED"

# Home automation
"Arduino dengan 4 relay module untuk smart home"
```

---

## 🔍 PANDUAN WEB SEARCH TOOL

### Basic Usage

```bash
# Search mode
python kicad_cli.py -s "ESP32 pinout"

# Interactive search
python kicad_cli.py -i
> /search ESP32 deep sleep mode
```

### Search Features

| Feature | Description |
|---------|-------------|
| **Basic Search** | Quick web search |
| **Advanced Search** | Deep content extraction |
| **Component Search** | Specific IC/module info |
| **Datasheet Search** | Technical documentation |

### Example Queries

```bash
/search DHT11 Arduino wiring
/search ESP32 PWM tutorial
/search BME280 I2C address
/search LM7805 pinout datasheet
```

---

## 🔬 PANDUAN DEEP RESEARCH TOOL

### Basic Usage

```bash
# Research mode
python kicad_cli.py -r "IoT weather station design"

# Interactive research
python kicad_cli.py -i
> /research Best practices for ESP32 battery powered projects
```

### Research Process

1. **Breadth Phase**: Parallel searches untuk berbagai aspek
2. **Depth Phase**: Follow-up questions untuk detail
3. **Synthesis**: Aggregasi dan validasi hasil
4. **Output**: Laporan lengkap dengan sumber

### Example Topics

```bash
/research Smart home automation dengan ESP32
/research Low power design untuk IoT sensor
/research PCB design best practices
/research Industrial IoT dengan Modbus
```

---

## 📧 PANDUAN GOOGLE WORKSPACE

### Quick Start

```bash
# Masuk ke Google Workspace mode
python kicad_cli.py -g

# Atau dari interactive mode
python kicad_cli.py -i
> /google
```

### 📧 GMAIL COMMANDS

| Command | Fungsi |
|---------|--------|
| `/gmail labels` | Lihat semua labels |
| `/gmail search <query>` | Cari email |
| `/gmail send` | Kirim email (interactive) |
| `/gmail draft` | Buat draft email |

**Contoh:**
```bash
/gmail labels
/gmail search from:google
/gmail search is:unread
/gmail search subject:invoice after:2024/01/01
/gmail send
  To: someone@email.com
  Subject: Test JAWIR OS
  Body: Hello from JAWIR OS!
```

### 📁 DRIVE COMMANDS

| Command | Fungsi |
|---------|--------|
| `/drive list` atau `/drive ls` | List files |
| `/drive search <query>` | Cari file |
| `/drive create <name> [content]` | Buat file baru |
| `/drive upload <filepath>` | Upload file |
| `/drive download <file_id> <dest>` | Download file |

**Contoh:**
```bash
/drive list
/drive search name contains 'project'
/drive search mimeType = 'application/pdf'
/drive create notes.txt "Catatan penting JAWIR OS"
/drive upload D:\projects\schematic.pdf
```

**⚠️ Catatan:** Create folder (`/drive mkdir`) tidak didukung oleh MCP server. Gunakan Google Drive web untuk membuat folder.

### 📅 CALENDAR COMMANDS

| Command | Fungsi |
|---------|--------|
| `/calendar list` | Lihat semua calendar |
| `/calendar events` | Lihat events |
| `/calendar add <text>` | Quick add event |

**Contoh:**
```bash
/calendar list
/calendar events
/calendar add "Meeting with client tomorrow 10am"
/calendar add "Review project Friday at 2pm"
```

**Quick Add Format:**
- "Meeting tomorrow at 3pm"
- "Call John next Monday 10am"
- "Project deadline Dec 25"

### 📊 SHEETS COMMANDS

| Command | Fungsi |
|---------|--------|
| `/sheets info <spreadsheet_id>` | Info spreadsheet |
| `/sheets read <id> <range>` | Baca data |
| `/sheets write <id> <range>` | Tulis data |
| `/sheets create <title>` | Buat spreadsheet baru |

**Contoh:**
```bash
/sheets info 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
/sheets read 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms Sheet1!A1:D10
/sheets create "Project Tracker JAWIR"
```

### 📝 FORMS COMMANDS

| Command | Fungsi |
|---------|--------|
| `/forms create <title>` | Buat form baru |
| `/forms get <form_id>` | Lihat form |
| `/forms responses <form_id>` | Lihat responses |

**Contoh:**
```bash
/forms create "Feedback JAWIR OS"
/forms get 1FAIpQLSdxxxxxxx
/forms responses 1FAIpQLSdxxxxxxx
```

---

## 🧠 REACT AGENT DEEP DIVE

### Apa itu ReAct Agent?

**ReAct = Reasoning + Acting**

ReAct adalah pattern AI yang menggabungkan proses berpikir (reasoning) dengan eksekusi aksi (acting) dalam loop iteratif. JAWIR OS menggunakan Gemini 2.0 Flash sebagai "otak" yang memproses semua request dengan pattern ini.

### Cara Kerja ReAct

```
┌─────────────────────────────────────────────────────────────┐
│                    ReAct Loop                               │
│                                                             │
│   User Request                                              │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────────┐                                           │
│   │   THOUGHT   │ ← Gemini menganalisis request             │
│   │ "Apa yang   │                                           │
│   │  diminta?"  │                                           │
│   └──────┬──────┘                                           │
│          │                                                  │
│          ▼                                                  │
│   ┌─────────────┐                                           │
│   │   ACTION    │ ← Pilih dan eksekusi tool yang tepat      │
│   │ tool(param) │                                           │
│   └──────┬──────┘                                           │
│          │                                                  │
│          ▼                                                  │
│   ┌─────────────┐                                           │
│   │ OBSERVATION │ ← Lihat hasil dari tool                   │
│   │   Result    │                                           │
│   └──────┬──────┘                                           │
│          │                                                  │
│          ▼                                                  │
│   ┌─────────────┐    NO     ┌─────────────┐                 │
│   │  Selesai?   │─────────→│ Loop Back   │                  │
│   └──────┬──────┘          └──────┬──────┘                  │
│          │ YES                    │                         │
│          ▼                        │                         │
│   ┌─────────────┐                 │                         │
│   │   FINISH    │ ←───────────────┘                         │
│   │  (answer)   │                                           │
│   └─────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Format Output ReAct

Setiap iterasi menghasilkan:

```
Thought: [Analisis situasi dan rencana]
Action: [nama_tool(parameter)]
```

Setelah tool dijalankan:
```
Observation: [Hasil dari tool - ✅ atau ❌]
```

Kemudian loop kembali atau finish:
```
Thought: [Evaluasi hasil]
Action: finish(jawaban final)
```

### Auto-Finish Feature

Untuk task sederhana (single-action), JAWIR OS memiliki **auto-finish** yang langsung menyelesaikan task tanpa iterasi tambahan:

**Simple Actions (Auto-finish enabled):**
- `play_youtube`, `search_youtube`
- `open_app`, `close_app`
- `open_spotify`, `play_spotify`, `spotify_control`, `close_spotify`
- `browse`, `search_google`
- `screenshot`
- `run_python`, `install_package`
- `create_word`, `create_pdf`, `create_txt`, dll

**Contoh Flow dengan Auto-finish:**
```
User: "putar musik jazz di spotify"

Iteration 1:
  💭 THOUGHT: User mau dengar jazz. Putar di Spotify.
  ⚡ ACTION: play_spotify(jazz relaxing music)
  👁️ OBSERVATION: ✅ Now playing on Spotify: jazz relaxing music
  
  [AUTO-FINISH TRIGGERED]
  
✅ FINAL ANSWER: Tugas selesai! ✅ Now playing on Spotify: jazz relaxing music
```

### Multi-Step Tasks

Untuk task kompleks, ReAct akan loop beberapa kali:

**Contoh: Research + Create Document**
```
User: "cari info tentang IoT lalu buatkan laporan word"

Iteration 1:
  💭 THOUGHT: User mau info IoT dan buat laporan. Cari dulu info IoT.
  ⚡ ACTION: web_search(Internet of Things penjelasan lengkap)
  👁️ OBSERVATION: ✅ Search results: [info tentang IoT...]

Iteration 2:
  💭 THOUGHT: Info sudah ada. Sekarang buat laporan Word.
  ⚡ ACTION: create_word(# Laporan IoT\n\n## Pendahuluan\nIoT adalah...)
  👁️ OBSERVATION: ✅ Word document created: output/document.docx

Iteration 3:
  💭 THOUGHT: Laporan berhasil dibuat. Selesai!
  ⚡ ACTION: finish(Laporan IoT berhasil dibuat di output/document.docx)

✅ FINAL ANSWER: Laporan IoT berhasil dibuat di output/document.docx
```

### Max Iterations

JAWIR OS membatasi maksimal **6 iterasi** untuk mencegah infinite loop. Jika belum selesai dalam 6 iterasi, agent akan otomatis berhenti dengan partial result.

### Error Handling

Jika action gagal (❌), agent akan:
1. Menganalisis error
2. Mencoba alternatif lain (jika ada)
3. Atau finish dengan error message

```
Iteration 1:
  💭 THOUGHT: User mau buka aplikasi XYZ
  ⚡ ACTION: open_app(xyz)
  👁️ OBSERVATION: ❌ Failed to open xyz: Application not found

Iteration 2:
  💭 THOUGHT: Aplikasi tidak ditemukan. Informasikan ke user.
  ⚡ ACTION: finish(Maaf, aplikasi XYZ tidak ditemukan di sistem.)

✅ FINAL ANSWER: Maaf, aplikasi XYZ tidak ditemukan di sistem.
```

### Tips Menggunakan ReAct

1. **Jelas dan Spesifik** - Request yang jelas = hasil lebih akurat
   ```
   ❌ "putar musik"
   ✅ "putar musik jazz di spotify"
   ```

2. **Satu Task per Request** - Lebih baik request terpisah
   ```
   ❌ "buka chrome, cari tutorial python, lalu buat catatan"
   ✅ "buka chrome"
   ✅ "cari tutorial python"
   ✅ "buat catatan tentang..."
   ```

3. **Gunakan Kata Kunci yang Tepat**
   - "putar" / "play" → Media playback
   - "buka" / "open" → Open app/browser
   - "cari" / "search" → Search/research
   - "buat" / "create" → File generation
   - "hitung" / "calculate" → Python execution

---

## 💻 CLI COMMANDS REFERENCE

### Startup Options

```bash
# Interactive mode (recommended)
python kicad_cli.py -i

# Direct KiCad generation
python kicad_cli.py "description"

# Web search mode
python kicad_cli.py -s "query"

# Research mode
python kicad_cli.py -r "topic"

# Google Workspace mode
python kicad_cli.py -g
```

### Interactive Mode Commands

| Command | Shortcut | Fungsi |
|---------|----------|--------|
| `/search <query>` | `/s` | Web search |
| `/research <topic>` | `/r` | Deep research |
| `/google` | `/g` | Google Workspace mode |
| `/gmail <action>` | - | Gmail operations |
| `/drive <action>` | - | Drive operations |
| `/calendar <action>` | `/cal` | Calendar operations |
| `/sheets <action>` | - | Sheets operations |
| `/forms <action>` | - | Forms operations |
| `/help` | `/h` | Show help |
| `/clear` | `/c` | Clear screen |
| `exit` | `quit` | Exit program |

### Natural Language Commands (via ReAct)

Cukup ketik dalam bahasa natural:

```
# Media Control
> putar musik jazz di spotify
> play video tutorial python di youtube
> pause musiknya
> next song

# Desktop Control
> buka chrome
> tutup notepad
> screenshot layar

# Python Execution
> hitung faktorial 20
> buat list bilangan prima 1-100

# File Generation
> buatkan laporan word tentang AI
> buat excel data penjualan

# KiCad Schematic
> buat ESP32 dengan sensor DHT11
> rangkaian arduino dengan 4 relay
```

### Direct Input (Legacy)

Ketik deskripsi langsung untuk generate skematik:
```
> Buat ESP32 dengan sensor suhu DHT11
> Arduino Uno dengan 3 LED dan push button
> Rangkaian power supply 12V ke 5V
```

---

## 🏗️ ARCHITECTURE

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      JAWIR OS Desktop                       │
├─────────────────────────┬───────────────────────────────────┤
│      Chat Panel         │         Workspace Panel           │
│  ┌─────────────────┐    │    ┌──────────────────────────┐   │
│  │ User Input      │    │    │ KiCad Viewer             │   │
│  │ AI Response     │    │    │ Research Results         │   │
│  │ Status Updates  │    │    │ Google Workspace         │   │
│  └─────────────────┘    │    └──────────────────────────┘   │
├─────────────────────────┴───────────────────────────────────┤
│                    FastAPI Backend                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 LangGraph Agent                       │  │
│  │  START → Supervisor → Researcher ↔ Validator →        │  │
│  │                         ↑    ↓                        │  │
│  │                         └────┘ (ReAct Loop)           │  │
│  │                              → Synthesizer → END      │  │
│  └───────────────────────────────────────────────────────┘  │
│                    │                     │                  │
│            ┌───────┴───────┐     ┌───────┴───────┐         │
│            │ Gemini 2.0    │     │ Tavily Search │         │
│            │ Flash LLM     │     │ Web Research  │         │
│            └───────────────┘     └───────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Agent Graph Flow

```
                    ┌─────────────┐
                    │    START    │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │ SUPERVISOR  │ (Plans execution)
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ RESEARCHER  │ │KICAD_DESIGNER│ │ SYNTHESIZER │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           ▼               │               │
    ┌─────────────┐        │               │
    │  VALIDATOR  │◄───────┘               │
    └──────┬──────┘                        │
           │ (loop if needed)              │
           ▼                               ▼
    ┌─────────────┐                 ┌─────────────┐
    │ SYNTHESIZER │                 │     END     │
    └──────┬──────┘                 └─────────────┘
           ▼
    ┌─────────────┐
    │     END     │
    └─────────────┘
```

---

## 🔧 TROUBLESHOOTING

### Common Issues

#### 1. Google OAuth Error
```
Error: Invalid or expired OAuth state parameter
```
**Solusi:**
```bash
cd d:\jawirv2\google_workspace_mcp
python manual_auth.py
```

#### 2. Encoding Error
```
Error: 'charmap' codec can't encode character
```
**Solusi:** Sudah ditangani dengan `PYTHONIOENCODING=utf-8`

#### 3. API Rate Limit
```
Error: Quota exceeded for gemini-2.0-flash
```
**Solusi:** JAWIR OS memiliki API key rotation otomatis

#### 4. MCP Server Connection
```
Error: Google Workspace MCP not found
```
**Solusi:**
```bash
# Pastikan path benar
cd d:\jawirv2\google_workspace_mcp
python main.py --single-user --tools gmail drive calendar sheets forms
```

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `.env` | `backend/` | API keys |
| `credentials.json` | `google_workspace_mcp/` | Google OAuth client |
| `<email>.json` | `~/.google_workspace_mcp/credentials/` | User tokens |

### Required API Keys

| Key | Service | Required For |
|-----|---------|--------------|
| `GOOGLE_API_KEY` | Gemini AI | LLM backbone |
| `TAVILY_API_KEY` | Tavily | Web search |
| `USER_GOOGLE_EMAIL` | Google Workspace | OAuth identity |

---

## 📞 QUICK REFERENCE CARD

```
┌──────────────────────────────────────────────────────────────────┐
│                       JAWIR OS QUICK REF                         │
├──────────────────────────────────────────────────────────────────┤
│ START: python kicad_cli.py -i                                    │
├──────────────────────────────────────────────────────────────────┤
│                    🎵 MEDIA CONTROL                              │
├──────────────────────────────────────────────────────────────────┤
│ SPOTIFY: "putar musik jazz di spotify"                           │
│          "pause musiknya" | "next song" | "stop musik"           │
│          "buka spotify" | "tutup spotify"                        │
│                                                                  │
│ YOUTUBE: "putar video tutorial python di youtube"                │
│          "cari video react di youtube"                           │
├──────────────────────────────────────────────────────────────────┤
│                    🖥️ DESKTOP CONTROL                            │
├──────────────────────────────────────────────────────────────────┤
│ APPS:    "buka chrome" | "buka vscode" | "buka notepad"          │
│          "tutup chrome" | "tutup spotify"                        │
│ BROWSER: "buka website github.com"                               │
│ SEARCH:  "cari di google python tutorial"                        │
│ CAPTURE: "screenshot layar"                                      │
├──────────────────────────────────────────────────────────────────┤
│                    🐍 PYTHON & FILES                             │
├──────────────────────────────────────────────────────────────────┤
│ PYTHON:  "hitung faktorial 10" | "buat list prima 1-50"          │
│ FILES:   "buatkan laporan word tentang IoT"                      │
│          "buat PDF tutorial python"                              │
│          "buat excel data penjualan"                             │
├──────────────────────────────────────────────────────────────────┤
│                    🔧 KICAD & RESEARCH                           │
├──────────────────────────────────────────────────────────────────┤
│ KICAD:   "buat ESP32 dengan sensor DHT11"                        │
│ SEARCH:  /search <query>                                         │
│ RESEARCH:/research <topic>                                       │
├──────────────────────────────────────────────────────────────────┤
│                    📧 GOOGLE WORKSPACE                           │
├──────────────────────────────────────────────────────────────────┤
│ MODE:    /google                                                 │
│ GMAIL:   /gmail labels | search | send | draft                   │
│ DRIVE:   /drive list | search | create | upload                  │
│ CALENDAR:/calendar list | events | add                           │
│ SHEETS:  /sheets info | read | write | create                    │
│ FORMS:   /forms create | get | responses                         │
├──────────────────────────────────────────────────────────────────┤
│ UTILS:   /help  /clear  exit                                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## ⚡ FUNCTION CALLING V2 (NEW!)

### Apa itu Function Calling?

JAWIR OS V2 menggunakan **Gemini Native Function Calling** — Gemini secara autonomous memilih dan memanggil tools tanpa hardcoded if-else routing.

**Sebelum (V1):** Gemini → structured output `{action, action_input}` → kode Python routing manual
**Sesudah (V2):** Gemini → `bind_tools()` → Gemini langsung pilih tool → auto-execute

### Cara Aktivasi

```env
# Di file backend/.env
USE_FUNCTION_CALLING=true    # Aktifkan V2 (Function Calling)
USE_FUNCTION_CALLING=false   # Kembali ke V1 (Legacy ReAct)
```

### FC Tools Tersedia (12 Tools)

| # | Tool | Deskripsi |
|---|------|-----------|
| 1 | `web_search` | Cari informasi di internet via Tavily API |
| 2 | `generate_kicad_schematic` | Generate skematik KiCad dari deskripsi |
| 3 | `run_python_code` | Eksekusi kode Python |
| 4 | `gmail_search` | Cari email di Gmail |
| 5 | `gmail_send` | Kirim email via Gmail |
| 6 | `drive_search` | Cari file di Google Drive |
| 7 | `drive_list` | List isi folder Drive |
| 8 | `calendar_list_events` | List event kalender |
| 9 | `calendar_create_event` | Buat event baru |
| 10 | `open_app` | Buka aplikasi desktop |
| 11 | `open_url` | Buka URL di browser |
| 12 | `close_app` | Tutup aplikasi |

### Architecture V2

```
┌─────────────────────────────────────────┐
│           User Request                   │
│              ↓                           │
│       quick_router_node                  │
│         (greeting?)                      │
│        /          \                      │
│   [yes]           [no]                   │
│     ↓               ↓                   │
│   END         fc_agent_node              │
│              (Gemini + bind_tools)       │
│                  ↓                       │
│           Tool Execution Loop            │
│           (max 5 iterations)             │
│                  ↓                       │
│                END                       │
└─────────────────────────────────────────┘
```

### Perbedaan V1 vs V2

| Aspek | V1 (Legacy) | V2 (Function Calling) |
|-------|-------------|----------------------|
| **Tool selection** | Manual if-else | Gemini autonomous |
| **Tools** | 42+ (kicad_cli.py) | 12 (tools_registry.py) |
| **Graph** | 6 nodes | 3 nodes |
| **Routing** | Python parsing | Native API |
| **Reliability** | Parsing bisa gagal | API stabil |
| **Fallback** | N/A | Bisa rollback ke V1 |

### Rollback ke V1

Jika V2 bermasalah, rollback instan:

```bash
# 1. Edit .env
USE_FUNCTION_CALLING=false

# 2. Restart server
# V1 otomatis aktif kembali
```

### Dokumentasi Terkait

- `backend/ARCHITECTURE_V2.md` — Arsitektur detail V2
- `backend/TOOLS_INVENTORY.md` — Inventaris lengkap semua tools
- `backend/ADDING_TOOLS.md` — Panduan menambah tools baru
- `backend/TROUBLESHOOTING_FC.md` — Troubleshooting FC issues
- `backend/ROLLBACK.md` — Prosedur rollback

---

## 🎯 CONTOH PENGGUNAAN LENGKAP

### Skenario 1: Kerja dengan Musik
```
User: buka spotify dan putar musik lo-fi
JAWIR: ✅ Spotify opened! ✅ Now playing: lo-fi

User: skip ke lagu berikutnya
JAWIR: ✅ Skipped to next track

User: pause dulu
JAWIR: ✅ Paused
```

### Skenario 2: Riset dan Buat Laporan
```
User: cari info tentang machine learning
JAWIR: ✅ Search results: [5 hasil tentang ML...]

User: buatkan laporan word dari info tadi
JAWIR: ✅ Word document created: output/document.docx
```

### Skenario 3: Development Session
```
User: buka vscode
JAWIR: ✅ Opened application: vscode

User: cari di google python fastapi tutorial
JAWIR: ✅ Google search opened for: python fastapi tutorial

User: hitung berapa 2 pangkat 32
JAWIR: ✅ Python executed: 4294967296
```

### Skenario 4: IoT Project
```
User: buat ESP32 dengan sensor DHT11 dan LED
JAWIR: [Proses ReAct - search component, generate schematic]
       ✅ Schematic created: output/esp32_dht11_led.kicad_sch
```

---

## 📄 LICENSE

MIT License - Feel free to use and modify.

---

**JAWIR OS** - *AI Assistant dari Ngawi, Jawa Terkuat!* 🇮🇩
