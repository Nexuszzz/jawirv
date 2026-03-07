# 🤖 JAWIR OS - Just Another Wise Intelligent Resource

Desktop AI Agent untuk Engineer dengan fokus pada KiCad schematic generation, desktop automation, dan Google Workspace integration.

<p align="center">
  <a href="https://youtu.be/k86AON_IQDk">
    <img src="https://img.youtube.com/vi/k86AON_IQDk/hqdefault.jpg" alt="Overview Video" width="720">
  </a>
</p>

## ✨ Fitur Lengkap

JAWIR OS memiliki **9 kategori fitur utama**:

### 1. 🎵 **Spotify Control**
   - Play musik dengan natural language atau slash commands
   - Kontrol playback: pause, resume, next, previous
   - Search dan play otomatis dari search results
   - Commands: `/spotify <query>`, `/pause`, `/resume`, `/next`, `/prev`, `/stop`

### 2. 📺 **YouTube Control**
   - Buka dan play video YouTube
   - Pilih browser (Chrome/Edge/Firefox)
   - Kontrol video (fullscreen)
   - Commands: `/yt <query>`, `/ytchrome <query>`, `/ytedge <query>`, `/ytfullscreen`, `/play <query>`

### 3. 🖥️ **Desktop Control**
   - Buka aplikasi Windows (Spotify, Steam, Discord, WhatsApp, dll)
   - Ambil screenshot
   - Kontrol window (minimize, maximize, close)
   - Mouse & keyboard automation
   - Commands: `/open <app>`, `/close <app>`, `/screenshot`, `/minimize`, `/maximize`

### 4. 🖥️ **Computer Use (NEW! Gemini Vision Browser Automation)**
   - Browser automation dengan natural language
   - Gemini Vision "melihat" browser seperti manusia
   - Multi-step task execution
   - **YouTube Play** - Play video otomatis di browser
   - **Journal Download** - Download paper dari arXiv otomatis
   - **Web Interaction** - AI-powered web browsing & interaction
   - Form filling otomatis
   - Commands: `/cu <task>`, `/ytplay <query>`, `/journal <query>`, `/download <url>`, `/interact <url> <task>`, `/vbrowse <url>`, `/webfill <url> <data>`, `/vsearch <query>`

### 5. 🐍 **Python Interpreter**
   - Eksekusi Python code real-time
   - Install packages otomatis
   - Data analysis & visualization
   - File operations
   - Commands: `/python <code>`, `/py <code>`, `/pip install <package>`

### 6. 🌐 **Web Browsing & Search**
   - Web search via Tavily API
   - Deep research dengan multi-level search
   - Buka website di browser
   - Extract dan summarize content
   - Commands: `/search <query>`, `/research <topic>`, `/browse <url>`

### 7. 📄 **File Generation**
   - Word documents (.docx)
   - PDF files
   - Text files (.txt, .md)
   - JSON files
   - Excel & CSV
   - Commands: `/word <content>`, `/pdf <content>`, `/excel <data>`, `/csv <data>`

### 8. 📧 **Google Workspace Integration**
   - Gmail: list, read, send, search emails
   - Google Drive: list, upload, download files
   - Google Calendar: list, create events
   - Google Sheets: read, write spreadsheets
   - Commands: `/gmail list`, `/drive upload`, `/calendar events`

### 9. ⚡ **KiCad Schematic Generation**
   - Generate schematic dari deskripsi natural language
   - Research mode untuk komponen elektronik
   - Auto-generate symbols & connections
   - Component placement optimization
   - Commands: `/kicad generate <description>`, `/kicad research <component>`

### 🧠 **ReAct Agent (Natural Language)**
   - Semua fitur di atas bisa dipanggil dengan bahasa natural
   - Multi-step planning & execution
   - Automatic retry dengan strategi berbeda
   - Real-time thinking dan validation

## 🧠 V2 Architecture - Gemini Native Function Calling

JAWIR OS sekarang mendukung **dual-mode architecture**:

### V2 Mode (Function Calling) ⚡ NEW
- **Gemini memilih tools secara autonomous** via `bind_tools()` API
- Tidak ada lagi hardcoded if-else routing
- 12 tools terdaftar sebagai LangChain `StructuredTool` dengan Pydantic schemas
- Graph: `START → quick_router → fc_agent → END`
- Aktivasi: `USE_FUNCTION_CALLING=true` di `.env`

### V1 Mode (Legacy)
- ReAct loop dengan structured output parsing
- Gemini menghasilkan `{thought, action, action_input}` → routing manual
- 42+ tools tersedia via `kicad_cli.py`
- Tetap tersedia sebagai fallback

### FC Tools (V2)

| Tool | Deskripsi |
|------|-----------|
| `web_search` | Cari info di internet via Tavily |
| `generate_kicad_schematic` | Generate skematik KiCad |
| `run_python_code` | Eksekusi kode Python |
| `gmail_search` / `gmail_send` | Gmail search & send |
| `drive_search` / `drive_list` | Google Drive operations |
| `calendar_list_events` / `calendar_create_event` | Calendar operations |
| `open_app` / `open_url` / `close_app` | Desktop control |

> Lihat `backend/TOOLS_INVENTORY.md` untuk inventaris lengkap.
> Lihat `backend/ADDING_TOOLS.md` untuk panduan menambah tools.
> Lihat `backend/ARCHITECTURE_V2.md` untuk arsitektur detail.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+ (tested with 3.13.7) atau Python 3.11+
- Node.js 18+
- Google Gemini API key
- Tavily API key
- Windows OS (for desktop automation features)

### Setup

1. **Clone & Install Backend**

```bash
cd jawirv2/backend/tools/kicad
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. **Configure API Keys**

Create `.env` file di `backend/tools/kicad/`:
```env
# Get from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Get from: https://tavily.com/
TAVILY_API_KEY=your_tavily_api_key_here

# Optional: Google Workspace
USER_GOOGLE_EMAIL=your_email@gmail.com
```

3. **Install Dependencies**

```bash
pip install pyautogui pywinauto langchain-core langchain-google-genai tavily-python python-docx reportlab openpyxl
```

4. **Run JAWIR CLI**

```bash
python kicad_cli.py -i
```

## 💬 Cara Penggunaan

### Mode Interactive (Recommended)

Jalankan CLI dalam mode interactive:
```bash
python kicad_cli.py -i
```

Lalu gunakan:
- **Natural Language**: "putar lagu bohemian rhapsody di spotify"
- **Slash Commands**: `/spotify bohemian rhapsody`

### Mode Single Command

```bash
python kicad_cli.py "putar lagu starboy weeknd"
```

## 📖 Dokumentasi Lengkap

### 🚀 Quick Reference - Computer Use Commands (NEW!)

| Command | Description | Example |
|---------|-------------|---------|
| `/journal <query>` | Download paper dari arXiv | `/journal LSTM time series` |
| `/ytplay <query>` | Play YouTube video | `/ytplay lofi study music` |
| `/ytsearch <query>` | Search YouTube only | `/ytsearch python tutorial` |
| `/download <url>` | Download file dari URL | `/download https://example.com/file.pdf` |
| `/interact <url> <task>` | AI web interaction | `/interact github.com find trending projects` |

**Download Locations:**
- Journals/Papers: `backend/downloads/journals/`
- General Files: `backend/downloads/`

---

### 🎵 SPOTIFY

**Slash Commands:**
```bash
/spotify <query>          # Play musik
/pause atau /stop         # Pause playback
/resume atau /play        # Resume playback
/next atau /skip          # Next track
/prev atau /previous      # Previous track
```

**Natural Language Examples:**
- "putar lagu bohemian rhapsody di spotify"
- "play some jazz music on spotify"
- "pause musik"
- "lanjut ke lagu berikutnya"

**How It Works:**
1. Buka Spotify app otomatis
2. Search lagu via `spotify:search:` URI
3. Klik tombol Play hijau secara otomatis
4. Kontrol playback via media keys

---

### 📺 YOUTUBE

**Slash Commands:**
```bash
/yt <query>               # Search YouTube (default Chrome)
/youtube <query>          # Same as /yt
/play <query>             # Search & play first video
/ytchrome <query>         # Force Chrome browser
/ytedge <query>           # Force Edge browser
/ytlist <query>           # List search results
/ytfullscreen             # Toggle fullscreen (press 'f')
/fullscreen               # Same as /ytfullscreen
```

**Natural Language Examples:**
- "buka youtube tutorial python"
- "play video cara membuat robot"
- "youtube music lofi hip hop"

**Features:**
- Auto search & play video
- Browser selection (Chrome/Edge/Firefox)
- Video controls (pause, fullscreen)
- Playlist support

---

### 🖥️ DESKTOP CONTROL

**Available Apps:**
- Spotify, Steam, Discord, WhatsApp
- Telegram, Chrome, Edge, Firefox
- VS Code, File Explorer, Calculator
- Notepad, Word, Excel, PowerPoint, KiCad

**Slash Commands:**
```bash
/open <app>              # Buka aplikasi
/close <app>             # Tutup aplikasi
/screenshot              # Ambil screenshot (atau /ss)
/minimize                # Minimize window (atau /min)
/maximize                # Maximize window (atau /max)
/url <url>               # Buka URL di browser
/apps                    # List aplikasi yang berjalan
```

**Natural Language Examples:**
- "buka spotify"
- "tutup steam"
- "ambil screenshot"
- "minimize window"

---

### �️ COMPUTER USE (Gemini Vision Browser Automation)

**FITUR BARU!** Browser automation menggunakan Gemini Vision - model AI yang bisa "melihat" browser seperti manusia dan melakukan aksi otomatis.

**Slash Commands:**
```bash
/cu <task>               # Natural language browser task
/computeruse <task>      # Alias untuk /cu
/vbrowse <url> [task]    # Visual browse dengan tugas spesifik
/webfill <url> <data>    # Isi form web otomatis
/vsearch <query>         # Visual web search
/webshot <url>           # Screenshot halaman web
```

**Contoh Penggunaan:**
```bash
# Browser automation dengan natural language
/cu search python tutorials on youtube and click first video
/cu go to github.com and find trending repositories
/cu fill login form with username=john password=secret123

# Visual browse - navigasi + tugas spesifik  
/vbrowse github.com/google find the most popular repository
/vbrowse amazon.com search for arduino starter kit

# Form filling otomatis
/webfill login.example.com username=john password=secret email=john@email.com
/webfill contact-form.com name=John message=Hello there

# Visual search dengan engine pilihan
/vsearch python machine learning tutorial
/vsearch --youtube arduino beginner project
/vsearch --bing best laptop 2026

# Web screenshot
/webshot https://github.com
```

**Cara Kerja Computer Use:**
1. **Screenshot** - Ambil screenshot dari browser
2. **Vision Analysis** - Gemini Vision menganalisis gambar
3. **Action Planning** - Model merencanakan aksi (click, type, scroll)
4. **Execution** - Playwright menjalankan aksi di browser
5. **Feedback Loop** - Ambil screenshot baru, ulangi sampai selesai

**Kelebihan Computer Use:**
- ✅ Natural language - cukup deskripsikan tugas dalam bahasa biasa
- ✅ Vision-based - model "melihat" UI seperti manusia
- ✅ Auto-retry - otomatis coba ulang jika gagal
- ✅ Multi-step - bisa handle tugas kompleks dengan banyak langkah
- ✅ Form filling - bisa isi form dengan data yang diberikan
- ✅ **YouTube Auto-Play** - Search dan play video otomatis
- ✅ **Journal Download** - Download paper dari arXiv ke local
- ✅ **Web Interaction** - Browse dan interaksi dengan website kompleks

**Fitur Baru Computer Use:**

#### 📚 **Journal Search & Download**
```bash
/journal <query>         # Download paper dari arXiv

# Contoh:
/journal Machine Learning IoT
/journal Artificial Intelligence healthcare
/journal LSTM time series forecasting
```

**Output:**
- PDF paper didownload ke `backend/downloads/journals/`
- Screenshot halaman abstract
- Info: judul, penulis, arXiv ID, ukuran file

**Tested:** ✅ arXiv:2602.03693 "OCRTurk: A Comprehensive OCR Benchmark for Turkish" (1005 KB)

#### ▶️ **YouTube Play (Computer Use)**
```bash
/ytplay <query>          # Search dan play YouTube video
/ytsearch <query>        # Search only (tanpa play)

# Contoh:
/ytplay lofi hip hop music
/ytplay relaxing piano music
/ytplay tutorial Arduino ESP32
/ytsearch Python machine learning
```

**Output:**
- Browser terbuka dan memutar video
- Menampilkan judul video yang sedang diputar
- Auto-click video pertama dari search results

**Tested:** ✅ "Relaxing Piano Music: Romantic Music, Beautiful Relaxing Music, Sleep Music, Stress Relief ★122"

#### 🌐 **Web Interaction & Download**
```bash
/interact <url> <task>   # AI-powered web interaction
/download <url> [name]   # Download file dari URL

# Contoh:
/interact github.com/trending cari project Python populer
/interact stackoverflow.com cari solusi error asyncio
/download https://arxiv.org/pdf/2301.12345.pdf mypaper.pdf
```

**Setup Computer Use:**
```bash
cd backend/tools/computer_use
python setup_computer_use.py

# Atau manual:
pip install google-genai playwright
playwright install chromium
```

**Requirements:**
- GEMINI_API_KEY environment variable
- Playwright browser (chromium)
- Python 3.11+
- Model: `gemini-3-pro-preview` (multimodal vision)

---

### �🐍 PYTHON INTERPRETER

**Slash Commands:**
```bash
/python <code>           # Eksekusi Python code
/py <code>               # Alias untuk /python
/pip install <package>   # Install Python package
```

**Natural Language Examples:**
- "hitung faktorial 10 dengan python"
- "buat chart dari data [1,2,3,4,5]"
- "install package numpy"

**Features:**
- Real-time code execution
- Persistent session
- Auto package installation
- Data visualization support

---

### 🌐 WEB BROWSING & SEARCH

**Slash Commands:**
```bash
/search <query>          # Web search via Tavily API
/google <query>          # Google search di browser
/browse <url>            # Buka website di browser
/research <topic>        # Deep research + KiCad mode
```

**Natural Language Examples:**
- "cari informasi tentang ESP32"
- "research tentang machine learning"
- "buka google.com"

**Deep Research Features:**
- Breadth-first search (4 concurrent sources)
- Depth exploration (2 levels)
- Source citation
- Comprehensive synthesis

---

### 📄 FILE GENERATION

**Slash Commands:**
```bash
/word <content>          # Generate Word document
/pdf <content>           # Generate PDF
/txt <content>           # Create text file
/md <content>            # Create Markdown file
/json <data>             # Create JSON file
/excel <data>            # Create Excel spreadsheet
/csv <data>              # Create CSV file
```

**Natural Language Examples:**
- "buatkan dokumen word tentang IoT"
- "generate pdf tutorial python"
- "buat file excel dengan data penjualan"

**Supported Formats:**
- Word (.docx) - formatted documents
- PDF - professional reports
- Text (.txt, .md) - plain text
- JSON - structured data
- Excel (.xlsx) - spreadsheets with formulas
- CSV - comma-separated values

---

### 📧 GOOGLE WORKSPACE

**Gmail Commands:**
```bash
/gmail list              # List emails
/gmail read <id>         # Read email
/gmail send              # Send email
/gmail search <query>    # Search emails
```

**Drive Commands:**
```bash
/drive list              # List files
/drive upload <path>     # Upload file
/drive download <id>     # Download file
/drive search <query>    # Search files
```

**Calendar Commands:**
```bash
/calendar events         # List upcoming events
/calendar create         # Create event
/calendar today          # Today's schedule
```

**Sheets Commands:**
```bash
/sheets read <id>        # Read spreadsheet
/sheets write <id>       # Write to spreadsheet
/sheets create           # Create new sheet
```

**Natural Language Examples:**
- "list email inbox saya"
- "upload file laporan.pdf ke drive"
- "jadwal meeting hari ini"
- "baca spreadsheet penjualan"

---

### ⚡ KICAD SCHEMATIC GENERATION

**Slash Commands:**
```bash
/kicad generate <desc>   # Generate schematic
/kicad research <comp>   # Research component
/kicad symbols           # List available symbols
```

**Natural Language Examples:**
- "buatkan schematic LED sederhana dengan resistor 220 ohm"
- "generate schematic powerbank dengan 18650"
- "research komponen ESP32 development board"

**Features:**
- Natural language → KiCad schematic
- Auto component research
- Symbol library integration
- Connection optimization
- Annotation & net labeling

## 🎯 Use Cases & Workflows

### 1. 📚 Academic Research Pipeline (NEW!)
```
# Morning research session
/ytplay lofi study music              # Background music
/journal transformer neural networks   # Download paper 1
/journal attention mechanism NLP       # Download paper 2
/journal BERT language model          # Download paper 3

Result: 3 papers in downloads/journals/ + music playing
```

**Natural language version:**
```
"play study music dan download paper tentang LSTM time series"
→ YouTube plays study music
→ arXiv search & download PDF
→ Save to local computer
```

### 2. 🎵 Music & Research Workflow
```
"putar lagu lofi hip hop dan search paper tentang machine learning"
→ Plays music di Spotify
→ Search academic papers
→ Summarize results
```

### 3. 💻 Development Workflow
```
"buka vscode dan spotify, putar lagu focus music"
→ Opens VS Code
→ Opens Spotify
→ Plays focus playlist
```

### 4. 🔬 Electronics Design Workflow
```
"research ESP32 specs dan buatkan schematic dengan LED indicator"
→ Research ESP32 datasheet
→ Generate KiCad schematic
→ Add LED circuit
```

### 5. 📧 Email & Calendar Management
```
"list email penting hari ini dan show jadwal meeting"
→ List priority emails
→ Show calendar events
→ Summarize agenda
```

### 6. 🌐 Web Research Automation (NEW!)
```
/interact github.com/trending find Python AI projects
/download https://example.com/dataset.csv mydata.csv
/interact stackoverflow.com search asyncio best practices

Result: AI browse websites + extract info + download files
```

## 🛠️ System Requirements

### Required Software
- **Python 3.11+** (tested with 3.11.9)
- **Windows 10/11** (for desktop automation)
- **Spotify Desktop App** (for Spotify features)
- **Chrome or Edge Browser** (for YouTube/web features)
- **KiCad 8.0+** (for schematic generation)

### Python Packages
```
langchain-core>=0.3.29
langchain-google-genai>=2.0.8
tavily-python>=0.5.0
pyautogui>=0.9.54
pywinauto>=0.6.9
python-docx>=1.1.2
reportlab>=4.2.5
openpyxl>=3.1.5
google-auth>=2.35.0
google-auth-oauthlib>=1.2.1
```

### API Keys Required
1. **Google Gemini API** - https://aistudio.google.com/app/apikey
   - Free tier: 15 requests/minute
   - Used for: ReAct Agent, natural language processing

2. **Tavily API** - https://tavily.com/
   - Free tier: 1000 searches/month
   - Used for: Web search & research

3. **Google OAuth** (Optional) - https://console.cloud.google.com/
   - For: Gmail, Drive, Calendar, Sheets integration
   - Required scopes: gmail, drive, calendar

## 💡 Tips & Tricks

### Multi-Step Commands
Gunakan kata "dan", "lalu", "kemudian" untuk multi-step:
```
"putar lagu jazz dan search tentang deep learning lalu buatkan summary"
```

### Command Chaining
Kombinasi slash commands:
```
/spotify chill music
/youtube tutorial python
/search best practices python
/journal deep learning computer vision
/ytplay lofi beats study
```

### Computer Use Automation
Download paper dan play background music:
```
/journal transformer neural network
/ytplay study music lofi
```

Web research dengan screenshot:
```
/interact github.com find trending AI projects
/download https://example.com/data.csv
```

### Research Mode
Untuk research mendalam:
```
"research komponen ESP32 untuk IoT project"
→ Deep research dengan 4 sumber
→ 2 level depth
→ Comprehensive synthesis
```

### Desktop Automation
Otomasi workflow harian:
```
"buka spotify, vscode, dan chrome lalu putar lagu focus"
```

### Python Quick Test
Test code cepat:
```
/python print([x**2 for x in range(10)])
```

## 🏗️ Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────┐
│                  JAWIR OS CLI Agent                      │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │          ReAct Agent (LangChain + Gemini)          │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │  Natural Language Understanding              │  │ │
│  │  │  → Multi-step Planning                       │  │ │
│  │  │  → Tool Selection & Execution                │  │ │
│  │  │  → Result Validation & Retry                 │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│          ┌───────────────┴───────────────┐              │
│          ▼                               ▼              │
│  ┌──────────────┐              ┌──────────────────┐    │
│  │ Slash Cmds   │              │ Tool Dispatcher  │    │
│  │ /spotify     │              │ - Desktop        │    │
│  │ /youtube     │              │ - Python         │    │
│  │ /search      │              │ - File           │    │
│  │ /python      │              │ - Google WS      │    │
│  │ /gmail       │              │ - KiCad          │    │
│  └──────────────┘              └──────────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Desktop    │  │  Google APIs │  │  Tavily API  │
│  Automation  │  │  (OAuth 2.0) │  │ (Web Search) │
│              │  │              │  │              │
│ - pyautogui  │  │ - Gmail      │  │ - Research   │
│ - pywinauto  │  │ - Drive      │  │ - Sources    │
│ - keyboard   │  │ - Calendar   │  │ - Summary    │
│ - mouse      │  │ - Sheets     │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

### ReAct Agent Flow
```
User Input → Parse Intent → Plan Steps → Execute Tools → Validate → Output
     ▲                                         │
     └─────────── Retry if Failed ─────────────┘
```

### Desktop Control Architecture
```
Natural Language / Slash Command
          ↓
   JawirInterpreter
          ↓
   desktop_control.py
          ↓
┌─────────┬─────────┬─────────┐
│ Spotify │ YouTube │  Apps   │
└─────────┴─────────┴─────────┘
    ↓         ↓         ↓
 pywinauto  pyautogui  subprocess
```

## 📁 Project Structure

```
jawirv2/
└── jawirv2/
    └── backend/
        └── tools/
            └── kicad/
                ├── kicad_cli.py           # Main CLI with ReAct Agent
                ├── interpreter.py         # JawirInterpreter (tool wrapper)
                ├── desktop_control.py     # Desktop automation
                ├── python_interpreter.py  # Python execution
                ├── file_ops.py           # File generation
                ├── google_auth.py        # Google OAuth
                ├── gmail_service.py      # Gmail integration
                ├── drive_service.py      # Drive integration
                ├── calendar_service.py   # Calendar integration
                ├── sheets_service.py     # Sheets integration
                └── kicad_generator.py    # Schematic generation
```

### Key Files

**kicad_cli.py** (3,259 lines)
- Main entry point
- ReAct Agent implementation
- Interactive mode
- Slash command handlers
- Multi-step detection
- Help system

**interpreter.py** (600+ lines)
- JawirInterpreter class
- Tool dispatcher
- Method wrappers for all features:
  - Desktop control
  - Python execution
  - File operations
  - Google Workspace
  - KiCad generation

**desktop_control.py** (800+ lines)
- Spotify control (search, play, pause, next, prev)
- YouTube control (open, play, browser selection)
- App launcher (Spotify, Discord, Steam, etc)
- Screenshot & window management
- Mouse & keyboard automation

## 🔧 Configuration

### Environment Variables (.env)

```env
# Required
GOOGLE_API_KEY=AIza...                    # Gemini API key
TAVILY_API_KEY=tvly-...                   # Tavily search API key

# Optional - Google Workspace
USER_GOOGLE_EMAIL=user@gmail.com          # Your Google email
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx

# Optional - Desktop Automation
DEFAULT_BROWSER=chrome                    # chrome or edge
SPOTIFY_INSTALL_PATH=C:\Users\...\Spotify.exe

# Optional - Python Interpreter
PYTHON_TIMEOUT=30                         # Execution timeout (seconds)
AUTO_INSTALL_PACKAGES=true                # Auto pip install

# Optional - File Generation
OUTPUT_DIR=./generated_files              # Output directory
DEFAULT_FONT=Arial                        # PDF font
```

### CLI Arguments

```bash
python kicad_cli.py [options] [command]

Options:
  -i, --interactive     Interactive mode (recommended)
  -h, --help           Show help message
  -v, --verbose        Verbose output
  --no-colors          Disable colored output
  --debug              Debug mode (show ReAct thinking)

Examples:
  python kicad_cli.py -i                  # Interactive mode
  python kicad_cli.py "play jazz music"   # Single command
  python kicad_cli.py -v -i               # Verbose interactive
```

## 🎨 UI Theme

JAWIR OS uses a custom coffee-inspired theme:

- **Primary**: `#dab80b` (Golden Yellow)
- **Background Dark**: `#181711` (Coffee Dark)
- **Background Light**: `#1f1e19` (Coffee Medium)
- **Cream**: `#f1f0ea` (Warm White)
- **Accent**: `#a66f35` (Copper)

## 🧪 Testing & Examples

### Test Individual Features

**Spotify Test:**
```bash
echo "/spotify starboy weeknd" | python kicad_cli.py -i
# Expected: ✅ Now Playing on Spotify: starboy weeknd
```

**Python Test:**
```bash
echo "/python print('Hello JAWIR!')" | python kicad_cli.py -i
# Expected: Hello JAWIR!
```

**Web Search Test:**
```bash
python kicad_cli.py "search tentang ESP32"
# Expected: Search results with sources
```

**Gmail Test:**
```bash
echo "/gmail list" | python kicad_cli.py -i
# Expected: List of recent emails
```

### Multi-Step Test

```bash
python kicad_cli.py "putar lagu jazz dan search tentang python"
# Expected: 
# 1. Plays jazz music on Spotify
# 2. Searches web for Python info
# 3. Returns combined results
```

### Natural Language Test

```bash
python kicad_cli.py -i
> buka spotify, putar lagu chill music, dan buatkan summary tentang AI
```

Expected flow:
1. Opens Spotify app
2. Searches and plays "chill music"
3. Performs web search about AI
4. Generates summary

## 🐛 Troubleshooting

### Computer Use - Browser Not Opening

**Problem:** `/ytplay` atau `/journal` error saat buka browser
**Solution:**
```bash
# Install Playwright browsers
pip install playwright
playwright install chromium

# Verify installation
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Computer Use - Asyncio Error

**Problem:** `Error: It looks like you are using Playwright Sync API inside the asyncio loop`
**Solution:** Already fixed! Uses `ThreadPoolExecutor` pattern. Update to latest version:
```bash
cd backend/tools/kicad
git pull
```

### Journal Download - No Results

**Problem:** `/journal` tidak menemukan paper
**Solution:**
1. Coba query lebih spesifik: `/journal LSTM time series forecasting`
2. Pastikan koneksi internet stabil
3. Check arXiv status: https://status.arxiv.org/

### YouTube Play - Video Not Playing

**Problem:** Video dibuka tapi tidak autoplay
**Solution:**
1. Pastikan browser tidak block autoplay
2. Chrome settings → Privacy → Site Settings → Additional content settings → Sound → Allow
3. Tunggu beberapa detik untuk loading

### Download Location Not Found

**Problem:** File downloaded tapi tidak ketemu
**Solution:**
```bash
# Default location:
cd d:\jawirv2\jawirv2\backend\downloads\journals\

# Atau check di terminal output:
📁 Location: <path_to_file>
```

### Spotify Not Playing

**Problem:** Music search works but doesn't play
**Solution:** 
1. Check if Spotify app is installed
2. Verify Spotify window can be focused
3. Adjust Play button coordinates in `desktop_control.py`:
```python
# Line ~450
play_x = rect.left + 420  # Adjust this value
play_y = rect.top + 340   # Adjust this value
```

### Python Import Errors

**Problem:** `ModuleNotFoundError`
**Solution:**
```bash
pip install -r requirements.txt
# or install individually:
pip install langchain-core langchain-google-genai tavily-python
```

### Google Workspace Auth Failed

**Problem:** OAuth authentication fails
**Solution:**
1. Check credentials in `.env`
2. Run manual auth:
```bash
cd google_workspace_mcp
$env:OAUTHLIB_INSECURE_TRANSPORT="1"
python main.py --single-user --tools gmail drive
```
3. Follow OAuth flow in browser

### Gemini API Rate Limit

**Problem:** "Resource exhausted" error
**Solution:**
- Free tier: 15 requests/minute
- Wait 1 minute between requests
- Or upgrade to paid tier

### Tavily Search Quota

**Problem:** "Quota exceeded"
**Solution:**
- Free tier: 1000 searches/month
- Check usage at https://tavily.com/dashboard
- Or upgrade plan

## 🔐 Security Notes

### API Key Safety
- Never commit `.env` file to git
- Use environment variables in production
- Rotate keys regularly

### Google OAuth
- Use OAuth 2.0 (never store passwords)
- Limit scopes to only what's needed
- Token stored securely in `~/.jawir/tokens/`

### Desktop Automation
- Automation scripts run with user privileges
- No elevation/admin required
- Safe for personal use

## 📊 Performance

### Benchmark Results (Average)

| Operation | Time | Notes |
|-----------|------|-------|
| Natural Language Parse | ~1-2s | Gemini 2.0 Flash |
| Web Search | ~2-3s | Tavily API |
| Deep Research | ~10-15s | 4 sources, 2 levels |
| Spotify Play | ~5-7s | App launch + search + click |
| Python Execution | <1s | Simple code |
| File Generation | ~2-5s | Depends on size |
| Gmail List | ~1-2s | OAuth + API call |

### Resource Usage

- **RAM**: ~200-300 MB (idle), ~500 MB (active)
- **CPU**: Low (5-10%) except during research
- **Network**: Minimal (API calls only)
- **Disk**: <100 MB (code + cache)

## 🚀 Advanced Features

### Custom Tool Integration

Add your own tools to `interpreter.py`:

```python
def my_custom_tool(self, param: str):
    """Your custom tool description"""
    # Your implementation
    return "result"
```

Then add to tool list in `kicad_cli.py`:

```python
tools.append(
    Tool(
        name="my_custom_tool",
        func=lambda p: interpreter.my_custom_tool(p),
        description="Description for ReAct agent"
    )
)
```

### Multi-Step Automation

Create automation scripts:

```python
# automation.py
import subprocess

commands = [
    "putar lagu focus music",
    "buka vscode",
    "search best python practices",
]

for cmd in commands:
    subprocess.run(['python', 'kicad_cli.py', cmd])
```

### Scheduled Tasks

Use Windows Task Scheduler:

1. Create task: "Open Music & IDE"
2. Trigger: Daily at 9 AM
3. Action: Run `python kicad_cli.py "buka spotify dan vscode"`

## 🔄 Updates & Changelog

### v2.2.0 (Current) - February 5, 2026 🆕
**🎯 ReAct Agent Compliance Update:**
JAWIR sekarang 100% sesuai konsep "AI Agent dengan ReAct Pattern"!

**Computer Use Integration ke ReAct:**
- ✅ `journal_search(query)` - Gemini bisa search & download paper
- ✅ `ytplay_vision(query)` - Gemini bisa play YouTube dengan AI vision
- ✅ `browse_interact(url|task)` - Gemini bisa browse & interaksi web
- ✅ `download_file(url|filename)` - Gemini bisa download file

**Google Workspace Integration ke ReAct:**
- ✅ `gmail_search(query)` - Search email
- ✅ `gmail_send(to|subject|body)` - Kirim email
- ✅ `gmail_draft(to|subject|body)` - Buat draft
- ✅ `drive_list(query)` - List/search Google Drive
- ✅ `drive_create(filename|content)` - Buat file di Drive
- ✅ `calendar_list()` - List events
- ✅ `calendar_add(text)` - Tambah event (natural language)
- ✅ `sheets_read(id|range)` - Baca Google Sheets
- ✅ `sheets_write(id|range|values)` - Tulis ke Sheets

**Conversational Mode:**
- ✅ Bisa ngobrol biasa tanpa tools
- ✅ Deteksi otomatis apakah perlu tools atau tidak
- ✅ Response casual yang friendly

**Contoh Penggunaan Baru:**
```
# Chat biasa (tanpa tools)
JAWIR> hai jawir!
💬 JAWIR: Hai! Piye kabare? Siap bantu!

# Tools via natural language (ReAct)
JAWIR> carikan paper tentang machine learning
🔧 Mode: ReAct Agent
💭 Thought: User mau paper. Gunakan journal_search.
⚡ Action: journal_search(machine learning)

JAWIR> kirim email ke boss tentang progress
🔧 Mode: ReAct Agent
💭 Thought: User mau kirim email. Gunakan gmail_send.
⚡ Action: gmail_send(boss@company.com|Progress|Update hari ini...)
```

### v2.1.0 - February 4, 2026
**Computer Use Enhancements:**
- ✅ **YouTube Auto-Play** - Search dan play video otomatis dengan Gemini Vision
- ✅ **Journal Download** - Download paper dari arXiv dengan 1 command
- ✅ **Web Interaction** - AI-powered browsing & task execution
- ✅ **File Download** - Direct download dari URL
- ✅ Thread-safe execution untuk Playwright integration
- ✅ Auto-screenshot & visual feedback
- ✅ Non-blocking browser control

**Tested Features:**
- ✅ YouTube: "Relaxing Piano Music: Romantic Music, Beautiful Relaxing Music, Sleep Music, Stress Relief ★122"
- ✅ Journal: arXiv:2602.03693 "OCRTurk: A Comprehensive OCR Benchmark for Turkish" (1005 KB)
- ✅ Download location: `backend/downloads/journals/`

**New Commands:**
- `/journal <query>` - Download paper dari arXiv
- `/ytplay <query>` - Search & play YouTube video
- `/ytsearch <query>` - Search YouTube (tanpa play)
- `/download <url> [filename]` - Download file dari URL
- `/interact <url> <task>` - AI-powered web interaction

### v2.0.0 - February 2026
- ✅ Added Spotify integration with coordinate-based clicking
- ✅ YouTube control with browser selection
- ✅ Desktop automation (apps, screenshot, window mgmt)
- ✅ Python interpreter with package management
- ✅ Google Workspace integration (Gmail, Drive, Calendar, Sheets)
- ✅ File generation (Word, PDF, Excel, CSV, JSON)
- ✅ ReAct Agent with natural language understanding
- ✅ Multi-step command support
- ✅ Comprehensive help system
- ✅ Interactive mode with slash commands

### v1.0.0 - January 2026
- Initial release
- KiCad schematic generation
- Web search via Tavily
- Basic ReAct agent

## 📝 Best Practices

### 1. Use Natural Language for Complex Tasks
```
❌ Don't: /search ESP32; /search Arduino; /create word summary
✅ Do: "research ESP32 vs Arduino dan buatkan comparison document"
```

### 2. Leverage Multi-Step Detection
```
❌ Don't: Run 3 separate commands
✅ Do: "buka spotify dan putar jazz lalu search about productivity"
```

### 3. Use Slash Commands for Quick Actions
```
✅ /spotify chill
✅ /youtube tutorial
✅ /python print(hello)
```

### 4. Combine Desktop Automation
```
✅ "buka spotify, discord, dan vscode lalu putar focus music"
```

### 5. Research Before Generating
```
✅ "research tentang IoT security lalu buatkan report PDF"
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. **More App Support**: Add support for more Windows apps
2. **MacOS/Linux Support**: Port desktop automation
3. **Spotify API**: Integrate official Spotify API (more reliable)
4. **Voice Control**: Add speech-to-text input
5. **GUI Frontend**: Build Electron/React UI
6. **Plugin System**: Extensible plugin architecture
7. **Cloud Sync**: Sync settings across devices

## 📜 License

MIT License - Feel free to use and modify.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - ReAct Agent framework
- [Google Gemini](https://ai.google.dev/) - LLM backbone (2.0 Flash)
- [Tavily](https://tavily.com/) - Web search API
- [PyAutoGUI](https://pyautogui.readthedocs.io/) - GUI automation
- [PyWinAuto](https://pywinauto.readthedocs.io/) - Windows UI automation
- [Spotify](https://www.spotify.com/) - Music streaming platform
- [Google Workspace](https://workspace.google.com/) - Productivity tools
- [KiCad](https://www.kicad.org/) - Electronics design automation

## 📞 Support

### Common Issues

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **API Key Issues**: Check `.env` file configuration
3. **Spotify Not Playing**: Adjust coordinates in `desktop_control.py`
4. **OAuth Failed**: Run manual auth script
5. **Rate Limit**: Wait or upgrade API plan

### Quick Fixes

```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt

# Clear cache
Remove-Item -Recurse ~\.jawir\cache\*

# Reset OAuth tokens
Remove-Item -Recurse ~\.jawir\tokens\*

# Test API keys
python kicad_cli.py "test api connection"
```

## 🎓 Learning Resources

### Tutorials
- **Getting Started**: Run `python kicad_cli.py --help`
- **Natural Language Examples**: Type `/help` in interactive mode
- **ReAct Pattern**: https://react-lm.github.io/
- **LangChain Docs**: https://python.langchain.com/

### Video Tutorials (Coming Soon)
- JAWIR OS Setup & Configuration
- Natural Language Command Basics
- Desktop Automation Workflows
- KiCad Schematic Generation

---

## 📈 Roadmap

### Q1 2026 (Current)
- ✅ Spotify integration
- ✅ Google Workspace
- ✅ File generation
- ⏳ MacOS support
- ⏳ Voice control

### Q2 2026
- 🎯 GUI Frontend (Electron)
- 🎯 Spotify MCP Server integration
- 🎯 Advanced KiCad features
- 🎯 Plugin system

### Q3 2026
- 🎯 Cloud sync
- 🎯 Mobile companion app
- 🎯 Collaborative features
- 🎯 Advanced automation workflows

---

**Made with ☕ and 💻 by JAWIR Team**

*Desktop AI Agent for the modern engineer*

<!-- kilo-review-trigger -->
