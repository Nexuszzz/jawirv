# 🤖 JAWIR OS V2 - PHASE 1: The Electronic Architect

## 📊 Current State Analysis

### ✅ What's Working
| Component | Status | Test Results |
|-----------|--------|--------------|
| **LangGraph Core** | ✅ Working | Graph built with StateGraph |
| **Supervisor V2** | ✅ Working | Pydantic structured output, 8/8 tests passed |
| **Web Research** | ✅ Working | Web search tool functional |
| **File Upload** | ✅ Working | 3/3 tests passed |
| **WebSocket** | ✅ Working | 5/5 integration tests passed |
| **API Key Rotation** | ✅ Working | 14 keys rotating |

### 📁 Current Project Structure
```
backend/
├── agent/
│   ├── graph.py              # ✅ LangGraph workflow
│   ├── state.py              # ✅ JawirState definition
│   ├── api_rotator.py        # ✅ API key rotation
│   ├── nodes/
│   │   ├── supervisor_v2.py  # ✅ Brain (router)
│   │   ├── researcher.py     # ✅ Web research
│   │   ├── validator.py      # ✅ Result validation
│   │   └── synthesizer.py    # ✅ Response synthesis
│   └── prompts/
│       ├── supervisor.txt
│       └── researcher.txt
├── tools/
│   └── web_search.py         # ✅ Search tool
│   └── kicad/                # 🆕 TO BE CREATED
└── app/
    ├── main.py               # ✅ FastAPI app
    └── api/
        ├── websocket.py      # ✅ WebSocket handler
        └── upload.py         # ✅ File upload
```

---

## 🎯 Phase 1 Goal

**Membuat JAWIR V2 sebagai Electronic Architect:**
- Bisa chat normal (sudah ada ✅)
- Bisa merancang skematik elektronika dengan KiCad
- Menghasilkan file `.kicad_sch` yang valid

---

## 🔗 Reference Repositories

| Repo | Path | Purpose |
|------|------|---------|
| **KiCad Reference (V1)** | `kicad-reference/` | TypeScript logic to port |
| **KiCad MCP Server** | `kicad-mcp-reference/` | Python interface reference |
| **LangGraph** | `langgraph/` | Multi-agent patterns |

---

## 🗺️ Execution Plan

### STEP A: Port KiCad Engine (TS → Python) [PRIORITY]

**Location:** `backend/tools/kicad/`

#### A1: Component Library (`library.py`)
- Port `kicad-reference/kicad-library.ts`
- Convert `COMPONENT_LIBRARY` dict
- Include: resistor, capacitor, LED, transistor, IC, power symbols
- Maintain pin offsets, rotations, lib_symbols

**Source Files:**
- `kicad-reference/kicad-library.ts` (2121 lines)

#### A2: Schema Definitions (`schemas.py`)
- Port `kicad-reference/gemini-tools.ts`
- Create Pydantic models for Gemini structured output
- Models: `ComponentPlacement`, `WireConnection`, `SchematicRequest`

**Source Files:**
- `kicad-reference/gemini-tools.ts`
- `kicad-reference/schematic-json.ts`

#### A3: Schematic Generator (`generator.py`)
- Port `kicad-reference/schematic-generator.ts`
- Pin position calculation with rotation
- Wire routing (L-shape, direct)
- Generate valid `.kicad_sch` S-expression

**Source Files:**
- `kicad-reference/schematic-generator.ts` (473 lines)

#### A4: Template Library (`templates.py`)
- Port `kicad-reference/schematic-templates.ts`
- Pre-defined circuits: LED blink, voltage divider, amplifier
- Quick start for common designs

**Source Files:**
- `kicad-reference/schematic-templates.ts`

---

### STEP B: Create KiCad Designer Node

**Location:** `backend/agent/nodes/kicad_designer.py`

#### B1: Node Structure
```python
async def kicad_designer_node(state: JawirState) -> dict:
    """
    1. Parse user request
    2. Call Gemini with structured output (schemas.py)
    3. Generate schematic (generator.py)
    4. Save to D:/sijawir/KiCad_Projects/{project_name}/
    5. Return success message with file path
    """
```

#### B2: Prompts
- Create `backend/agent/prompts/kicad_designer.txt`
- System prompt for electronics design
- Include component library reference

---

### STEP C: Update Supervisor Router

**Location:** `backend/agent/nodes/supervisor_v2.py`

#### C1: Add KiCad Route
- Update `response_type` to include `"kicad"`
- Add detection for electronics-related queries
- Keywords: schematic, circuit, PCB, resistor, LED, etc.

#### C2: Update Graph
- Add `kicad_designer` node to graph
- Add conditional edge from supervisor

---

### STEP D: Testing & Validation

#### D1: Unit Tests
- `test_kicad_library.py` - Component definitions
- `test_kicad_generator.py` - Schematic generation
- `test_kicad_integration.py` - Full flow

#### D2: Integration Test
- Request: "Buatkan skematik LED blink dengan 555 timer"
- Expected: Valid `.kicad_sch` file generated

---

## 📋 File Creation Checklist

### New Files to Create:
```
backend/tools/kicad/
├── __init__.py
├── library.py          # Component definitions
├── schemas.py          # Pydantic models
├── generator.py        # Schematic generator
├── templates.py        # Circuit templates
└── utils.py            # Helper functions

backend/agent/nodes/
└── kicad_designer.py   # KiCad worker node

backend/agent/prompts/
└── kicad_designer.txt  # System prompt

tests/
├── test_kicad_library.py
├── test_kicad_generator.py
└── test_kicad_integration.py
```

### Files to Modify:
```
backend/agent/nodes/supervisor_v2.py  # Add kicad route
backend/agent/graph.py                 # Add kicad_designer node
backend/agent/state.py                 # Add kicad-related fields
```

---

## 🚀 Execution Order

1. **A1: library.py** - Foundation (component data)
2. **A2: schemas.py** - Pydantic models for LLM
3. **A3: generator.py** - Core logic
4. **A4: templates.py** - Pre-made circuits
5. **B1-B2: kicad_designer.py** - Node integration
6. **C1-C2: Update supervisor & graph** - Routing
7. **D1-D2: Testing** - Validation

---

## ⚠️ Constraints

- ❌ **DO NOT** implement Web Search improvements (already working)
- ❌ **DO NOT** implement Deep Research (Phase 2)
- ❌ **DO NOT** implement Open Interpreter (Phase 3)
- ✅ **FOCUS** on LangGraph + KiCad only

---

## 📈 Success Metrics

| Metric | Target |
|--------|--------|
| Component Library | ≥20 components |
| Template Circuits | ≥5 templates |
| Generator Test | Valid .kicad_sch output |
| Integration Test | End-to-end working |
| Chat + KiCad routing | 100% accurate |

---

## 🔄 Dependencies

```
# No new pip packages needed!
# KiCad logic is pure Python, generates files directly
# Gemini structured output already implemented
```

---

*Created: 2026-02-02*
*Phase: 1 of 3*
*Status: ✅ COMPLETED*

---

## ✅ COMPLETION SUMMARY

### Phase 1 Implementation Results (Completed)

| Task | Status | Test Results |
|------|--------|--------------|
| **A1: library.py** | ✅ Done | 50+ components |
| **A2: schemas.py** | ✅ Done | Pydantic models |
| **A3: generator.py** | ✅ Done | Semantic wire routing |
| **A4: templates.py** | ✅ Done | 7 circuit templates |
| **B1: kicad_designer.py** | ✅ Done | LangGraph node |
| **B2: Prompt** | ✅ Done | Embedded in node |
| **C1: Update supervisor** | ✅ Done | "kicad" response_type |
| **C2: Update graph** | ✅ Done | kicad_designer node added |
| **D1: Unit tests** | ✅ Done | 27/27 passed |
| **D2: Integration tests** | ✅ Done | 18/18 passed |
| **D3: Routing tests** | ✅ Done | 11/11 passed |

### Total Tests: **56/56 PASSED** 🎉

### Files Created:
```
backend/tools/kicad/
├── __init__.py       ✅
├── library.py        ✅ (50+ components)
├── schemas.py        ✅ (Pydantic models)
├── generator.py      ✅ (Semantic wire routing)
└── templates.py      ✅ (7 templates)

backend/agent/nodes/
└── kicad_designer.py ✅ (LangGraph node)

backend/
├── test_kicad.py             ✅ (27 tests)
├── test_kicad_integration.py ✅ (18 tests)
└── test_kicad_routing.py     ✅ (11 tests)
```

### Files Modified:
```
backend/agent/nodes/supervisor_v2.py  ✅ Added "kicad" response_type
backend/agent/graph.py                 ✅ Added kicad_designer node
backend/agent/state.py                 ✅ Added "designing_kicad" status
```

### Success Metrics Achieved:
| Metric | Target | Actual |
|--------|--------|--------|
| Component Library | ≥20 | **50+** ✅ |
| Template Circuits | ≥5 | **7** ✅ |
| Generator Test | Valid output | **100%** ✅ |
| Integration Test | Working | **100%** ✅ |
| Chat + KiCad routing | 100% | **100%** ✅ |

