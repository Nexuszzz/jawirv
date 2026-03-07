"""
JAWIR OS - Agent State Schema
TypedDict definitions for LangGraph state management.
"""

from typing import TypedDict, List, Optional, Literal, Annotated, Any
from datetime import datetime
from langgraph.graph import MessagesState
from langchain_core.messages import BaseMessage


# ============================================
# Sub-Types
# ============================================

class ResearchSource(TypedDict):
    """Single research source from web search."""
    url: str
    title: str
    content: str
    relevance_score: float
    retrieved_at: str


class ToolResult(TypedDict):
    """Result from a tool execution."""
    tool_name: str
    status: Literal["success", "error", "pending"]
    data: dict
    error_message: Optional[str]
    executed_at: str


class PlanStep(TypedDict):
    """Single step in the execution plan."""
    step_number: int
    description: str
    tool_needed: Optional[str]
    status: Literal["pending", "in_progress", "completed", "failed"]


class AgentThinking(TypedDict):
    """
    Structured thinking for ReAct pattern.
    Based on Browser-Use's AgentOutput pattern.
    """
    thought: str                      # Chain of Thought
    evaluation: Optional[str]         # Evaluation of previous action
    memory: Optional[str]             # What to remember
    next_goal: Optional[str]          # Next goal to achieve


class ResearchProgress(TypedDict):
    """Track deep research progress for UI updates."""
    current_depth: int
    total_depth: int
    current_breadth: int
    total_breadth: int
    current_query: Optional[str]
    completed_queries: int
    total_queries: int


# ============================================
# Main Agent State
# ============================================

class JawirState(MessagesState):
    """
    Main state schema for JAWIR OS Agent.
    Inherits MessagesState for automatic message history management.
    
    This is the central state that flows through all nodes in the graph.
    """
    
    # ---- Request Context ----
    user_query: str                    # Original user query
    session_id: str                    # Unique session identifier
    request_timestamp: str             # When the request was received
    file_data: Optional[dict]          # Attached file data (image/PDF)
    
    # ---- Planning (Supervisor) ----
    understanding: str                 # Model's understanding of the request
    plan: List[PlanStep]               # Planned execution steps
    current_step: int                  # Index of current step (0-based)
    tools_needed: List[str]            # Tools identified as needed
    
    # ---- Research Results ----
    research_sources: List[ResearchSource]  # Collected sources
    research_summary: str              # Summarized research findings
    research_progress: Optional[ResearchProgress]  # For deep research UI
    
    # ---- Tool Execution ----
    tool_results: List[ToolResult]     # Results from tool executions
    pending_tools: List[str]           # Tools yet to be executed
    tool_calls_history: List[dict]     # Function calling tool call history
    
    # ---- Thinking & Memory (ReAct Pattern) ----
    thinking_history: List[AgentThinking]  # All thinking steps
    current_thinking: Optional[AgentThinking]  # Current thought
    learnings: List[str]               # Accumulated learnings
    
    # ---- Self-Correction ----
    errors: List[str]                  # Error log for learning
    retry_count: int                   # Number of retries (max 3)
    validation_feedback: Optional[str] # Feedback from validator
    
    # ---- Output ----
    final_response: str                # Final response to user
    sources_used: List[str]            # URLs used in response
    status: Literal[
        "planning",         # Supervisor is creating plan
        "researching",      # Researcher is gathering info
        "executing",        # Executing tools
        "validating",       # Validator is checking results
        "synthesizing",     # Creating final response
        "designing_kicad",  # KiCad designer is creating schematic
        "done",             # Successfully completed
        "error"             # Failed with error
    ]
    
    # ---- Internal (not serialized) ----
    _streamer: Optional[Any]           # WebSocket status streamer (internal)


# ============================================
# State Factory
# ============================================

def create_initial_state(
    user_query: str,
    session_id: str,
    messages: Optional[List[BaseMessage]] = None,
) -> JawirState:
    """
    Create a fresh JawirState with default values.
    
    Args:
        user_query: The user's question or command
        session_id: Unique session identifier
        messages: Optional existing message history
    
    Returns:
        Initialized JawirState
    """
    return JawirState(
        # Messages (from MessagesState)
        messages=messages or [],
        
        # Request Context
        user_query=user_query,
        session_id=session_id,
        request_timestamp=datetime.now().isoformat(),
        file_data=None,
        
        # Planning
        understanding="",
        plan=[],
        current_step=0,
        tools_needed=[],
        
        # Research
        research_sources=[],
        research_summary="",
        research_progress=None,
        
        # Tool Execution
        tool_results=[],
        pending_tools=[],
        tool_calls_history=[],
        
        # Thinking
        thinking_history=[],
        current_thinking=None,
        learnings=[],
        
        # Self-Correction
        errors=[],
        retry_count=0,
        validation_feedback=None,
        
        # Output
        final_response="",
        sources_used=[],
        status="planning",
    )


# ============================================
# State Helpers
# ============================================

def add_thinking(state: JawirState, thinking: AgentThinking) -> JawirState:
    """Add a thinking step to the history."""
    state["thinking_history"].append(thinking)
    state["current_thinking"] = thinking
    return state


def add_error(state: JawirState, error: str) -> JawirState:
    """Add an error to the log and increment retry count."""
    state["errors"].append(error)
    state["retry_count"] += 1
    return state


def add_source(state: JawirState, source: ResearchSource) -> JawirState:
    """Add a research source to the collection."""
    state["research_sources"].append(source)
    return state


def add_tool_result(state: JawirState, result: ToolResult) -> JawirState:
    """Add a tool result to the collection."""
    state["tool_results"].append(result)
    return state
