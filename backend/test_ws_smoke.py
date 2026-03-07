"""Quick WebSocket smoke test for JAWIR OS"""
import asyncio
import json
import websockets

async def test_websocket():
    try:
        async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
            # Get connection message
            msg = await ws.recv()
            data = json.loads(msg)
            print(f"✅ Connected: {data.get('status')}")
            print(f"   Message: {data.get('message', '')[:50]}...")
            
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            pong = await asyncio.wait_for(ws.recv(), timeout=5)
            pong_data = json.loads(pong)
            print(f"✅ Ping/Pong: {pong_data.get('type')}")
            
            print("\n🎉 WebSocket smoke test PASSED!")
            return True
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket())
