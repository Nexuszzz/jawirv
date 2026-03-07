"""
JAWIR OS - Tests for Conditional Tool Execution
==================================================
Tests untuk tool_conditional.py: Condition, ConditionalStep, ConditionalChain.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.tool_chain import ChainContext
from agent.tool_conditional import (
    Condition,
    ConditionalStep,
    ConditionalChain,
)


# ============================================
# Condition Tests
# ============================================

class TestCondition:
    def _ctx(self, prev_output: str = "") -> ChainContext:
        ctx = ChainContext(user_input="test")
        ctx.step_outputs[0] = prev_output
        ctx.current_step = 1
        return ctx

    def test_always(self):
        assert Condition.always()(self._ctx()) is True

    def test_never(self):
        assert Condition.never()(self._ctx()) is False

    def test_contains_true(self):
        ctx = self._ctx("Hello World Error")
        assert Condition.contains("error")(ctx) is True

    def test_contains_false(self):
        ctx = self._ctx("Hello World")
        assert Condition.contains("error")(ctx) is False

    def test_contains_case_sensitive(self):
        ctx = self._ctx("Hello World Error")
        assert Condition.contains("error", case_sensitive=True)(ctx) is False
        assert Condition.contains("Error", case_sensitive=True)(ctx) is True

    def test_not_contains(self):
        ctx = self._ctx("Success!")
        assert Condition.not_contains("error")(ctx) is True
        ctx2 = self._ctx("Error occurred")
        assert Condition.not_contains("error")(ctx2) is False

    def test_matches_regex(self):
        ctx = self._ctx("Temperature: 25.5°C")
        assert Condition.matches(r"\d+\.\d+")(ctx) is True
        ctx2 = self._ctx("No numbers here")
        assert Condition.matches(r"\d+\.\d+")(ctx2) is False

    def test_output_longer_than(self):
        ctx = self._ctx("a" * 100)
        assert Condition.output_longer_than(50)(ctx) is True
        assert Condition.output_longer_than(200)(ctx) is False

    def test_output_shorter_than(self):
        ctx = self._ctx("short")
        assert Condition.output_shorter_than(50)(ctx) is True
        assert Condition.output_shorter_than(3)(ctx) is False

    def test_prev_step_succeeded(self):
        ctx = self._ctx("✅ Search results: ESP32 datasheet")
        assert Condition.prev_step_succeeded()(ctx) is True
        ctx2 = self._ctx("❌ Error: API timeout")
        assert Condition.prev_step_succeeded()(ctx2) is False
        ctx3 = self._ctx("")
        assert Condition.prev_step_succeeded()(ctx3) is False

    def test_prev_step_failed(self):
        ctx = self._ctx("❌ Error: API timeout")
        assert Condition.prev_step_failed()(ctx) is True
        ctx2 = self._ctx("Success data")
        assert Condition.prev_step_failed()(ctx2) is False

    def test_custom_condition(self):
        fn = lambda ctx: len(ctx.user_input) > 5
        ctx1 = ChainContext(user_input="hi")
        assert Condition.custom(fn)(ctx1) is False
        ctx2 = ChainContext(user_input="hello world")
        assert Condition.custom(fn)(ctx2) is True

    def test_all_of(self):
        ctx = self._ctx("Long error output with many details")
        cond = Condition.all_of(
            Condition.contains("error"),
            Condition.output_longer_than(10),
        )
        assert cond(ctx) is True

        ctx2 = self._ctx("Short ok")
        cond2 = Condition.all_of(
            Condition.contains("error"),
            Condition.output_longer_than(10),
        )
        assert cond2(ctx2) is False

    def test_any_of(self):
        ctx = self._ctx("No issues here")
        cond = Condition.any_of(
            Condition.contains("error"),
            Condition.contains("issues"),
        )
        assert cond(ctx) is True

    def test_none_of(self):
        ctx = self._ctx("All good")
        cond = Condition.none_of(
            Condition.contains("error"),
            Condition.contains("failed"),
        )
        assert cond(ctx) is True


# ============================================
# ConditionalStep Tests
# ============================================

class TestConditionalStep:
    def test_create_conditional_step(self):
        step = ConditionalStep(
            tool_name="web_search",
            input_mapping={"query": "$user_input"},
            condition=Condition.always(),
        )
        assert step.tool_name == "web_search"
        assert step.condition is not None

    def test_step_with_skip_message(self):
        step = ConditionalStep(
            tool_name="test",
            skip_message="Custom skip reason",
            fallback_output="fallback",
        )
        assert step.skip_message == "Custom skip reason"
        assert step.fallback_output == "fallback"

    def test_step_defaults(self):
        step = ConditionalStep(tool_name="test")
        assert step.condition is None
        assert step.skip_message == "Step skipped (condition not met)"
        assert step.fallback_output == ""


# ============================================
# ConditionalChain Tests
# ============================================

class TestConditionalChain:
    def _mock_tool(self, name: str, return_value: str = "mock output"):
        tool = MagicMock()
        tool.name = name
        tool.coroutine = AsyncMock(return_value=return_value)
        tool.ainvoke = AsyncMock(return_value=return_value)
        return tool

    async def test_all_steps_execute(self):
        """When no conditions, all steps execute."""
        tool1 = self._mock_tool("web_search", "results")
        tool2 = self._mock_tool("run_python_code", "processed")

        chain = ConditionalChain(
            name="no_cond",
            steps=[
                ConditionalStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
                ConditionalStep(
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
        assert len(result.step_results) == 2
        assert all(s["success"] for s in result.step_results)

    async def test_step_skipped_by_condition(self):
        """Step should be skipped when condition is False."""
        tool1 = self._mock_tool("web_search", "Success: found 5 results")
        tool2 = self._mock_tool("run_python_code", "should not run")

        chain = ConditionalChain(
            name="skip_test",
            steps=[
                ConditionalStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
                ConditionalStep(
                    tool_name="run_python_code",
                    input_mapping={"code": "$prev_output"},
                    condition=Condition.prev_step_failed(),
                    skip_message="Search was successful, no need to retry",
                    fallback_output="used search results directly",
                ),
            ],
        )

        result = await chain.execute(
            user_input="test",
            tools_map={"web_search": tool1, "run_python_code": tool2},
        )

        assert result.success is True
        assert result.step_results[1]["skipped"] is True
        assert "successful" in result.step_results[1]["skip_reason"]
        tool2.ainvoke.assert_not_called()

    async def test_step_executes_on_condition_true(self):
        """Step should execute when condition is True."""
        tool1 = self._mock_tool("web_search", "❌ Error: API timeout")
        tool2 = self._mock_tool("run_python_code", "retry result")

        chain = ConditionalChain(
            name="execute_test",
            steps=[
                ConditionalStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
                ConditionalStep(
                    tool_name="run_python_code",
                    input_mapping={"code": "$prev_output"},
                    condition=Condition.prev_step_failed(),
                ),
            ],
        )

        result = await chain.execute(
            user_input="test",
            tools_map={"web_search": tool1, "run_python_code": tool2},
        )

        assert result.success is True
        assert result.step_results[1].get("skipped") is not True
        tool2.ainvoke.assert_called_once()

    async def test_fallback_output_used(self):
        """When step is skipped, fallback_output should be available."""
        tool1 = self._mock_tool("web_search", "Good results")

        chain = ConditionalChain(
            name="fallback_test",
            steps=[
                ConditionalStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
                ConditionalStep(
                    tool_name="run_python_code",
                    condition=Condition.never(),
                    fallback_output="skipped step output",
                ),
            ],
        )

        result = await chain.execute(
            user_input="test",
            tools_map={"web_search": tool1},
        )

        assert result.success is True
        assert result.final_output == "skipped step output"

    async def test_chain_with_all_of_condition(self):
        """Composite condition with all_of."""
        tool1 = self._mock_tool("web_search", "Long error output with details")
        tool2 = self._mock_tool("run_python_code", "retry")

        chain = ConditionalChain(
            name="composite_test",
            steps=[
                ConditionalStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                ),
                ConditionalStep(
                    tool_name="run_python_code",
                    input_mapping={"code": "$prev_output"},
                    condition=Condition.all_of(
                        Condition.contains("error"),
                        Condition.output_longer_than(10),
                    ),
                ),
            ],
        )

        result = await chain.execute(
            user_input="test",
            tools_map={"web_search": tool1, "run_python_code": tool2},
        )

        assert result.success is True
        tool2.ainvoke.assert_called_once()
