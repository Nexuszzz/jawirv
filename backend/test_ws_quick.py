import asyncio
import websockets
import json

async def test():
    uri = "ws://127.0.0.1:8000/ws/chat"
    try:
        async with websockets.connect(uri, open_timeout=5) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"[1] Connection: type={data.get('type')}")
            
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {"content": "halo", "session_id": "test123"}
            }))
            
            for i in range(5):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=15)
                    data = json.loads(msg)
                    t = data.get("type", "?")
                    c = str(data.get("content", data.get("message", "?")))[:100]
                    print(f"[{i+2}] {t}: {c}")
                    if t in ("agent_response", "error"):
                        break
                except asyncio.TimeoutError:
                    print(f"[{i+2}] TIMEOUT")
                    break
            print("DONE")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

asyncio.run(test())
