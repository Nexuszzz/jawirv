import asyncio
import websockets
import json

async def test_chat():
    uri = 'ws://localhost:8000/ws/chat'
    async with websockets.connect(uri) as ws:
        # Receive welcome message
        welcome = await asyncio.wait_for(ws.recv(), timeout=5)
        print("Welcome:", welcome[:200])
        
        # Send a chat message
        msg = json.dumps({
            "type": "user_message",
            "data": {
                "content": "halo jawir, siapa kamu?",
                "session_id": "test-session-123"
            }
        })
        await ws.send(msg)
        print("Sent message")
        
        # Receive responses (wait up to 30 seconds)
        for i in range(20):
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(response)
                msg_type = data.get("type", "unknown")
                print("Response " + str(i+1) + " type=" + msg_type + ": " + str(data)[:300])
                if msg_type == "agent_response":
                    break
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break

asyncio.run(test_chat())
