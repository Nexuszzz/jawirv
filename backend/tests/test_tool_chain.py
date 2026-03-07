"""
JAWIR OS - Tests for Tool Chaining Framework
===============================================
Tests untuk tool_chain.py: ChainStep, ChainContext, ToolChain, ChainRegistry.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.tool_chain import (
    ChainStep,
    ChainContext,
    ChainResult,
    ToolChain,
    ChainRegistry,
)


# ============================================
# ChainStep Tests
# ============================================

class TestChainStep:
    def test_create_step(self):
        step = ChainStep(tool_name="web_search", input_mapping={"query": "$user_input"})
        assert step.tool_name == "web_search"
        assert step.input_mapping["query"] == "$user_input"

    def test_step_defaults(self):
        step = ChainStep(tool_name="test")
        assert step.input_mapping == {}
        assert step.transform is None
        assert step.description == ""

    def test_step_with_transform(self):
        transform_fn = lambda x: x.upper()
        step = ChainStep(
            tool_name="run_python_code",
            input_mapping={"code": "$prev_output"},
            transform=transform_fn,
        )
        assert step.transform is not None
        assert step.transform("hello") == "HELLO"


# ============================================
# ChainContext Tests
# ============================================

class TestChainContext:
    def test_create_context(self):
        ctx = ChainContext(user_input="test query")
        assert ctx.user_input == "test query"
        assert ctx.current_step == 0
        assert ctx.step_outputs == {}

    def test_resolve_user_input(self):
        ctx = ChainContext(user_input="hello world")
        assert ctx.resolve_value("$user_input") == "hello world"

    def test_resolve_prev_output_first_step(self):
        ctx = ChainContext(user_input="fallback")
        ctx.current_step = 0
        assert ctx.resolve_value("$prev_output") == "fallback"

    def test_resolve_prev_output(self):
        ctx = ChainContext(user_input="original")
        ctx.step_outputs[0] = "step 0 result"
        ctx.current_step = 1
        assert ctx.resolve_value("$prev_output") == "step 0 result"

    def test_resolve_step_n_output(self):
        ctx = ChainContext()
        ctx.step_outputs[0] = "first"
        ctx.step_outputs[1] = "second"
        ctx.step_outputs[2] = "third"
        assert ctx.resolve_value("$step_0_output") == "first"
        assert ctx.resolve_value("$step_2_output") == "third"

    def test_resolve_literal(self):
        ctx = ChainContext()
        assert ctx.resolve_value("literal value") == "literal value"

    def test_resolve_invalid_step_ref(self):
        ctx = ChainContext()
        assert ctx.resolve_value("$step_abc_output") == "$step_abc_output"


# ============================================
# ChainResult Tests
# ============================================

class TestChainResult:
    def test_default_result(self):
        result = ChainResult()
        assert result.success is False
        assert result.final_output == ""
        assert result.step_results == []
        assert result.total_time_ms == 0.0
        assert result.error == ""

    def test_successful_result(self):
        result = ChainResult(
            success=True,
            final_output="final answer",
            total_time_ms=1234.5,
        )
        assert result.success is True
        assert result.final_output == "final answer"


# ============================================
# ToolChain Tests
# ============================================

class TestToolChain:
    def _mock_tool(self, name: str, return_value: str = "mock output"):
        """Create a mock tool."""
        tool = MagicMock()
        tool.name = name
        tool.coroutine = AsyncMock(return_value=return_value)
        tool.ainvoke = AsyncMock(return_value=return_value)
        return tool

    def test_create_chain(self):
        chain = ToolChain(
            name="test_chain",
            steps=[ChainStep(tool_name="web_search")],
        )
        assert chain.name == "test_chain"
        assert len(chain.steps) == 1

    def test_chain_repr(self):
        chain = ToolChain(
            name="my_chain",
            steps=[
                ChainStep(tool_name="web_search"),
                ChainStep(tool_name="run_python_code"),
            ],
        )
        assert "web_search → run_python_code" in repr(chain)

    async def test_single_step_chain(self):
        mock_tool = self._mock_tool("web_search", "search results here")
        chain = ToolChain(
            name="single",
            steps=[
                ChainStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
            ],
        )
        
        result = await chain.execute(
            user_input="ESP32",
            tools_map={"web_search": mock_tool},
        )
        
        assert result.success is True
        assert result.final_output == "search results here"
        assert len(result.step_results) == 1
        assert result.step_results[0]["success"] is True

    async def test_two_step_chain(self):
        tool1 = self._mock_tool("web_search", "search data")
        tool2 = self._mock_tool("run_python_code", "processed data")
        
        chain = ToolChain(
            name="two_step",
            steps=[
                ChainStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
                ChainStep(
                    tool_name="run_python_code",
                    input_mapping={"code": "$prev_output"},
                ),
            ],
        )
        
        result = await chain.execute(
            user_input="test",
            tools_map={"web_search": tool1, "run_python_code": tool2},
        )
        
        assert result.success is True
        assert result.final_output == "processed data"
        assert len(result.step_results) == 2

    async def test_chain_stops_on_missing_tool(self):
        chain = ToolChain(
            name="missing",
            steps=[
                ChainStep(tool_name="nonexistent_tool", input_mapping={"x": "$user_input"}),
            ],
            stop_on_error=True,
        )
        
        result = await chain.execute(
            user_input="test",
            tools_map={},
        )
        
        assert result.success is False
        assert "not found" in result.error

    async def test_chain_continues_on_error(self):
        tool2 = self._mock_tool("run_python_code", "fallback output")
        
        chain = ToolChain(
            name="continue",
            steps=[
                ChainStep(tool_name="nonexistent"),
                ChainStep(
                    tool_name="run_python_code",
                    input_mapping={"code": "$user_input"},
                ),
            ],
            stop_on_error=False,
        )
        
        result = await chain.execute(
            user_input="print('hello')",
            tools_map={"run_python_code": tool2},
        )
        
        assert result.success is True
        assert len(result.step_results) == 2

    async def test_chain_with_transform(self):
        mock_tool = self._mock_tool("run_python_code", "42")
        
        chain = ToolChain(
            name="transform",
            steps=[
                ChainStep(
                    tool_name="run_python_code",
                    input_mapping={"code": "$user_input"},
                    transform=lambda x: f"print({x})",
                ),
            ],
        )
        
        result = await chain.execute(
            user_input="2+2",
            tools_map={"run_python_code": mock_tool},
        )
        
        assert result.success is True
        # Verify transform was applied
        call_args = mock_tool.ainvoke.call_args[0][0]
        assert "print(" in call_args["code"]

    async def test_chain_timing(self):
        mock_tool = self._mock_tool("web_search", "fast")
        
        chain = ToolChain(
            name="timed",
            steps=[
                ChainStep(tool_name="web_search", input_mapping={"query": "$user_input"}),
            ],
        )
        
        result = await chain.execute(
            user_input="test",
            tools_map={"web_search": mock_tool},
        )
        
        assert result.total_time_ms >= 0
        assert result.step_results[0]["time_ms"] >= 0


# ============================================
# ChainRegistry Tests
# ============================================

class TestChainRegistry:
    def setup_method(self):
        """Reset singleton before each test."""
        ChainRegistry.reset()

    def test_singleton(self):
        r1 = ChainRegistry()
        r2 = ChainRegistry()
        assert r1 is r2

    def test_register_and_get(self):
        registry = ChainRegistry()
        chain = ToolChain(name="test", steps=[])
        
        registry.register(chain)
        assert registry.get("test") is chain

    def test_get_nonexistent(self):
        registry = ChainRegistry()
        assert registry.get("nope") is None

    def test_list_chains(self):
        registry = ChainRegistry()
        registry.register(ToolChain(name="a", steps=[]))
        registry.register(ToolChain(name="b", steps=[]))
        
        names = registry.list_chains()
        assert "a" in names
        assert "b" in names

    def test_remove_chain(self):
        registry = ChainRegistry()
        registry.register(ToolChain(name="removable", steps=[]))
        
        assert registry.remove("removable") is True
        assert registry.get("removable") is None
        assert registry.remove("removable") is False

    def test_clear(self):
        registry = ChainRegistry()
        registry.register(ToolChain(name="a", steps=[]))
        registry.register(ToolChain(name="b", steps=[]))
        
        registry.clear()
        assert registry.list_chains() == []
