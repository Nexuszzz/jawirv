# 🧪 JAWIR OS - Manual QA Checklist

> Checklist untuk manual testing UI flow JAWIR OS sebelum deploy.  
> Dijalankan oleh QA/developer saat Electron UI sudah running.  
> **Estimasi waktu**: 30-45 menit

---

## Pre-requisites

- [ ] Backend server running (`venv_new\Scripts\python.exe -m uvicorn app.main:app --port 8765`)
- [ ] Frontend Electron app running (`cd frontend && npm run dev`)
- [ ] `.env` configured with valid `GOOGLE_API_KEY` dan `TAVILY_API_KEY`
- [ ] `USE_FUNCTION_CALLING=true` di `.env`
- [ ] Internet connection available

---

## 1. Connection & Basic UI

| # | Test Case | Steps | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 1.1 | App launch | Buka Electron app | Window muncul, loading selesai | |
| 1.2 | WebSocket connect | Check console/network tab | WebSocket connected to ws://localhost:8765/ws/chat | |
| 1.3 | Welcome message | Observe chat area | "Selamat datang di JAWIR OS!" muncul | |
| 1.4 | Input area ready | Check text input | Input area fokus, bisa ketik | |
| 1.5 | Send button visible | Check UI | Tombol kirim terlihat dan enabled | |

---

## 2. Conversational Mode (Tanpa Tools)

| # | Test Case | Input | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 2.1 | Greeting | "Halo JAWIR!" | Respons sapaan sopan, tanpa tool call | |
| 2.2 | Knowledge question | "Apa itu resistor?" | Jawaban pengetahuan, tanpa tool call | |
| 2.3 | Opini/reasoning | "Mana lebih bagus Arduino atau ESP32?" | Jawaban perbandingan, no tool | |
| 2.4 | Bahasa Jawa | "Piye kabare?" | Respons dalam bahasa Jawa/campur | |
| 2.5 | Empty message | Kirim pesan kosong | Error message "Pesan kosong" | |
| 2.6 | Long message | Kirim 500+ karakter | Respons normal tanpa error | |

---

## 3. Web Search Tool

| # | Test Case | Input | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 3.1 | Basic search | "Berapa harga ESP32 terbaru?" | Tool call web_search, hasil URL+snippet | |
| 3.2 | News search | "Berita terbaru tentang AI" | Tool call web_search, berita terkini | |
| 3.3 | Specific search | "Cuaca Jakarta hari ini" | Tool call web_search, data cuaca | |
| 3.4 | Status indicator | Observe UI saat search | "Mencari..." status muncul | |

---

## 4. KiCad Tool

| # | Test Case | Input | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 4.1 | Simple design | "Buatkan skematik LED blink" | Tool call kicad, file .kicad_sch dibuat | |
| 4.2 | Complex design | "Desain sensor suhu DHT22 dengan ESP32" | File skematik valid dengan komponen | |
| 4.3 | Result info | Check response | Info file path, komponen count, koneksi | |

---

## 5. Python Interpreter Tool

| # | Test Case | Input | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 5.1 | Simple math | "Hitung 2 pangkat 20" | Tool call run_python, output: 1048576 | |
| 5.2 | Code execution | "Jalankan: print('Hello JAWIR')" | Output: Hello JAWIR | |
| 5.3 | Error handling | "Jalankan: 1/0" | Error message ZeroDivisionError | |

---

## 6. Google Workspace Tools

| # | Test Case | Input | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 6.1 | Gmail search | "Cari email terbaru" | Tool call gmail_search, daftar email | |
| 6.2 | Gmail send | "Kirim email ke test@test.com isi halo" | Tool call gmail_send, konfirmasi | |
| 6.3 | Drive search | "Cari file laporan di Drive" | Tool call drive_search, daftar file | |
| 6.4 | Drive list | "Lihat isi Google Drive" | Tool call drive_list, folder contents | |
| 6.5 | Calendar list | "Cek jadwal hari ini" | Tool call calendar_list, events | |
| 6.6 | Calendar create | "Buat meeting besok jam 10 pagi" | Tool call calendar_create, konfirmasi | |

> **Note**: Google Workspace tools butuh OAuth credentials yang sudah dikonfigurasi.

---

## 7. Desktop Control Tools

| # | Test Case | Input | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 7.1 | Open app | "Buka calculator" | Tool call open_app, Calculator terbuka | |
| 7.2 | Open URL | "Buka google.com" | Tool call open_url, browser buka Google | |
| 7.3 | Close app | "Tutup calculator" | Tool call close_app, Calculator tertutup | |

---

## 8. Agent Status Streaming

| # | Test Case | Observation | Expected Result | ✅/❌ |
|---|-----------|-------------|-----------------|------|
| 8.1 | Thinking status | Kirim pesan kompleks | "Memahami pertanyaan..." muncul | |
| 8.2 | Searching status | Kirim query web search | "Mencari: [query]" muncul | |
| 8.3 | Writing status | Observe saat menyusun jawaban | "Menyusun jawaban..." muncul | |
| 8.4 | Done status | Setelah respons selesai | "Selesai!" muncul | |
| 8.5 | Tool result card | Setelah tool execution | Card dengan hasil tool muncul | |

---

## 9. Error Handling

| # | Test Case | Steps | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 9.1 | Network error | Matikan internet, kirim web search query | Error message user-friendly | |
| 9.2 | API rate limit | Kirim banyak request cepat | Rate limit handling, retry atau error message | |
| 9.3 | Invalid tool args | (Internal - check logs) | Error caught, user gets message | |
| 9.4 | WebSocket disconnect | Tutup tab/refresh | Reconnect attempt atau error | |

---

## 10. Performance & UX

| # | Test Case | Steps | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 10.1 | Response time (no tool) | "Halo JAWIR" | Response < 3 detik | |
| 10.2 | Response time (with tool) | "Cari harga ESP32" | Response < 10 detik | |
| 10.3 | Multiple messages | Kirim 5 pesan berturut-turut | Semua diproses tanpa hang | |
| 10.4 | Memory usage | Check Task Manager setelah 10 pesan | Memory stabil, tidak leak | |
| 10.5 | UI responsiveness | Kirim pesan, interact UI saat proses | UI tetap responsive | |

---

## 11. Monitoring API

| # | Test Case | Steps | Expected Result | ✅/❌ |
|---|-----------|-------|-----------------|------|
| 11.1 | Health check | `GET /api/monitoring/health` | Status healthy, deps OK | |
| 11.2 | Analytics | `GET /api/monitoring/analytics` | Tool usage stats | |
| 11.3 | Tool list | `GET /api/monitoring/tools` | 12 tools listed | |
| 11.4 | Top tools | `GET /api/monitoring/top-tools` | Ranked by usage | |

---

## Sign-off

| Item | Value |
|------|-------|
| **Tester Name** | |
| **Date** | |
| **Build/Commit** | |
| **OS** | Windows 11 |
| **Total Tests** | 45 |
| **Passed** | |
| **Failed** | |
| **Blocked** | |
| **Notes** | |

---

## Severity Guide

- 🔴 **Critical**: App crash, data loss, security issue
- 🟠 **Major**: Feature not working, wrong behavior
- 🟡 **Minor**: UI glitch, cosmetic issue
- 🟢 **Enhancement**: Nice-to-have improvement
