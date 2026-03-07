# JAWIR OS — Runbook & Smoke Test (Phase 7–8)

## Phase 7: Start All Services & Healthcheck

### Prerequisites
```
cd d:\jawirv4\jawirv4\jawirv2\backend
```

Ensure `.env` has:
```env
USE_FUNCTION_CALLING=true
IOT_ENABLED=true
GEMINI_API_KEY=<key1>
GEMINI_API_KEY_SECONDARY=<key2>
MQTT_HOST=6975c5257bf14a6380bdd8d8cd5613ee.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USER=Jawir
MQTT_PASSWORD=@@U93BqZzU9mt6Q
```

### 7.1 — Start Backend
```powershell
cd d:\jawirv4\jawirv4\jawirv2\backend
.\venv_work\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 7.2 — Healthcheck Endpoints

| Endpoint | Method | Expected |
|---|---|---|
| `http://localhost:8000/health` | GET | `{"status":"ok"}` |
| `http://localhost:8000/health/iot` | GET | `{"status":"connected","broker":{...},"devices":{...}}` |
| `http://localhost:8000/api/iot/devices` | GET | `{"success":true,"devices":[...2 devices...]}` |
| `http://localhost:8000/api/iot/events?limit=5` | GET | `{"success":true,"events":[...]}` |

```powershell
# Quick healthcheck commands
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/iot
Invoke-RestMethod http://localhost:8000/api/iot/devices
Invoke-RestMethod http://localhost:8000/api/iot/events?limit=5
```

### 7.3 — Start Frontend (Electron)
```powershell
cd d:\jawirv4\jawirv4\jawirv2\frontend
npm run dev
```
Or for Electron:
```powershell
npm run electron:dev
```

---

## Phase 8: Smoke Tests & Regression Checklist

### Test 1 — WebSocket Connect + Chat (Critical)
1. Open browser/Electron → Chat tab
2. Type "Halo Jawir" → Send
3. **Expected**: Agent responds normally. No "Server disconnected without sending a response."
4. **Verify**: Browser DevTools WS tab shows messages flowing, no premature close

### Test 2 — IoT Health Endpoint
```powershell
$h = Invoke-RestMethod http://localhost:8000/health/iot
$h.status   # Should be "connected"
$h.devices  # Should show total_devices: 2
```

### Test 3 — IoT Device List (Real Data)
```powershell
$d = Invoke-RestMethod http://localhost:8000/api/iot/devices
$d.devices | ForEach-Object { "$($_.device_id): online=$($_.online), temp=$($_.temperature)" }
```
- **Expected**: device_id `fan-01` and `fire-detector-01` present
- Temperature should be a real number (or null if device offline / DHT invalid)

### Test 4 — Fan Speed Control (MQTT Publish)
```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/iot/devices/fan-01/control `
    -Method POST -ContentType "application/json" `
    -Body '{"action":"set_speed","value":"high"}'
```
- **Expected**: `{"success":true,"message":"Control command sent: set_speed=high"}`
- Physical fan (if connected) changes speed

### Test 5 — Fire Detector Alarm Reset
```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/iot/devices/fire-detector-01/control `
    -Method POST -ContentType "application/json" `
    -Body '{"action":"buzzer_off"}'
```

### Test 6 — DHT Invalid → Frontend Shows "—"
- If device sends `NaN` temperature → backend filters it out → device.temperature = null
- Frontend `safeNum()` returns "—" instead of crashing on `.toFixed(NaN)`

### Test 7 — V2 Function Calling: IoT via Chat
1. In Chat tab, type: **"nyalakan kipas kecepatan tinggi"**
2. **Expected flow**:
   - Gemini calls `iot_set_device_state` tool with `device_id="fan-01"`, `state={"speed":"high"}`
   - Agent executes tool → MQTT publish → response streamed
   - Agent responds: "Kipas sudah diatur ke kecepatan tinggi"
3. Type: **"berapa suhu ruangan?"**
   - Gemini calls `iot_get_device_state` → returns real temperature from ESP32
   
### Test 8 — IoT Dashboard UI (Frontend)
1. Click "IoT" tab in sidebar
2. **Verify**:
   - Stats grid shows real device count, MQTT status, event count
   - Device cards display temperature/humidity with real values (or "—" if invalid)
   - Fan speed buttons work → clicking "HIGH" sends POST, re-fetches state
   - Events section shows real events from backend (not just local actions)
   - Error banner appears if backend is stopped

### Test 9 — WebSocket Resilience
1. While chat is active, trigger an error (e.g., stop Gemini API temporarily)
2. **Expected**: Error message appears in chat ("Terjadi kesalahan internal: ...")
3. Agent status resets to "idle" (not stuck on "thinking")
4. User can send next message normally without reconnecting

### Test 10 — Full Regression
- [ ] Chat V2 Function Calling works with all 30+ tools
- [ ] Google Workspace tools still functional
- [ ] Voice input/output (if enabled) unaffected
- [ ] Dashboard panel loads without errors
- [ ] Sidebar navigation between all tabs works
- [ ] No console errors in browser DevTools

---

## Summary of All Changes Made

### Backend

| File | Change | Risk |
|---|---|---|
| `app/main.py` | WS handler: inner try/except sends `{type:"error", recoverable:true}` + idle status reset | LOW — additive, doesn't change happy path |
| `services/iot_bridge.py` | `connect()`: replaced blocking `time.sleep(0.5)` with `threading.Event.wait(5s)` | LOW — same behavior, non-blocking |
| `services/iot_bridge.py` | `_handle_fire_telemetry()`: DHT NaN validation via `math.isnan()` + range checks | LOW — additive filter |
| `services/iot_bridge.py` | `_handle_fan_status()`: Same DHT robustness for fan temperature | LOW — additive filter |
| `services/iot_state.py` | Event buffer maxlen 100 → 200 | NONE — just buffer size |

### Frontend

| File | Change | Risk |
|---|---|---|
| `components/IoTPanel.tsx` | Added `safeNum()` helper for NaN-safe `.toFixed()` | NONE — pure function |
| `components/IoTPanel.tsx` | Added `fetchEvents()` from `GET /api/iot/events?limit=20` | LOW — new fetch, no breaking change |
| `components/IoTPanel.tsx` | Polling: devices 3s→5s, health 5s→30s, events new 10s | LOW — reduces server load |
| `components/IoTPanel.tsx` | Added `fetchError` state + red error banner UI | LOW — additive UI |
| `components/IoTPanel.tsx` | Events section: always shows (empty state) + from backend | LOW — better UX |
| `components/IoTPanel.tsx` | Stats "Event" card uses `event_count` from backend | LOW — more accurate |

**All changes are additive and non-breaking.** No existing behavior was removed.
