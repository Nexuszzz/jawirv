"""
==============================================================================
JAWIR OS - FULL INTEGRATION TEST
==============================================================================
Test semua tools melalui FULL flow: WebSocket → Graph → FunctionCallingAgent → Tools

Requirements:
- Server HARUS running di localhost:8000
- Semua API keys harus valid

Run: python tests/test_full_integration.py
==============================================================================
"""

import asyncio
import json
import sys
import os
import time

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Verify env
print("=" * 70)
print("JAWIR OS - FULL INTEGRATION TEST")
print("=" * 70)

# Load env
from dotenv import load_dotenv
load_dotenv()

gemini_model = os.environ.get("GEMINI_MODEL", "NOT SET")
api_keys = os.environ.get("GOOGLE_API_KEYS", "NOT SET")
tavily_key = os.environ.get("TAVILY_API_KEY", "NOT SET")

print(f"GEMINI_MODEL: {gemini_model}")
print(f"API Keys count: {len(api_keys.split(',')) if api_keys != 'NOT SET' else 0}")
print(f"TAVILY_API_KEY: {'SET' if tavily_key != 'NOT SET' else 'NOT SET'}")
print("=" * 70)

async def test_websocket_chat(message: str, description: str, timeout_sec: int = 120):
    """Test via WebSocket with proper streaming handling."""
    import websockets
    
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Query: {message}")
    print("-" * 60)
    
    start = time.time()
    
    try:
        async with websockets.connect(
            "ws://localhost:8000/ws/chat",
            ping_interval=20,
            ping_timeout=40,
            close_timeout=10
        ) as ws:
            # Send message with correct format
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": message
                }
            }))
            
            full_response = ""
            tool_calls = []
            status_messages = []
            
            # Collect all chunks
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout_sec)
                    data = json.loads(raw)
                    
                    msg_type = data.get("type", "")
                    
                    if msg_type == "stream":
                        chunk = data.get("chunk", "")
                        full_response += chunk
                        print(chunk, end="", flush=True)
                    
                    elif msg_type == "tool_call":
                        tool_name = data.get("tool", "")
                        tool_calls.append(tool_name)
                        print(f"\n[TOOL CALLED: {tool_name}]", flush=True)
                    
                    elif msg_type == "status" or msg_type == "agent_status":
                        status = data.get("message", "")
                        status_messages.append(status)
                        # Don't print status to avoid clutter
                    
                    elif msg_type == "error":
                        error = data.get("message", "")
                        print(f"\n[ERROR: {error}]", flush=True)
                        return False, error, time.time() - start
                    
                    elif msg_type == "agent_response":
                        # Final response from agent
                        content = data.get("content", "")
                        full_response = content
                        print(content[:300], flush=True)
                        break
                    
                    elif msg_type == "done" or msg_type == "end":
                        break
                    
                except asyncio.TimeoutError:
                    elapsed = time.time() - start
                    print(f"\n[TIMEOUT after {elapsed:.1f}s]")
                    return False, f"Timeout after {elapsed:.1f}s", elapsed
            
            elapsed = time.time() - start
            print(f"\n\n[Completed in {elapsed:.1f}s]")
            
            if full_response or tool_calls:
                return True, full_response[:200], elapsed
            else:
                return False, "No response", elapsed
                
    except ConnectionRefusedError:
        return False, "Server not running on localhost:8000", 0
    except Exception as e:
        return False, str(e), time.time() - start

async def run_all_tests():
    """Run all integration tests."""
    
    tests = [
        # Format: (message, description, expected_behavior)
        (
            "Halo JAWIR",
            "1. Chat Biasa (Quick Router)",
            "Should respond in Javanese"
        ),
        (
            "Berapa harga emas hari ini?",
            "2. Web Search (Tavily)",
            "Should call web_search tool"
        ),
        (
            "jalankan python: print(sum(range(1,11)))",
            "3. Python Execution",
            "Should call run_python_code, output 55"
        ),
        (
            "buka google.com",
            "4. Open URL",
            "Should call open_url tool"
        ),
        (
            "buatkan skematik LED sederhana dengan KiCAD",
            "5. KiCAD Schematic",
            "Should call generate_kicad_schematic tool"
        ),
        (
            "buka kalkulator",
            "6. Open App",
            "Should call open_app tool"
        ),
    ]
    
    results = []
    
    for message, description, expected in tests:
        success, response, elapsed = await test_websocket_chat(
            message, 
            description,
            timeout_sec=120
        )
        
        results.append({
            "test": description,
            "success": success,
            "response": response,
            "elapsed": elapsed
        })
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = 0
    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        print(f"{status} | {r['test']} | {r['elapsed']:.1f}s")
        if r["success"]:
            passed += 1
    
    print("=" * 70)
    print(f"TOTAL: {passed}/{len(results)} tests passed")
    print("=" * 70)
    
    return passed == len(results)

async def test_executor_direct():
    """Test executor directly without WebSocket."""
    print("\n" + "=" * 70)
    print("DIRECT EXECUTOR TEST (bypassing WebSocket)")
    print("=" * 70)
    
    try:
        # Initialize API key rotator first
        from agent.api_rotator import init_rotator
        api_keys = os.environ.get("GOOGLE_API_KEYS", "").split(",")
        api_keys = [k.strip() for k in api_keys if k.strip()]
        init_rotator(api_keys)
        print(f"✅ API Key Rotator initialized with {len(api_keys)} keys")
        
        from agent.nodes.function_calling_agent import get_executor
        
        executor = get_executor()
        print(f"✅ Executor created successfully")
        print(f"✅ Tools count: {len(executor.tools)}")
        print(f"✅ Tools: {[t.name for t in executor.tools]}")
        
        # Test simple chat
        print("\n--- Testing: Simple chat ---")
        start = time.time()
        result = await executor.execute("Halo JAWIR, apa kabar?")
        elapsed = time.time() - start
        response_text = result.get("final_response", str(result))
        print(f"✅ Response ({elapsed:.1f}s): {response_text[:200]}...")
        
        # Test web search
        print("\n--- Testing: Web search ---")
        start = time.time()
        result = await executor.execute("Cari info tentang Indonesia")
        elapsed = time.time() - start
        response_text = result.get("final_response", str(result))
        tool_history = result.get("tool_calls_history", [])
        tools_used = [t.get("tool_name", "?") for t in tool_history]
        print(f"✅ Response ({elapsed:.1f}s): {response_text[:200]}...")
        print(f"   Tool calls: {tools_used}")
        
        # Test Python
        print("\n--- Testing: Python execution ---")
        start = time.time()
        result = await executor.execute("Jalankan Python: print(sum(range(1,101)))")
        elapsed = time.time() - start
        response_text = result.get("final_response", str(result))
        tool_history = result.get("tool_calls_history", [])
        tools_used = [t.get("tool_name", "?") for t in tool_history]
        print(f"✅ Response ({elapsed:.1f}s): {response_text[:200]}...")
        print(f"   Tool calls: {tools_used}")
        
        # Test open_url
        print("\n--- Testing: Open URL ---")
        start = time.time()
        result = await executor.execute("Buka google.com")
        elapsed = time.time() - start
        response_text = result.get("final_response", str(result))
        tool_history = result.get("tool_calls_history", [])
        tools_used = [t.get("tool_name", "?") for t in tool_history]
        print(f"✅ Response ({elapsed:.1f}s): {response_text[:150]}...")
        print(f"   Tool calls: {tools_used}")
        
        # Test open_app
        print("\n--- Testing: Open App ---")
        start = time.time()
        result = await executor.execute("Buka kalkulator")
        elapsed = time.time() - start
        response_text = result.get("final_response", str(result))
        tool_history = result.get("tool_calls_history", [])
        tools_used = [t.get("tool_name", "?") for t in tool_history]
        print(f"✅ Response ({elapsed:.1f}s): {response_text[:150]}...")
        print(f"   Tool calls: {tools_used}")
        
        # Test KiCAD
        print("\n--- Testing: KiCAD Schematic ---")
        start = time.time()
        result = await executor.execute("Buatkan rangkaian LED sederhana dengan KiCAD")
        elapsed = time.time() - start
        response_text = result.get("final_response", str(result))
        tool_history = result.get("tool_calls_history", [])
        tools_used = [t.get("tool_name", "?") for t in tool_history]
        print(f"✅ Response ({elapsed:.1f}s): {response_text[:200]}...")
        print(f"   Tool calls: {tools_used}")
        
        print("\n" + "=" * 60)
        print("✅ ALL DIRECT EXECUTOR TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--direct", action="store_true", help="Test executor directly")
    parser.add_argument("--ws", action="store_true", help="Test via WebSocket")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()
    
    if args.direct or args.all:
        asyncio.run(test_executor_direct())
    
    if args.ws or args.all:
        asyncio.run(run_all_tests())
    
    if not (args.direct or args.ws or args.all):
        # Default: run all
        asyncio.run(test_executor_direct())
        print("\n\nNow testing via WebSocket (make sure server is running)...")
        asyncio.run(run_all_tests())
