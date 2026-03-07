#!/usr/bin/env python
"""Debug WebSocket connection"""

import asyncio
import json
import websockets
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def debug_ws():
    uri = "ws://localhost:8000/ws/chat"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri, ping_timeout=30) as ws:
            print("Connected!")
            
            # Send message
            msg = {"type": "user_message", "data": {"content": "Halo"}}
            print(f"Sending: {msg}")
            await ws.send(json.dumps(msg))
            
            # Receive all responses
            print("Waiting for response...")
            for i in range(10):  # Max 10 messages
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(response)
                    print(f"Received [{i}]: type={data.get('type')}")
                    print(f"  Full data: {json.dumps(data, indent=2)[:500]}")
                    
                    if data.get("type") == "agent_response":
                        print("\n=== AGENT RESPONSE ===")
                        content = data.get("data", {}).get("content", "")
                        print(f"Content: '{content}'")
                        break
                except asyncio.TimeoutError:
                    print(f"Timeout after message {i}")
                    break
                    
    except ConnectionRefusedError:
        print("ERROR: Connection refused - is server running?")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(debug_ws())
