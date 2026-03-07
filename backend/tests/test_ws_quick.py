"""
==============================================================================
JAWIR OS - Quick WebSocket Test
==============================================================================
Simple test that connects to running server and sends a message.
Make sure server is running FIRST: 
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
==============================================================================
"""

import asyncio
import json
import sys
import os
import time

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_single_query(message: str, timeout: int = 120):
    """Test a single query via WebSocket."""
    import websockets
    
    print(f"\n{'='*60}")
    print(f"Testing: {message}")
    print("-" * 60)
    
    start = time.time()
    
    try:
        async with websockets.connect(
            "ws://localhost:8000/ws/chat",
            ping_interval=20,
            ping_timeout=40,
        ) as ws:
            # Send message with correct format: type=user_message, data.content
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": message
                }
            }))
            
            full_response = ""
            tool_calls = []
            
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    data = json.loads(raw)
                    
                    msg_type = data.get("type", "")
                    
                    if msg_type == "stream":
                        chunk = data.get("chunk", "")
                        full_response += chunk
                        print(chunk, end="", flush=True)
                    
                    elif msg_type == "tool_call":
                        tool_name = data.get("tool", "")
                        tool_calls.append(tool_name)
                        print(f"\n[TOOL: {tool_name}]", flush=True)
                    
                    elif msg_type == "status":
                        status = data.get("message", "")
                        print(f"\n[STATUS: {status}]", flush=True)
                    
                    elif msg_type == "error":
                        error = data.get("message", "")
                        print(f"\n[ERROR: {error}]")
                        return False
                    
                    elif msg_type == "agent_response":
                        # Final response from agent
                        content = data.get("content", "")
                        print(f"\n{content}")
                        break
                    
                    elif msg_type in ("done", "end"):
                        break
                    
                except asyncio.TimeoutError:
                    print(f"\n[TIMEOUT after {time.time()-start:.1f}s]")
                    return False
            
            print(f"\n\n✅ Completed in {time.time()-start:.1f}s")
            if tool_calls:
                print(f"   Tools used: {tool_calls}")
            return True
                
    except ConnectionRefusedError:
        print("❌ Server not running on localhost:8000")
        print("   Start it first: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Halo JAWIR, apa kabar?"
    
    success = asyncio.run(test_single_query(query))
    sys.exit(0 if success else 1)
