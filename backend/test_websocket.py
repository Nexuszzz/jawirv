"""
Test WebSocket connection and message handling.
"""

import asyncio
import json
import websockets


async def test_websocket():
    """Test WebSocket communication with JAWIR OS backend."""
    uri = "ws://localhost:8000/ws/chat"
    
    print("🔌 Connecting to WebSocket...")
    
    async with websockets.connect(uri) as websocket:
        print("✅ Connected!")
        
        # Send a simple test message
        test_message = {
            "type": "user_message",
            "data": {
                "content": "What is ESP32?"
            }
        }
        
        print(f"📤 Sending: {test_message}")
        await websocket.send(json.dumps(test_message))
        
        # Receive responses
        print("\n📥 Receiving responses:")
        print("-" * 50)
        
        while True:
            try:
                response = await asyncio.wait_for(
                    websocket.recv(), 
                    timeout=60.0  # 60 second timeout
                )
                data = json.loads(response)
                msg_type = data.get("type", "unknown")
                
                if msg_type == "status":
                    status = data.get("data", {}).get("status", "")
                    message = data.get("data", {}).get("message", "")
                    print(f"📊 STATUS: {status} - {message}")
                    
                elif msg_type == "thinking":
                    content = data.get("data", {}).get("content", "")
                    print(f"🤔 THINKING: {content[:100]}...")
                    
                elif msg_type == "tool_result":
                    title = data.get("data", {}).get("title", "")
                    print(f"🔧 TOOL: {title}")
                    
                elif msg_type == "agent_message":
                    content = data.get("data", {}).get("content", "")
                    print(f"\n🤖 RESPONSE:\n{content[:500]}...")
                    print("\n✅ Test completed successfully!")
                    break
                    
                elif msg_type == "error":
                    error = data.get("data", {}).get("message", "")
                    print(f"❌ ERROR: {error}")
                    break
                    
                else:
                    print(f"📨 {msg_type}: {data}")
                    
            except asyncio.TimeoutError:
                print("⏱️ Timeout waiting for response")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break


if __name__ == "__main__":
    print("=" * 50)
    print("JAWIR OS WebSocket Integration Test")
    print("=" * 50)
    asyncio.run(test_websocket())
