"""
JAWIR OS - Multi-Agent Collaboration Framework
=================================================
Framework untuk multi-agent collaboration: 2+ agent bekerja sama
menyelesaikan tugas kompleks.

Architecture:
    - AgentRole: Mendefinisikan peran, tools, dan system prompt per agent
    - AgentTeam: Kumpulan agent yang bekerja bersama
    - CollaborationProtocol: Strategi kolaborasi (sequential, parallel, debate)
    - TeamResult: Aggregated result dari kolaborasi

Usage:
    from agent.multi_agent import AgentRole, AgentTeam, CollaborationProtocol

    researcher = AgentRole(
        name="researcher",
        tools=["web_search"],
        system_prompt="You are a research specialist.",
    )
    coder = AgentRole(
        name="coder",
        tools=["run_python_code"],
        system_prompt="You are a coding specialist.",
    )

    team = AgentTeam(
        name="research_and_code",
        roles=[researcher, coder],
        protocol=CollaborationProtocol.SEQUENTIAL,
    )

    result = await team.execute("Research ESP32 and write example code")
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger("jawir.agent.multi_agent")


# ============================================
# Collaboration Protocols
# ============================================

class CollaborationProtocol(str, Enum):
    """Strategy for how agents collaborate."""
    SEQUENTIAL = "sequential"    # Agent A → Agent B → Agent C
    PARALLEL = "parallel"        # Agent A + B + C simultaneously
    DEBATE = "debate"            # Agents discuss/debate, summarizer picks best
    PIPELINE = "pipeline"        # Output of A becomes instruction for B


# ============================================
# Agent Role Definition
# ============================================

@dataclass
class AgentRole:
    """
    Defines a single agent's role in a multi-agent team.
    
    Attributes:
        name: Unique identifier for this agent role
        tools: List of tool names this agent can use
        system_prompt: System instruction for this agent
        description: Human-readable description of what this agent does
        max_iterations: Max FC iterations for this agent
        can_delegate: Whether this agent can pass work to others
    """
    name: str
    tools: list[str] = field(default_factory=list)
    system_prompt: str = ""
    description: str = ""
    max_iterations: int = 3
    can_delegate: bool = False


# ============================================
# Agent Message
# ============================================

@dataclass
class AgentMessage:
    """
    A message passed between agents during collaboration.
    
    Attributes:
        sender: Name of the sending agent
        recipient: Name of the receiving agent ("all" for broadcast)
        content: Message content
        metadata: Additional data (tool outputs, etc)
    """
    sender: str
    recipient: str = "all"
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================
# Team Result
# ============================================

@dataclass
class TeamResult:
    """
    Aggregated result from multi-agent collaboration.
    
    Attributes:
        success: Whether collaboration succeeded
        final_output: Combined final output
        agent_outputs: Per-agent outputs
        messages: Messages exchanged between agents
        total_time_ms: Total execution time
        protocol: Which protocol was used
        error: Error message if failed
    """
    success: bool = False
    final_output: str = ""
    agent_outputs: dict[str, str] = field(default_factory=dict)
    messages: list[AgentMessage] = field(default_factory=list)
    total_time_ms: float = 0.0
    protocol: str = ""
    error: str = ""


# ============================================
# Agent Executor (per-role)
# ============================================

class RoleExecutor:
    """
    Executes a single agent role with its assigned tools.
    
    This wraps the Gemini FC executor to run a sub-task
    with a specific subset of tools and a role-specific prompt.
    """
    
    def __init__(self, role: AgentRole, tool_executor: Optional[Callable] = None):
        """
        Args:
            role: AgentRole configuration
            tool_executor: Optional callable(role, user_input, context) → output.
                          If None, uses a simple mock for testing.
        """
        self.role = role
        self._executor = tool_executor
    
    async def execute(
        self,
        user_input: str,
        context: Optional[dict] = None,
    ) -> str:
        """
        Execute this agent role's task.
        
        Args:
            user_input: Task description / input
            context: Shared context (outputs from other agents, etc)
            
        Returns:
            Agent output string
        """
        context = context or {}
        
        logger.info(f"🤖 Agent '{self.role.name}' executing...")
        
        if self._executor:
            result = await self._executor(self.role, user_input, context)
            return str(result)
        
        # Default: return a description of what would happen
        tool_list = ", ".join(self.role.tools) if self.role.tools else "none"
        return (
            f"[{self.role.name}] Processed: '{user_input[:100]}' "
            f"using tools: [{tool_list}]"
        )


# ============================================
# Agent Team
# ============================================

class AgentTeam:
    """
    A team of agents that collaborate to solve a complex task.
    
    Supports multiple collaboration protocols:
    - SEQUENTIAL: Agents run one after another, passing context
    - PARALLEL: All agents run simultaneously on the same input
    - DEBATE: Agents produce independent outputs, then a final merge
    - PIPELINE: Output of agent A becomes the instruction for agent B
    """
    
    def __init__(
        self,
        name: str,
        roles: list[AgentRole],
        protocol: CollaborationProtocol = CollaborationProtocol.SEQUENTIAL,
        description: str = "",
        tool_executor: Optional[Callable] = None,
        merge_strategy: Optional[Callable] = None,
    ):
        """
        Args:
            name: Team name
            roles: List of agent roles
            protocol: Collaboration strategy
            description: What this team does
            tool_executor: Custom executor for each role
            merge_strategy: Custom function to merge outputs. 
                           fn(agent_outputs: dict[str, str]) → str
        """
        self.name = name
        self.roles = roles
        self.protocol = protocol
        self.description = description
        self._merge_strategy = merge_strategy
        
        # Create executors for each role
        self._executors = {
            role.name: RoleExecutor(role, tool_executor)
            for role in roles
        }
    
    async def execute(self, user_input: str) -> TeamResult:
        """Execute the team collaboration."""
        start_time = time.perf_counter()
        result = TeamResult(protocol=self.protocol.value)
        
        logger.info(
            f"🏢 Team '{self.name}' starting "
            f"({self.protocol.value}, {len(self.roles)} agents)"
        )
        
        try:
            if self.protocol == CollaborationProtocol.SEQUENTIAL:
                await self._execute_sequential(user_input, result)
            elif self.protocol == CollaborationProtocol.PARALLEL:
                await self._execute_parallel(user_input, result)
            elif self.protocol == CollaborationProtocol.DEBATE:
                await self._execute_debate(user_input, result)
            elif self.protocol == CollaborationProtocol.PIPELINE:
                await self._execute_pipeline(user_input, result)
            
            result.success = True
            
        except Exception as e:
            result.error = str(e)
            logger.error(f"❌ Team '{self.name}' failed: {e}")
        
        result.total_time_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )
        return result
    
    async def _execute_sequential(self, user_input: str, result: TeamResult):
        """
        Sequential: Each agent runs after the previous one finishes.
        Each agent receives the shared context (all prior outputs).
        """
        context = {}
        
        for role in self.roles:
            executor = self._executors[role.name]
            output = await executor.execute(user_input, context)
            
            result.agent_outputs[role.name] = output
            context[role.name] = output
            
            result.messages.append(AgentMessage(
                sender=role.name,
                recipient="team",
                content=output,
            ))
        
        result.final_output = self._merge_outputs(result.agent_outputs)
    
    async def _execute_parallel(self, user_input: str, result: TeamResult):
        """
        Parallel: All agents run simultaneously on the same input.
        """
        tasks = []
        for role in self.roles:
            executor = self._executors[role.name]
            tasks.append(executor.execute(user_input, {}))
        
        outputs = await asyncio.gather(*tasks, return_exceptions=True)
        
        for role, output in zip(self.roles, outputs):
            if isinstance(output, Exception):
                result.agent_outputs[role.name] = f"Error: {output}"
            else:
                result.agent_outputs[role.name] = output
            
            result.messages.append(AgentMessage(
                sender=role.name,
                recipient="team",
                content=result.agent_outputs[role.name],
            ))
        
        result.final_output = self._merge_outputs(result.agent_outputs)
    
    async def _execute_debate(self, user_input: str, result: TeamResult):
        """
        Debate: All agents produce independent outputs, then merge.
        Unlike parallel, debate logs inter-agent 'debate' messages.
        """
        # Phase 1: Independent outputs
        tasks = []
        for role in self.roles:
            executor = self._executors[role.name]
            tasks.append(executor.execute(user_input, {}))
        
        outputs = await asyncio.gather(*tasks, return_exceptions=True)
        
        for role, output in zip(self.roles, outputs):
            out_str = str(output)
            result.agent_outputs[role.name] = out_str
            
            # Each agent broadcasts their position
            result.messages.append(AgentMessage(
                sender=role.name,
                recipient="all",
                content=out_str,
                metadata={"phase": "position"},
            ))
        
        # Phase 2: Merge/summarize
        result.final_output = self._merge_outputs(result.agent_outputs)
    
    async def _execute_pipeline(self, user_input: str, result: TeamResult):
        """
        Pipeline: Output of agent A becomes the input for agent B.
        """
        current_input = user_input
        
        for role in self.roles:
            executor = self._executors[role.name]
            output = await executor.execute(current_input, {})
            
            result.agent_outputs[role.name] = output
            result.messages.append(AgentMessage(
                sender=role.name,
                recipient=(
                    self.roles[self.roles.index(role) + 1].name
                    if self.roles.index(role) < len(self.roles) - 1
                    else "final"
                ),
                content=output,
            ))
            
            current_input = output  # Pipeline: output → next input
        
        result.final_output = output  # Last agent's output
    
    def _merge_outputs(self, agent_outputs: dict[str, str]) -> str:
        """
        Merge all agent outputs into a single final output.
        Uses custom merge strategy if provided, else concatenates.
        """
        if self._merge_strategy:
            return self._merge_strategy(agent_outputs)
        
        parts = []
        for name, output in agent_outputs.items():
            parts.append(f"=== {name.upper()} ===\n{output}")
        return "\n\n".join(parts)


# ============================================
# Team Registry (Singleton)
# ============================================

class TeamRegistry:
    """
    Registry of pre-configured agent teams.
    Singleton pattern, same as ChainRegistry.
    """
    _instance = None
    _teams: dict[str, AgentTeam] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._teams = {}
        return cls._instance
    
    def register(self, team: AgentTeam) -> None:
        """Register a team."""
        self._teams[team.name] = team
        logger.info(f"📝 Team '{team.name}' registered")
    
    def get(self, name: str) -> Optional[AgentTeam]:
        """Get a team by name."""
        return self._teams.get(name)
    
    def list_teams(self) -> list[str]:
        """List all registered team names."""
        return list(self._teams.keys())
    
    def remove(self, name: str) -> bool:
        """Remove a team. Returns True if removed."""
        if name in self._teams:
            del self._teams[name]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all teams."""
        self._teams.clear()
