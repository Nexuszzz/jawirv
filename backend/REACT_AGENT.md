# JAWIR ReAct Agent Architecture

## Overview

JAWIR (Just Another Wise Intelligent Resource) is a **true ReAct (Reasoning and Acting) AI Agent** that autonomously solves tasks through iterative reasoning and tool execution.

## ReAct Loop Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                    JAWIR ReAct Agent Loop                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐    ┌──────────┐    ┌─────────────┐               │
│   │  THOUGHT │ ──▶│  ACTION  │ ──▶│ OBSERVATION │               │
│   │  Reason  │    │  Execute │    │  Analyze    │               │
│   │  + Plan  │    │  Tool    │    │  Result     │               │
│   └──────────┘    └──────────┘    └─────────────┘               │
│        ▲                                │                        │
│        │         ┌──────────────┐       │                        │
│        └─────────│  EVALUATION  │◀──────┘                        │
│                  │  Self-Check  │                                │
│                  │  + Memory    │                                │
│                  └──────────────┘                                │
│                         │                                        │
│                    [Goal Achieved?]                              │
│                    /           \                                 │
│                 YES             NO                               │
│                  │               │                               │
│            ┌─────▼─────┐    ┌────▼────┐                         │
│            │   DONE    │    │  RETRY  │                         │
│            │  Response │    │  + Learn│                         │
│            └───────────┘    └─────────┘                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Autonomous Decision Making
JAWIR decides independently which tools to use based on the user's query. No hardcoded routing.

### 2. Self-Correction
When a tool fails, JAWIR:
- Analyzes the error
- Learns from the failure (adds to memory)
- Tries a different approach or parameters
- Up to 2 retries per unique tool call

### 3. Memory System
```python
class AgentMemory:
    goal: str                    # What we're trying to achieve
    attempts: list               # All attempts made
    successful_tools: list       # Tools that worked
    failed_tools: list           # Tools that failed
    learned: list                # Lessons learned
```

### 4. Thinking Trace
Every step is recorded:
- `thought`: What the agent is thinking
- `action`: Which tool is being executed
- `observation`: What the tool returned
- `evaluation`: Whether the goal was achieved

## Available Tools (19)

| Category | Tools | Description |
|----------|-------|-------------|
| 🔍 Search | `web_search` | Real-time internet search |
| 🐍 Python | `run_python_code` | Execute Python code |
| ⚡ Electronics | `generate_kicad_schematic` | Create circuit designs |
| 📧 Gmail | `gmail_search`, `gmail_send` | Email operations |
| 📁 Drive | `drive_search`, `drive_list` | File management |
| 📅 Calendar | `calendar_list_events`, `calendar_create_event` | Schedule management |
| 📊 Sheets | `sheets_read`, `sheets_write`, `sheets_create` | Spreadsheet ops |
| 📄 Docs | `docs_read`, `docs_create` | Document operations |
| 📝 Forms | `forms_read`, `forms_create` | Form operations |
| 🖥️ Desktop | `open_app`, `open_url`, `close_app` | Desktop control |

## Usage Examples

### Python Computation
```
User: "Hitung 2 pangkat 100"
JAWIR: [THOUGHT] User minta kalkulasi besar
       [ACTION] run_python_code: print(2**100)
       [OBSERVE] 1267650600228229401496703205376
       [DONE] "Hasil: 1.27 × 10³⁰"
```

### Multi-Step Research
```
User: "Cari harga Bitcoin dan buatkan grafik trend"
JAWIR: [THOUGHT] Perlu data real-time + visualisasi
       [ACTION] web_search: "harga bitcoin hari ini"
       [OBSERVE] Data harga dari CoinGecko
       [THOUGHT] Sudah punya data, buat grafik
       [ACTION] run_python_code: matplotlib code
       [OBSERVE] Grafik berhasil dibuat
       [DONE] "Bitcoin: Rp 1.3M, grafik trend: [link]"
```

### Self-Correction Example
```
User: "Kirim email ke boss@company.com"
JAWIR: [THOUGHT] Perlu kirim email
       [ACTION] gmail_send: to=boss@company.com
       [ERROR] Authentication failed
       [LEARN] "Gmail perlu OAuth token"
       [THOUGHT] Mungkin perlu refresh token
       [ACTION] gmail_send: (retry dengan refresh)
       [OBSERVE] Email terkirim
       [DONE] "Email berhasil dikirim"
```

## Architecture Files

```
agent/
├── react_executor.py      # Main ReAct loop implementation
├── function_calling_executor.py  # Legacy executor (fallback)
├── graph.py               # LangGraph state machine
├── state.py               # State schema definitions
├── tools_registry.py      # Tool registration
└── nodes/
    └── function_calling_agent.py  # Agent node wrapper
```

## Configuration

### Environment Variables
```bash
JAWIR_USE_REACT=true      # Use ReAct (default) or legacy FC
GEMINI_MODEL=gemini-3-pro-preview  # Model to use
```

### Max Iterations
- ReAct: 7 iterations max
- Legacy FC: 5 iterations max

### Retry Limits
- Max 2 retries per unique tool call
- After 2 failures, agent tries different approach

## Comparison: JAWIR vs Simple Chatbot

| Feature | JAWIR | Simple Chatbot |
|---------|-------|----------------|
| Tool Selection | Autonomous | None/Manual |
| Error Handling | Self-correction | Fail & Report |
| Memory | ✅ Tracks attempts | ❌ None |
| Learning | ✅ From failures | ❌ None |
| Multi-step | ✅ Iterative | ❌ Single response |
| Reasoning | ✅ Explicit | ❌ Hidden |

## Test Results

```
✅ JAWIR ReAct Agent Test Suite
   - Simple Greeting: PASS (no tools needed)
   - Python Execution: PASS (run_python_code)
   - Web Search: PASS (web_search)
   - Drive Operations: PASS (drive_list)
   - Desktop Control: PASS (open_app)
   
Total: 5/5 tests passed
```

## Future Improvements

1. **Streaming Status** - Real-time tool execution updates
2. **Parallel Tool Calls** - Execute independent tools simultaneously
3. **Long-term Memory** - Persist learnings across sessions
4. **Plan Visualization** - Show agent's plan in UI
5. **Human-in-the-Loop** - Ask for confirmation on risky actions
