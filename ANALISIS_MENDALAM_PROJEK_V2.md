# 📋 ANALISIS MENDALAM PROJEK JAWIR OS
## AI Agent Assistant untuk Mahasiswa Polinema
### Dokumentasi Arsitektur & Implementasi — Evidence-Based Analysis

---

## 📑 DAFTAR ISI

1. [Executive Summary](#1-executive-summary)
2. [Arsitektur High-Level](#2-arsitektur-high-level)
3. [Backend Analysis](#3-backend-analysis)
4. [Frontend Analysis](#4-frontend-analysis)
5. [Voice System (Deepgram)](#5-voice-system-deepgram)
6. [Gemini Function Calling Flow](#6-gemini-function-calling-flow)
7. [IoT Integration](#7-iot-integration)
8. [Tools Registry](#8-tools-registry)
9. [WebSocket Communication](#9-websocket-communication)
10. [State Management (Zustand)](#10-state-management-zustand)
11. [Key Design Patterns](#11-key-design-patterns)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [File Reference Map](#13-file-reference-map)

---

## 1. EXECUTIVE SUMMARY

### 1.1 Overview Projek

**JAWIR OS** (Jarvis-like Windows Intelligent Runtime) adalah AI Agent Assistant berbasis web yang dirancang khusus untuk mahasiswa Politeknik Negeri Malang. Sistem ini mengintegrasikan:

| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| AI Brain | Google Gemini 1.5 (`gemini-3-pro-preview`) | Natural Language Understanding + Function Calling |
| Voice | Deepgram Nova-2 + Web Speech API | Speech-to-Text + Wake Word Detection |
| Backend | FastAPI + WebSocket | REST API + Real-time Communication |
| Frontend | React 18 + TypeScript + Vite | Single Page Application |
| IoT | MQTT + Custom Bridge | Smart Home Device Control |
| Scraper | Playwright (Python) | Polinema SIAKAD Integration |

### 1.2 Key Metrics

```
📁 Total Files Analyzed: 25+ core files
📊 Backend Lines: ~2500 lines (Python)
📊 Frontend Lines: ~3000 lines (TypeScript/React)
🔧 Registered Tools: 22+ Gemini function calling tools
🎤 Voice Latency: <500ms (Deepgram streaming)
```

---

## 2. ARSITEKTUR HIGH-LEVEL

### 2.1 Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Port 5173)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   ChatPanel  │  │   IoTPanel   │  │  SiakadPanel │  │    VoiceButton   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
│         │                 │                 │                   │           │
│  ┌──────┴─────────────────┴─────────────────┴───────────────────┴─────────┐ │
│  │                         Zustand State Stores                            │ │
│  │  useChatStore | useAgentStore | useUIStore | useVoiceStore | useIoTStore│ │
│  └──────────────────────────────────────────┬──────────────────────────────┘ │
│                                             │                                │
│  ┌──────────────────────────────────────────┴──────────────────────────────┐ │
│  │                    React Hooks Layer                                     │ │
│  │   useWebSocket  |  useDeepgram  |  useVoiceManager  |  useWakeWord      │ │
│  └──────────────────────────────────┬───────────────────────────────────────┘ │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │ WebSocket (ws://localhost:8000/ws/chat)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (Port 8000)                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application (main.py)                    │   │
│  │  - CORS Middleware  - Lifespan Handler  - Router Mounting             │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│  ┌───────────────┬───────────────────┼───────────────────┬───────────────┐  │
│  │   REST API    │                   │                   │   IoT Router  │  │
│  │  /api/upload  │                   ▼                   │  /api/iot/*   │  │
│  │  /api/monitor │   ┌───────────────────────────────┐   │               │  │
│  └───────────────┘   │   WebSocket Handler           │   └───────────────┘  │
│                      │   /ws/chat                     │                      │
│                      └───────────────┬───────────────┘                      │
│                                      │                                       │
│  ┌───────────────────────────────────┴───────────────────────────────────┐  │
│  │                    Function Calling Executor                           │  │
│  │     execute() → Gemini API → tool_calls → Execute → Re-invoke         │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│  ┌───────────────────────────────────┴───────────────────────────────────┐  │
│  │                         Tools Registry                                 │  │
│  │  web | google | desktop | iot | kicad | python | polinema | playfab  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
    ┌───────────┐             ┌───────────────┐            ┌───────────────┐
    │  Gemini   │             │ Google APIs   │            │   MQTT/IoT    │
    │  API      │             │ Gmail/Drive/  │            │   Devices     │
    │           │             │ Calendar      │            │               │
    └───────────┘             └───────────────┘            └───────────────┘
```

### 2.2 Technology Stack Detail

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | React | 18.x | Component-based UI |
| | TypeScript | 5.x | Type safety |
| | Vite | 5.x | Build tool & dev server |
| | TailwindCSS | 3.x | Utility-first styling |
| | Zustand | 4.x | Lightweight state management |
| **Backend** | FastAPI | 0.104+ | Async REST & WebSocket |
| | LangChain | 0.3.x | LLM abstraction & tools |
| | Playwright | 1.4x | Browser automation |
| | Pydantic | 2.x | Data validation |
| **AI/ML** | Google Gemini | gemini-3-pro-preview | LLM with function calling |
| | Deepgram | Nova-2 | Real-time STT |
| **IoT** | MQTT | Paho Client | Device communication |
| **Infra** | WebSocket | Native | Bidirectional real-time |

---

## 3. BACKEND ANALYSIS

### 3.1 Entry Point: `app/main.py`

**File:** `backend/app/main.py` (322 lines)

```python
# Key Components in main.py

# 1. Lifespan Handler - Startup/Shutdown Events
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting JAWIR OS Backend...")
    
    # Initialize IoT MQTT Bridge
    if settings.mqtt_broker and iot_bridge:
        iot_bridge.set_websocket_broadcast(broadcast_iot_status)
        await iot_bridge.connect()
        
    yield  # Application running
    
    # Cleanup on shutdown
    if iot_bridge:
        await iot_bridge.disconnect()
    logger.info("👋 JAWIR OS Backend stopped")

# 2. FastAPI App with CORS
app = FastAPI(
    title="JAWIR OS Backend",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Router Registration
app.include_router(upload_router, prefix="/api/upload")
app.include_router(monitoring_router, prefix="/api/monitoring")
if settings.mqtt_broker:
    app.include_router(iot_router, prefix="/api/iot")
```

**Key Takeaways:**
- Uses async context manager for clean startup/shutdown
- CORS configured for Vite dev server (port 5173)
- IoT router conditionally loaded based on MQTT config
- WebSocket broadcast callback passed to IoT bridge

### 3.2 Function Calling Executor: `agent/function_calling_executor.py`

**File:** `backend/agent/function_calling_executor.py` (599 lines)

This is the **brain** of JAWIR OS - the orchestrator that manages AI-tool interactions.

#### 3.2.1 System Prompt (Lines 26-180)

```python
FUNCTION_CALLING_SYSTEM_PROMPT = """
Kamu adalah JAWIR (Jarvis-like AI), asisten AI cerdas yang membantu mahasiswa Politeknik Negeri Malang.

## KEMAMPUAN UTAMA
Kamu memiliki akses ke berbagai tools:
- web_search: Mencari informasi terkini di internet
- gmail_search, gmail_send: Membaca dan mengirim email
- drive_search, drive_list: Mencari file di Google Drive
- calendar_list, calendar_create: Melihat dan membuat jadwal
- open_app, close_app, open_url: Kontrol aplikasi desktop
- list_iot_devices, get_iot_device_state, set_iot_device_state: Kontrol IoT
- generate_kicad_schematic: Buat skematik elektronik
- get_polinema_biodata, get_polinema_data_akademik: Akses SIAKAD
- run_python_code: Eksekusi kode Python

## ATURAN PENGGUNAAN TOOLS
1. SIAKAD Polinema:
   - URL login: https://siakad.polinema.ac.id/
   - SELALU minta NIM dan password jika belum diberikan
   - Jangan pernah output password user
   
2. Voice Response:
   - Jika user bicara via voice, jawab singkat dan natural
   - Hindari format markdown untuk voice response

3. IoT Control:
   - List devices dulu sebelum mengontrol
   - Konfirmasi sebelum melakukan aksi berbahaya
"""
```

#### 3.2.2 Core Execute Method

```python
class FunctionCallingExecutor:
    def __init__(self, tools: List[StructuredTool], status_callback: Callable = None):
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        self.status_callback = status_callback
        self.max_iterations = 5
        self.timeout_per_call = 60  # seconds
        
    async def execute(
        self,
        query: str,
        session_id: str,
        history: List[BaseMessage] = None,
        attached_files: List[dict] = None,
    ) -> str:
        """Main execution loop with function calling."""
        
        # 1. Build messages with history
        messages = self._build_messages(query, history, attached_files)
        
        # 2. Create Gemini client with bound tools
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-pro-preview",
            google_api_key=settings.gemini_api_key,
        )
        llm_with_tools = llm.bind_tools(self.tools)  # Native function calling!
        
        # 3. Iteration loop
        for iteration in range(self.max_iterations):
            await self._set_status("thinking", f"Iteration {iteration + 1}")
            
            # Call Gemini
            response = await asyncio.wait_for(
                llm_with_tools.ainvoke(messages),
                timeout=self.timeout_per_call,
            )
            
            # Check for tool calls
            tool_calls = response.tool_calls
            if not tool_calls:
                # No tools needed, return text response
                return response.content
            
            # 4. Execute tools in parallel
            await self._set_status("executing_tool", f"Running {len(tool_calls)} tools")
            tool_results = await self._execute_tools_parallel(tool_calls)
            
            # 5. Append results and re-invoke
            messages.append(response)
            for result in tool_results:
                messages.append(ToolMessage(
                    content=result["output"],
                    tool_call_id=result["tool_call_id"],
                ))
        
        return "Max iterations reached."
```

**Key Insights:**
1. **`bind_tools()`** - Uses Gemini's native function calling (not manual JSON parsing)
2. **Parallel Tool Execution** - Multiple tool calls run concurrently via `asyncio.gather()`
3. **Iteration Loop** - Max 5 iterations to prevent infinite loops
4. **60s Timeout** - Per Gemini API call to handle slow responses
5. **Status Callbacks** - Real-time status updates via WebSocket

#### 3.2.3 Parallel Tool Execution

```python
async def _execute_tools_parallel(self, tool_calls: List) -> List[dict]:
    """Execute multiple tool calls concurrently."""
    
    async def execute_single(tc):
        tool_name = tc["name"]
        tool_args = tc["args"]
        
        if tool_name not in self.tool_map:
            return {"tool_call_id": tc["id"], "output": f"Tool not found: {tool_name}"}
        
        tool = self.tool_map[tool_name]
        try:
            result = await tool.ainvoke(tool_args)
            return {"tool_call_id": tc["id"], "output": str(result)}
        except Exception as e:
            return {"tool_call_id": tc["id"], "output": f"Error: {str(e)}"}
    
    # Run all tools concurrently
    results = await asyncio.gather(*[execute_single(tc) for tc in tool_calls])
    return results
```

### 3.3 WebSocket Handler: `app/api/websocket.py`

**File:** `backend/app/api/websocket.py` (599 lines)

#### 3.3.1 Connection Manager

```python
class ConnectionManager:
    """Manages WebSocket connections per session."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"Client connected: {session_id}")
        
    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            
    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(data)
```

#### 3.3.2 Agent Status Streamer

```python
class AgentStatusStreamer:
    """Streams agent status updates to frontend."""
    
    def __init__(self, manager: ConnectionManager, session_id: str):
        self.manager = manager
        self.session_id = session_id
        
    async def send_status(self, status: str, message: str = ""):
        await self.manager.send_json(self.session_id, {
            "type": "agent_status",
            "data": {
                "status": status,
                "message": message,
                "timestamp": time.time(),
            }
        })
        
    async def send_tool_result(self, tool_name: str, result: str):
        await self.manager.send_json(self.session_id, {
            "type": "tool_result", 
            "data": {
                "tool_name": tool_name,
                "result": result[:500],  # Truncate for display
                "timestamp": time.time(),
            }
        })
```

#### 3.3.3 WebSocket Endpoint

```python
@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    await manager.connect(session_id, websocket)
    
    # Send connection confirmation
    await manager.send_json(session_id, {
        "type": "connection",
        "data": {"session_id": session_id, "status": "connected"}
    })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "user_message":
                content = data.get("data", {}).get("content", "")
                files = data.get("data", {}).get("attached_files", [])
                
                # Create status streamer
                streamer = AgentStatusStreamer(manager, session_id)
                
                # Execute with function calling
                executor = FunctionCallingExecutor(
                    tools=tools_registry.get_all_tools(),
                    status_callback=streamer.send_status,
                )
                
                response = await executor.execute(
                    query=content,
                    session_id=session_id,
                    attached_files=files,
                )
                
                # Send final response
                await manager.send_json(session_id, {
                    "type": "agent_response",
                    "data": {"content": response}
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(session_id)
```

---

## 4. FRONTEND ANALYSIS

### 4.1 Main Application: `src/App.tsx`

**File:** `frontend/src/App.tsx` (327 lines)

```tsx
export default function App() {
  const { addMessage, updateLastBotMessage } = useChatStore();
  const { setStatus, setStatusMessage, addToolResult, setIterationCount } = useAgentStore();
  const { setFireAlert, activeTab, setActiveTab } = useUIStore();
  
  // WebSocket message handler
  const handleMessage = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
      case 'connection':
        console.log('Connected:', data.data.session_id);
        break;
        
      case 'agent_status':
        setStatus(data.data.status);
        setStatusMessage(data.data.message || '');
        break;
        
      case 'tool_result':
        addToolResult({
          tool_name: data.data.tool_name,
          result: data.data.result,
          timestamp: data.data.timestamp,
        });
        break;
        
      case 'agent_response':
        addMessage({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.data.content,
          timestamp: Date.now(),
        });
        setStatus('idle');
        break;
        
      case 'agent_response_stream':
        // Streaming text response
        updateLastBotMessage(data.data.chunk);
        break;
        
      case 'iot_fire_alert':
        // Fire detected! Show alert
        setFireAlert({
          active: true,
          room: data.data.room,
          message: data.data.message,
          timestamp: data.data.timestamp,
        });
        break;
        
      case 'iot_device_update':
        // IoT device state changed
        useIoTStore.getState().updateDevice(data.data);
        break;
    }
  }, [addMessage, setStatus, setFireAlert, ...]);
  
  // WebSocket connection
  const { sendMessage, isConnected } = useWebSocket({
    url: 'ws://localhost:8000/ws/chat',
    onMessage: handleMessage,
  });
  
  return (
    <div className="flex h-screen bg-coffee-dark text-coffee-text">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      
      <main className="flex-1 flex flex-col">
        {activeTab === 'chat' && <ChatPanel sendMessage={sendMessage} />}
        {activeTab === 'iot' && <IoTPanel />}
        {activeTab === 'siakad' && <SiakadPanel />}
        {activeTab === 'settings' && <SettingsPanel />}
      </main>
      
      {/* Fire Alert Modal */}
      <FireAlert />
    </div>
  );
}
```

### 4.2 Chat Panel: `src/components/ChatPanel.tsx`

**File:** `frontend/src/components/ChatPanel.tsx` (526 lines)

#### 4.2.1 Voice Integration

```tsx
export default function ChatPanel({ sendMessage }: ChatPanelProps) {
  const { messages, addMessage } = useChatStore();
  const { status, isConnected } = useAgentStore();
  
  // Voice transcript handler
  const handleVoiceTranscript = useCallback((transcript: string) => {
    // Add user message to store
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: transcript,
      timestamp: Date.now(),
    });
    
    // Send via WebSocket
    sendMessage({
      type: 'user_message',
      data: {
        content: transcript,
        session_id: getOrCreateSessionId(),
      },
    });
  }, [addMessage, sendMessage]);
  
  // Voice manager hook
  const {
    isRecording,
    isWakeWordListening,
    interimTranscript,
    audioLevel,
    startRecording,
    stopRecording,
    toggleWakeWord,
  } = useVoiceManager({ onTranscriptReady: handleVoiceTranscript });
  
  // ... render chat UI with VoiceButton
}
```

#### 4.2.2 File Upload

```tsx
// Multi-file upload support
const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
  const files = e.target.files;
  const MAX_FILES = 10;
  const MAX_SIZE = 20 * 1024 * 1024; // 20MB
  
  const ALLOWED_FILE_TYPES = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'text/markdown', 'text/csv',
    'application/json',
  ];
  
  // Upload each file to /api/upload/file
  for (const file of validFiles) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('/api/upload/file', {
      method: 'POST',
      body: formData,
    });
    
    // Store uploaded file reference
    uploadedFiles.push(await response.json());
  }
  
  setAttachedFiles([...attachedFiles, ...uploadedFiles]);
};
```

### 4.3 Voice Button: `src/components/VoiceButton.tsx`

**File:** `frontend/src/components/VoiceButton.tsx` (176 lines)

```tsx
/**
 * Push-to-Talk Voice Button
 * Uses PointerCapture for reliable hold detection
 */

const VoiceButton: React.FC<VoiceButtonProps> = ({
  onStartRecording,
  onStopRecording,
  disabled = false,
  isRecording = false,
  audioLevel = 0,
}) => {
  const btnRef = useRef<HTMLButtonElement>(null);
  const activePointerRef = useRef<number | null>(null);
  const didStartRef = useRef(false);
  
  // Pointer down: capture + start after 150ms hold
  const handlePointerDown = (e: React.PointerEvent) => {
    if (disabled || activePointerRef.current !== null) return;
    
    // Lock pointer to this button
    btnRef.current?.setPointerCapture(e.pointerId);
    activePointerRef.current = e.pointerId;
    
    // Require 150ms hold to avoid accidental taps
    pressTimerRef.current = setTimeout(() => {
      didStartRef.current = true;
      onStartRecording();
    }, 150);
  };
  
  // Pointer up: stop recording
  const handlePointerUp = (e: React.PointerEvent) => {
    if (e.pointerId !== activePointerRef.current) return;
    
    clearTimeout(pressTimerRef.current);
    activePointerRef.current = null;
    
    if (didStartRef.current) {
      didStartRef.current = false;
      onStopRecording();
    }
  };
  
  return (
    <button
      ref={btnRef}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      style={{ touchAction: 'none' }}
      className={isRecording ? 'bg-red-600 scale-110' : 'bg-coffee-medium'}
    >
      {isRecording ? <WaveformBars audioLevel={audioLevel} /> : <MicIcon />}
    </button>
  );
};
```

**Key Features:**
- **Pointer Capture API** - Prevents button losing focus during scale animation
- **150ms Hold Threshold** - Prevents accidental taps from triggering recording
- **Audio Level Visualization** - Waveform bars react to voice input

---

## 5. VOICE SYSTEM (DEEPGRAM)

### 5.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VOICE SYSTEM FLOW                                │
│                                                                         │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────────────┐  │
│  │  useWakeWord │ ──► │useVoiceManager│ ──► │    useDeepgram         │  │
│  │  (Detection) │     │  (Controller) │     │    (STT Client)        │  │
│  └─────────────┘     └──────────────┘     └─────────────────────────┘  │
│         │                    │                        │                 │
│         ▼                    ▼                        ▼                 │
│  Web Speech API        State Machine          Deepgram WebSocket       │
│  - Always listening    - idle/recording/      wss://api.deepgram.com   │
│  - Keywords lookup       processing           - PCM16 streaming         │
│  - Free (browser)      - Auto-resume          - Nova-2 model           │
│                        - 60s max recording    - Interim results        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Wake Word Detection: `useWakeWord.ts`

**File:** `frontend/src/hooks/useWakeWord.ts` (337 lines)

```tsx
// Wake word variants for fuzzy matching
const WAKE_WORDS = ['jawir', 'jawer', 'javier', 'jauir'];

export function useWakeWord({ onWakeWordDetected, enabled }: UseWakeWordOptions) {
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const isListeningRef = useRef(false);
  
  // Check browser support
  const isSupported = typeof window !== 'undefined' && 
    ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window);
  
  const startListening = useCallback(() => {
    if (!isSupported || isListeningRef.current) return;
    
    const SpeechRecognition = window.webkitSpeechRecognition || window.SpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;       // Keep listening
    recognition.interimResults = true;   // Get partial results
    recognition.lang = 'id-ID';          // Indonesian
    
    recognition.onresult = (event) => {
      const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();
      
      // Check for wake word
      const detected = WAKE_WORDS.some(word => 
        transcript.includes(word) || 
        levenshteinDistance(transcript, word) <= 2  // Fuzzy match
      );
      
      if (detected) {
        stopListening();
        onWakeWordDetected();
      }
    };
    
    // Auto-restart on end (continuous listening)
    recognition.onend = () => {
      if (isListeningRef.current) {
        recognition.start();  // Restart immediately
      }
    };
    
    recognition.start();
    recognitionRef.current = recognition;
    isListeningRef.current = true;
  }, [onWakeWordDetected, isSupported]);
  
  return {
    isListening: isListeningRef.current,
    isSupported,
    startListening,
    stopListening,
  };
}
```

**Key Features:**
- **Web Speech API** - Free, built into Chrome/Edge (no API key needed)
- **Continuous Mode** - Auto-restarts when browser closes recognition
- **Fuzzy Matching** - Levenshtein distance for "jawir" variants
- **Indonesian Language** - `lang: 'id-ID'` for better recognition

### 5.3 Deepgram STT: `useDeepgram.ts`

**File:** `frontend/src/hooks/useDeepgram.ts` (253 lines)

#### 5.3.1 Audio Pipeline

```tsx
export function useDeepgram(options: UseDeepgramOptions) {
  const socketRef = useRef<WebSocket | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  
  const startListening = useCallback(async () => {
    const { apiKey, onTranscript, onInterimTranscript } = options;
    
    // 1. Get microphone
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      }
    });
    mediaStreamRef.current = stream;
    
    // 2. Connect to Deepgram WebSocket
    const socket = new WebSocket(
      'wss://api.deepgram.com/v1/listen?' + new URLSearchParams({
        model: 'nova-2',
        language: 'id',        // Indonesian
        punctuate: 'true',
        interim_results: 'true',
        encoding: 'linear16',  // PCM16
        sample_rate: '16000',
      }),
      ['token', apiKey]  // Token auth via protocol
    );
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const transcript = data.channel?.alternatives?.[0]?.transcript;
      
      if (transcript) {
        if (data.is_final) {
          onTranscript(transcript);
        } else {
          onInterimTranscript?.(transcript);
        }
      }
    };
    
    // 3. Setup audio processing
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    
    // ScriptProcessor for PCM16 conversion
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    processor.onaudioprocess = (event) => {
      const inputData = event.inputBuffer.getChannelData(0);
      
      // Convert Float32 to Int16 (PCM16)
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
      }
      
      // Send to Deepgram
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(pcm16.buffer);
      }
    };
    
    source.connect(processor);
    processor.connect(audioContext.destination);
    
  }, [options]);
  
  // ...
}
```

**Technical Details:**
- **Deepgram Nova-2** - Latest model with improved accuracy
- **PCM16 Encoding** - Linear16 (16-bit signed integer)
- **16kHz Sample Rate** - Standard for speech recognition
- **Interim Results** - Real-time feedback while speaking
- **Indonesian Language** - `language: 'id'`

#### 5.3.2 Audio Level Calculation

```tsx
// Calculate audio level for visualization
const calculateAudioLevel = useCallback((buffer: Float32Array): number => {
  let sum = 0;
  for (let i = 0; i < buffer.length; i++) {
    sum += buffer[i] * buffer[i];
  }
  const rms = Math.sqrt(sum / buffer.length);
  return Math.min(1, rms * 10);  // Normalize to 0-1
}, []);
```

### 5.4 Voice Manager: `useVoiceManager.ts`

**File:** `frontend/src/hooks/useVoiceManager.ts` (239 lines)

```tsx
type VoiceMode = 'idle' | 'recording' | 'processing';

export function useVoiceManager({ onTranscriptReady }: UseVoiceManagerOptions) {
  const [mode, setMode] = useState<VoiceMode>('idle');
  const [isWakeWordListening, setIsWakeWordListening] = useState(false);
  const shouldResumeWakeWordRef = useRef(false);
  
  // Wake word hook
  const wakeWord = useWakeWord({
    enabled: isWakeWordListening,
    onWakeWordDetected: () => {
      // Wake word detected - start recording
      shouldResumeWakeWordRef.current = true;
      setIsWakeWordListening(false);
      startRecording();
    },
  });
  
  // Deepgram hook
  const deepgram = useDeepgram({
    apiKey: voiceConfig.deepgramApiKey,
    onTranscript: async (transcript) => {
      setMode('processing');
      
      // Send transcript to callback
      await onTranscriptReady(transcript);
      
      setMode('idle');
      
      // Resume wake word listening
      if (shouldResumeWakeWordRef.current) {
        shouldResumeWakeWordRef.current = false;
        setIsWakeWordListening(true);
      }
    },
    onInterimTranscript: setInterimTranscript,
  });
  
  // Start recording (called by VoiceButton or wake word)
  const startRecording = useCallback(() => {
    setMode('recording');
    deepgram.startListening();
    
    // Max 60 seconds recording
    maxRecordingTimer.current = setTimeout(() => {
      stopRecording();
    }, 60000);
  }, [deepgram]);
  
  const stopRecording = useCallback(() => {
    clearTimeout(maxRecordingTimer.current);
    deepgram.stopListening();
    // Mode will change to 'processing' in onTranscript callback
  }, [deepgram]);
  
  return {
    mode,
    isRecording: mode === 'recording',
    isProcessing: mode === 'processing',
    isWakeWordListening,
    isWakeWordSupported: wakeWord.isSupported,
    interimTranscript,
    audioLevel: deepgram.audioLevel,
    startRecording,
    stopRecording,
    toggleWakeWord,
  };
}
```

**State Machine:**
```
          ┌──────────────────────────────────────────┐
          │                                          │
          ▼                                          │
     ┌────────┐    startRecording()   ┌───────────┐  │
     │  idle  │ ───────────────────►  │ recording │  │
     └────────┘                       └─────┬─────┘  │
          ▲                                 │        │
          │     stopRecording()             │        │
          │                                 ▼        │
          │                          ┌────────────┐  │
          └────────── onResponse ─── │ processing │──┘
                                     └────────────┘
```

---

## 6. GEMINI FUNCTION CALLING FLOW

### 6.1 Complete Request Flow

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        FUNCTION CALLING FLOW                               │
│                                                                           │
│  User: "Carikan email dari dosen tentang tugas"                          │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ Iteration 1                                                          │ │
│  │ ┌─────────┐     ┌────────────────────────────────────────────────┐  │ │
│  │ │ User    │ ──► │  Gemini (gemini-3-pro-preview)                  │  │ │
│  │ │ Message │     │  with bind_tools([gmail_search, drive_search,...])│ │ │
│  │ └─────────┘     └────────────────────────┬───────────────────────┘  │ │
│  │                                          │                          │ │
│  │                                          ▼                          │ │
│  │                              ┌───────────────────┐                  │ │
│  │                              │ tool_calls: [     │                  │ │
│  │                              │   {              │                  │ │
│  │                              │     name: "gmail_search",           │ │
│  │                              │     args: {                         │ │
│  │                              │       query: "from:dosen tugas",   │ │
│  │                              │       max_results: 5               │ │
│  │                              │     }                               │ │
│  │                              │   }              │                  │ │
│  │                              │ ]                │                  │ │
│  │                              └─────────┬─────────┘                  │ │
│  │                                        │                            │ │
│  │                                        ▼                            │ │
│  │                              ┌───────────────────┐                  │ │
│  │                              │ Execute Tool:      │                  │ │
│  │                              │ gmail_search(...)  │                  │ │
│  │                              │                    │                  │ │
│  │                              │ Result: "3 emails │                  │ │
│  │                              │ found from Dr.X"  │                  │ │
│  │                              └─────────┬─────────┘                  │ │
│  └────────────────────────────────────────┼────────────────────────────┘ │
│                                           │                              │
│  ┌────────────────────────────────────────┼────────────────────────────┐ │
│  │ Iteration 2                            │                            │ │
│  │                                        ▼                            │ │
│  │              ┌─────────────────────────────────────────────┐        │ │
│  │              │ Messages:                                    │        │ │
│  │              │ 1. User: "Carikan email..."                 │        │ │
│  │              │ 2. Assistant: (tool_call: gmail_search)     │        │ │
│  │              │ 3. ToolMessage: "3 emails found..."         │        │ │
│  │              └─────────────────────┬───────────────────────┘        │ │
│  │                                    │                                │ │
│  │                                    ▼                                │ │
│  │              ┌─────────────────────────────────────────────┐        │ │
│  │              │ Gemini Response (no tool_calls):            │        │ │
│  │              │ "Saya menemukan 3 email dari dosen:         │        │ │
│  │              │  1. Tugas Praktikum dari Dr. Budi           │        │ │
│  │              │  2. Revisi Laporan dari Dr. Siti            │        │ │
│  │              │  3. Reminder UTS dari Dr. Ahmad"            │        │ │
│  │              └─────────────────────────────────────────────┘        │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Tool Binding (Native Gemini)

```python
# In FunctionCallingExecutor

# Create Gemini client
llm = ChatGoogleGenerativeAI(
    model="gemini-3-pro-preview",
    google_api_key=settings.gemini_api_key,
)

# Bind tools - this tells Gemini about available functions
llm_with_tools = llm.bind_tools(self.tools)

# How bind_tools works internally:
# 1. Extracts name, description, args_schema from each StructuredTool
# 2. Converts Pydantic schema to JSON Schema
# 3. Sends function definitions to Gemini API
# 4. Gemini can now output tool_calls in response
```

### 6.3 Tool Response Format

```python
# Gemini response with tool calls
AIMessage(
    content="",  # Empty when calling tools
    tool_calls=[
        {
            "id": "call_abc123",
            "name": "gmail_search",
            "args": {
                "query": "from:dosen tugas",
                "max_results": 5
            }
        }
    ]
)

# Tool result message
ToolMessage(
    content="3 emails found:\n1. Tugas Praktikum...",
    tool_call_id="call_abc123",  # Must match!
)
```

---

## 7. IOT INTEGRATION

### 7.1 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           IOT SYSTEM                                     │
│                                                                         │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────────┐  │
│  │  ESP32/MQTT  │ ◄────► │  MQTT Broker │ ◄────► │  IoT Bridge      │  │
│  │  Devices     │        │  (Mosquitto) │        │  (Python Client) │  │
│  └──────────────┘        └──────────────┘        └────────┬─────────┘  │
│                                                           │             │
│                                                           ▼             │
│                                              ┌────────────────────────┐ │
│                                              │  IoT State Manager     │ │
│                                              │  (Thread-safe Singleton)│ │
│                                              └────────────┬───────────┘ │
│                                                           │             │
│                            ┌──────────────────────────────┼─────────┐  │
│                            ▼                              ▼         │  │
│               ┌────────────────────┐         ┌─────────────────────┐│  │
│               │  IoT Tools         │         │ WebSocket Broadcast ││  │
│               │  (Gemini Access)   │         │ (Real-time Updates) ││  │
│               └────────────────────┘         └─────────────────────┘│  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 IoT State Manager: `services/iot_state.py`

**File:** `backend/services/iot_state.py` (255 lines)

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable
from collections import deque
import threading
import time

class DeviceType(Enum):
    FAN = "fan"
    FIRE_DETECTOR = "fire_detector"

@dataclass
class FanState:
    device_id: str = "fan-001"
    device_type: DeviceType = DeviceType.FAN
    name: str = "Kipas Angin"
    is_on: bool = False
    speed: int = 0  # 0-100
    mode: str = "normal"  # normal, eco, turbo
    temperature: float = 25.0

@dataclass
class FireDetectorState:
    device_id: str = "fire-001"
    device_type: DeviceType = DeviceType.FIRE_DETECTOR
    name: str = "Detektor Api"
    flame_detected: bool = False
    smoke_level: int = 0  # 0-100
    gas_analog: int = 0
    alarm_active: bool = False
    last_trigger: Optional[float] = None

class IoTStateManager:
    """Thread-safe singleton for IoT device state management."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._state_lock = threading.Lock()
        self._devices: Dict[str, object] = {}
        self._events: deque = deque(maxlen=200)  # Last 200 events
        self._websocket_broadcast: Optional[Callable] = None
        
        # Initialize default devices
        self._devices["fan-001"] = FanState()
        self._devices["fire-001"] = FireDetectorState()
        
        self._initialized = True
    
    def set_websocket_broadcast(self, callback: Callable):
        """Set callback for broadcasting updates to WebSocket clients."""
        self._websocket_broadcast = callback
    
    def update_device(self, device_id: str, **kwargs) -> bool:
        """Update device state and broadcast."""
        with self._state_lock:
            if device_id not in self._devices:
                return False
            
            device = self._devices[device_id]
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
            
            # Log event
            self._events.append({
                "device_id": device_id,
                "changes": kwargs,
                "timestamp": time.time(),
            })
            
            # Broadcast to WebSocket
            if self._websocket_broadcast:
                asyncio.create_task(self._websocket_broadcast({
                    "type": "iot_device_update",
                    "data": self.get_device_state(device_id),
                }))
            
            return True
    
    def trigger_fire_alert(self, room: str = "Kos"):
        """Trigger fire alert and broadcast to all clients."""
        with self._state_lock:
            fire_detector = self._devices.get("fire-001")
            if fire_detector:
                fire_detector.flame_detected = True
                fire_detector.alarm_active = True
                fire_detector.last_trigger = time.time()
            
            # Broadcast fire alert
            if self._websocket_broadcast:
                asyncio.create_task(self._websocket_broadcast({
                    "type": "iot_fire_alert",
                    "data": {
                        "room": room,
                        "message": f"🔥 PERINGATAN! Api terdeteksi di {room}!",
                        "timestamp": time.time(),
                    },
                }))
```

### 7.3 IoT Tools: `agent/tools/iot.py`

**File:** `backend/agent/tools/iot.py` (425 lines)

```python
# 5 IoT Tools for Gemini Function Calling

def create_list_iot_devices_tool() -> StructuredTool:
    """List all IoT devices and their current state."""
    
    async def _list_devices() -> str:
        manager = IoTStateManager()
        devices = manager.get_all_devices()
        
        output = "📟 **Daftar Perangkat IoT:**\n"
        for device in devices:
            status = "🟢 ON" if getattr(device, 'is_on', False) else "🔴 OFF"
            output += f"- {device.name} ({device.device_id}): {status}\n"
        
        return output
    
    return StructuredTool.from_function(
        func=_list_devices,
        coroutine=_list_devices,
        name="list_iot_devices",
        description="Lihat daftar semua perangkat IoT yang tersedia dan statusnya.",
    )

def create_set_iot_device_state_tool() -> StructuredTool:
    """Control IoT device state."""
    
    async def _set_state(device_id: str, **kwargs) -> str:
        manager = IoTStateManager()
        success = manager.update_device(device_id, **kwargs)
        
        if success:
            return f"✅ Berhasil mengubah state {device_id}"
        else:
            return f"❌ Gagal mengubah state {device_id}"
    
    return StructuredTool.from_function(
        func=_set_state,
        coroutine=_set_state,
        name="set_iot_device_state",
        description=(
            "Ubah state perangkat IoT. Contoh: nyalakan kipas, matikan lampu, "
            "atur kecepatan fan. Gunakan device_id dari list_iot_devices."
        ),
        args_schema=SetIoTStateInput,
    )

def create_reset_fire_alarm_tool() -> StructuredTool:
    """Reset fire alarm after fire is handled."""
    
    async def _reset_alarm() -> str:
        manager = IoTStateManager()
        manager.reset_fire_alarm()
        return "✅ Alarm kebakaran berhasil direset."
    
    return StructuredTool.from_function(
        func=_reset_alarm,
        coroutine=_reset_alarm,
        name="reset_fire_alarm",
        description="Reset alarm kebakaran setelah api berhasil dipadamkan.",
    )
```

---

## 8. TOOLS REGISTRY

### 8.1 Registry Pattern: `agent/tools_registry.py`

**File:** `backend/agent/tools_registry.py` (100 lines)

```python
"""
JAWIR OS - Tools Registry
==========================
Central registry for all Gemini function calling tools.
"""

from typing import List
from langchain_core.tools import StructuredTool

# Import tool factories
from agent.tools.web import create_web_search_tool
from agent.tools.google import (
    create_gmail_search_tool,
    create_gmail_send_tool,
    create_drive_search_tool,
    create_drive_list_tool,
    create_calendar_list_tool,
    create_calendar_create_tool,
)
from agent.tools.desktop import (
    create_open_app_tool,
    create_open_url_tool,
    create_close_app_tool,
)
from agent.tools.iot import (
    create_list_iot_devices_tool,
    create_get_iot_device_state_tool,
    create_set_iot_device_state_tool,
    create_get_iot_events_tool,
    create_reset_fire_alarm_tool,
)
from agent.tools.kicad import create_kicad_schematic_tool
from agent.tools.python_exec import create_python_exec_tool
from agent.tools.polinema import (
    create_polinema_biodata_tool,
    create_polinema_akademik_tool,
)


def get_all_tools() -> List[StructuredTool]:
    """
    Get all registered tools for Gemini function calling.
    
    Total: 22+ tools across 8 categories:
    - Web: web_search
    - Google: gmail_search, gmail_send, drive_search, drive_list, 
              calendar_list, calendar_create
    - Desktop: open_app, open_url, close_app
    - IoT: list_iot_devices, get_iot_device_state, set_iot_device_state,
           get_iot_events, reset_fire_alarm
    - KiCad: generate_kicad_schematic
    - Python: run_python_code
    - Polinema: get_polinema_biodata, get_polinema_data_akademik
    """
    
    tools = []
    
    # Web tools
    tools.append(create_web_search_tool())
    
    # Google Workspace tools
    tools.extend([
        create_gmail_search_tool(),
        create_gmail_send_tool(),
        create_drive_search_tool(),
        create_drive_list_tool(),
        create_calendar_list_tool(),
        create_calendar_create_tool(),
    ])
    
    # Desktop control tools
    tools.extend([
        create_open_app_tool(),
        create_open_url_tool(),
        create_close_app_tool(),
    ])
    
    # IoT tools
    tools.extend([
        create_list_iot_devices_tool(),
        create_get_iot_device_state_tool(),
        create_set_iot_device_state_tool(),
        create_get_iot_events_tool(),
        create_reset_fire_alarm_tool(),
    ])
    
    # KiCad schematic tool
    tools.append(create_kicad_schematic_tool())
    
    # Python execution tool
    tools.append(create_python_exec_tool())
    
    # Polinema SIAKAD tools
    tools.extend([
        create_polinema_biodata_tool(),
        create_polinema_akademik_tool(),
    ])
    
    return tools
```

### 8.2 Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **Web** | `web_search` | Internet search via Tavily API |
| **Google** | `gmail_search`, `gmail_send`, `drive_search`, `drive_list`, `calendar_list`, `calendar_create` | Google Workspace integration |
| **Desktop** | `open_app`, `open_url`, `close_app` | Windows application control |
| **IoT** | `list_iot_devices`, `get/set_iot_device_state`, `get_iot_events`, `reset_fire_alarm` | Smart home control |
| **KiCad** | `generate_kicad_schematic` | Electronic schematic generation |
| **Python** | `run_python_code` | Code execution sandbox |
| **Polinema** | `get_polinema_biodata`, `get_polinema_data_akademik` | SIAKAD scraping |

---

## 9. WEBSOCKET COMMUNICATION

### 9.1 Message Types

```typescript
// Frontend → Backend
type ClientMessage = 
  | { type: 'user_message', data: { content: string, session_id: string, attached_files?: File[] } }
  | { type: 'ping' }
  | { type: 'iot_command', data: { device_id: string, action: string } };

// Backend → Frontend
type ServerMessage =
  | { type: 'connection', data: { session_id: string, status: 'connected' } }
  | { type: 'agent_status', data: { status: AgentStatus, message: string, timestamp: number } }
  | { type: 'tool_result', data: { tool_name: string, result: string, timestamp: number } }
  | { type: 'agent_response', data: { content: string } }
  | { type: 'agent_response_stream', data: { chunk: string } }
  | { type: 'iot_fire_alert', data: { room: string, message: string, timestamp: number } }
  | { type: 'iot_device_update', data: DeviceState }
  | { type: 'pong' };
```

### 9.2 Agent Status Values

```typescript
type AgentStatus = 
  | 'idle'           // Ready for input
  | 'thinking'       // Processing user query
  | 'planning'       // Deciding which tools to use
  | 'executing_tool' // Running a tool
  | 'searching'      // Web search in progress
  | 'reading'        // Reading files/emails
  | 'writing'        // Generating response
  | 'observation'    // Analyzing tool results
  | 'iteration_start'; // Starting new iteration
```

### 9.3 Connection Management (Frontend)

**File:** `frontend/src/hooks/useWebSocket.ts`

```typescript
export function useWebSocket({ url, onMessage }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  
  const connect = useCallback(() => {
    const socket = new WebSocket(url);
    
    socket.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };
    
    socket.onmessage = onMessage;
    
    socket.onclose = () => {
      setIsConnected(false);
      
      // Auto-reconnect with exponential backoff
      const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttempts.current++;
        connect();
      }, delay);
    };
    
    socketRef.current = socket;
  }, [url, onMessage]);
  
  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return;
    
    const interval = setInterval(() => {
      socketRef.current?.send(JSON.stringify({ type: 'ping' }));
    }, 30000);
    
    return () => clearInterval(interval);
  }, [isConnected]);
  
  const sendMessage = useCallback((data: object) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);
  
  return { isConnected, sendMessage };
}
```

---

## 10. STATE MANAGEMENT (ZUSTAND)

### 10.1 Store Overview

**File:** `frontend/src/stores/index.ts` (270 lines)

```typescript
// 5 Zustand Stores

// 1. Chat Store - Message history
export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      messages: [],
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
      })),
      updateLastBotMessage: (chunk) => set((state) => {
        const messages = [...state.messages];
        const lastBot = messages.findLast(m => m.role === 'assistant');
        if (lastBot) {
          lastBot.content += chunk;
        }
        return { messages };
      }),
      clearMessages: () => set({ messages: [] }),
    }),
    { name: 'jawir-chat-storage' }
  )
);

// 2. Agent Store - AI processing status
export const useAgentStore = create<AgentStore>((set) => ({
  isConnected: false,
  status: 'idle',
  statusMessage: '',
  iterationCount: 0,
  toolResults: [],
  
  setStatus: (status) => set({ status }),
  setStatusMessage: (message) => set({ statusMessage: message }),
  addToolResult: (result) => set((state) => ({
    toolResults: [...state.toolResults.slice(-10), result]  // Keep last 10
  })),
}));

// 3. UI Store - Tab navigation, modals
export const useUIStore = create<UIStore>((set) => ({
  activeTab: 'chat',
  settingsOpen: false,
  fireAlert: null,
  
  setActiveTab: (tab) => set({ activeTab: tab }),
  setFireAlert: (alert) => set({ fireAlert: alert }),
}));

// 4. Voice Store - Deepgram config, transcripts
export const useVoiceStore = create<VoiceStore>()(
  persist(
    (set) => ({
      config: {
        deepgramApiKey: '',
        language: 'id',
        model: 'nova-2',
      },
      interimTranscript: '',
      setConfig: (config) => set((state) => ({
        config: { ...state.config, ...config }
      })),
    }),
    { name: 'jawir-voice-storage' }
  )
);

// 5. IoT Store - Device states
export const useIoTStore = create<IoTStore>((set) => ({
  devices: [],
  updateDevice: (device) => set((state) => ({
    devices: state.devices.map(d => 
      d.device_id === device.device_id ? device : d
    )
  })),
  setDevices: (devices) => set({ devices }),
}));
```

### 10.2 Persistence Configuration

```typescript
// Stores with localStorage persistence:
// 1. useChatStore - 'jawir-chat-storage'
// 2. useVoiceStore - 'jawir-voice-storage'

// Stores without persistence (ephemeral):
// 3. useAgentStore - Reset on page refresh
// 4. useUIStore - Reset on page refresh
// 5. useIoTStore - Reset on page refresh (fetched from backend)
```

---

## 11. KEY DESIGN PATTERNS

### 11.1 Factory Pattern (Tools)

```python
# Each tool is created via a factory function
def create_web_search_tool() -> StructuredTool:
    async def _web_search(query: str, max_results: int = 5) -> str:
        # Implementation
        pass
    
    return StructuredTool.from_function(
        func=_web_search,
        coroutine=_web_search,  # Async version
        name="web_search",
        description="Search internet...",
        args_schema=WebSearchInput,  # Pydantic schema
    )
```

**Benefits:**
- Encapsulation of tool logic
- Easy testing (unit test each factory)
- Lazy initialization

### 11.2 Singleton Pattern (IoT State)

```python
class IoTStateManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

**Benefits:**
- Single source of truth for device state
- Thread-safe access
- Consistent state across all agents

### 11.3 Observer Pattern (WebSocket Broadcast)

```python
# IoT State notifies WebSocket clients
self._websocket_broadcast = callback  # Set by main.py

def update_device(self, device_id: str, **kwargs):
    # Update state
    # ...
    
    # Notify all observers
    if self._websocket_broadcast:
        asyncio.create_task(self._websocket_broadcast({
            "type": "iot_device_update",
            "data": self.get_device_state(device_id),
        }))
```

### 11.4 Hooks Pattern (React)

```typescript
// Custom hooks encapsulate complex logic
function useVoiceManager({ onTranscriptReady }) {
  const deepgram = useDeepgram({ ... });
  const wakeWord = useWakeWord({ ... });
  
  // Compose and coordinate
  return {
    startRecording: () => { ... },
    stopRecording: () => { ... },
  };
}
```

### 11.5 State Machine Pattern (Voice)

```typescript
type VoiceMode = 'idle' | 'recording' | 'processing';

// Transitions:
// idle → recording (startRecording)
// recording → processing (stopRecording)
// processing → idle (onTranscriptReady callback completes)
```

---

## 12. DATA FLOW DIAGRAMS

### 12.1 Chat Message Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CHAT MESSAGE FLOW                                │
│                                                                         │
│  User Input ──► useChatStore.addMessage() ──► sendMessage() ──►        │
│                                                                         │
│  ──► WebSocket ──► Backend /ws/chat ──► FunctionCallingExecutor        │
│                                                                         │
│  ──► Gemini API ──► (tool_calls?) ──► Execute Tools ──►                │
│                                                                         │
│  ──► WebSocket (agent_status, tool_result, agent_response) ──►         │
│                                                                         │
│  ──► handleMessage() ──► useAgentStore/useChatStore.addMessage()       │
│                                                                         │
│  ──► React Re-render ──► MessageBubble displayed                        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Voice Command Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          VOICE COMMAND FLOW                              │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Option A: Wake Word                                               │  │
│  │                                                                    │  │
│  │ "Jawir!" ──► useWakeWord ──► onWakeWordDetected ──►              │  │
│  │ ──► useVoiceManager.startRecording() ──► useDeepgram.start()     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Option B: Push-to-Talk                                            │  │
│  │                                                                    │  │
│  │ VoiceButton hold ──► onStartRecording ──►                        │  │
│  │ ──► useVoiceManager.startRecording() ──► useDeepgram.start()     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ── Common Path ──                                                      │
│                                                                         │
│  Microphone Audio ──► AudioContext ──► ScriptProcessor ──►             │
│  ──► PCM16 Conversion ──► Deepgram WebSocket ──►                       │
│  ──► Interim Transcripts ──► Final Transcript ──►                      │
│  ──► onTranscriptReady() ──► sendMessage() ──► [Chat Flow]             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 12.3 IoT Fire Alert Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         IOT FIRE ALERT FLOW                              │
│                                                                         │
│  ESP32 Sensor ──► MQTT Publish (fire/detected) ──►                     │
│  ──► MQTT Broker ──► IoT Bridge (on_message) ──►                       │
│  ──► IoTStateManager.trigger_fire_alert() ──►                          │
│                                                                         │
│  ┌─────────────────────────────────────────┐                           │
│  │ State Update:                            │                           │
│  │ fire_detector.flame_detected = True      │                           │
│  │ fire_detector.alarm_active = True        │                           │
│  └─────────────────────────────────────────┘                           │
│                                                                         │
│  ──► websocket_broadcast({type: 'iot_fire_alert', ...}) ──►            │
│  ──► All Connected WebSocket Clients ──►                               │
│  ──► handleMessage() case 'iot_fire_alert' ──►                         │
│  ──► useUIStore.setFireAlert() ──►                                     │
│  ──► <FireAlert /> Component ──► Modal + Audio Alert                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 13. FILE REFERENCE MAP

### 13.1 Backend Files

| File | Lines | Purpose |
|------|-------|---------|
| `app/main.py` | 322 | FastAPI entry, lifespan, CORS |
| `app/api/websocket.py` | 599 | WebSocket handler, ConnectionManager |
| `app/config.py` | ~100 | Settings via Pydantic |
| `agent/function_calling_executor.py` | 599 | Gemini orchestrator |
| `agent/tools_registry.py` | 100 | Tool aggregator |
| `agent/tools/web.py` | 60 | Web search tool |
| `agent/tools/google.py` | 661 | Gmail, Drive, Calendar tools |
| `agent/tools/desktop.py` | 150 | App control tools |
| `agent/tools/iot.py` | 425 | IoT control tools |
| `agent/tools/kicad.py` | ~200 | KiCad schematic tool |
| `agent/tools/python_exec.py` | ~150 | Python execution tool |
| `agent/tools/polinema.py` | ~400 | SIAKAD scraper tools |
| `services/iot_state.py` | 255 | IoT state manager |

### 13.2 Frontend Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/App.tsx` | 327 | Main component, WebSocket handler |
| `src/components/ChatPanel.tsx` | 526 | Chat UI, file upload |
| `src/components/VoiceButton.tsx` | 176 | Push-to-talk button |
| `src/components/FireAlert.tsx` | ~100 | Fire alert modal |
| `src/components/IoTPanel.tsx` | ~300 | IoT dashboard |
| `src/components/SiakadPanel.tsx` | ~200 | SIAKAD interface |
| `src/hooks/useWebSocket.ts` | 120 | WebSocket connection |
| `src/hooks/useDeepgram.ts` | 253 | Deepgram STT client |
| `src/hooks/useVoiceManager.ts` | 239 | Voice controller |
| `src/hooks/useWakeWord.ts` | 337 | Wake word detection |
| `src/stores/index.ts` | 270 | Zustand stores |
| `src/types/index.ts` | ~150 | TypeScript types |

---

## 📝 KESIMPULAN

### Kelebihan Arsitektur JAWIR OS

1. **Modular Tools** - Setiap tool terisolasi dengan factory pattern
2. **Real-time Communication** - WebSocket untuk status updates
3. **Voice-First UX** - Wake word + push-to-talk flexibility
4. **Type Safety** - TypeScript frontend + Pydantic backend
5. **Native Function Calling** - Gemini `bind_tools()` lebih reliable

### Area untuk Improvement

1. **Error Handling** - Perlu try-catch lebih comprehensive
2. **Testing** - Belum ada unit tests
3. **Caching** - Tool results bisa di-cache
4. **Rate Limiting** - Perlu proteksi API abuse
5. **Logging** - Structured logging untuk debugging

### Tech Stack Summary

```
Frontend: React 18 + TypeScript + Vite + TailwindCSS + Zustand
Backend:  FastAPI + LangChain + Playwright + Pydantic
AI:       Google Gemini (gemini-3-pro-preview) + Deepgram Nova-2
IoT:      MQTT + Custom Python Bridge
Infra:    WebSocket + REST API
```

---

*Dokumen ini di-generate berdasarkan analisis kode aktual dari repository JAWIR OS.*
*Last updated: Based on codebase state at analysis time*
