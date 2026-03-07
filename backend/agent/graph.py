"""
JAWIR OS - Agent Graph
LangGraph StateGraph definition with ReAct loop pattern.
"""

import logging
from typing import Any, Optional

from langgraph.graph import StateGraph, START, END

from agent.state import JawirState, create_initial_state
from agent.nodes.supervisor_v2 import supervisor_node, get_fallback_response
from agent.nodes.researcher import researcher_node
from agent.nodes.validator import validator_node, should_continue
from agent.nodes.synthesizer import synthesizer_node
from agent.nodes.kicad_designer import kicad_designer_node
from agent.nodes.function_calling_agent import function_calling_agent_node

logger = logging.getLogger("jawir.agent.graph")


def build_jawir_graph() -> StateGraph:
    """
    Build the JAWIR OS agent graph with ReAct loop pattern.
    
    Graph Structure:
    ```
    START → supervisor → researcher ←→ validator → synthesizer → END
                                         ↑     ↓
                                         └─────┘ (ReAct Loop)
    ```
    
    Returns:
        Compiled StateGraph ready for invocation
    """
    logger.info("🔧 Building JAWIR agent graph...")
    
    # Create graph with JawirState schema
    graph = StateGraph(JawirState)
    
    # ============================================
    # Add Nodes
    # ============================================
    
    # Supervisor: Plans the execution strategy
    graph.add_node("supervisor", supervisor_node)
    
    # Researcher: Executes web searches
    graph.add_node("researcher", researcher_node)
    
    # Validator: Checks if research is sufficient
    graph.add_node("validator", validator_node)
    
    # Synthesizer: Creates final response
    graph.add_node("synthesizer", synthesizer_node)
    
    # KiCad Designer: Creates electronic schematics
    graph.add_node("kicad_designer", kicad_designer_node)
    
    # ============================================
    # Add Edges
    # ============================================
    
    # START → supervisor (always start with planning)
    graph.add_edge(START, "supervisor")
    
    # supervisor → researcher OR synthesizer OR kicad_designer OR END (direct response)
    # Note: Supervisor sets status to "researching", "synthesizing", "designing_kicad", or "done"
    def route_after_supervisor(state):
        """Route based on supervisor decision."""
        status = state.get("status", "")
        tools = state.get("tools_needed", [])
        
        # Direct response - go straight to END
        if status == "done" and state.get("final_response"):
            return END
        # KiCad design request
        elif status == "designing_kicad":
            return "kicad_designer"
        # Need research
        elif tools:
            return "researcher"
        # No tools but need synthesis
        else:
            return "synthesizer"
    
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "researcher": "researcher",
            "synthesizer": "synthesizer",
            "kicad_designer": "kicad_designer",
            END: END,  # Direct response path
        }
    )
    
    # researcher → validator (validate after research)
    graph.add_edge("researcher", "validator")
    
    # validator → researcher OR synthesizer (ReAct loop!)
    # This is the KEY conditional edge that enables the loop
    graph.add_conditional_edges(
        "validator",
        should_continue,
        {
            "researcher": "researcher",  # Loop back for more research
            "synthesizer": "synthesizer",  # Proceed to final response
        }
    )
    
    # synthesizer → END (finish)
    graph.add_edge("synthesizer", END)
    
    # kicad_designer → END (finish)
    graph.add_edge("kicad_designer", END)
    
    logger.info("✅ JAWIR agent graph built successfully")
    
    return graph


def build_jawir_graph_v2() -> StateGraph:
    """
    Build the JAWIR OS agent graph V2 with Gemini Function Calling.
    
    Simplified graph where Gemini autonomously decides tools:
    ```
    START → quick_router → function_calling_agent → END
                 ↓ (fallback match)
                END
    ```
    
    Returns:
        Compiled StateGraph with function calling support
    """
    logger.info("🔧 Building JAWIR agent graph V2 (Function Calling)...")
    
    graph = StateGraph(JawirState)
    
    # ============================================
    # Quick Router Node (handles greetings/identity without LLM)
    # ============================================
    async def quick_router_node(state):
        """Check if query is a simple fallback (greeting, identity, thanks)."""
        from langchain_core.messages import HumanMessage, AIMessage
        
        query = state["user_query"]
        fallback = get_fallback_response(query)
        
        if fallback:
            logger.info("✅ Quick router: fallback response (no LLM needed)")
            return {
                "understanding": "Query sederhana (fallback)",
                "plan": [],
                "tools_needed": [],
                "current_step": 0,
                "pending_tools": [],
                "status": "done",
                "final_response": fallback,
                "sources_used": [],
                "messages": state.get("messages", []) + [
                    HumanMessage(content=query),
                    AIMessage(content=fallback),
                ],
            }
        
        # Not a fallback → route to FC agent
        logger.info("🔀 Quick router: routing to function_calling_agent")
        return {"status": "executing"}
    
    # ============================================
    # Add Nodes
    # ============================================
    graph.add_node("quick_router", quick_router_node)
    graph.add_node("fc_agent", function_calling_agent_node)
    
    # ============================================
    # Add Edges
    # ============================================
    graph.add_edge(START, "quick_router")
    
    def route_after_router(state):
        """Route based on quick_router result."""
        status = state.get("status", "")
        if status == "done" and state.get("final_response"):
            return END
        return "fc_agent"
    
    graph.add_conditional_edges(
        "quick_router",
        route_after_router,
        {
            "fc_agent": "fc_agent",
            END: END,
        }
    )
    
    graph.add_edge("fc_agent", END)
    
    logger.info("✅ JAWIR agent graph V2 (FC) built successfully")
    return graph


# Compile the graph once at module load
_compiled_graph = None


def get_compiled_graph():
    """Get or create the compiled graph singleton.
    
    Uses feature flag USE_FUNCTION_CALLING to decide which graph to build:
    - True:  build_jawir_graph_v2() (Gemini function calling)
    - False: build_jawir_graph() (legacy manual routing)
    """
    global _compiled_graph
    if _compiled_graph is None:
        from app.config import settings
        
        if settings.use_function_calling:
            logger.info("🚀 Using Function Calling graph (V2)")
            graph = build_jawir_graph_v2()
        else:
            logger.info("📋 Using Legacy manual routing graph (V1)")
            graph = build_jawir_graph()
        
        _compiled_graph = graph.compile()
    return _compiled_graph


async def invoke_agent(
    user_query: str,
    session_id: str,
    streamer: Optional[Any] = None,
    file_data: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Invoke the JAWIR agent with a user query.
    
    This is the main entry point for running the agent.
    
    Args:
        user_query: The user's question or command
        session_id: Unique session identifier
        streamer: Optional AgentStatusStreamer for real-time updates
        file_data: Optional file data dict with type, filename, content/data
    
    Returns:
        Dictionary with final_response, thinking_process, sources_used
    """
    logger.info(f"🚀 Invoking agent for session {session_id}")
    logger.info(f"   Query: {user_query[:100]}...")
    if file_data:
        logger.info(f"   File: {file_data.get('filename', 'unknown')} ({file_data.get('type', 'unknown')})")
    
    # ============================================
    # MEMORY: Load conversation history
    # ============================================
    from memory import get_conversation_store
    memory_store = get_conversation_store()
    
    # Save user message to memory
    await memory_store.add_message(session_id, "user", user_query)
    
    # Get history as LangChain messages
    history_messages = memory_store.get_history(session_id, as_langchain=True)
    logger.info(f"📝 Loaded {len(history_messages)} messages from memory")
    
    # Create initial state with history
    initial_state = create_initial_state(
        user_query=user_query,
        session_id=session_id,
        messages=history_messages,  # Pass existing history!
    )
    
    # Add file data to state if provided
    if file_data:
        initial_state["file_data"] = file_data
    
    # CRITICAL: Pass streamer to state for fc_agent node to use
    if streamer:
        initial_state["_streamer"] = streamer
    
    # Get compiled graph
    graph = get_compiled_graph()
    
    # Stream status updates if streamer provided
    if streamer:
        await streamer.send_thinking("Memahami permintaan Anda...")
    
    try:
        # Run the graph with streaming
        final_state = None
        
        async for event in graph.astream(initial_state):
            # Get the current node and state
            for node_name, node_state in event.items():
                logger.debug(f"Node '{node_name}' completed")
                
                # Send status updates
                if streamer:
                    if node_name == "supervisor":
                        plan = node_state.get("plan", [])
                        status = node_state.get("status", "")
                        
                        # Check if direct response (no research)
                        if status == "done" and node_state.get("final_response"):
                            # Direct response - skip research phase
                            await streamer.send_done()
                        elif plan:
                            await streamer.send_status(
                                "planning",
                                f"Rencana: {len(plan)} langkah",
                                {"plan": [s.get("description", "") for s in plan]}
                            )
                        else:
                            await streamer.send_status(
                                "thinking",
                                "Menyusun respons...",
                                {}
                            )
                    
                    elif node_name == "researcher":
                        sources = node_state.get("research_sources", [])
                        if sources:
                            # Send research card
                            await streamer.send_research_card(
                                title=f"Hasil Pencarian: {user_query[:50]}...",
                                summary=node_state.get("research_summary", "")[:300],
                                sources=[
                                    {
                                        "url": s.get("url", ""),
                                        "title": s.get("title", ""),
                                        "snippet": s.get("content", "")[:200],
                                    }
                                    for s in sources[:5]
                                ],
                            )
                    
                    elif node_name == "validator":
                        feedback = node_state.get("validation_feedback", "")
                        if "NEED_MORE" in feedback.upper():
                            await streamer.send_status(
                                "searching",
                                "Perlu penelitian tambahan...",
                            )
                        else:
                            await streamer.send_writing()
                    
                    elif node_name == "synthesizer":
                        await streamer.send_done()
                    
                    elif node_name == "kicad_designer":
                        # KiCad designer completed
                        final_resp = node_state.get("final_response", "")
                        if "✅" in final_resp:
                            await streamer.send_done()
                        else:
                            await streamer.send_error("KiCad design failed")
                
                # Update final state
                final_state = node_state
        
        # Extract results
        if final_state:
            final_response = final_state.get("final_response", "")
            
            # ============================================
            # MEMORY: Save assistant response
            # ============================================
            if final_response:
                await memory_store.add_message(
                    session_id, 
                    "assistant", 
                    final_response,
                    metadata={
                        "tools_used": [t.get("thought", "") for t in final_state.get("thinking_history", [])],
                    }
                )
                logger.info(f"💾 Saved response to memory for session {session_id[:8]}...")
            
            return {
                "final_response": final_response,
                "thinking_process": [
                    t.get("thought", "") 
                    for t in final_state.get("thinking_history", [])
                ],
                "sources_used": final_state.get("sources_used", []),
                "status": final_state.get("status", "done"),
            }
        else:
            return {
                "final_response": "Maaf, terjadi kesalahan dalam memproses permintaan.",
                "thinking_process": [],
                "sources_used": [],
                "status": "error",
            }
            
    except Exception as e:
        logger.error(f"Agent invocation error: {e}")
        
        if streamer:
            await streamer.send_error(str(e))
        
        return {
            "final_response": f"Mohon maaf, terjadi kesalahan: {str(e)}",
            "thinking_process": [],
            "sources_used": [],
            "status": "error",
        }


# ============================================
# Test Function
# ============================================

async def test_graph():
    """Test the agent graph with a sample query."""
    import asyncio
    
    result = await invoke_agent(
        user_query="Apa itu ESP32 dan apa kelebihannya untuk IoT?",
        session_id="test-session-001",
    )
    
    print("\n" + "="*60)
    print("JAWIR OS Agent Test Result")
    print("="*60)
    print(f"\n📝 Final Response:\n{result['final_response']}")
    print(f"\n🧠 Thinking Process:")
    for i, thought in enumerate(result['thinking_process'], 1):
        print(f"   {i}. {thought}")
    print(f"\n📚 Sources Used: {len(result['sources_used'])}")
    for url in result['sources_used'][:5]:
        print(f"   - {url}")
    print(f"\n✅ Status: {result['status']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_graph())
