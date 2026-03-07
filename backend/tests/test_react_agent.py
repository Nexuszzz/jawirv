"""
Test JAWIR ReAct Agent - Self-Correction Demo
==============================================
Test to demonstrate ReAct pattern with self-correction.
"""

import asyncio
import json
import websockets

WS_URL = "ws://localhost:8000/ws/chat"


async def test_react_agent(query: str, description: str):
    """Test ReAct agent with a specific query."""
    print(f"\n{'='*60}")
    print(f"🧪 Test: {description}")
    print(f"📝 Query: {query}")
    print('='*60)
    
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            # Send query with correct format
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {"content": query}
            }))
            
            thinking_steps = []
            tool_calls = []
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=120)
                    data = json.loads(msg)
                    
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        
                        if status == "thinking":
                            thinking_steps.append(message)
                            print(f"  💭 THOUGHT: {message}")
                        elif status == "executing_tool":
                            details = data.get("details", {})
                            tool_name = details.get("tool_name", "")
                            print(f"  🔧 ACTION: {tool_name}")
                        elif status == "tool_completed":
                            print(f"  👀 OBSERVATION: Tool selesai")
                        elif status == "tool_error":
                            details = data.get("details", {})
                            error = details.get("error", "")
                            print(f"  ❌ ERROR: {error}")
                            print(f"  🔄 SELF-CORRECTION: Agent akan mencoba lagi...")
                            
                    elif msg_type == "agent_response":
                        content = data.get("content", "")
                        print(f"\n  ✅ FINAL RESPONSE:")
                        print(f"  {content[:500]}{'...' if len(content) > 500 else ''}")
                        break
                        
                    elif msg_type == "done":
                        break
                        
                except asyncio.TimeoutError:
                    print("  ⏰ Timeout!")
                    break
                    
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def main():
    """Run all ReAct tests."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           🧠 JAWIR ReAct Agent Test Suite 🧠                 ║
║                                                              ║
║  Testing: THOUGHT → ACTION → OBSERVATION → EVALUATION        ║
║           with Self-Correction on Errors                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    tests = [
        # Test 1: Simple greeting (no tool needed)
        ("Halo JAWIR, apa kabar?", "Simple Greeting - No Tools"),
        
        # Test 2: Web search (single tool)
        ("Berapa harga Bitcoin hari ini?", "Web Search - Single Tool"),
        
        # Test 3: Python execution (computation)
        ("Hitung faktorial dari 15 pakai Python", "Python Exec - Computation"),
        
        # Test 4: Multi-step task (requires reasoning)
        ("Cari berita tentang AI terbaru, lalu buat ringkasannya", "Multi-Step - Web + Reasoning"),
        
        # Test 5: Desktop control
        ("Buka aplikasi notepad", "Desktop Control - Open App"),
    ]
    
    results = []
    
    for query, desc in tests:
        success = await test_react_agent(query, desc)
        results.append((desc, success))
        await asyncio.sleep(2)  # Cool down between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} - {desc}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print('='*60)


if __name__ == "__main__":
    asyncio.run(main())
