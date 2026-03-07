# 🤖 JAWIR OS - Architecture Blueprint (Phase 1)

> **Just Another Wise Intelligent Resource**  
> Desktop AI Agent dengan kemampuan True Agentic Workflow & Deep Research
> 
> **Target**: Gemini 3 Flash sebagai "otak" yang bisa berpikir-bertindak-mengamati secara berulang (ReAct Loop)

---

## 🆕 V2 UPDATE: Function Calling Migration

> **Status**: ✅ Core FC infrastructure complete (86% of migration tasks done)

JAWIR OS sekarang mendukung **dual-mode architecture** via feature flag:

- **V2 (FC mode)**: `USE_FUNCTION_CALLING=true` → Gemini native function calling via `bind_tools()`
- **V1 (Legacy)**: `USE_FUNCTION_CALLING=false` → ReAct loop with manual routing (original)

### V2 Graph Flow
```
START → quick_router → fc_agent (bind_tools, max 5 iterations) → END
```

### Key V2 Files
- `backend/agent/tools_registry.py` — 12 StructuredTool objects
- `backend/agent/function_calling_executor.py` — FC execution loop
- `backend/agent/nodes/function_calling_agent.py` — LangGraph node
- `backend/ARCHITECTURE_V2.md` — Detail arsitektur V2

> Untuk detail lengkap, lihat `backend/ARCHITECTURE_V2.md` dan `TODO.md`

---

## 📋 Executive Summary

**JAWIR OS** adalah aplikasi desktop AI Agent yang dibangun dengan arsitektur **Hybrid Stack**:
- **Backend (Python)**: Otak AI menggunakan LangGraph + Gemini 3 Flash
- **Frontend (Electron + React)**: UI/UX premium dengan desain Batik Indonesia

### Fokus Phase 1:
1. ✅ **True Agent** - ReAct Loop (Reason → Act → Observe → Loop)
2. ✅ **Web Search & Deep Research** - Kemampuan riset mendalam otomatis
3. ❌ KiCad Integration (Phase 2)
4. ❌ WhatsApp/IoT (Phase 3)

---

## 🧠 TRUE AGENT ARCHITECTURE (Konsep Inti)

### Apa itu "True Agent"?

Pola kerja **"berpikir-bertindak-mengamati"** secara berulang sampai target tercapai. Ini bukan chatbot biasa yang hanya menjawab 1x, melainkan agent yang:

1. **ReAct (Reasoning and Acting)** - Framework utama
   - **Reason**: Model menuliskan pemikiran/rencananya (Chain of Thought)
   - **Act**: Model memilih dan menjalankan tool (web search, scraping, dll)
   - **Observe**: Model melihat hasil dari tindakan (output/error)
   - **Loop**: Jika belum selesai atau ada error → kembali ke Reason

2. **Autonomous AI Agent**
   - **Planning**: Memecah tugas besar menjadi sub-tugas kecil
   - **Memory**: Mengingat apa yang sudah dicoba (tidak mengulangi kesalahan)
   - **Tool Use**: Kemampuan menggunakan external tools (API, browser, file)

3. **Agentic Loops (Self-Correction)**
   - Jika hasil tidak memuaskan → coba lagi dengan strategi berbeda
   - Maksimal 3x retry sebelum menyerah
   - Setiap error menjadi "pembelajaran" untuk percobaan selanjutnya

### Reference Repositories (Sudah Dianalisis)

| Repo | Insight Utama untuk Jawir |
|------|---------------------------|
| **LangGraph** | `StateGraph` pattern, `MessagesState`, conditional edges untuk loop, `create_react_agent` sebagai template |
| **GPT-Researcher** | `DeepResearchSkill` dengan breadth/depth control, `ResearchConductor` orchestrator, context trimming (max 25k words) |
| **Browser-Use** | `AgentState` dengan thinking/memory/next_goal, `AgentOutput` schema, step timeout & retry logic |

---

## 🎨 Design System Analysis

### Dari folder `stitch_jawir_os_listening_state_overlay`:

#### Color Palette (Tailwind Config)
```javascript
colors: {
    "primary": "#dab80b",           // Emas/Gold - Aksen utama
    "primary-hover": "#bfa10a",     // Gold darker
    "background-light": "#f8f8f5",  // Light mode bg
    "background-dark": "#221f10",   // Dark mode bg (Dark Coffee)
    "coffee-dark": "#181711",       // Surface dark
    "coffee-medium": "#2d2a1e",     // Card background
    "coffee-light": "#393628",      // Border/divider
    "cream": "#f1f0ea",             // Light text bg
    "cream-muted": "#bab59c",       // Muted text
    "cream-pill": "#fdfcf5",        // Overlay background
    "surface-dark": "#27251b",      // Alternative surface
    "surface-border": "#393628",    // Border color
    "text-muted": "#bab59c",        // Secondary text
}
```

#### Typography
- **Font Family**: Inter (wght 100-900)
- **Icon Set**: Material Symbols Outlined

#### Key UI Components (dari HTML):
1. **Listening State Overlay** - Modal dengan waveform visualizer & mic icon
2. **Action Confirmation Modal** - Dialog konfirmasi aksi sensitif
3. **Chat Interface** - Layout 2 kolom (Chat kiri, Workspace kanan)
4. **Status Indicator** - "Standby", "Mendengar", "Berpikir"
5. **Workspace Tabs** - KiCad, Browser, WhatsApp, Google, IoT
6. **Research Cards** - Card dengan batik trim accent

#### Visual Elements:
- **Batik Trim**: Pattern emas di border atas
- **Rounded Corners**: `rounded-xl` (1.5rem), `rounded-2xl` (2rem)
- **Shadows**: `shadow-lg shadow-primary/20` untuk depth
- **Animations**: `animate-pulse`, `animate-ping` untuk status

---

## 📁 Directory Structure

```
jawirv2/
├── 📂 backend/                     # Python Backend (FastAPI + LangGraph)
│   ├── 📂 app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Environment & settings
│   │   └── 📂 api/
│   │       ├── __init__.py
│   │       ├── routes.py           # HTTP endpoints
│   │       └── websocket.py        # WebSocket handler (/ws/chat)
│   │
│   ├── 📂 agent/                   # LangGraph Agent Logic
│   │   ├── __init__.py
│   │   ├── state.py                # JawirState TypedDict
│   │   ├── graph.py                # StateGraph definition
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── supervisor.py       # Supervisor Node (Planner)
│   │   │   ├── researcher.py       # Research Node (Deep Research)
│   │   │   ├── executor.py         # Tool Executor Node
│   │   │   └── validator.py        # Output Validator (Self-Correction)
│   │   └── prompts/
│   │       ├── supervisor.txt      # System prompt supervisor
│   │       └── researcher.txt      # System prompt researcher
│   │
│   ├── 📂 tools/                   # Agent Tools
│   │   ├── __init__.py
│   │   ├── web_search.py           # Tavily Search wrapper
│   │   ├── web_scraper.py          # Playwright scraper
│   │   └── utils.py                # Helper functions
│   │
│   ├── 📂 memory/                  # Memory & Checkpointer
│   │   ├── __init__.py
│   │   └── checkpointer.py         # SQLite checkpointer
│   │
│   ├── requirements.txt
│   └── pyproject.toml
│
├── 📂 frontend/                    # Electron + React (electron-vite-react)
│   ├── 📂 electron/
│   │   ├── main/
│   │   │   └── index.ts            # Electron main process
│   │   └── preload/
│   │       └── index.ts            # Preload script
│   │
│   ├── 📂 src/
│   │   ├── App.tsx                 # Root component
│   │   ├── main.tsx                # React entry
│   │   │
│   │   ├── 📂 components/
│   │   │   ├── 📂 chat/
│   │   │   │   ├── ChatContainer.tsx
│   │   │   │   ├── ChatBubble.tsx
│   │   │   │   ├── ChatInput.tsx
│   │   │   │   └── MicButton.tsx
│   │   │   │
│   │   │   ├── 📂 overlay/
│   │   │   │   ├── ListeningOverlay.tsx
│   │   │   │   ├── WaveformVisualizer.tsx
│   │   │   │   └── ConfirmationModal.tsx
│   │   │   │
│   │   │   ├── 📂 workspace/
│   │   │   │   ├── WorkspacePanel.tsx
│   │   │   │   ├── WorkspaceTabs.tsx
│   │   │   │   └── ResearchCard.tsx
│   │   │   │
│   │   │   ├── 📂 layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── StatusBadge.tsx
│   │   │   │
│   │   │   └── 📂 ui/              # Reusable UI primitives
│   │   │       ├── Button.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Input.tsx
│   │   │       └── Modal.tsx
│   │   │
│   │   ├── 📂 hooks/
│   │   │   ├── useWebSocket.ts     # WebSocket connection hook
│   │   │   ├── useAgentStatus.ts   # Agent status management
│   │   │   └── useMicrophone.ts    # Audio recording hook
│   │   │
│   │   ├── 📂 stores/
│   │   │   ├── chatStore.ts        # Zustand - Chat state
│   │   │   ├── agentStore.ts       # Zustand - Agent state
│   │   │   └── settingsStore.ts    # Zustand - App settings
│   │   │
│   │   ├── 📂 lib/
│   │   │   ├── websocket.ts        # WebSocket client
│   │   │   └── constants.ts        # App constants
│   │   │
│   │   └── 📂 styles/
│   │       └── globals.css         # Tailwind + custom styles
│   │
│   ├── tailwind.config.js          # Tailwind with Jawir theme
│   ├── package.json
│   └── vite.config.ts
│
├── 📂 stitch_jawir_os_listening_state_overlay/  # UI/UX Reference (existing)
│
├── PLAN.md                         # This file
├── TODO.md                         # Granular task list
└── README.md                       # Project documentation
```

---

## 🔄 Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              JAWIR OS DATA FLOW                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐                              ┌──────────────────┐
    │   USER (Voice/   │                              │    WORKSPACE     │
    │     Typing)      │                              │   (Cards/Tabs)   │
    └────────┬─────────┘                              └────────▲─────────┘
             │                                                  │
             ▼                                                  │
    ┌──────────────────┐                              ┌────────┴─────────┐
    │  ELECTRON REACT  │◄────────────────────────────►│   RESULT CARDS   │
    │   (Frontend UI)  │                              │  (Research/Tool) │
    └────────┬─────────┘                              └──────────────────┘
             │                                                  ▲
             │ WebSocket (/ws/chat)                             │
             │ ──────────────────►                              │
             ▼                                                  │
    ┌──────────────────┐                              ┌────────┴─────────┐
    │     FastAPI      │                              │   TOOL RESULTS   │
    │  (WebSocket Hub) │                              │   (JSON Cards)   │
    └────────┬─────────┘                              └──────────────────┘
             │                                                  ▲
             ▼                                                  │
    ╔══════════════════════════════════════════════════════════╧═══════╗
    ║                        LANGGRAPH ENGINE                          ║
    ║  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐   ║
    ║  │ SUPERVISOR  │───►│  EXECUTOR   │───►│     VALIDATOR       │   ║
    ║  │   (Plan)    │    │  (Tools)    │    │  (Self-Correction)  │   ║
    ║  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘   ║
    ║         │                  │                       │              ║
    ║         ▼                  ▼                       │              ║
    ║  ┌─────────────────────────────────────┐          │              ║
    ║  │         GEMINI 3 FLASH              │◄─────────┘              ║
    ║  │   (thinking_level="high")           │     (Loop if error)     ║
    ║  └─────────────────────────────────────┘                         ║
    ╚══════════════════════════════════════════════════════════════════╝
                              │
                              ▼
                   ┌─────────────────────┐
                   │   TOOLS (Tavily,    │
                   │   Playwright, etc)  │
                   └─────────────────────┘
```

### WebSocket Message Protocol

#### Client → Server (Request)
```json
{
    "type": "user_message",
    "content": "Carikan riset tentang buck converter 12V ke 5V",
    "timestamp": "2026-02-01T20:00:00Z",
    "metadata": {
        "source": "voice" | "text",
        "session_id": "uuid-v4"
    }
}
```

#### Server → Client (Streaming Response)
```json
{
    "type": "agent_status",
    "status": "thinking" | "searching" | "reading" | "writing" | "done" | "error",
    "message": "Sedang mencari di Tavily...",
    "timestamp": "2026-02-01T20:00:01Z"
}
```

#### Server → Client (Tool Result Card)
```json
{
    "type": "tool_result",
    "tool_name": "web_search",
    "status": "success" | "error",
    "data": {
        "title": "Hasil Pencarian: Buck Converter",
        "summary": "Ditemukan 5 sumber relevan...",
        "sources": [
            {"url": "...", "title": "...", "snippet": "..."}
        ]
    },
    "actions": ["open_url", "save", "retry"]
}
```

#### Server → Client (Final Response)
```json
{
    "type": "agent_response",
    "content": "Berdasarkan riset yang saya lakukan...",
    "thinking_process": ["Step 1...", "Step 2..."],
    "sources_used": ["url1", "url2"],
    "timestamp": "2026-02-01T20:00:10Z"
}
```

---

## 🧠 Agent State Schema (LangGraph)

```python
from typing import TypedDict, List, Optional, Literal
from langgraph.graph import MessagesState

class ResearchSource(TypedDict):
    url: str
    title: str
    content: str
    relevance_score: float

class ToolResult(TypedDict):
    tool_name: str
    status: Literal["success", "error", "pending"]
    data: dict
    error_message: Optional[str]

class JawirState(MessagesState):
    """
    State schema untuk JAWIR OS Agent.
    Inherits MessagesState untuk message history.
    """
    # Current request
    user_query: str
    session_id: str
    
    # Planning
    plan: List[str]                    # Langkah-langkah yang direncanakan
    current_step: int                  # Index langkah saat ini
    
    # Research
    research_sources: List[ResearchSource]  # Sumber yang sudah dikumpulkan
    research_summary: str              # Rangkuman riset
    
    # Tool execution
    tool_results: List[ToolResult]     # Hasil eksekusi tool
    pending_tools: List[str]           # Tool yang belum dieksekusi
    
    # Self-correction
    errors: List[str]                  # Log error untuk learning
    retry_count: int                   # Jumlah retry (max 3)
    
    # Output
    final_response: str                # Respons final ke user
    status: Literal["planning", "researching", "executing", "validating", "done", "error"]
```

---

## 🎭 Agent Persona Definitions

### Supervisor (Planner) - `prompts/supervisor.txt`
```
Kamu adalah JAWIR (Just Another Wise Intelligent Resource), asisten AI pribadi dengan kepribadian:
- Berbahasa Indonesia dengan sentuhan Jawa yang sopan
- Bijaksana, teliti, dan tidak terburu-buru
- Selalu memikirkan langkah terbaik sebelum bertindak

TUGAS UTAMA:
Kamu adalah "Supervisor" yang bertugas MERENCANAKAN langkah-langkah untuk menjawab permintaan user.

ATURAN PLANNING:
1. Pecah permintaan kompleks menjadi sub-tugas kecil
2. Tentukan tool mana yang dibutuhkan untuk setiap sub-tugas
3. Prioritaskan: web_search untuk fakta, scraper untuk detail
4. Jangan langsung menjawab - SELALU buat rencana dulu

FORMAT OUTPUT (JSON):
{
    "understanding": "Pemahaman saya tentang permintaan user...",
    "plan": [
        "1. Cari informasi dasar tentang X",
        "2. Baca detail dari sumber terpercaya",
        "3. Rangkum dan susun jawaban"
    ],
    "tools_needed": ["web_search", "web_scraper"],
    "estimated_steps": 3
}
```

### Researcher - `prompts/researcher.txt`
```
Kamu adalah "Researcher" di tim JAWIR OS.

TUGAS:
- Mencari informasi dari berbagai sumber
- Membaca dan merangkum konten website
- Memvalidasi informasi dari multiple sources
- Menyusun laporan riset yang terstruktur

ATURAN RESEARCH:
1. Gunakan minimal 3 sumber berbeda untuk topik penting
2. Prioritaskan: sumber resmi > blog > forum
3. Jangan copy-paste, selalu parafrase
4. Catat URL setiap sumber

BILA DATA KURANG:
- Cari dengan kata kunci berbeda
- Eksplorasi related topics
- Jangan menyerah sampai 3x percobaan
```

---

## � ReAct Loop Implementation (dari Analisis LangGraph)

### Pattern dari `langgraph/libs/prebuilt/chat_agent_executor.py`

```python
# Konsep utama: Conditional Edge yang membuat loop

def should_continue(state: AgentState) -> Literal["tools", END]:
    """
    Cek apakah perlu loop (panggil tools) atau selesai.
    INI ADALAH INTI DARI ReAct LOOP!
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # Jika ada tool_calls → lanjut ke node tools (ACT)
    if last_message.tool_calls:
        return "tools"
    
    # Jika tidak ada tool_calls → selesai (STOP)
    return END

# Graph dengan loop
graph = StateGraph(AgentState)
graph.add_node("agent", call_model)      # REASON
graph.add_node("tools", ToolNode(tools)) # ACT
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)  # CONDITIONAL LOOP
graph.add_edge("tools", "agent")  # OBSERVE → kembali ke REASON
```

### Pattern Retry/Self-Correction (dari Browser-Use)

```python
# Dari browser_use/agent/views.py
class AgentState(BaseModel):
    consecutive_failures: int = 0  # Track failures untuk retry
    last_result: list[ActionResult] | None = None
    
class AgentSettings(BaseModel):
    max_failures: int = 3  # Max retry sebelum menyerah
    final_response_after_failure: bool = True  # Coba 1x lagi setelah max failures
```

### Pattern Deep Research (dari GPT-Researcher)

```python
# Dari gpt_researcher/skills/deep_research.py
class DeepResearchSkill:
    def __init__(self, researcher):
        self.breadth = 4   # Jumlah sub-query per level
        self.depth = 2     # Kedalaman research (levels)
        self.concurrency_limit = 2  # Parallel research
        self.learnings = []  # Accumulated knowledge
        self.context = []    # All gathered context
    
    async def deep_research(self, query, breadth, depth, learnings=None):
        """
        RECURSIVE RESEARCH:
        1. Generate sub-queries
        2. Research each sub-query
        3. Extract learnings
        4. Generate follow-up questions
        5. Recurse with depth-1
        """
        # ... implementation
```

---

## 🎯 Jawir Agent Graph (Final Design)

```
                    ┌─────────────────────────────────────────┐
                    │                 START                    │
                    └────────────────────┬────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │              SUPERVISOR                  │
                    │  (Gemini 3 Flash thinking_level=high)   │
                    │                                          │
                    │  Input: user_query                       │
                    │  Output: plan[], tools_needed[]          │
                    └────────────────────┬────────────────────┘
                                         │
                         ┌───────────────┴───────────────┐
                         │  Conditional: has_tools?       │
                         └───────────────┬───────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │ YES                │                 NO │
                    ▼                    │                    ▼
    ┌───────────────────────────┐        │    ┌───────────────────────────┐
    │        RESEARCHER         │        │    │       RESPONDER           │
    │                           │        │    │                           │
    │  • web_search (Tavily)    │        │    │  Generate final answer    │
    │  • web_scraper (optional) │        │    │  from current context     │
    │  • deep_research loop     │        │    └───────────────┬───────────┘
    └───────────────┬───────────┘        │                    │
                    │                    │                    │
                    ▼                    │                    │
    ┌───────────────────────────┐        │                    │
    │        VALIDATOR          │        │                    │
    │                           │        │                    │
    │  • Check result quality   │        │                    │
    │  • Count errors           │        │                    │
    │  • Decide: retry or done  │        │                    │
    └───────────────┬───────────┘        │                    │
                    │                    │                    │
         ┌──────────┴──────────┐         │                    │
         │ need_retry?         │         │                    │
         └──────────┬──────────┘         │                    │
                    │                    │                    │
         ┌──────────┼──────────┐         │                    │
         │ YES      │       NO │         │                    │
         │ (< 3)    │          │         │                    │
         ▼          │          ▼         │                    │
    ┌────────┐      │    ┌───────────────────────────┐        │
    │ Loop   │──────┘    │       SYNTHESIZER         │        │
    │ back   │           │                           │        │
    │ to     │           │  Combine all research     │        │
    │RESEARCH│           │  into final response      │        │
    └────────┘           └───────────────┬───────────┘        │
                                         │                    │
                                         ▼                    │
                    ┌─────────────────────────────────────────┘
                    │
                    ▼
                    ┌─────────────────────────────────────────┐
                    │                  END                     │
                    │                                          │
                    │  Output: final_response, sources_used    │
                    └─────────────────────────────────────────┘
```

---

## 🔧 Gemini 3 Flash Configuration

```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Untuk Supervisor (butuh reasoning dalam)
llm_supervisor = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    thinking_level="high",  # Kunci untuk deep thinking
    temperature=0.3,        # Konsisten untuk planning
)

# Untuk Researcher (butuh cepat)
llm_researcher = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview", 
    thinking_level="medium",  # Balance speed & quality
    temperature=0.5,          # Sedikit kreatif untuk parafrase
)

# Untuk Validator (butuh strict)
llm_validator = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    thinking_level="low",    # Cepat untuk validasi
    temperature=0,           # Tidak kreatif, strict check
)
```

---

## �🛠 Tech Stack Details

### Backend (Python 3.12+)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ^0.109 | API Framework |
| `uvicorn` | ^0.27 | ASGI Server |
| `websockets` | ^12.0 | WebSocket support |
| `langgraph` | ^0.0.45 | Agent orchestration |
| `langchain-google-genai` | ^1.0 | Gemini 3 Flash |
| `tavily-python` | ^0.3 | Web search API |
| `playwright` | ^1.41 | Web scraping |
| `pydantic` | ^2.5 | Data validation |
| `python-dotenv` | ^1.0 | Environment vars |

### Frontend (Node 20+)

| Package | Version | Purpose |
|---------|---------|---------|
| `electron` | ^28.0 | Desktop framework |
| `react` | ^18.2 | UI library |
| `typescript` | ^5.3 | Type safety |
| `tailwindcss` | ^3.4 | Styling |
| `zustand` | ^4.5 | State management |
| `framer-motion` | ^11.0 | Animations |

---

## 🔐 Environment Variables

```env
# Backend (.env)
GOOGLE_API_KEY=your-gemini-api-key
TAVILY_API_KEY=your-tavily-api-key
DATABASE_URL=sqlite:///./jawir.db
ENVIRONMENT=development
LOG_LEVEL=INFO

# Frontend (.env)
VITE_WS_URL=ws://localhost:8000/ws/chat
VITE_API_URL=http://localhost:8000/api
```

---

## 🚀 Startup Sequence

1. **Backend startup** (Port 8000):
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend startup** (Electron):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Communication**:
   - Frontend connects to `ws://localhost:8000/ws/chat`
   - All agent operations go through WebSocket
   - HTTP endpoints for config/status only

---

## 📊 Deep Research Pattern (dari GPT-Researcher)

### Context Management
```python
# Dari gpt_researcher/skills/deep_research.py
MAX_CONTEXT_WORDS = 25000  # 25k words safety margin

def trim_context_to_word_limit(context_list, max_words=MAX_CONTEXT_WORDS):
    """
    Trim context untuk mencegah token overflow.
    Prioritaskan item terbaru (most recent).
    """
    total_words = 0
    trimmed = []
    for item in reversed(context_list):
        words = len(item.split())
        if total_words + words <= max_words:
            trimmed.insert(0, item)
            total_words += words
        else:
            break
    return trimmed
```

### Research Progress Tracking
```python
class ResearchProgress:
    """Track progress untuk UI feedback"""
    def __init__(self, total_depth, total_breadth):
        self.current_depth = 1
        self.total_depth = total_depth
        self.current_breadth = 0
        self.total_breadth = total_breadth
        self.current_query = None
        self.completed_queries = 0
```

### Deep Research Flow
```
Query: "Bandingkan ESP32 vs STM32 untuk IoT project"
           │
           ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: Generate Sub-Queries (breadth=4)              │
│                                                          │
│  1. "ESP32 specifications and features 2026"            │
│  2. "STM32 microcontroller comparison IoT"              │
│  3. "ESP32 vs STM32 power consumption"                  │
│  4. "ESP32 STM32 development ecosystem tools"           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: Research Each Query (concurrency=2)           │
│                                                          │
│  For each query:                                         │
│    1. Tavily Search → 5-10 results                      │
│    2. Extract learnings                                  │
│    3. Generate follow-up questions                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: Recurse (depth=2)                             │
│                                                          │
│  Jika depth > 0:                                        │
│    - Ambil follow-up questions                          │
│    - Research lagi dengan depth-1                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 4: Synthesize                                     │
│                                                          │
│  Combine all learnings → Final comprehensive report     │
└─────────────────────────────────────────────────────────┘
```

---

## 🌐 Browser Control Pattern (dari Browser-Use)

### Agent Thinking Structure
```python
# Dari browser_use/agent/views.py
class AgentOutput(BaseModel):
    thinking: str | None = None          # Chain of Thought
    evaluation_previous_goal: str | None  # Evaluasi hasil sebelumnya
    memory: str | None = None             # Apa yang perlu diingat
    next_goal: str | None = None          # Goal berikutnya
    action: list[ActionModel]             # Aksi yang akan dilakukan
```

### Step Timeout & Retry
```python
class AgentSettings(BaseModel):
    max_failures: int = 3           # Max retry
    llm_timeout: int = 60           # Timeout per LLM call (seconds)
    step_timeout: int = 180         # Timeout per step (seconds)
    final_response_after_failure: bool = True  # 1x recovery attempt
```

**Insight untuk Jawir**: Browser-Use memberikan model "thinking" struktur yang jelas. Setiap step agent harus punya:
1. **Thinking**: Apa yang sedang dipikirkan
2. **Evaluation**: Apakah aksi sebelumnya berhasil
3. **Memory**: Info penting yang harus diingat
4. **Next Goal**: Apa yang akan dilakukan selanjutnya

---

## ✅ Success Criteria (Phase 1)

1. [ ] User bisa chat via text dan menerima respons streaming
2. [ ] Agent bisa melakukan web search via Tavily
3. [ ] Agent bisa loop (retry) jika hasil search kurang relevan
4. [ ] Agent menampilkan thinking process (Chain of Thought)
5. [ ] Deep research dengan minimal 3 sources
6. [ ] UI menampilkan status agent real-time (Thinking/Searching/etc)
7. [ ] Hasil research ditampilkan sebagai Card di workspace
8. [ ] Self-correction: jika error, retry dengan strategi berbeda (max 3x)
9. [ ] Context trimming jika melebihi 25k words
10. [ ] Tidak crash selama 10 percakapan berturut-turut

---

## 📚 Reference Repos (Cloned for Analysis)

| Repo | Location | Key Files to Study |
|------|----------|-------------------|
| LangGraph | `jawirv2/langgraph/` | `libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py`, `libs/langgraph/langgraph/graph/state.py` |
| GPT-Researcher | `jawirv2/gpt-researcher/` | `gpt_researcher/agent.py`, `gpt_researcher/skills/deep_research.py`, `gpt_researcher/skills/researcher.py` |
| Browser-Use | `jawirv2/browser-use/` | `browser_use/agent/service.py`, `browser_use/agent/views.py` |

---

**Last Updated**: 2026-02-01  
**Author**: AI Agent (Jawir OS Team)
