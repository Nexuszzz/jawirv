"""Quick test for WebSocket connection"""
import asyncio
import websockets
import json

async def test():
    print('Connecting to ws://localhost:8000/ws/chat...')
    try:
        ws = await asyncio.wait_for(
            websockets.connect('ws://localhost:8000/ws/chat', ping_interval=None),
            timeout=10
        )
        print('Connected!')
        
        await ws.send(json.dumps({'type': 'user_message', 'data': {'content': 'halo jawir'}}))
        print('Sent message')
        
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
                data = json.loads(msg)
                msg_type = data.get("type", "")
                print(f'Received: {msg_type}')
                print(f'  Full data: {json.dumps(data, indent=2)[:500]}')
                if msg_type == "status":
                    print(f'  Status: {data.get("data", {}).get("status", "")}')
                    print(f'  Message: {data.get("data", {}).get("message", "")}')
                elif msg_type == "response":
                    print(f'  Content: {data.get("content", "")[:200]}')
                    break
                elif msg_type == "done":
                    break
                elif msg_type == "error":
                    print(f'  Error: {data.get("error", "NO ERROR FIELD")}')
                    print(f'  Message: {data.get("message", "NO MESSAGE FIELD")}')
                    print(f'  Data: {data.get("data", "NO DATA FIELD")}')
                    break
            except asyncio.TimeoutError:
                print('Timeout waiting for response')
                break
        await ws.close()
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
