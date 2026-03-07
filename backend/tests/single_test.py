"""Quick single test with full output"""
import asyncio
import websockets
import json

async def test():
    print("Connecting...")
    async with websockets.connect('ws://localhost:8000/ws/chat', ping_interval=None) as ws:
        print("Connected! Sending message...")
        await ws.send(json.dumps({'type': 'user_message', 'data': {'content': 'Jalankan kode Python: print(2**100)'}}))
        print("Message sent. Waiting for response...")
        
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
                data = json.loads(msg)
                msg_type = data.get("type", "")
                print(f"\n=== {msg_type.upper()} ===")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
                if msg_type == 'agent_response':
                    break
            except asyncio.TimeoutError:
                print("Timeout!")
                break

if __name__ == "__main__":
    asyncio.run(test())
