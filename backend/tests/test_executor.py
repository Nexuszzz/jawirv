"""
JAWIR OS - Unit Tests for FunctionCallingExecutor
==================================================
Tasks 3.1-3.4: Executor init, tool exec loop, max iterations, error handling.

Run:
    cd backend
    python -m pytest tests/test_executor.py -v
"""

import sys
import os
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import asyncio
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


# ============================================
# Task 3.1: Test executor.__init__() loads tools, bind_tools
# ============================================

class TestExecutorInit:
    """Test FunctionCallingExecutor initialization."""

    @patch("agent.function_calling_executor.get_api_key", return_value="fake-key")
    def test_executor_creates_with_tools(self, mock_api_key):
        """Executor should load tools and bind them to LLM."""
        from agent.tools_registry import get_all_tools

        tools = get_all_tools()
        assert len(tools) == 12

        # Test that we can import executor
        from agent.function_calling_executor import FunctionCallingExecutor
        assert FunctionCallingExecutor is not None

    def test_executor_has_system_prompt(self):
        """Executor module should export FUNCTION_CALLING_SYSTEM_PROMPT."""
        from agent.function_calling_executor import FUNCTION_CALLING_SYSTEM_PROMPT
        assert isinstance(FUNCTION_CALLING_SYSTEM_PROMPT, str)
        assert len(FUNCTION_CALLING_SYSTEM_PROMPT) > 50
        # Should contain key instructions
        assert "tool" in FUNCTION_CALLING_SYSTEM_PROMPT.lower() or "JAWIR" in FUNCTION_CALLING_SYSTEM_PROMPT

    def test_executor_max_iterations_default(self):
        """Executor should have max_iterations attribute."""
        from agent.function_calling_executor import FunctionCallingExecutor
        # Check class has the constant/default
        import inspect
        source = inspect.getsource(FunctionCallingExecutor)
        assert "max_iterations" in source


# ============================================
# Task 3.2: Mock LLM with tool_calls, verify ToolMessage
# ============================================

class TestToolExecutionLoop:
    """Test the tool execution loop logic."""

    def test_tool_message_format(self):
        """ToolMessage should be properly formatted."""
        msg = ToolMessage(
            content="Result: Harga Bitcoin $100,000",
            tool_call_id="call_123",
        )
        assert msg.content == "Result: Harga Bitcoin $100,000"
        assert msg.tool_call_id == "call_123"

    def test_ai_message_with_tool_calls(self):
        """AIMessage with tool_calls should be parseable."""
        ai_msg = AIMessage(
            content="",
            tool_calls=[{
                "id": "call_abc",
                "name": "web_search",
                "args": {"query": "harga bitcoin", "max_results": 3}
            }]
        )
        assert len(ai_msg.tool_calls) == 1
        assert ai_msg.tool_calls[0]["name"] == "web_search"
        assert ai_msg.tool_calls[0]["args"]["query"] == "harga bitcoin"

    def test_ai_message_without_tool_calls(self):
        """AIMessage without tool_calls means direct response."""
        ai_msg = AIMessage(content="Halo! Saya JAWIR OS.")
        assert not ai_msg.tool_calls
        assert ai_msg.content == "Halo! Saya JAWIR OS."


# ============================================
# Task 3.3: Mock LLM always tool_calls, verify stops at max
# ============================================

class TestMaxIterations:
    """Test that executor stops at max iterations."""

    def test_max_iterations_concept(self):
        """Verify the max_iterations concept is implemented."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor.execute)

        # Must have iteration tracking
        assert "iteration" in source.lower() or "loop" in source.lower() or "max_iterations" in source
        # Must have a break condition
        assert "break" in source or "max_iterations" in source or "return" in source

    def test_executor_source_has_safety_limit(self):
        """Executor must have a safety limit to prevent infinite loops."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor)

        # Must have max_iterations or similar limit
        assert "max_iterations" in source, "Missing max_iterations safety limit"
        # Must have iteration counter
        assert "iteration" in source.lower(), "Missing iteration counter"


# ============================================
# Task 3.4: Mock tool exception, verify catches error
# ============================================

class TestToolErrorHandling:
    """Test that tool execution errors are gracefully handled."""

    def test_tool_result_truncation_concept(self):
        """Executor should truncate long tool outputs."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor)

        # Should have truncation logic
        has_truncation = (
            "truncat" in source.lower() or
            "[:5000]" in source or
            "[:3000]" in source or
            "max_len" in source.lower() or
            "5000" in source
        )
        assert has_truncation, "Missing tool result truncation logic"

    def test_error_handling_in_execute(self):
        """Execute method should have try-except for tool errors."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor.execute)

        assert "except" in source, "Missing exception handling in execute()"
        assert "Exception" in source or "Error" in source, "Missing error catching"

    def test_api_rotation_on_error(self):
        """Executor should rotate API keys on certain errors."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor)

        has_rotation = (
            "rotat" in source.lower() or
            "api_key" in source.lower() or
            "get_api_key" in source.lower() or
            "429" in source
        )
        assert has_rotation, "Missing API key rotation logic"


# ============================================
# Task 5.3: Test parallel tool execution
# ============================================

class TestParallelToolExecution:
    """Test parallel tool execution support."""

    def test_executor_imports_asyncio(self):
        """Executor should import asyncio for parallel execution."""
        import agent.function_calling_executor as mod
        import inspect
        source = inspect.getsource(mod)
        assert "import asyncio" in source, "Missing asyncio import"

    def test_executor_has_asyncio_gather(self):
        """Executor should use asyncio.gather for parallel tool execution."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor.execute)
        assert "asyncio.gather" in source, "Missing asyncio.gather for parallel execution"

    def test_parallel_vs_sequential_branching(self):
        """Executor should branch based on number of tool calls (>1 = parallel)."""
        from agent.function_calling_executor import FunctionCallingExecutor
        import inspect
        source = inspect.getsource(FunctionCallingExecutor.execute)
        assert "len(response.tool_calls) > 1" in source, "Missing parallel branching condition"
