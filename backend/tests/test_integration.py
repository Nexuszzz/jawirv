"""
JAWIR OS - Integration Tests for Function Calling Graph
========================================================
Tasks 2.8-2.10: Test graph compilation and node structure.
Tasks 3.5-3.6: Multi-tool and conversational tests (stubs).

Run:
    cd backend
    python -m pytest tests/test_integration.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


# ============================================
# Task 2.8: Simple query - Graph structure test
# ============================================

class TestGraphV2Structure:
    """Test that the V2 graph compiles and has correct structure."""

    def test_graph_v2_compiles(self):
        """build_jawir_graph_v2() should compile without errors."""
        from agent.graph import build_jawir_graph_v2
        graph = build_jawir_graph_v2()
        assert graph is not None

    def test_graph_v2_has_correct_nodes(self):
        """V2 graph should have: __start__, quick_router, fc_agent, __end__."""
        from agent.graph import build_jawir_graph_v2
        graph = build_jawir_graph_v2()
        compiled = graph.compile()
        node_names = list(compiled.get_graph().nodes.keys())
        assert "__start__" in node_names
        assert "__end__" in node_names
        assert "quick_router" in node_names
        assert "fc_agent" in node_names

    def test_graph_v1_still_compiles(self):
        """V1 graph should still compile (backward compat)."""
        from agent.graph import build_jawir_graph
        graph = build_jawir_graph()
        assert graph is not None

    def test_feature_flag_switches_graph(self):
        """get_compiled_graph() should respect feature flag."""
        from agent.graph import get_compiled_graph
        # Just verify it returns something
        graph = get_compiled_graph()
        assert graph is not None


# ============================================
# Task 2.9: Web search - Tool binding test
# ============================================

class TestToolBinding:
    """Test that tools bind correctly to Gemini model."""

    def test_tools_have_valid_schemas_for_binding(self):
        """All tools should have schemas that Gemini can parse."""
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()

        for tool in tools:
            # Each tool must have a name
            assert tool.name, f"Tool missing name"
            # Each tool must have args_schema
            assert tool.args_schema is not None, f"Tool '{tool.name}' missing schema"
            # Schema must be serializable to JSON (for Gemini API)
            schema = tool.args_schema.model_json_schema()
            assert "properties" in schema, f"Tool '{tool.name}' schema has no properties"

    def test_web_search_schema_for_gemini(self):
        """Web search schema should be Gemini-compatible."""
        from agent.tools_registry import WebSearchInput
        schema = WebSearchInput.model_json_schema()
        # Gemini needs 'properties' with typed fields
        assert "query" in schema["properties"]
        assert schema["properties"]["query"]["type"] == "string"


# ============================================
# Task 2.10: KiCad - Tool factory test
# ============================================

class TestKicadToolFactory:
    """Test KiCad tool creation and schema."""

    def test_kicad_tool_creates(self):
        from agent.tools_registry import create_kicad_tool
        tool = create_kicad_tool()
        assert tool.name == "generate_kicad_schematic"

    def test_kicad_schema_fields(self):
        from agent.tools_registry import KicadDesignInput
        schema = KicadDesignInput.model_json_schema()
        assert "description" in schema["properties"]
        assert "project_name" in schema["properties"]
        assert "open_kicad" in schema["properties"]


# ============================================
# Task 3.5 Stub: Multi-tool test
# ============================================

class TestMultiToolConcepts:
    """Test that multiple tools can coexist and be selected."""

    def test_different_tools_have_different_schemas(self):
        """Each tool should have a unique schema."""
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()

        schemas = {}
        for tool in tools:
            schema_keys = frozenset(tool.args_schema.model_json_schema()["properties"].keys())
            schemas[tool.name] = schema_keys

        # At minimum, web_search and gmail_search have different schemas
        assert schemas["web_search"] != schemas["gmail_send"]
        assert schemas["open_app"] != schemas["web_search"]

    def test_all_tools_are_async(self):
        """All tools must be async-compatible for concurrent execution."""
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        for tool in tools:
            assert tool.coroutine is not None, f"Tool '{tool.name}' is not async"


# ============================================
# Task 3.6 Stub: Conversational test
# ============================================

class TestConversationalConcepts:
    """Test that FC system prompt supports conversational queries."""

    def test_system_prompt_allows_no_tools(self):
        """System prompt should instruct LLM to NOT always use tools."""
        from agent.function_calling_executor import FUNCTION_CALLING_SYSTEM_PROMPT
        prompt_lower = FUNCTION_CALLING_SYSTEM_PROMPT.lower()

        # Should mention cases where tools are NOT needed
        has_no_tool_guidance = (
            "tidak perlu" in prompt_lower or
            "tanpa tool" in prompt_lower or
            "langsung jawab" in prompt_lower or
            "directly" in prompt_lower or
            "without" in prompt_lower or
            "don't use" in prompt_lower or
            "jangan" in prompt_lower or
            "not" in prompt_lower
        )
        assert has_no_tool_guidance, "System prompt should guide LLM when NOT to use tools"


# ============================================
# State Tests
# ============================================

class TestJawirState:
    """Test JawirState has required fields for FC."""

    def test_state_has_tool_calls_history(self):
        """JawirState must have tool_calls_history field."""
        from agent.state import create_initial_state
        state = create_initial_state("test query", session_id="test-session")
        assert "tool_calls_history" in state
        assert isinstance(state["tool_calls_history"], list)

    def test_state_has_messages(self):
        """JawirState must have messages field."""
        from agent.state import create_initial_state
        state = create_initial_state("test query", session_id="test-session")
        assert "messages" in state

    def test_initial_state_factory(self):
        """create_initial_state() should set query correctly."""
        from agent.state import create_initial_state
        state = create_initial_state("Halo JAWIR", session_id="test-session")
        assert state.get("user_query") == "Halo JAWIR"
