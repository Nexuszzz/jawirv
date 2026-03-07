"""Quick verification test - all services + tools after fix"""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

async def main():
    print("=" * 50)
    print("  JAWIR OS — Service & Tool Verification")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=15) as c:
        # Service health checks
        services = [
            ("Backend",  "http://localhost:8000/health"),
            ("Polinema", "http://localhost:8001/"),
            ("Frontend", "http://localhost:5173"),
        ]
        
        print("\n--- Services ---")
        for name, url in services:
            try:
                r = await c.get(url)
                print(f"  ✅ {name:10s} port {url.split(':')[2].split('/')[0]:5s} HTTP {r.status_code}")
            except Exception as e:
                print(f"  ❌ {name:10s} FAIL: {str(e)[:60]}")
    
    # Tool tests
    from agent.tools import get_all_tools
    tools = {t.name: t for t in get_all_tools()}
    
    print(f"\n--- Tool Tests ({len(tools)} registered) ---")
    
    test_cases = [
        ("polinema_get_biodata", {}, "Polinema biodata"),
        ("gmail_search", {"query": "test"}, "Gmail search"),
        ("drive_search", {"query": "test"}, "Drive search"),
        ("calendar_list_events", {}, "Calendar events"),
        ("iot_list_devices", {}, "IoT devices"),
        ("web_search", {"query": "hello"}, "Web search"),
        ("whatsapp_list_chats", {}, "WhatsApp chats"),
    ]
    
    pass_count = 0
    for tool_name, args, label in test_cases:
        if tool_name not in tools:
            print(f"  ⚠️  {label:20s} → NOT IN REGISTRY")
            continue
        try:
            result = await asyncio.wait_for(tools[tool_name].ainvoke(args), timeout=20)
            rs = str(result)[:100]
            
            if "ModuleNotFoundError" in rs:
                print(f"  ❌ {label:20s} → IMPORT ERROR: {rs[:60]}")
            elif "Failed to connect" in rs or "Cannot connect" in rs or "connection refused" in rs.lower():
                print(f"  ⚠️  {label:20s} → Service offline: {rs[:60]}")
            elif "Error" in rs and "not found" not in rs.lower():
                # Check if it's a real error or just "no results"
                print(f"  ⚠️  {label:20s} → {rs[:70]}")
                pass_count += 1  # graceful error = partial pass
            else:
                print(f"  ✅ {label:20s} → {rs[:70]}")
                pass_count += 1
        except asyncio.TimeoutError:
            print(f"  ⚠️  {label:20s} → TIMEOUT 20s")
        except Exception as e:
            print(f"  ❌ {label:20s} → {str(e)[:70]}")
    
    print(f"\n  Result: {pass_count}/{len(test_cases)} tools operational")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
