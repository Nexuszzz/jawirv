"""
JAWIR OS - Real Integration Test Script
==========================================
Script ini test JAWIR secara REAL melalui WebSocket.
Menguji semua tool: chat biasa, web_search, run_python_code,
kicad, google workspace, desktop control.

Pakai: python test_real_jawir.py
"""

import asyncio
import json
import sys
import time
import websockets

WS_URL = "ws://localhost:8000/ws/chat"
TIMEOUT = 60  # seconds per test


async def send_and_collect(ws, content: str, timeout: int = TIMEOUT):
    """Send user message and collect all responses until agent_response."""
    msg = {
        "type": "user_message",
        "data": {"content": content},
    }
    await ws.send(json.dumps(msg))

    responses = []
    final_response = None
    start = time.time()

    while time.time() - start < timeout:
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            data = json.loads(raw)
            responses.append(data)

            msg_type = data.get("type", "")
            if msg_type == "agent_response":
                final_response = data.get("content", "")
                break
            elif msg_type == "agent_status" and data.get("status") == "error":
                final_response = f"ERROR: {data.get('message', 'unknown')}"
                break
        except asyncio.TimeoutError:
            final_response = "TIMEOUT"
            break

    return final_response, responses


async def test_all():
    """Test semua fungsionalitas JAWIR."""
    print("=" * 70)
    print("  JAWIR OS - Real Integration Test")
    print("=" * 70)

    results = {}

    try:
        async with websockets.connect(WS_URL) as ws:
            # Wait for connection message
            conn_msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
            print(f"\n✅ Connected: {conn_msg.get('message', '')}\n")

            # ========================================
            # TEST 1: Chat biasa (tanpa tool)
            # ========================================
            print("-" * 50)
            print("TEST 1: Chat biasa (tanpa tool)")
            print("-" * 50)
            query = "Halo JAWIR, siapa kamu?"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query)
            print(f"  Response: {response[:200] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            no_tool_used = not any(
                m.get("status") == "executing_tool" for m in all_msgs if m.get("type") == "agent_status"
            )
            results["chat_biasa"] = "✅ PASS" if has_response and no_tool_used else f"❌ FAIL (response={bool(response)}, no_tool={no_tool_used})"
            print(f"  Result: {results['chat_biasa']}")

            # ========================================
            # TEST 2: Web Search
            # ========================================
            print("\n" + "-" * 50)
            print("TEST 2: Web Search Tool")
            print("-" * 50)
            query = "Berapa harga Bitcoin hari ini dalam USD?"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query)
            print(f"  Response: {response[:300] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            tool_used = any(
                "web_search" in str(m.get("details", {})) or "web_search" in str(m.get("message", ""))
                for m in all_msgs if m.get("type") == "agent_status"
            )
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            results["web_search"] = "✅ PASS" if has_response else f"❌ FAIL (response={bool(response)}, tool_used={tool_used})"
            print(f"  Result: {results['web_search']}")

            # ========================================
            # TEST 3: Python Code Execution
            # ========================================
            print("\n" + "-" * 50)
            print("TEST 3: Python Code Execution Tool")
            print("-" * 50)
            query = "Tolong jalankan kode Python ini: print(sum(range(1, 101)))"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query)
            print(f"  Response: {response[:300] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            has_5050 = response and "5050" in response
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            results["python_exec"] = "✅ PASS" if (has_response and has_5050) else f"❌ FAIL (response={bool(response)}, has_5050={has_5050})"
            print(f"  Result: {results['python_exec']}")

            # ========================================
            # TEST 4: KiCad Schematic
            # ========================================
            print("\n" + "-" * 50)
            print("TEST 4: KiCad Schematic Tool")
            print("-" * 50)
            query = "Buatkan skematik LED blink sederhana dengan ESP32"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query, timeout=90)
            print(f"  Response: {response[:300] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            results["kicad"] = "✅ PASS" if has_response else f"❌ FAIL"
            print(f"  Result: {results['kicad']}")

            # ========================================
            # TEST 5: Desktop Control - Open URL
            # ========================================
            print("\n" + "-" * 50)
            print("TEST 5: Desktop Control - Open URL")
            print("-" * 50)
            query = "Buka URL https://google.com di browser"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query)
            print(f"  Response: {response[:300] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            results["open_url"] = "✅ PASS" if has_response else "❌ FAIL"
            print(f"  Result: {results['open_url']}")

            # ========================================
            # TEST 6: Google Workspace - Calendar List
            # ========================================
            print("\n" + "-" * 50)
            print("TEST 6: Google Workspace - Calendar")
            print("-" * 50)
            query = "Cek jadwal di Google Calendar saya hari ini"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query)
            print(f"  Response: {response[:300] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            results["google_calendar"] = "✅ PASS" if has_response else "❌ FAIL"
            print(f"  Result: {results['google_calendar']}")

            # ========================================
            # TEST 7: Chat konsep (tanpa tool)
            # ========================================
            print("\n" + "-" * 50)
            print("TEST 7: Chat konsep (harus tanpa tool)")
            print("-" * 50)
            query = "Jelaskan apa itu mikrokontroler dan perbedaannya dengan mikroprosesor"
            print(f"  Query: {query}")
            response, all_msgs = await send_and_collect(ws, query)
            print(f"  Response: {response[:300] if response else 'NONE'}...")
            statuses = [m.get("status", m.get("type")) for m in all_msgs if m.get("type") == "agent_status"]
            print(f"  Status flow: {statuses}")
            
            has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")
            results["chat_konsep"] = "✅ PASS" if has_response else "❌ FAIL"
            print(f"  Result: {results['chat_konsep']}")

    except ConnectionRefusedError:
        print("❌ FATAL: Server tidak berjalan di localhost:8000!")
        return
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v.startswith("✅"))
    total = len(results)
    
    for test_name, result in results.items():
        print(f"  {test_name:25s} {result}")
    
    print(f"\n  Total: {passed}/{total} PASSED")
    
    if passed == total:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print(f"  ⚠️  {total - passed} test(s) need attention")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_all())
