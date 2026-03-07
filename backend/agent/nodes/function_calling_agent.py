"""
JAWIR OS - Function Calling Agent Node
LangGraph node yang menggunakan ReAct Executor untuk true agentic behavior.

ReAct Pattern:
    THOUGHT → ACTION → OBSERVATION → EVALUATION → (loop atau done)
    
Features:
- Self-correction: Retry dengan strategi berbeda jika error
- Memory: Ingat apa yang sudah dicoba
- Iterative refinement: Terus improve sampai goal tercapai
"""

import logging
import os
from typing import Any, Optional

from langchain_core.messages import HumanMessage, AIMessage

from agent.state import JawirState, AgentThinking
from agent.react_executor import ReActExecutor, get_react_executor
from agent.function_calling_executor import FunctionCallingExecutor

logger = logging.getLogger("jawir.agent.nodes.function_calling_agent")

# Singleton executors (reuse across invocations)
_fc_executor: Optional[FunctionCallingExecutor] = None
_react_executor: Optional[ReActExecutor] = None


def get_executor(use_react: bool = True):
    """Get or create the appropriate executor.
    
    Args:
        use_react: If True, use ReActExecutor (default). 
                   If False, use legacy FunctionCallingExecutor.
    """
    if use_react:
        global _react_executor
        if _react_executor is None:
            _react_executor = get_react_executor()
        return _react_executor
    else:
        global _fc_executor
        if _fc_executor is None:
            _fc_executor = FunctionCallingExecutor()
        return _fc_executor


async def function_calling_agent_node(state: JawirState) -> dict[str, Any]:
    """
    ReAct Agent Node for LangGraph.
    
    Implements true agentic behavior with:
    1. THOUGHT: Reasoning before action
    2. ACTION: Tool execution
    3. OBSERVATION: Result analysis
    4. EVALUATION: Self-correction if needed
    5. MEMORY: Track what worked/failed
    
    Args:
        state: Current JawirState
        
    Returns:
        Updated state dict with final_response, thinking trace, tool results
    """
    query = state["user_query"]
    logger.info(f"🤖 ReAct Agent processing: {query[:80]}...")

    # Get streamer from state if available
    streamer = state.get("_streamer")

    # Check if we should use ReAct (default) or legacy FC
    use_react = os.environ.get("JAWIR_USE_REACT", "true").lower() == "true"
    
    # Get appropriate executor
    executor = get_executor(use_react=use_react)
    
    executor_type = "ReAct" if use_react else "FunctionCalling"
    logger.info(f"🧠 Using {executor_type} executor")
    
    # Get history messages from state (includes summary, user info, and past messages)
    history_messages = state.get("messages", [])
    logger.info(f"📝 History messages: {len(history_messages)}")

    try:
        # Execute with more iterations for ReAct (complex reasoning)
        max_iters = 25 if use_react else 5
        
        # Get file_data from state for multimodal input (images)
        file_data = state.get("file_data")
        if file_data:
            logger.info(f"📎 File attached: {file_data.get('filename', 'unknown')} ({file_data.get('type', 'unknown')})")
        
        result = await executor.execute(
            user_query=query,
            max_iterations=max_iters,
            streamer=streamer,
            history_messages=history_messages,  # Pass conversation history!
            file_data=file_data,  # Pass file data for multimodal (images)
        )

        final_response = result["final_response"]
        tool_calls_history = result["tool_calls_history"]
        iterations = result["iterations"]
        execution_time = result["execution_time"]
        
        # Get thinking trace from ReAct executor
        thinking_trace = result.get("thinking_trace", [])
        memory_info = result.get("memory", {})

        # Build thinking record
        if tool_calls_history:
            tools_used = [tc["tool_name"] for tc in tool_calls_history]
            unique_tools = list(set(tools_used))
            
            # Include ReAct-specific info
            thinking_summary = f"Menggunakan {len(tool_calls_history)} tools: {', '.join(unique_tools)}"
            if memory_info.get("learned"):
                thinking_summary += f" | Learned: {len(memory_info['learned'])} hal"
            
            thinking = AgentThinking(
                thought=thinking_summary,
                evaluation=f"Selesai dalam {iterations} iterasi ({execution_time:.1f}s)",
                memory=str(memory_info.get("learned", [])[:3]) if memory_info else None,
                next_goal=None,
            )
        else:
            thinking = AgentThinking(
                thought=f"Menjawab langsung tanpa tools",
                evaluation=f"Direct response ({execution_time:.1f}s)",
                memory=None,
                next_goal=None,
            )

        # Build tool_results for state compatibility
        from agent.state import ToolResult
        from datetime import datetime
        
        tool_results = []
        for tc in tool_calls_history:
            tool_results.append(ToolResult(
                tool_name=tc["tool_name"],
                status="success" if tc["status"] == "success" else "error",
                data={"args": tc["args"], "result_preview": tc["result"][:500]},
                error_message=tc["result"] if tc["status"] == "error" else None,
                executed_at=datetime.now().isoformat(),
            ))

        # Return updated state with ReAct-specific data
        return {
            "understanding": f"ReAct Agent: {query[:100]}",
            "plan": [],
            "tools_needed": [],
            "current_step": 0,
            "pending_tools": [],
            "tool_results": state.get("tool_results", []) + tool_results,
            "tool_calls_history": tool_calls_history,
            "thinking_history": state.get("thinking_history", []) + [thinking],
            "thinking_trace": thinking_trace,  # Full ReAct trace
            "current_thinking": thinking,
            "agent_memory": memory_info,  # What agent learned
            "status": "done",
            "final_response": final_response,
            "sources_used": [],
            "messages": state.get("messages", []) + [
                HumanMessage(content=query),
                AIMessage(content=final_response or ""),
            ],
        }

    except Exception as e:
        logger.error(f"❌ ReAct Agent error: {e}")
        
        error_msg = f"Mohon maaf, terjadi kesalahan: {str(e)}"
        
        return {
            "understanding": "Error",
            "plan": [],
            "tools_needed": [],
            "current_step": 0,
            "pending_tools": [],
            "status": "error",
            "final_response": error_msg,
            "sources_used": [],
            "errors": state.get("errors", []) + [str(e)],
            "messages": state.get("messages", []) + [
                HumanMessage(content=query),
                AIMessage(content=error_msg),
            ],
        }
