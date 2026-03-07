# GoWA Integration Analysis untuk JAWIR OS

## 📊 Analisis Repo go-whatsapp-web-multidevice

### Repository Info
- **Version:** 8.2.0
- **Architecture:** ARM & AMD support
- **Deployment:** VPS sudah running di `http://13.55.23.245:3000`
- **Auth:** Basic Auth (admin:jawir2026) ✅
- **Protocol:** REST API + WebSocket + MCP (Model Context Protocol)
- **Database:** SQLite3 (default) atau PostgreSQL
- **Status:** Active, service `gowa.service` running sejak Feb 4, 2026

---

## 🎯 Fitur Utama yang Bisa Diintegrasikan

### 1. **SEND OPERATIONS** (Kirim Pesan)
| API Endpoint | Fungsi | Priority |
|-------------|---------|----------|
| `POST /send/message` | Kirim text message, mention, ghost mention @everyone | ⭐⭐⭐ HIGH |
| `POST /send/image` | Kirim gambar + caption, auto compress | ⭐⭐⭐ HIGH |
| `POST /send/file` | Kirim dokumen (PDF, Excel, Word) | ⭐⭐⭐ HIGH |
| `POST /send/video` | Kirim video + caption, auto compress | ⭐⭐ MEDIUM |
| `POST /send/audio` | Kirim audio/voice note | ⭐⭐ MEDIUM |
| `POST /send/contact` | Kirim kontak vCard | ⭐ LOW |
| `POST /send/location` | Kirim lokasi GPS | ⭐ LOW |
| `POST /send/sticker` | Kirim sticker (auto convert JPG/PNG → WebP) | ⭐⭐ MEDIUM |
| `POST /send/poll` | Kirim polling ke grup | ⭐ LOW |

**Fitur Spesial:**
- **Ghost Mentions:** Mention tanpa tampilkan `@phone` di text
- **Mention All:** Keyword `@everyone` auto-mention semua member grup
- **Reply Message:** Parameter `reply_message_id` untuk reply
- **Disappearing Message:** Durasi auto-delete (7 hari, 24 jam, 90 hari)
- **Forward Message:** Flag `is_forwarded=true`

---

### 2. **READ OPERATIONS** (Baca Data)
| API Endpoint | Fungsi | Priority |
|-------------|---------|----------|
| `GET /user/my/contacts` | List semua kontak user | ⭐⭐⭐ HIGH |
| `GET /user/my/groups` | List 500 grup terakhir yang diikuti | ⭐⭐⭐ HIGH |
| `GET /user/info?phone={phone}` | Info user (nama, status, avatar) | ⭐⭐ MEDIUM |
| `GET /user/avatar?phone={phone}` | Ambil foto profil user/grup | ⭐ LOW |
| `GET /user/my/privacy` | Setting privacy user | ⭐ LOW |
| `GET /chat/conversations` | List chat (personal + grup) | ⭐⭐⭐ HIGH |
| `GET /chat/{phone}/messages?limit={n}` | Baca history chat (text, media, dll) | ⭐⭐⭐ HIGH |
| `GET /user/check?phone={phone}` | Cek nomor terdaftar di WhatsApp | ⭐⭐ MEDIUM |

**Limitasi:**
- Max 500 grup (WhatsApp protocol limitation)
- History message terbatas sejak device connect

---

### 3. **GROUP MANAGEMENT** (Kelola Grup)
| API Endpoint | Fungsi | Priority |
|-------------|---------|----------|
| `POST /group/create` | Buat grup baru | ⭐⭐ MEDIUM |
| `POST /group/{groupId}/participants/add` | Tambah member | ⭐⭐ MEDIUM |
| `POST /group/{groupId}/participants/remove` | Kick member | ⭐⭐ MEDIUM |
| `POST /group/{groupId}/participants/promote` | Jadikan admin | ⭐ LOW |
| `POST /group/{groupId}/participants/demote` | Cabut admin | ⭐ LOW |
| `POST /group/{groupId}/update/name` | Ubah nama grup | ⭐ LOW |
| `POST /group/{groupId}/update/description` | Ubah deskripsi grup | ⭐ LOW |
| `POST /group/{groupId}/leave` | Keluar dari grup | ⭐ LOW |
| `POST /group/{groupId}/join/link` | Join grup via link | ⭐⭐ MEDIUM |
| `GET /group/{groupId}/participants` | List member grup | ⭐⭐ MEDIUM |

---

### 4. **MESSAGE MANIPULATION** (Kelola Pesan)
| API Endpoint | Fungsi | Priority |
|-------------|---------|----------|
| `POST /message/{msgId}/revoke` | Hapus pesan (delete for everyone) | ⭐⭐ MEDIUM |
| `POST /message/{msgId}/react` | Reaksi emoji ke pesan | ⭐⭐ MEDIUM |
| `POST /message/{msgId}/update` | Edit pesan yang sudah dikirim | ⭐⭐ MEDIUM |
| `POST /message/{msgId}/read` | Mark as read manual | ⭐ LOW |

---

### 5. **WEBHOOK EVENTS** (Real-time Notifications)
| Event Type | Deskripsi | Priority |
|-----------|-----------|----------|
| `message` | Pesan masuk (text, media, contact, location) | ⭐⭐⭐ HIGH |
| `message.ack` | Delivery receipt (sent, delivered, read) | ⭐⭐ MEDIUM |
| `message.reaction` | Reaksi emoji dari orang lain | ⭐ LOW |
| `message.revoked` | Pesan dihapus | ⭐ LOW |
| `message.edited` | Pesan diedit | ⭐ LOW |
| `group.participants` | Member join/leave/promote/demote | ⭐⭐ MEDIUM |
| `group.joined` | Kita ditambahkan ke grup | ⭐⭐ MEDIUM |
| `call.offer` | Panggilan masuk | ⭐ LOW |

**Webhook Security:**
- HMAC SHA256 signature di header `X-Hub-Signature`
- Secret key: `secret` (bisa diganti via `--webhook-secret`)
- Payload: JSON dengan `device_id`, `event`, `payload`

---

## 💡 Rekomendasi Integrasi JAWIR OS

### **Approach 1: REST API Tools (RECOMMENDED)**
Buat 8-10 tools baru di JAWIR yang wrapper HTTP calls ke GoWA API.

#### Tools yang Harus Dibuat:

```python
# agent/tools/whatsapp.py

1. whatsapp_send_message(phone, message, mentions=[])
   → POST /send/message
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "kirim WA ke bos saya 'meeting besok jam 10'"

2. whatsapp_send_image(phone, image_path, caption="")
   → POST /send/image
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "kirim screenshot error ini ke tim IT"

3. whatsapp_send_file(phone, file_path)
   → POST /send/file
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "kirim PDF laporan ke client"

4. whatsapp_list_contacts()
   → GET /user/my/contacts
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "siapa aja kontak WA saya?"

5. whatsapp_list_groups()
   → GET /user/my/groups
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "grup WA apa aja yang saya ikuti?"

6. whatsapp_get_chat_history(phone, limit=50)
   → GET /chat/{phone}/messages?limit={limit}
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "baca 20 chat terakhir dari John"

7. whatsapp_check_number(phone)
   → GET /user/check?phone={phone}
   → Priority: ⭐⭐ MEDIUM
   → Use case: "cek nomor 08123456789 punya WA?"

8. whatsapp_list_chats()
   → GET /chat/conversations
   → Priority: ⭐⭐⭐ HIGH
   → Use case: "siapa aja yang ngechat saya hari ini?"

9. whatsapp_get_user_info(phone)
   → GET /user/info?phone={phone}
   → Priority: ⭐⭐ MEDIUM
   → Use case: "info profile si Budi"

10. whatsapp_send_to_group(group_id, message, mention_all=False)
    → POST /send/message dengan mentions=["@everyone"]
    → Priority: ⭐⭐⭐ HIGH
    → Use case: "kirim ke grup tim 'meeting dibatalkan' mention all"
```

#### Konfigurasi:
```python
# .env atau config.py
GOWA_BASE_URL = "http://13.55.23.245:3000"
GOWA_USERNAME = "admin"
GOWA_PASSWORD = "jawir2026"
```

#### Implementation Pattern (mirip google.py):
```python
# agent/tools/whatsapp.py
from tools.gowa_client import GoWAClient

def create_whatsapp_send_tool() -> StructuredTool:
    async def _send_message(phone: str, message: str, mentions: List[str] = []) -> str:
        try:
            gowa = GoWAClient()
            result = gowa.send_message(phone=phone, message=message, mentions=mentions)
            
            if result.get("success"):
                return f"✅ Pesan berhasil dikirim ke {phone}"
            else:
                return f"❌ Gagal kirim: {result.get('error')}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    return StructuredTool.from_function(
        func=_send_message,
        coroutine=_send_message,
        name="whatsapp_send_message",
        description="Kirim pesan WhatsApp ke nomor/grup. Gunakan format: 628xxxx",
        args_schema=WhatsAppSendInput,
    )
```

---

### **Approach 2: MCP Server (ADVANCED)**
Gunakan MCP protocol untuk direct integration (seperti Google Workspace).

**Keuntungan:**
- Native MCP support di GoWA v8+
- Standardized protocol
- Auto-discovery tools
- Better for AI agents

**Kekurangan:**
- Lebih kompleks setup
- Perlu MCP client library
- GoWA MCP masih evolving (v8 baru)

**Setup:**
```bash
# Di VPS, restart GoWA dalam mode MCP
sudo systemctl stop gowa.service
/home/ubuntu/whatsapp mcp -b admin:jawir2026
```

---

### **Approach 3: Webhook Listener (REAL-TIME)**
Buat FastAPI endpoint untuk terima webhook dari GoWA.

```python
# app/routes/webhooks.py

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    # Verify HMAC signature
    signature = request.headers.get("X-Hub-Signature")
    body = await request.body()
    
    # Process event
    payload = await request.json()
    event_type = payload["event"]
    device_id = payload["device_id"]
    data = payload["payload"]
    
    if event_type == "message":
        # Auto-reply logic
        # Trigger JAWIR agent untuk respond
        # Save to database
        pass
    
    return {"status": "ok"}
```

**Config di VPS:**
```bash
# Restart dengan webhook
sudo systemctl stop gowa.service
sudo nano /etc/systemd/system/gowa.service

# Tambahkan flag webhook
ExecStart=/home/ubuntu/whatsapp rest -b admin:jawir2026 \
  --webhook="http://13.55.23.245:8000/webhook/whatsapp" \
  --webhook-secret="jawir-secret-2026"
```

---

## 🚀 Recommended Implementation Plan

### **Phase 1: Basic Send & Read (1-2 hari)**
✅ Tools yang WAJIB:
1. `whatsapp_send_message` - Kirim text
2. `whatsapp_send_image` - Kirim gambar
3. `whatsapp_list_contacts` - List kontak
4. `whatsapp_list_groups` - List grup
5. `whatsapp_get_chat_history` - Baca chat

**File yang perlu dibuat:**
- `agent/tools/whatsapp.py` (500-700 lines, mirip google.py)
- `tools/gowa_client.py` (HTTP client wrapper)
- Update `agent/config.py` (tambah GOWA config)
- Update `core/tool_registry.py` (register 5 tools)

---

### **Phase 2: Advanced Features (2-3 hari)**
✅ Tools tambahan:
6. `whatsapp_send_file` - Kirim dokumen
7. `whatsapp_check_number` - Cek nomor valid
8. `whatsapp_list_chats` - List percakapan
9. `whatsapp_get_user_info` - Info user
10. `whatsapp_send_to_group` - Kirim ke grup + mention all

---

### **Phase 3: Real-time (3-5 hari)**
✅ Webhook integration:
- Buat endpoint `/webhook/whatsapp`
- Signature validation (HMAC SHA256)
- Event processing (message, group, ack)
- Auto-reply logic
- Database logging

---

### **Phase 4: Automation (1 minggu)**
✅ Use cases keren:
- Auto-forward Gmail → WhatsApp
- Schedule WA blast
- WA bot responder (Q&A)
- Group monitoring & analytics
- Media downloader
- Backup chat ke Google Docs

---

## 📝 Sample Use Cases

### Use Case 1: "kirim email CEO via WA"
```python
User: "kirim summary email dari bos@company.com minggu ini ke grup tim via WA"

Agent steps:
1. gmail_search(query="from:bos@company.com newer_than:7d")
2. Summarize emails dengan LLM
3. whatsapp_list_groups() → find "Tim Engineering"
4. whatsapp_send_to_group(group_id=tim_eng, message=summary, mention_all=True)
```

---

### Use Case 2: "baca WA dari client"
```python
User: "baca 30 chat terakhir dari client John, cari yang urgent"

Agent steps:
1. whatsapp_list_contacts() → find John's phone
2. whatsapp_get_chat_history(phone=john_phone, limit=30)
3. Analyze dengan LLM untuk keyword "urgent", "important", "deadline"
4. Summarize urgent messages
```

---

### Use Case 3: "kirim laporan ke client"
```python
User: "buat laporan sales Q1 dari sheets, export PDF, kirim ke client via WA"

Agent steps:
1. sheets_read(spreadsheet_id=sales_sheet)
2. run_python_code(analyze data, generate plot)
3. docs_create(title="Laporan Q1", content=analysis)
4. Export to PDF (via Google Drive API)
5. whatsapp_send_file(phone=client_phone, file_path=report.pdf)
```

---

## ⚠️ Considerations

### Security
- ✅ Basic Auth sudah aktif (admin:jawir2026)
- ⚠️ UFW firewall opened port 3000
- ⚠️ Pertimbangkan ganti password lebih kuat
- ⚠️ Setup HTTPS dengan reverse proxy (nginx + Let's Encrypt)
- ⚠️ Rate limiting untuk prevent spam

### Scalability
- SQLite3 OK untuk single device < 10k messages/day
- PostgreSQL recommended untuk heavy load
- Multi-device support (v8) jika butuh > 1 WhatsApp account

### Reliability
- ✅ systemd service auto-restart
- ⚠️ Monitor memory usage (Go app ~ 20-30MB)
- ⚠️ Backup database secara berkala
- ⚠️ WhatsApp bisa ban jika spam/automation berlebihan

### Legal & ToS
- ⚠️ WhatsApp ToS melarang automated messaging
- ⚠️ Gunakan untuk personal/internal use only
- ⚠️ Jangan spam atau unsolicited messages
- ⚠️ Respect user privacy

---

## 📊 Effort Estimation

| Phase | Effort | Output |
|-------|--------|--------|
| Phase 1: Basic Tools | 8-12 jam | 5 tools ready, basic send/read working |
| Phase 2: Advanced | 12-16 jam | 10 tools total, full CRUD operations |
| Phase 3: Webhooks | 16-20 jam | Real-time events, auto-reply |
| Phase 4: Automation | 24-32 jam | Complex workflows, integrations |
| **TOTAL** | **60-80 jam** | **Full WhatsApp AI assistant** |

---

## 🎯 Next Steps

1. **Decide Approach:** REST API (recommended) vs MCP vs Webhook
2. **Create `tools/gowa_client.py`:** HTTP client dengan auth
3. **Create `agent/tools/whatsapp.py`:** 5-10 tool factories
4. **Register tools:** Update `tool_registry.py`
5. **Test manually:** Via CLI `/ask "kirim WA ke 08xxx hello"`
6. **Iterate:** Add error handling, retries, logging

---

## 🔗 Resources

- **OpenAPI Spec:** `go-whatsapp-web-multidevice/docs/openapi.yaml` (4319 lines)
- **Webhook Docs:** `docs/webhook-payload.md`
- **VPS GoWA:** http://13.55.23.245:3000 (admin:jawir2026)
- **GitHub Repo:** https://github.com/aldinokemal/go-whatsapp-web-multidevice
- **Go Code:** `src/domains/`, `src/pkg/`, `src/validations/`

---

**Recommendation:** Start dengan **Phase 1 (5 basic tools)** menggunakan REST API approach. Implementasi paling simple, cepat, dan reliable. Kalo sudah jalan smooth, baru expand ke webhook dan automation.

Mau saya mulai implement Phase 1 sekarang? 🚀
