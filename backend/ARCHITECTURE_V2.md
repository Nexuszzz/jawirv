# JAWIR OS - Architecture V2 (Function Calling)

## Overview

JAWIR OS V2 menggunakan **Gemini native function calling** melalui `bind_tools()` API.
Gemini secara autonomous memilih tools yang tepat tanpa hardcoded if-else routing.

## Graph Architecture

### V2 Graph (Function Calling - `USE_FUNCTION_CALLING=true`)
```
┌─────────┐     ┌──────────────┐     ┌──────────┐     ┌─────────┐
│ __start__│ ──► │ quick_router │ ──► │ fc_agent │ ──► │ __end__ │
└─────────┘     └──────────────┘     └──────────┘     └─────────┘
                      │                    │
                      │               ┌────┴────┐
                      │               │ Gemini  │
                      │               │bind_tools│
                      │               └────┬────┘
                      │                    │
                      │            ┌───────┴───────┐
                      │            │  12 Tools     │
                      │            │ auto-selected │
                      │            └───────────────┘
                      │
                 Simple queries
                 (greetings, etc)
                 → direct response
```

### V1 Graph (Legacy - `USE_FUNCTION_CALLING=false`)
```
┌─────────┐     ┌────────────┐     ┌────────────┐     ┌─────────┐
│ __start__│ ──► │ supervisor │ ──► │ specialist │ ──► │ __end__ │
└─────────┘     └────────────┘     │   nodes    │     └─────────┘
                                   ├────────────┤
                                   │ researcher │
                                   │ validator  │
                                   │ synthesizer│
                                   │ kicad_des. │
                                   └────────────┘
```

## Key Components

### 1. Tool Registry (`agent/tools_registry.py`)
Central registry of all tools. Each tool has:
- **Name**: Unique identifier (e.g., `web_search`)
- **Description**: Natural language description for Gemini
- **Input Schema**: Pydantic BaseModel for type-safe arguments
- **Coroutine**: Async function implementation

#### Registered Tools (12 total)
| # | Name | Category | Schema |
|---|------|----------|--------|
| 1 | `web_search` | Search | WebSearchInput |
| 2 | `generate_kicad_schematic` | Electronics | KicadDesignInput |
| 3 | `run_python_code` | Execution | PythonCodeInput |
| 4 | `gmail_search` | Google Workspace | GmailSearchInput |
| 5 | `gmail_send` | Google Workspace | GmailSendInput |
| 6 | `drive_search` | Google Workspace | DriveSearchInput |
| 7 | `drive_list` | Google Workspace | DriveListInput |
| 8 | `calendar_list_events` | Google Workspace | CalendarListEventsInput |
| 9 | `calendar_create_event` | Google Workspace | CalendarCreateEventInput |
| 10 | `open_app` | Desktop Control | OpenAppInput |
| 11 | `open_url` | Desktop Control | OpenUrlInput |
| 12 | `close_app` | Desktop Control | CloseAppInput |

### 2. Function Calling Executor (`agent/function_calling_executor.py`)
Core execution loop:
```
User Query
    → Gemini (with 12 tools bound via bind_tools())
    → tool_calls? 
        YES → Execute tool → Append ToolMessage → Loop back to Gemini
        NO  → Return final text response
    → Max 5 iterations safety limit
```

Features:
- **bind_tools()**: Native Gemini function calling API
- **Max iterations**: 5 (prevents infinite loops)
- **Result truncation**: 5000 chars max per tool result
- **API key rotation**: Auto-switch on 429/PERMISSION_DENIED
- **Structured metrics**: iterations, tool_count, execution_time, errors

### 3. FC Agent Node (`agent/nodes/function_calling_agent.py`)
LangGraph node wrapping FunctionCallingExecutor:
- Singleton pattern (one executor per process)
- Reads `user_query` from JawirState
- Writes `final_response` and `tool_calls_history` back to state

### 4. Feature Flag
```python
# backend/app/config.py
class Settings:
    use_function_calling: bool = False  # Default safe

# backend/agent/graph.py
def get_compiled_graph():
    if settings.use_function_calling:
        return build_jawir_graph_v2()  # FC mode
    else:
        return build_jawir_graph()     # Legacy mode
```

## Data Flow (FC Mode)

```
1. WebSocket message arrives at FastAPI
2. get_compiled_graph() → returns V2 graph (if FC=true)
3. quick_router_node:
   - Simple greetings → immediate response
   - Everything else → route to fc_agent
4. fc_agent_node:
   - Creates FunctionCallingExecutor (singleton)
   - Calls executor.execute(user_query)
   - Gemini decides which tools to call (or none)
   - Tools execute, results sent back to Gemini
   - Gemini generates final response
5. Response streamed back via WebSocket
```

## Test Coverage

- **62 tests** across 4 test files
- Tool registry: 30 tests (schemas, factory, count)
- Web search: 7 tests (mock, validation, error handling)  
- Executor: 11 tests (init, loop, iterations, error)
- Integration: 14 tests (graph, state, binding)

## Adding New Tools

See `ADDING_TOOLS.md` for the developer guide.
