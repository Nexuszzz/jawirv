"""
JAWIR OS - Tests for Multi-Agent Collaboration Framework
===========================================================
Tests untuk multi_agent.py: AgentRole, AgentTeam, CollaborationProtocol,
TeamRegistry.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.multi_agent import (
    AgentRole,
    AgentMessage,
    AgentTeam,
    CollaborationProtocol,
    RoleExecutor,
    TeamResult,
    TeamRegistry,
)


# ============================================
# AgentRole Tests
# ============================================

class TestAgentRole:
    def test_create_role(self):
        role = AgentRole(
            name="researcher",
            tools=["web_search"],
            system_prompt="You are a research specialist.",
            description="Searches the web for information",
        )
        assert role.name == "researcher"
        assert role.tools == ["web_search"]
        assert role.max_iterations == 3
        assert role.can_delegate is False

    def test_role_defaults(self):
        role = AgentRole(name="basic")
        assert role.tools == []
        assert role.system_prompt == ""
        assert role.description == ""

    def test_role_with_multiple_tools(self):
        role = AgentRole(
            name="full_agent",
            tools=["web_search", "run_python_code", "gmail_send"],
            max_iterations=5,
            can_delegate=True,
        )
        assert len(role.tools) == 3
        assert role.max_iterations == 5
        assert role.can_delegate is True


# ============================================
# AgentMessage Tests
# ============================================

class TestAgentMessage:
    def test_create_message(self):
        msg = AgentMessage(
            sender="researcher",
            recipient="coder",
            content="Here are the search results",
        )
        assert msg.sender == "researcher"
        assert msg.recipient == "coder"
        assert msg.metadata == {}

    def test_broadcast_message(self):
        msg = AgentMessage(sender="researcher", content="broadcast")
        assert msg.recipient == "all"

    def test_message_with_metadata(self):
        msg = AgentMessage(
            sender="coder",
            metadata={"tool_used": "run_python_code", "execution_time": 1.5},
        )
        assert msg.metadata["tool_used"] == "run_python_code"


# ============================================
# RoleExecutor Tests
# ============================================

class TestRoleExecutor:
    async def test_default_executor(self):
        role = AgentRole(name="tester", tools=["web_search", "run_python_code"])
        executor = RoleExecutor(role)
        output = await executor.execute("Find ESP32 info")
        assert "[tester]" in output
        assert "web_search" in output
        assert "run_python_code" in output

    async def test_custom_executor(self):
        role = AgentRole(name="custom")
        custom_fn = AsyncMock(return_value="Custom output for testing")
        executor = RoleExecutor(role, tool_executor=custom_fn)
        output = await executor.execute("Test input", {"key": "val"})
        assert output == "Custom output for testing"
        custom_fn.assert_called_once_with(role, "Test input", {"key": "val"})

    async def test_executor_no_tools(self):
        role = AgentRole(name="empty")
        executor = RoleExecutor(role)
        output = await executor.execute("hello")
        assert "none" in output


# ============================================
# AgentTeam — Sequential
# ============================================

class TestSequentialTeam:
    async def test_two_agents_sequential(self):
        team = AgentTeam(
            name="test_seq",
            roles=[
                AgentRole(name="researcher", tools=["web_search"]),
                AgentRole(name="coder", tools=["run_python_code"]),
            ],
            protocol=CollaborationProtocol.SEQUENTIAL,
        )
        result = await team.execute("Build ESP32 blink sketch")
        assert result.success is True
        assert "researcher" in result.agent_outputs
        assert "coder" in result.agent_outputs
        assert len(result.messages) == 2
        assert result.protocol == "sequential"

    async def test_sequential_context_passing(self):
        """Each agent should receive context from prior agents."""
        received_contexts = []

        async def capture_executor(role, user_input, context):
            received_contexts.append(dict(context))
            return f"output_from_{role.name}"

        team = AgentTeam(
            name="ctx_test",
            roles=[
                AgentRole(name="a"),
                AgentRole(name="b"),
                AgentRole(name="c"),
            ],
            protocol=CollaborationProtocol.SEQUENTIAL,
            tool_executor=capture_executor,
        )
        result = await team.execute("test")
        assert result.success is True
        # Agent A gets empty context
        assert received_contexts[0] == {}
        # Agent B gets A's output
        assert received_contexts[1] == {"a": "output_from_a"}
        # Agent C gets A and B's outputs
        assert received_contexts[2] == {"a": "output_from_a", "b": "output_from_b"}


# ============================================
# AgentTeam — Parallel
# ============================================

class TestParallelTeam:
    async def test_parallel_execution(self):
        team = AgentTeam(
            name="test_par",
            roles=[
                AgentRole(name="agent_a", tools=["web_search"]),
                AgentRole(name="agent_b", tools=["run_python_code"]),
            ],
            protocol=CollaborationProtocol.PARALLEL,
        )
        result = await team.execute("Parallel task")
        assert result.success is True
        assert len(result.agent_outputs) == 2
        assert result.protocol == "parallel"

    async def test_parallel_handles_exception(self):
        """If one agent raises, it should be captured as Error, not crash."""
        async def failing_executor(role, user_input, context):
            if role.name == "bad_agent":
                raise ValueError("Agent exploded")
            return "success"

        team = AgentTeam(
            name="fail_par",
            roles=[
                AgentRole(name="good_agent"),
                AgentRole(name="bad_agent"),
            ],
            protocol=CollaborationProtocol.PARALLEL,
            tool_executor=failing_executor,
        )
        result = await team.execute("test")
        assert result.success is True
        assert "Error" in result.agent_outputs["bad_agent"]
        assert result.agent_outputs["good_agent"] == "success"


# ============================================
# AgentTeam — Pipeline
# ============================================

class TestPipelineTeam:
    async def test_pipeline_output_becomes_input(self):
        """Output of agent A becomes input for agent B."""
        received_inputs = []

        async def track_executor(role, user_input, context):
            received_inputs.append(user_input)
            return f"processed_by_{role.name}"

        team = AgentTeam(
            name="pipe",
            roles=[
                AgentRole(name="step1"),
                AgentRole(name="step2"),
                AgentRole(name="step3"),
            ],
            protocol=CollaborationProtocol.PIPELINE,
            tool_executor=track_executor,
        )
        result = await team.execute("original_input")
        assert result.success is True
        assert received_inputs[0] == "original_input"
        assert received_inputs[1] == "processed_by_step1"
        assert received_inputs[2] == "processed_by_step2"
        assert result.final_output == "processed_by_step3"

    async def test_pipeline_messages_have_correct_recipients(self):
        team = AgentTeam(
            name="pipe_msg",
            roles=[
                AgentRole(name="a"),
                AgentRole(name="b"),
                AgentRole(name="c"),
            ],
            protocol=CollaborationProtocol.PIPELINE,
        )
        result = await team.execute("test")
        assert result.messages[0].recipient == "b"
        assert result.messages[1].recipient == "c"
        assert result.messages[2].recipient == "final"


# ============================================
# AgentTeam — Debate
# ============================================

class TestDebateTeam:
    async def test_debate_protocol(self):
        team = AgentTeam(
            name="debate",
            roles=[
                AgentRole(name="optimist"),
                AgentRole(name="pessimist"),
            ],
            protocol=CollaborationProtocol.DEBATE,
        )
        result = await team.execute("Should we use ESP32 or STM32?")
        assert result.success is True
        assert "optimist" in result.agent_outputs
        assert "pessimist" in result.agent_outputs
        assert all(m.metadata.get("phase") == "position" for m in result.messages)


# ============================================
# Custom Merge Strategy
# ============================================

class TestMergeStrategy:
    async def test_custom_merge(self):
        def merge_fn(outputs: dict) -> str:
            return " | ".join(f"{k}:{v[:10]}" for k, v in outputs.items())

        team = AgentTeam(
            name="merge_test",
            roles=[
                AgentRole(name="a"),
                AgentRole(name="b"),
            ],
            protocol=CollaborationProtocol.PARALLEL,
            merge_strategy=merge_fn,
        )
        result = await team.execute("test")
        assert "|" in result.final_output
        assert "a:" in result.final_output
        assert "b:" in result.final_output

    async def test_default_merge(self):
        team = AgentTeam(
            name="default_merge",
            roles=[AgentRole(name="alpha"), AgentRole(name="beta")],
            protocol=CollaborationProtocol.PARALLEL,
        )
        result = await team.execute("test")
        assert "=== ALPHA ===" in result.final_output
        assert "=== BETA ===" in result.final_output


# ============================================
# TeamRegistry Tests
# ============================================

class TestTeamRegistry:
    def setup_method(self):
        TeamRegistry._instance = None

    def test_register_and_get(self):
        reg = TeamRegistry()
        team = AgentTeam(
            name="my_team",
            roles=[AgentRole(name="a")],
        )
        reg.register(team)
        assert reg.get("my_team") is team

    def test_list_teams(self):
        reg = TeamRegistry()
        reg.register(AgentTeam(name="t1", roles=[AgentRole(name="x")]))
        reg.register(AgentTeam(name="t2", roles=[AgentRole(name="y")]))
        assert sorted(reg.list_teams()) == ["t1", "t2"]

    def test_remove(self):
        reg = TeamRegistry()
        reg.register(AgentTeam(name="tmp", roles=[AgentRole(name="z")]))
        assert reg.remove("tmp") is True
        assert reg.get("tmp") is None
        assert reg.remove("nonexistent") is False

    def test_clear(self):
        reg = TeamRegistry()
        reg.register(AgentTeam(name="a", roles=[AgentRole(name="x")]))
        reg.register(AgentTeam(name="b", roles=[AgentRole(name="y")]))
        reg.clear()
        assert reg.list_teams() == []

    def test_get_nonexistent(self):
        reg = TeamRegistry()
        assert reg.get("nope") is None


# ============================================
# TeamResult Tests
# ============================================

class TestTeamResult:
    def test_default_values(self):
        r = TeamResult()
        assert r.success is False
        assert r.final_output == ""
        assert r.agent_outputs == {}
        assert r.messages == []
        assert r.total_time_ms == 0.0

    async def test_result_has_timing(self):
        team = AgentTeam(
            name="timing",
            roles=[AgentRole(name="a")],
            protocol=CollaborationProtocol.SEQUENTIAL,
        )
        result = await team.execute("test")
        assert result.total_time_ms > 0
