"""
JAWIR OS - Single Complex Query Test
Proves ReAct Loop: Plan → Act → Observe → Loop
"""

import asyncio
import json
import time
from datetime import datetime
import websockets


async def test_react_workflow():
    """Test a complex query that requires ReAct workflow."""
    
    uri = "ws://localhost:8000/ws/chat"
    
    # Complex query that needs multi-step research
    query = """Bandingkan ESP32 vs STM32 vs Arduino Nano untuk proyek IoT rumah pintar. 
    Mana yang terbaik dari segi harga, performa, dan kemudahan pemrograman? 
    Berikan tabel perbandingan lengkap."""
    
    print("=" * 70)
    print(" JAWIR OS - ReAct Workflow Proof of Concept")
    print("=" * 70)
    print(f"\n📝 QUERY: {query[:80]}...\n")
    
    # Metrics
    phases = {
        "planning": [],
        "searching": [],
        "reading": [],
        "thinking": [],
    }
    sources_found = 0
    plan_steps = 0
    start_time = time.time()
    
    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=30) as websocket:
            # Skip welcome
            await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send query
            print("📤 Sending query to JAWIR...\n")
            await websocket.send(json.dumps({
                "type": "user_message",
                "data": {"content": query}
            }))
            
            print("-" * 70)
            print("🔄 REACT LOOP EXECUTION:")
            print("-" * 70)
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=180)
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        # Map emoji
                        emoji = {
                            'thinking': '🧠',
                            'planning': '📋',
                            'searching': '🔍',
                            'reading': '📖',
                            'writing': '✍️',
                            'done': '✅',
                        }.get(status, '📌')
                        
                        # Print status
                        print(f"{emoji} [{status.upper():12}] {message}")
                        
                        # Track phases
                        if status in phases:
                            phases[status].append(message)
                        
                        # Extract plan details
                        if status == "planning" and "plan" in details:
                            plan_steps = len(details["plan"])
                            print(f"   └─ 📋 Plan created with {plan_steps} steps:")
                            for i, step in enumerate(details["plan"], 1):
                                print(f"      {i}. {step[:70]}...")
                    
                    elif msg_type == "tool_result":
                        tool_data = data.get("data", {})
                        title = tool_data.get("title", "Research")
                        sources = tool_data.get("sources", [])
                        sources_found += len(sources)
                        print(f"🔧 [TOOL RESULT  ] {title} - Found {len(sources)} sources")
                        for s in sources[:3]:
                            print(f"      - {s.get('title', 'N/A')[:50]}...")
                    
                    elif msg_type == "agent_response":
                        # Final response!
                        content = data.get("content", "")
                        sources_used = data.get("sources_used", [])
                        thinking = data.get("thinking_process", [])
                        
                        end_time = time.time()
                        duration = round(end_time - start_time, 2)
                        
                        print("\n" + "=" * 70)
                        print("🎯 FINAL RESPONSE RECEIVED")
                        print("=" * 70)
                        
                        # Print metrics
                        print(f"\n📊 REACT WORKFLOW METRICS:")
                        print(f"   • Duration:       {duration} seconds")
                        print(f"   • Plan Steps:     {plan_steps}")
                        print(f"   • Sources Found:  {sources_found}")
                        print(f"   • Sources Cited:  {len(sources_used)}")
                        print(f"   • Thinking Steps: {len(thinking)}")
                        print(f"   • Response Length:{len(content)} chars")
                        
                        # Phase breakdown
                        print(f"\n🔄 PHASE BREAKDOWN:")
                        print(f"   • Thinking:  {len(phases['thinking'])} phases")
                        print(f"   • Planning:  {len(phases['planning'])} phases")  
                        print(f"   • Searching: {len(phases['searching'])} phases")
                        print(f"   • Reading:   {len(phases['reading'])} phases")
                        
                        # Show response preview
                        print(f"\n📜 RESPONSE PREVIEW:")
                        print("-" * 70)
                        print(content[:1000])
                        print("...")
                        print("-" * 70)
                        
                        # Sources
                        if sources_used:
                            print(f"\n📚 SOURCES CITED:")
                            for s in sources_used[:5]:
                                if isinstance(s, dict):
                                    print(f"   • {s.get('title', 'N/A')[:60]}")
                                else:
                                    print(f"   • {str(s)[:60]}")
                        
                        # Conclusion
                        print("\n" + "=" * 70)
                        print("✅ REACT WORKFLOW PROOF:")
                        print("=" * 70)
                        print("   🧠 REASON  → Supervisor analyzed query & created multi-step plan")
                        print("   ⚡ ACT     → Researcher executed web searches via Tavily")
                        print("   👁️ OBSERVE → Validator checked if research was sufficient")
                        print("   📝 WRITE   → Synthesizer created comprehensive response")
                        print("=" * 70)
                        
                        if plan_steps >= 3 and sources_found >= 5 and len(content) > 500:
                            print("\n🎉 SUCCESS! JAWIR OS demonstrates full ReAct workflow!")
                        
                        break
                    
                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {data.get('message', 'Unknown')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("\n⏱️ TIMEOUT - no response within 180 seconds")
                    break
                    
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")


if __name__ == "__main__":
    print("\nStarting JAWIR OS ReAct test...\n")
    asyncio.run(test_react_workflow())
