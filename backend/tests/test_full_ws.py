#!/usr/bin/env python
"""
FULL INTEGRATION TEST - All Tools via WebSocket
"""

import asyncio
import json
import websockets
import time


async def test_ws(query: str, test_name: str, timeout: int = 60):
    """Test single query via WebSocket."""
    uri = "ws://localhost:8000/ws/chat"
    start = time.time()
    
    try:
        async with websockets.connect(uri, ping_timeout=timeout) as ws:
            # Send message
            msg = {"type": "user_message", "data": {"content": query}}
            await ws.send(json.dumps(msg))
            
            # Wait for response
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    data = json.loads(response)
                    
                    if data.get("type") == "agent_response":
                        elapsed = time.time() - start
                        content = data.get("data", {}).get("content", "")[:300]
                        return True, elapsed, content
                    elif data.get("type") == "error":
                        return False, time.time() - start, data.get("data", {}).get("message", "Error")
                except asyncio.TimeoutError:
                    return False, timeout, "Timeout"
    except Exception as e:
        return False, time.time() - start, str(e)


async def main():
    print("=" * 70)
    print("🧪 JAWIR OS - FULL INTEGRATION TEST (WebSocket)")
    print("=" * 70)
    
    tests = [
        # Basic
        ("Halo, siapa kamu?", "Chat Biasa", 30),
        
        # Web Search
        ("Cari info tentang Python 3.13", "Web Search", 30),
        
        # Python Code
        ("Hitung 2 pangkat 100 pakai Python", "Python Exec", 30),
        
        # Desktop
        ("Buka notepad", "Open App", 30),
        
        # Google Workspace - Gmail
        ("List label gmail saya", "Gmail Labels", 60),
        
        # Google Workspace - Drive
        ("List file di Google Drive saya", "Drive List", 60),
        
        # Google Workspace - Calendar
        ("List kalender Google saya", "Calendar List", 60),
        
        # Google Workspace - Sheets
        ("Buat spreadsheet baru dengan nama JAWIR WS Test", "Sheets Create", 60),
    ]
    
    results = []
    
    for query, name, timeout in tests:
        print(f"\n🔄 {name}...")
        print(f"   Query: {query}")
        
        ok, elapsed, content = await test_ws(query, name, timeout)
        
        if ok:
            print(f"   ✅ PASS ({elapsed:.1f}s)")
            print(f"   Response: {content[:150]}...")
        else:
            print(f"   ❌ FAIL ({elapsed:.1f}s)")
            print(f"   Error: {content[:150]}")
        
        results.append((name, ok, elapsed))
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    
    for name, ok, elapsed in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name} ({elapsed:.1f}s)")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} tests failed")


if __name__ == "__main__":
    asyncio.run(main())
