"""
Simple WebSocket test for JAWIR OS.
"""
import asyncio
import json
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def test_websocket():
    """Test WebSocket communication."""
    import websockets
    
    uri = "ws://localhost:8000/ws/chat"
    
    print("[*] Connecting to WebSocket...")
    
    async with websockets.connect(uri) as ws:
        print("[+] Connected!")
        
        # Send message
        msg = {
            "type": "user_message",
            "data": {"content": "Apa itu LED?"}
        }
        
        print(f"[>] Sending: {msg['data']['content']}")
        await ws.send(json.dumps(msg))
        
        # Receive responses
        print("\n[<] Receiving responses:")
        print("-" * 50)
        
        while True:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=60.0)
                data = json.loads(response)
                msg_type = data.get("type", "unknown")
                
                if msg_type == "agent_status":
                    status = data.get("status", "")
                    message = data.get("message", "")
                    print(f"[STATUS] {status}: {message}")
                    
                elif msg_type == "thinking":
                    content = data.get("data", {}).get("content", "")[:80]
                    print(f"[THINKING] {content}...")
                    
                elif msg_type == "agent_response":
                    content = data.get("content", "")
                    print(f"\n[RESPONSE]\n{content[:800]}...")
                    print("\n[+] Test completed!")
                    break
                    
                elif msg_type == "error":
                    print(f"[ERROR] {data.get('message', '')}")
                    break
                    
            except asyncio.TimeoutError:
                print("[!] Timeout")
                break

if __name__ == "__main__":
    print("=" * 50)
    print("JAWIR OS - WebSocket Test")
    print("=" * 50)
    asyncio.run(test_websocket())
