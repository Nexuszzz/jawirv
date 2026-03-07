# 🎤 JAWIR OS Voice Implementation Plan

> **Voice-to-Text dengan Deepgram, Push-to-Talk, dan Wake Word "Hey Jawir"**

---

## 📋 Executive Summary

Menambahkan kemampuan voice input ke JAWIR OS untuk pengalaman hands-free yang natural. User dapat berbicara langsung ke JAWIR menggunakan:
1. **Push-to-Talk (PTT)** - Tekan tombol untuk bicara
2. **Wake Word** - Ucapkan "Hey Jawir" untuk aktivasi
3. **Voice Activity Detection (VAD)** - Deteksi otomatis kapan user selesai bicara

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      JAWIR OS Frontend                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │  Microphone  │ getUserMedia({ audio: true })                 │
│  │  Access      │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              VoiceManager (Central Controller)            │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ State Machine:                                       │ │   │
│  │  │  IDLE → WAKE_LISTENING → RECORDING → PROCESSING     │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ├─────────────────┬─────────────────┐                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │ Push-to-    │   │ Wake Word   │   │ VAD         │           │
│  │ Talk Mode   │   │ Detector    │   │ (Silero)    │           │
│  │             │   │ "Hey Jawir" │   │             │           │
│  │ Hold button │   │ Porcupine   │   │ Auto-stop   │           │
│  │ to record   │   │ WASM        │   │ on silence  │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Deepgram WebSocket Stream                    │   │
│  │  wss://api.deepgram.com/v1/listen                        │   │
│  │                                                           │   │
│  │  Config:                                                  │   │
│  │  - model: nova-2                                         │   │
│  │  - language: id,en (multilingual)                        │   │
│  │  - interim_results: true                                 │   │
│  │  - endpointing: 500ms                                    │   │
│  │  - smart_format: true                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Transcript Handler                           │   │
│  │  - Live preview di chat input                            │   │
│  │  - Auto-submit saat silence terdeteksi                   │   │
│  │  - Kirim ke JAWIR AI agent via WebSocket                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencies

| Package | Version | Purpose | Size |
|---------|---------|---------|------|
| `@deepgram/sdk` | ^3.x | Speech-to-Text streaming | ~50KB |
| `@picovoice/porcupine-web` | ^3.x | Wake word detection (WASM) | ~2MB |
| `@ricky0123/vad-web` | ^0.0.x | Voice Activity Detection | ~3MB |

---

## 📁 New Files Structure

```
frontend/src/
├── hooks/
│   ├── useWebSocket.ts           # ✅ Existing
│   ├── useVoiceManager.ts        # 🆕 Central voice controller
│   ├── useDeepgram.ts            # 🆕 Deepgram STT hook
│   ├── usePushToTalk.ts          # 🆕 PTT logic
│   ├── useWakeWord.ts            # 🆕 Porcupine wake word
│   └── useVAD.ts                 # 🆕 Voice activity detection
├── components/
│   ├── ChatPanel.tsx             # ✅ Modify - add voice button
│   ├── VoiceButton.tsx           # 🆕 PTT button with animations
│   ├── VoiceWaveform.tsx         # 🆕 Audio visualization
│   └── VoiceSettings.tsx         # 🆕 Voice config in settings
├── stores/
│   └── index.ts                  # ✅ Modify - add voiceStore
├── types/
│   └── index.ts                  # ✅ Modify - add Voice types
├── utils/
│   └── audio.ts                  # 🆕 Audio processing utilities
└── assets/
    └── sounds/
        ├── wake-detected.mp3     # 🆕 Wake word feedback
        ├── recording-start.mp3   # 🆕 Recording started
        └── recording-end.mp3     # 🆕 Recording ended
```

---

## 🔧 Implementation Phases

### Phase 1: Core Infrastructure (Priority: HIGH)

#### 1.1 Voice Types & Store
- [ ] Add `VoiceState` interface to types
- [ ] Add `voiceStore` to Zustand stores
- [ ] Define voice mode enum: `idle | wake_listening | recording | processing`

#### 1.2 Deepgram Integration
- [ ] Create `useDeepgram.ts` hook
- [ ] WebSocket connection to Deepgram
- [ ] Handle interim and final transcripts
- [ ] Error handling and reconnection

#### 1.3 Push-to-Talk
- [ ] Create `usePushToTalk.ts` hook
- [ ] Microphone access management
- [ ] Audio chunk streaming
- [ ] Create `VoiceButton.tsx` component

### Phase 2: Wake Word Detection (Priority: MEDIUM)

#### 2.1 Porcupine Setup
- [ ] Create `useWakeWord.ts` hook
- [ ] Load Porcupine WASM model
- [ ] Custom "Hey Jawir" keyword (or use built-in similar)
- [ ] Always-on listening mode (optional)

#### 2.2 Voice Activity Detection
- [ ] Create `useVAD.ts` hook
- [ ] Detect speech start/end
- [ ] Auto-stop recording on silence
- [ ] Integrate with Deepgram endpointing

### Phase 3: Central Voice Manager (Priority: HIGH)

#### 3.1 State Machine
- [ ] Create `useVoiceManager.ts` - central controller
- [ ] Coordinate PTT, Wake Word, VAD, Deepgram
- [ ] Mode switching logic
- [ ] Error recovery

#### 3.2 UI Integration
- [ ] Modify `ChatPanel.tsx` - add voice controls
- [ ] Create `VoiceWaveform.tsx` - audio visualization
- [ ] Integrate into Settings modal

### Phase 4: Polish & UX (Priority: LOW)

#### 4.1 Audio Feedback
- [ ] Sound effects for wake word detected
- [ ] Recording start/stop sounds
- [ ] Visual feedback animations

#### 4.2 Settings & Persistence
- [ ] Voice enable/disable toggle
- [ ] Wake word enable/disable
- [ ] Language selection (ID/EN)
- [ ] Microphone selection
- [ ] Store preferences in localStorage

---

## 🔑 API Keys & Configuration

### Deepgram Setup
1. Sign up at https://deepgram.com (free $200 credit)
2. Create API key with "Usage: Transcription" permission
3. Store in `.env`: `VITE_DEEPGRAM_API_KEY=xxx`

### Picovoice Setup (untuk Wake Word)
1. Sign up at https://console.picovoice.ai
2. Create Access Key (free tier: 3 custom wake words)
3. Train "Hey Jawir" model di console
4. Download `.ppn` file
5. Store key in `.env`: `VITE_PICOVOICE_ACCESS_KEY=xxx`

---

## 📊 State Machine Diagram

```
                    ┌─────────────────┐
                    │      IDLE       │
                    │  (not listening)│
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ WAKE_LISTENING  │ │   PTT_PRESSED   │ │    DISABLED     │
│ (always-on mic) │ │ (button held)   │ │ (voice off)     │
└────────┬────────┘ └────────┬────────┘ └─────────────────┘
         │                   │
         │ "Hey Jawir"       │ button down
         │ detected          │
         ▼                   ▼
┌─────────────────────────────────────────────┐
│                 RECORDING                    │
│  - Streaming audio to Deepgram              │
│  - Showing live transcript preview          │
│  - VAD monitoring for silence               │
└─────────────────────┬───────────────────────┘
                      │
                      │ silence detected / button up
                      ▼
┌─────────────────────────────────────────────┐
│                PROCESSING                    │
│  - Waiting for final transcript             │
│  - Show processing indicator                │
└─────────────────────┬───────────────────────┘
                      │
                      │ transcript received
                      ▼
┌─────────────────────────────────────────────┐
│                 SENDING                      │
│  - Submit transcript to JAWIR agent         │
│  - Return to IDLE or WAKE_LISTENING         │
└─────────────────────────────────────────────┘
```

---

## 🎨 UI/UX Specifications

### Voice Button Design

```
┌─────────────────────────────────────────────────────────────┐
│                     Voice Button States                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  IDLE              LISTENING         RECORDING    PROCESSING │
│                                                              │
│  ┌────────┐        ┌────────┐       ┌────────┐   ┌────────┐ │
│  │   🎤   │        │ 🎤 ))) │       │ 🔴 🎤  │   │ ⏳ 🎤  │ │
│  │  gray  │        │  gold  │       │  red   │   │  gold  │ │
│  │        │        │ pulse  │       │ glow   │   │  spin  │ │
│  └────────┘        └────────┘       └────────┘   └────────┘ │
│                                                              │
│  "Tekan utk        "Ucapkan         "Merekam.." "Memproses" │
│   bicara"          Hey Jawir"                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Voice Waveform Visualization

```css
/* Animated bars during recording */
.voice-waveform {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 24px;
}

.voice-waveform .bar {
  width: 3px;
  background: var(--primary);
  border-radius: 2px;
  animation: waveform 0.5s ease-in-out infinite;
}
```

---

## ⚡ Performance Considerations

| Aspect | Approach |
|--------|----------|
| **CPU Usage** | Porcupine WASM optimized, ~3% CPU when idle |
| **Memory** | ~5MB for VAD + Wake Word models |
| **Battery** | Pause wake word when tab not focused |
| **Bandwidth** | Deepgram ~100KB/min for audio streaming |
| **Latency** | Target <300ms from speech end to transcript |

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] `useDeepgram` - connection, streaming, error handling
- [ ] `usePushToTalk` - button states, audio capture
- [ ] `useWakeWord` - keyword detection accuracy
- [ ] `useVAD` - speech detection timing

### Integration Tests
- [ ] Full flow: PTT → Deepgram → Chat submit
- [ ] Full flow: Wake word → Recording → Submit
- [ ] Error recovery: network disconnect
- [ ] Browser compatibility: Chrome, Edge, Firefox

### Manual Testing
- [ ] Noise environments
- [ ] Various accents
- [ ] Quick successive commands
- [ ] Long utterances (>30 seconds)

---

## 📅 Timeline Estimate

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | 2-3 hours | PTT + Deepgram working |
| Phase 2 | 2-3 hours | Wake word detection |
| Phase 3 | 1-2 hours | Integrated voice manager |
| Phase 4 | 1-2 hours | Polish, sounds, settings |
| **Total** | **6-10 hours** | Complete voice feature |

---

## 🚀 Quick Start Implementation Order

1. **Install dependencies**
2. **Add types & store**
3. **Create useDeepgram hook**
4. **Create VoiceButton component**
5. **Integrate into ChatPanel**
6. **Test PTT flow**
7. **Add wake word (optional)**
8. **Add VAD auto-stop**
9. **Polish UI/UX**
10. **Final testing**

---

## ⚠️ Potential Issues & Mitigations

| Issue | Mitigation |
|-------|------------|
| Browser mic permission denied | Clear error message, settings guidance |
| Deepgram rate limit | Implement backoff, show user feedback |
| Wake word false positives | Adjustable sensitivity in settings |
| Poor audio quality | Show audio level indicator, suggest headset |
| Network latency | Buffer audio, show reconnecting state |

---

## 📚 References

- [Deepgram Docs](https://developers.deepgram.com/docs/getting-started-with-live-streaming-audio)
- [Picovoice Porcupine Web](https://github.com/Picovoice/porcupine/tree/master/binding/web)
- [Silero VAD](https://github.com/ricky0123/vad)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

---

*Last Updated: February 7, 2026*
