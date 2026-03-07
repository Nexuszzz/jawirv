"""
JAWIR OS - Direct Agent Test (No WebSocket)
Tests ReAct Loop directly without WebSocket
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent components
from agent.graph import build_agent_graph
from agent.state import AgentState


async def test_react_direct():
    """Test agent directly without WebSocket."""
    
    print("=" * 70)
    print(" JAWIR OS - Direct ReAct Workflow Test")
    print(" Testing: Plan → Act → Observe → Loop")
    print("=" * 70)
    
    # Complex comparison query
    query = """Bandingkan ESP32 vs STM32 vs Arduino Nano untuk proyek IoT rumah pintar. 
    Mana yang terbaik dari segi harga, performa, dan kemudahan pemrograman?"""
    
    print(f"\n📝 QUERY: {query[:80]}...\n")
    
    # Build graph
    print("🔧 Building agent graph...")
    graph = build_agent_graph()
    print("✅ Graph built\n")
    
    # Create initial state
    initial_state = AgentState(
        query=query,
        messages=[],
        plan=[],
        search_results=[],
        validation_status="pending",
        retry_count=0,
        max_retries=3,
        final_response="",
        sources=[],
        thinking_process=[],
        current_step=0,
        error=None,
    )
    
    # Track execution
    start_time = time.time()
    phases = []
    
    print("-" * 70)
    print("🔄 EXECUTING REACT LOOP:")
    print("-" * 70)
    
    try:
        # Run graph with streaming to see each node
        async for event in graph.astream(initial_state):
            for node_name, state_update in event.items():
                timestamp = datetime.now().strftime("%H:%M:%S")
                phases.append(node_name)
                
                if node_name == "supervisor":
                    plan = state_update.get("plan", [])
                    print(f"\n🧠 [{timestamp}] SUPERVISOR - Created {len(plan)} step plan:")
                    for i, step in enumerate(plan, 1):
                        print(f"   {i}. {step[:60]}...")
                
                elif node_name == "researcher":
                    results = state_update.get("search_results", [])
                    print(f"\n🔍 [{timestamp}] RESEARCHER - Found {len(results)} sources")
                    for r in results[:5]:
                        print(f"   • {r.get('title', 'N/A')[:50]}...")
                
                elif node_name == "validator":
                    status = state_update.get("validation_status", "")
                    thinking = state_update.get("thinking_process", [])
                    print(f"\n✅ [{timestamp}] VALIDATOR - Status: {status}")
                    if thinking:
                        print(f"   Thinking: {thinking[-1][:60]}...")
                
                elif node_name == "synthesizer":
                    response = state_update.get("final_response", "")
                    sources = state_update.get("sources", [])
                    print(f"\n✍️ [{timestamp}] SYNTHESIZER - Created response ({len(response)} chars)")
                    print(f"   Sources cited: {len(sources)}")
        
        end_time = time.time()
        duration = round(end_time - start_time, 2)
        
        # Get final state
        final_state = initial_state
        for event in phases:
            pass  # Would need to accumulate state properly
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 EXECUTION SUMMARY")
        print("=" * 70)
        print(f"   Duration:     {duration} seconds")
        print(f"   Phases Run:   {' → '.join(phases)}")
        print(f"   Phase Count:  {len(phases)}")
        
        # ReAct Pattern Analysis  
        print("\n" + "=" * 70)
        print("🔄 REACT PATTERN PROVEN:")
        print("=" * 70)
        
        if "supervisor" in phases:
            print("   ✅ REASON  - Supervisor analyzed & planned")
        if "researcher" in phases:
            print("   ✅ ACT     - Researcher executed searches")
        if "validator" in phases:
            print("   ✅ OBSERVE - Validator checked results")
        if "synthesizer" in phases:
            print("   ✅ WRITE   - Synthesizer created response")
        
        # Check for retry loop
        retry_count = phases.count("researcher") - 1
        if retry_count > 0:
            print(f"   🔄 LOOP    - Researcher retried {retry_count} times")
        
        print("\n🎉 JAWIR OS ReAct workflow executed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_react_direct())
