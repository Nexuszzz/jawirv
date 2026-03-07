#!/usr/bin/env python
"""
JAWIR CLI Quick Test - Send multiple prompts
"""

import asyncio
import json
import websockets
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def send_message(message: str, timeout: int = 60) -> str:
    """Send message to JAWIR via WebSocket."""
    uri = "ws://localhost:8000/ws/chat"
    
    try:
        async with websockets.connect(uri, ping_timeout=timeout) as ws:
            msg = {"type": "user_message", "data": {"content": message}}
            await ws.send(json.dumps(msg))
            
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    data = json.loads(response)
                    
                    if data.get("type") == "agent_response":
                        # Content is directly in data, not data.data.content
                        return data.get("content", "") or data.get("data", {}).get("content", "")
                    elif data.get("type") == "error":
                        return f"Error: {data.get('message', '')}"
                except asyncio.TimeoutError:
                    return "Timeout"
    except Exception as e:
        return f"Error: {e}"


async def main():
    prompts = [
        "Siapa kamu?",
        "Hitung 123 * 456 pakai Python",
        "List label gmail saya",
        "List file di drive saya",
        "Buka notepad",
    ]
    
    print("=" * 60)
    print("JAWIR CLI - Multiple Prompts Test")
    print("=" * 60)
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] {prompt}")
        print("-" * 40)
        response = await send_message(prompt)
        # Show first 300 chars
        print(response[:300] if response else "(empty)")
        print()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
