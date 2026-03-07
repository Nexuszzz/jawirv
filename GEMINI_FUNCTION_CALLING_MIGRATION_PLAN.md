# 🚀 GEMINI FUNCTION CALLING MIGRATION PLAN

> **Goal**: Migrate JAWIR dari manual tool routing ke TRUE Gemini native function calling untuk agentic behavior yang lebih autonomous.
>
> **Current State**: Tools dipanggil manual via hardcoded routing di Supervisor  
> **Target State**: Gemini autonomously choose tools via function calling API  
> **Effort**: 2-3 days (Medium complexity)  
> **Priority**: 🔴 CRITICAL - Untuk TRUE agent behavior

---

## 📋 EXECUTIVE SUMMARY

### **Current Architecture (Manual Routing)**
```
User Query → Supervisor (LLM + if-else) → hardcoded route → researcher/kicad/synthesizer
                                                               ↓
                                                         Manual tool call
```

**Problems:**
- ❌ Gemini TIDAK memilih tools sendiri
- ❌ Adding new tool = modify supervisor routing code
- ❌ BUKAN true agentic behavior (code-driven, not model-driven)

---

### **Target Architecture (Function Calling)**
```
User Query → Agent Executor → Gemini (with tools registered)
                                ↓
                          returns tool_calls
                                ↓
                    Execute tools automatically
                                ↓
                    Return results to Gemini
                                ↓
                    Loop until done
```

**Benefits:**
- ✅ Gemini autonomously decides tools
- ✅ Easy to add tools (just register)
- ✅ TRUE agentic behavior (model-driven)
- ✅ Better scalability & flexibility

---

## 🎯 MIGRATION STRATEGY

### **Phase 1: Function Calling Infrastructure** (Day 1 Morning)
Setup foundational infrastructure untuk function calling.

#### **1.1 Create Tool Definitions Module**
**File**: `backend/agent/tools_registry.py`

Define all tools sebagai LangChain Tool objects:

```python
from langchain_core.tools import Tool, StructuredTool
from pydantic import BaseModel, Field

# ===== WEB SEARCH TOOL =====
class WebSearchInput(BaseModel):
    query: str = Field(description="Search query untuk mencari informasi terkini")
    max_results: int = Field(default=5, description="Maksimal hasil pencarian")

def create_web_search_tool():
    from tools.web_search import TavilySearchTool
    from app.config import settings
    
    search = TavilySearchTool(api_key=settings.tavily_api_key)
    
    async def search_wrapper(query: str, max_results: int = 5):
        results = await search.search(query, max_results)
        return {
            "results": [r.to_dict() for r in results],
            "count": len(results)
        }
    
    return StructuredTool.from_function(
        func=search_wrapper,
        name="web_search",
        description="Search internet untuk informasi terkini (berita, harga, data real-time). Gunakan untuk pertanyaan yang butuh data terbaru.",
        args_schema=WebSearchInput,
        coroutine=search_wrapper,
    )

# ===== KICAD SCHEMATIC TOOL =====
class KicadDesignInput(BaseModel):
    description: str = Field(description="Deskripsi rangkaian elektronika yang ingin dibuat")
    project_name: str = Field(description="Nama project (tanpa spasi)")

def create_kicad_tool():
    async def kicad_wrapper(description: str, project_name: str):
        from tools.kicad import generate_schematic_from_description
        result = await generate_schematic_from_description(description, project_name)
        return {
            "success": result.success,
            "file_path": result.file_path,
            "message": result.message
        }
    
    return StructuredTool.from_function(
        func=kicad_wrapper,
        name="generate_kicad_schematic",
        description="Generate schematic rangkaian elektronika (.kicad_sch file). Gunakan untuk permintaan desain circuit, PCB, atau komponen elektronik.",
        args_schema=KicadDesignInput,
        coroutine=kicad_wrapper,
    )

# ===== GOOGLE WORKSPACE TOOLS =====
# (Similar pattern untuk Gmail, Drive, Calendar, dll)

# ===== TOOL REGISTRY =====
def get_all_tools() -> list[Tool]:
    """Get all available tools for Gemini function calling."""
    return [
        create_web_search_tool(),
        create_kicad_tool(),
        # Add more tools...
    ]
```

---

#### **1.2 Create Function Calling Agent Executor**
**File**: `backend/agent/function_calling_executor.py`

Create executor yang handle function calling loop:

```python
from typing import Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from agent.tools_registry import get_all_tools
from agent.api_rotator import get_api_key

class FunctionCallingExecutor:
    """
    Executor untuk Gemini function calling agent.
    Handles tool execution loop dengan retry logic.
    """
    
    def __init__(self):
        self.tools = get_all_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """Create Gemini LLM with tools bound."""
        api_key = get_api_key()
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
        )
        # BIND TOOLS - Critical untuk function calling!
        return llm.bind_tools(self.tools)
    
    async def execute(
        self,
        user_query: str,
        max_iterations: int = 5,
        streamer: Optional[Any] = None,
    ) -> dict[str, Any]:
        """
        Execute agent loop dengan function calling.
        
        Loop:
        1. Send query + history to Gemini
        2. If Gemini returns tool_calls → execute tools
        3. Add tool results to history
        4. Loop back to step 1 until Gemini gives final response
        """
        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(content=user_query),
        ]
        
        iteration = 0
        final_response = None
        
        while iteration < max_iterations:
            iteration += 1
            
            # Step 1: Invoke Gemini
            response = await self.llm.ainvoke(messages)
            
            # Step 2: Check if tool calls
            if not response.tool_calls:
                # No tool calls = final response
                final_response = response.content
                break
            
            # Step 3: Execute tools
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                if streamer:
                    await streamer.send_status(
                        "executing_tool",
                        f"Executing {tool_name}..."
                    )
                
                # Execute tool
                tool = self.tool_map.get(tool_name)
                if tool:
                    try:
                        tool_result = await tool.ainvoke(tool_args)
                        
                        # Add tool result to messages
                        messages.append(AIMessage(content="", tool_calls=[tool_call]))
                        messages.append(ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call["id"]
                        ))
                    except Exception as e:
                        # Handle tool error
                        messages.append(ToolMessage(
                            content=f"Error: {str(e)}",
                            tool_call_id=tool_call["id"]
                        ))
            
            # Loop back to invoke Gemini with tool results
        
        return {
            "final_response": final_response,
            "iterations": iteration,
            "messages": messages,
        }
    
    def _get_system_prompt(self) -> str:
        return """Kamu adalah JAWIR (Just Another Wise Intelligent Resource), asisten AI yang bijaksana.

KEMAMPUANMU:
- Kamu punya akses ke TOOLS untuk menyelesaikan tugas
- Gunakan tools HANYA jika benar-benar butuh (sapaan/identitas tidak perlu tools)
- Jika butuh info terkini → gunakan web_search
- Jika diminta desain circuit → gunakan generate_kicad_schematic
- Jika hanya pertanyaan konsep → jawab langsung tanpa tools

Berikan respons yang informatif dengan bahasa Indonesia + sentuhan Jawa yang sopan.
"""
```

---

### **Phase 2: Integrate with LangGraph** (Day 1 Afternoon)

#### **2.1 Create Function Calling Node**
**File**: `backend/agent/nodes/function_calling_agent.py`

```python
from agent.function_calling_executor import FunctionCallingExecutor
from agent.state import JawirState

async def function_calling_agent_node(state: JawirState) -> dict[str, Any]:
    """
    Function Calling Agent Node.
    Replace old supervisor + researcher + kicad flow.
    """
    executor = FunctionCallingExecutor()
    
    result = await executor.execute(
        user_query=state["user_query"],
        streamer=state.get("streamer"),
    )
    
    return {
        "final_response": result["final_response"],
        "messages": state.get("messages", []) + result["messages"],
        "status": "done",
    }
```

---

#### **2.2 Update Graph to Use Function Calling**
**File**: `backend/agent/graph.py`

```python
# NEW SIMPLIFIED GRAPH
def build_jawir_graph_v2() -> StateGraph:
    graph = StateGraph(JawirState)
    
    # Option 1: Single function calling node (simplest)
    graph.add_node("agent", function_calling_agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    
    # Option 2: Keep fallback + function calling hybrid
    graph.add_node("router", quick_router_node)  # Check fallback
    graph.add_node("agent", function_calling_agent_node)
    
    graph.add_edge(START, "router")
    graph.add_conditional_edges(
        "router",
        lambda s: "done" if s.get("final_response") else "agent",
        {"done": END, "agent": "agent"}
    )
    graph.add_edge("agent", END)
    
    return graph
```

---

### **Phase 3: Testing & Validation** (Day 2 Morning)

#### **3.1 Unit Tests**
**File**: `backend/tests/test_function_calling.py`

```python
import pytest
from agent.function_calling_executor import FunctionCallingExecutor

@pytest.mark.asyncio
async def test_web_search_tool():
    executor = FunctionCallingExecutor()
    result = await executor.execute("Harga iPhone 16 terbaru?")
    assert result["final_response"]
    assert "iPhone" in result["final_response"]

@pytest.mark.asyncio
async def test_no_tool_needed():
    executor = FunctionCallingExecutor()
    result = await executor.execute("Halo!")
    assert result["iterations"] == 1  # No tool calls
    assert "Sugeng" in result["final_response"]

@pytest.mark.asyncio
async def test_kicad_tool():
    executor = FunctionCallingExecutor()
    result = await executor.execute("Buat rangkaian LED dengan resistor")
    # Should call generate_kicad_schematic
    assert any("generate_kicad_schematic" in str(m) for m in result["messages"])
```

---

#### **3.2 Integration Tests**
**File**: `backend/tests/test_full_flow_fc.py`

Test end-to-end flow dengan WebSocket:

```python
@pytest.mark.asyncio
async def test_websocket_function_calling():
    # Connect to WS
    # Send query
    # Verify agent uses tools correctly
    # Check final response
```

---

### **Phase 4: Migration & Rollout** (Day 2 Afternoon)

#### **4.1 Feature Flag**
Add feature flag untuk gradual rollout:

```python
# app/config.py
class Settings(BaseSettings):
    use_function_calling: bool = True  # Toggle for rollback
```

```python
# agent/graph.py
def get_compiled_graph():
    if settings.use_function_calling:
        return build_jawir_graph_v2().compile()  # New
    else:
        return build_jawir_graph().compile()  # Old
```

---

#### **4.2 A/B Testing**
Test both versions dengan sample queries:

| Query | Old (Manual) | New (Function Calling) | Expected Winner |
|-------|--------------|------------------------|-----------------|
| "Halo" | Direct | Direct (no tools) | Tie |
| "Harga Bitcoin?" | web_search via researcher | web_search via FC | Tie (both work) |
| "Buat LED circuit" | kicad via designer | kicad via FC | Tie |
| "Jelaskan async" | synthesizer | Direct response | **New (faster)** |
| "3 tools sekaligus" | ❌ Can't | ✅ Can parallel | **New (better)** |

---

#### **4.3 Rollout Plan**
1. Day 2 PM: Deploy with `use_function_calling=False` (old behavior)
2. Day 3 AM: Enable for 10% users
3. Day 3 PM: Enable for 50% users
4. Day 4: Enable for 100% if metrics good
5. Day 5: Remove old code if stable

---

## 📊 SUCCESS METRICS

### **Technical Metrics**
- ✅ Gemini makes tool calls autonomously (no manual routing)
- ✅ All tools (web_search, kicad, gmail, etc) registered successfully
- ✅ Function calling loop converges dalam <5 iterations
- ✅ Tool execution time <2s per tool
- ✅ Error rate <5%

### **User Experience Metrics**
- ✅ Response quality maintained or improved
- ✅ Multi-tool queries work (old: can't, new: can)
- ✅ No regression in simple queries (greetings, identity)
- ✅ Faster for code/knowledge queries (no unnecessary research)

---

## 🚨 RISKS & MITIGATION

### **Risk 1: Gemini hallucinates non-existent tools**
- **Mitigation**: Clear tool descriptions + system prompt instructions
- **Fallback**: Catch unknown tool calls, return error to Gemini

### **Risk 2: Infinite loop (Gemini keeps calling tools)**
- **Mitigation**: `max_iterations=5` limit
- **Fallback**: Force stop + synthesize partial results

### **Risk 3: Tool execution failures**
- **Mitigation**: Try-catch di tool executor, return error message to Gemini
- **Fallback**: Gemini can retry with different params or give up gracefully

### **Risk 4: Performance degradation**
- **Mitigation**: Parallel tool execution (if Gemini calls multiple)
- **Monitoring**: Log tool execution times

---

## 📋 ROLLBACK PLAN

If function calling causes issues:

1. **Immediate**: Set `use_function_calling=False` (instant rollback)
2. **Short-term**: Fix bugs in function calling code
3. **Long-term**: Improve prompts or tool definitions

Rollback is **SAFE** karena old code masih ada (feature flag).

---

## 🎓 LEARNING OUTCOMES

After migration, team akan understand:
- ✅ Gemini function calling API (production-grade)
- ✅ LangChain Tool abstractions
- ✅ Agentic loop patterns
- ✅ Tool registration & execution
- ✅ Error handling in agent systems

---

## 📚 REFERENCES

- [LangChain Tools Docs](https://python.langchain.com/docs/modules/tools/)
- [Gemini Function Calling Guide](https://ai.google.dev/gemini-api/docs/function-calling)
- [LangGraph Tool Integration](https://langchain-ai.github.io/langgraph/how-tos/tool-calling/)

---

## 🔄 NEXT STEPS AFTER MIGRATION

1. **Add more tools easily** (sekarang tinggal register)
2. **Multi-tool queries** (Gemini bisa call multiple tools sekaligus)
3. **Tool chaining** (output tool A → input tool B)
4. **Conditional tool use** (Gemini decides optimal strategy)
5. **Tool usage analytics** (which tools most useful?)

---

**Status**: 📋 READY TO IMPLEMENT  
**Owner**: Backend Team  
**Reviewers**: Tech Lead, Senior Engineer  
**Start Date**: TBD  
**Target Completion**: 3 days after start
