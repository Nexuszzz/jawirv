"""Test with queries that TRULY need tools - not something model can answer from knowledge."""
import asyncio
import websockets
import json

async def test_query(query: str, desc: str):
    print(f"\n{'='*60}")
    print(f"📝 {desc}")
    print(f"Query: {query}")
    print('='*60)
    
    async with websockets.connect('ws://localhost:8000/ws/chat', ping_interval=None) as ws:
        await ws.send(json.dumps({'type': 'user_message', 'data': {'content': query}}))
        
        tool_actions = []
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=90)
                data = json.loads(msg)
                msg_type = data.get("type", "")
                
                if msg_type == "agent_status":
                    status = data.get("status", "")
                    message = data.get("message", "")
                    details = data.get("details", {})
                    
                    if status == "thinking":
                        print(f"  💭 {message}")
                    elif status == "executing_tool":
                        tool_name = details.get("tool_name", "?")
                        tool_actions.append(tool_name)
                        print(f"  🔧 Executing: {tool_name}")
                    elif status == "tool_completed":
                        print(f"  ✅ Tool completed")
                    elif status == "tool_error":
                        print(f"  ❌ Tool error: {details.get('error', '')[:50]}")
                        
                elif msg_type == "agent_response":
                    content = data.get("content", "")
                    thinking = data.get("thinking_process", [])
                    
                    print(f"\n  📊 Response:")
                    print(f"     Thinking: {thinking}")
                    print(f"     Tools streamed: {tool_actions}")
                    print(f"     Content: {content[:200]}...")
                    break
                    
            except asyncio.TimeoutError:
                print("  ⏰ Timeout!")
                break

async def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║      🧪 Test Queries That TRULY Need Tools                    ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # These queries cannot be answered without external data
    tests = [
        # File system operation - needs actual execution
        ("Jalankan Python: import os; print(os.getcwd())", "Print current directory"),
        
        # Current time - cannot be known from training
        ("Jalankan Python: import datetime; print(datetime.datetime.now())", "Print current time"),
        
        # Google Drive - needs API
        ("Cek isi Google Drive saya dan beri tahu nama file terbaru", "List Drive Files"),
    ]
    
    for query, desc in tests:
        await test_query(query, desc)
        await asyncio.sleep(2)
    
    print("\n✅ Tests complete!")

if __name__ == "__main__":
    asyncio.run(main())
