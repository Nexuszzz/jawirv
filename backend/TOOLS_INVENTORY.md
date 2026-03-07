# 🛠️ JAWIR OS - Complete Tools Inventory

> Inventaris lengkap semua tools yang tersedia di JAWIR OS.
> Termasuk legacy tools (V1) dan Function Calling tools (V2).

**Last Updated**: Auto-generated during FC Migration  
**Total Legacy Tools**: 40+  
**Total FC-Wrapped Tools (V2)**: 12  

---

## 📊 Overview

| Kategori | Legacy (V1) | FC-Wrapped (V2) | Status |
|----------|:-----------:|:----------------:|--------|
| General/Control | 2 | 0 | V1 only (finish, respond) |
| Web Search | 2 | 1 | `web_search` wrapped |
| Desktop Control | 3 | 3 | `open_app`, `open_url`, `close_app` wrapped |
| YouTube | 3 | 0 | V1 only |
| Spotify | 5 | 0 | V1 only |
| Browser | 2 | 0 | Covered by `open_url` in V2 |
| Python Interpreter | 2 | 1 | `run_python_code` wrapped |
| File Generation | 6 | 0 | V1 only |
| KiCad Electronics | 2 | 1 | `generate_kicad_schematic` wrapped |
| Computer Use (Vision) | 4 | 0 | V1 only |
| Google Workspace | 11 | 6 | Partially wrapped |
| **TOTAL** | **42** | **12** | |

---

## 🔵 V2 Function Calling Tools (Native Gemini FC)

Tools yang sudah di-wrap sebagai `LangChain StructuredTool` dan terdaftar di `backend/agent/tools_registry.py`.
Gemini memilih dan memanggil tools ini secara autonomous via `bind_tools()`.

### Registry: `backend/agent/tools_registry.py`

| # | Tool Name | Input Schema | Kategori | Deskripsi |
|---|-----------|-------------|----------|-----------|
| 1 | `web_search` | `WebSearchInput(query, max_results)` | Search | Cari informasi terkini di internet via Tavily API |
| 2 | `generate_kicad_schematic` | `KicadDesignInput(description, project_name, open_kicad)` | Electronics | Generate skematik KiCad dari deskripsi natural language |
| 3 | `run_python_code` | `PythonCodeInput(code)` | Python | Eksekusi kode Python via subprocess |
| 4 | `gmail_search` | `GmailSearchInput(query, max_results)` | Google | Cari email di Gmail |
| 5 | `gmail_send` | `GmailSendInput(to, subject, body)` | Google | Kirim email via Gmail |
| 6 | `drive_search` | `DriveSearchInput(query)` | Google | Cari file di Google Drive |
| 7 | `drive_list` | `DriveListInput(folder_id)` | Google | List isi folder Google Drive |
| 8 | `calendar_list_events` | `CalendarListEventsInput(calendar_id, max_results)` | Google | List event di Google Calendar |
| 9 | `calendar_create_event` | `CalendarCreateEventInput(summary, start_time, end_time, description, location)` | Google | Buat event baru di Calendar |
| 10 | `open_app` | `OpenAppInput(app_name, args)` | Desktop | Buka aplikasi desktop (chrome, spotify, vscode, dll) |
| 11 | `open_url` | `OpenUrlInput(url, browser)` | Desktop | Buka URL di browser |
| 12 | `close_app` | `CloseAppInput(app_name)` | Desktop | Tutup aplikasi desktop |

---

## 🟡 V1 Legacy Tools (Manual If-Else Routing)

Tools yang dipanggil via ReAct loop di `kicad_cli.py` dengan Gemini structured output.
Gemini menghasilkan `{action, action_input}` dan kode Python melakukan routing manual.

### General Tools

| Tool | Parameter | Deskripsi |
|------|-----------|-----------|
| `finish(answer)` | answer: str | Selesaikan task dengan jawaban final |
| `respond(message)` | message: str | Balas user tanpa menyelesaikan task |

### Web Search Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `web_search(query)` | query: str | Cari informasi di internet via Tavily | ✅ |
| `search_component(name)` | name: str | Cari info komponen elektronik (pinout, datasheet) | ❌ |

### Desktop Control Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `open_app(app_name)` | app_name: str | Buka aplikasi desktop | ✅ |
| `close_app(app_name)` | app_name: str | Tutup aplikasi | ✅ |
| `screenshot()` | - | Ambil screenshot layar | ❌ |

**Supported Apps (20+):** chrome, firefox, edge, spotify, vscode, notepad, notepad++, explorer, cmd, powershell, calc, paint, word, excel, powerpoint, discord, slack, telegram, whatsapp

### YouTube Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `play_youtube(query)` | query: str | Search & play video YouTube (autoplay) | ❌ |
| `search_youtube(query)` | query: str | Buka halaman hasil search YouTube | ❌ |
| `youtube_results(query)` | query: str | Dapatkan list hasil pencarian | ❌ |

### Spotify Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `open_spotify()` | - | Buka aplikasi Spotify | ❌ |
| `play_spotify(query)` | query: str | Search & play musik di Spotify | ❌ |
| `spotify_control(action)` | action: str | Kontrol playback: play/pause/next/prev/stop | ❌ |
| `close_spotify()` | - | Tutup Spotify | ❌ |
| `play_spotify_uri(uri)` | uri: str | Play langsung via Spotify URI | ❌ |

### Browser Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `browse(url)` | url: str | Buka website di browser | ✅ (via `open_url`) |
| `search_google(query)` | query: str | Cari di Google | ❌ |

### Python Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `run_python(code)` | code: str | Eksekusi kode Python inline/subprocess | ✅ |
| `install_package(pkg)` | pkg: str | Install pip package | ❌ |

### File Generation Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `create_word(content)` | content: str | Buat dokumen Word (.docx) | ❌ |
| `create_pdf(content)` | content: str | Buat dokumen PDF | ❌ |
| `create_txt(content)` | content: str | Buat file teks (.txt) | ❌ |
| `create_markdown(content)` | content: str | Buat file Markdown (.md) | ❌ |
| `create_json(data)` | data: str | Buat file JSON | ❌ |
| `create_excel(data)` | data: str | Buat file Excel (.xlsx) | ❌ |

### KiCad Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `generate_schematic(spec)` | spec: str | Generate skematik KiCad | ✅ |
| `search_component(name)` | name: str | Cari info komponen (via web_search) | ❌ |

### Computer Use (Vision) Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `journal_search(query)` | query: str | Download paper akademik dari arXiv via AI vision | ❌ |
| `ytplay_vision(query)` | query: str | Play YouTube dengan AI vision (lebih akurat) | ❌ |
| `browse_interact(url\|task)` | url, task: str | AI browse website dan lakukan task | ❌ |
| `download_file(url\|filename)` | url, filename: str | Download file dari URL | ❌ |

### Google Workspace Tools

| Tool | Parameter | Deskripsi | V2? |
|------|-----------|-----------|-----|
| `gmail_search(query)` | query: str | Cari email di Gmail | ✅ |
| `gmail_send(to\|subject\|body)` | to, subject, body: str | Kirim email | ✅ |
| `gmail_draft(to\|subject\|body)` | to, subject, body: str | Buat draft email | ❌ |
| `drive_list(query)` | query: str | List/cari file di Drive | ✅ |
| `drive_create(filename\|content)` | filename, content: str | Buat file di Drive | ❌ |
| `calendar_list()` | - | List event kalender | ✅ |
| `calendar_add(text)` | text: str | Tambah event (natural language) | ✅ |
| `sheets_read(id\|range)` | spreadsheet_id, range: str | Baca data dari Sheets | ❌ |
| `sheets_write(id\|range\|values)` | spreadsheet_id, range, values: str | Tulis data ke Sheets | ❌ |
| `list_gmail_labels()` | - | List label Gmail | ❌ |
| `search_docs(query)` | query: str | Cari Google Docs | ❌ |

---

## 📁 Source Files

| File | Deskripsi | Tools Count |
|------|-----------|:-----------:|
| `backend/agent/tools_registry.py` | V2 FC tool registry (StructuredTool) | 12 |
| `backend/agent/function_calling_executor.py` | V2 FC execution loop (bind_tools) | - |
| `backend/tools/kicad/kicad_cli.py` | V1 ReAct agent + all legacy tools | 42 |
| `backend/tools/python_interpreter/desktop_control.py` | Desktop control, Spotify, YouTube | 14 |
| `backend/tools/python_interpreter/executor.py` | Python code execution | 2 |
| `backend/tools/python_interpreter/file_generator.py` | File generation (Word, PDF, Excel, etc.) | 6 |
| `backend/tools/web_search.py` | Tavily web search wrapper | 1 |
| `backend/tools/google_workspace.py` | Google Workspace MCP client | 11 |

---

## 🗺️ Migration Roadmap

### Already Migrated (12 tools) ✅
- web_search, generate_kicad_schematic, run_python_code
- gmail_search, gmail_send, drive_search, drive_list
- calendar_list_events, calendar_create_event
- open_app, open_url, close_app

### High Priority - Next to Migrate
- `screenshot` - Sering dipakai untuk desktop monitoring
- `play_spotify` / `spotify_control` - Musik request populer
- `play_youtube` - Video request populer
- `create_word` / `create_pdf` - File generation

### Medium Priority
- `search_google`, `browse` - Browser automation
- `install_package` - Python package management
- `gmail_draft` - Email drafting
- `sheets_read` / `sheets_write` - Spreadsheet ops

### Low Priority (Future)
- Computer Use / Vision tools (complex, separate system)
- `search_component` - Niche, electronics only
- `drive_create`, `search_docs` - Less frequently used

---

## 📝 Notes

- **V2 mode** diaktifkan via `USE_FUNCTION_CALLING=true` di `.env`
- **V1 mode** tetap tersedia sebagai fallback (`USE_FUNCTION_CALLING=false`)
- Tools V2 menggunakan **Gemini native function calling** via `llm.bind_tools()`
- Tools V1 menggunakan **structured output parsing** dengan manual if-else routing
- Lihat `ADDING_TOOLS.md` untuk panduan menambah tools baru ke V2
