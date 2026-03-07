"""
JAWIR OS - 10 Complex Multi-Tool Test Cases
=============================================
Tests ReAct loop streaming with various tool combinations.
Self-contained: starts server as subprocess, runs tests, stops server.

Run:
    cd backend
    python tests/test_10_cases_final.py
"""
import asyncio
import json
import time
import subprocess
import sys
import os
import threading

BACKEND_DIR = r"D:\expo\jawirv3\jawirv2\jawirv2\backend"
PYTHON = os.path.join(BACKEND_DIR, "venv_fresh", "Scripts", "python.exe")
WS_URL = "ws://localhost:8000/ws/chat"
TOTAL_TIMEOUT = 300  # 5 min per case max


# ============================================================
# 10 Test Cases
# ============================================================
TEST_CASES = [
    {
        "id": 1,
        "name": "Web Search + Docs Create",
        "query": "Cari info tentang ESP32 lalu buat dokumen Google Docs tentang ESP32",
        "min_tools": 2,
        "timeout": 180,
    },
    {
        "id": 2,
        "name": "Multiple Web Searches",
        "query": "Bandingkan Arduino Uno vs ESP32 vs Raspberry Pi dari segi harga, fitur, dan kegunaan",
        "min_tools": 1,
        "timeout": 120,
    },
    {
        "id": 3,
        "name": "Python Code Execution",
        "query": "Buatkan kode Python untuk menghitung faktorial dari 10, 15, dan 20 lalu jalankan",
        "min_tools": 1,
        "timeout": 120,
    },
    {
        "id": 4,
        "name": "Search + Summary",
        "query": "Cari informasi terbaru tentang AI dan machine learning lalu buat ringkasan singkat",
        "min_tools": 1,
        "timeout": 120,
    },
    {
        "id": 5,
        "name": "Docs + Content",
        "query": "Buatkan dokumen Google Docs berjudul 'Panduan Arduino untuk Pemula' yang berisi pengenalan Arduino, komponen dasar, dan contoh project sederhana",
        "min_tools": 1,
        "timeout": 120,
    },
    {
        "id": 6,
        "name": "Calendar Check",
        "query": "Tampilkan jadwal kalender saya untuk minggu ini",
        "min_tools": 1,
        "timeout": 90,
    },
    {
        "id": 7,
        "name": "Drive Search",
        "query": "Cari file di Google Drive saya yang berkaitan dengan Arduino",
        "min_tools": 1,
        "timeout": 90,
    },
    {
        "id": 8,
        "name": "Research Intensive",
        "query": "Cari info tentang sensor DHT22 dan cara menggunakannya dengan ESP32, termasuk wiring diagram dan kode contoh",
        "min_tools": 1,
        "timeout": 180,
    },
    {
        "id": 9,
        "name": "Multi-step Research + Docs",
        "query": "Cari informasi tentang protokol MQTT untuk IoT, lalu buat dokumen Google Docs yang berisi materi lengkap tentang MQTT untuk pemula",
        "min_tools": 2,
        "timeout": 180,
    },
    {
        "id": 10,
        "name": "Python + Search Combo",
        "query": "Buatkan kode Python untuk web scraping sederhana, jalankan hasilnya, dan cari informasi tentang best practices web scraping",
        "min_tools": 2,
        "timeout": 180,
    },
]


# ============================================================
# Server Management
# ============================================================
def _drain_stdout(proc, ready_event):
    """Drain server stdout to prevent buffer deadlock."""
    for line in iter(proc.stdout.readline, ''):
        line = line.rstrip()
        if "Uvicorn running" in line:
            ready_event.set()
    proc.stdout.close()


def start_server():
    """Start uvicorn as subprocess."""
    print("🚀 Starting JAWIR server...")
    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    ready_event = threading.Event()
    drain_thread = threading.Thread(target=_drain_stdout, args=(proc, ready_event), daemon=True)
    drain_thread.start()
    
    if not ready_event.wait(timeout=30):
        print("  ❌ Server failed to start!")
        return None
    
    print("  ✅ Server ready!")
    time.sleep(1)
    return proc


# ============================================================
# Test Runner
# ============================================================
async def run_single_test(case: dict) -> dict:
    """Run a single test case. Returns result dict."""
    import websockets
    
    test_id = case["id"]
    test_name = case["name"]
    query = case["query"]
    min_tools = case["min_tools"]
    timeout = case["timeout"]
    
    print(f"\n{'='*60}")
    print(f"  TEST {test_id}: {test_name}")
    print(f"{'='*60}")
    print(f"  Query: {query[:80]}...")
    
    start = time.time()
    result = {
        "id": test_id,
        "name": test_name,
        "success": False,
        "tools_used": [],
        "statuses": [],
        "has_response": False,
        "error": None,
        "duration": 0,
    }
    
    try:
        async with websockets.connect(
            WS_URL,
            ping_interval=15,
            ping_timeout=30,
            close_timeout=5,
        ) as ws:
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": query,
                    "session_id": f"test_{test_id}_{int(time.time())}",
                }
            }))
            
            tools_used = []
            statuses = []
            
            while True:
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(resp)
                    mt = data.get("type", "")
                    
                    if mt == "agent_status":
                        s = data.get("status", "")
                        m = data.get("message", "")
                        d = data.get("details", {})
                        e = time.time() - start
                        statuses.append(s)
                        
                        if s == "iteration_start":
                            it = d.get("iteration", "?")
                            mx = d.get("max", "?")
                            print(f"  [{e:5.1f}s] ━━━ Loop {it}/{mx} ━━━")
                        elif s == "thinking":
                            # Only print non-heartbeat thoughts
                            if "Memproses" not in m and "langkah" not in m:
                                print(f"  [{e:5.1f}s] 🧠 {m[:70]}")
                        elif s == "planning":
                            tools = d.get("tools", [])
                            print(f"  [{e:5.1f}s] 📋 PLAN: {tools}")
                        elif s == "executing_tool":
                            t = d.get("tool", m)
                            tools_used.append(t)
                            print(f"  [{e:5.1f}s] ⚡ {t}")
                        elif s == "tool_completed":
                            print(f"  [{e:5.1f}s] ✓ {m[:60]}")
                        elif s == "observation":
                            print(f"  [{e:5.1f}s] 👁️ {m[:60]}")
                        elif s == "done":
                            print(f"  [{e:5.1f}s] ✅ DONE")
                    
                    elif mt == "agent_response":
                        c = data.get("content", "") or data.get("data", {}).get("content", "")
                        e = time.time() - start
                        print(f"  [{e:5.1f}s] 📝 Response ({len(c)} chars)")
                        result["has_response"] = True
                        break
                    
                    elif mt == "error":
                        e = time.time() - start
                        err = data.get("message", "?")
                        print(f"  [{e:5.1f}s] ❌ {err}")
                        result["error"] = err
                        break
                        
                except asyncio.TimeoutError:
                    e = time.time() - start
                    if e > timeout:
                        result["error"] = f"Timeout after {e:.0f}s"
                        print(f"  [{e:5.1f}s] ⏰ TIMEOUT!")
                        break
                    # Keep waiting silently
            
            result["tools_used"] = tools_used
            result["statuses"] = statuses
            
    except Exception as ex:
        result["error"] = str(ex)
        print(f"  ❌ Exception: {ex}")
    
    result["duration"] = time.time() - start
    
    # Evaluate success
    has_streaming = "iteration_start" in statuses or "thinking" in statuses
    has_tools = len(tools_used) >= min_tools
    has_response = result["has_response"]
    no_error = result["error"] is None
    
    result["success"] = has_response and no_error
    
    # Print verdict
    dur = result["duration"]
    if result["success"]:
        print(f"  ✅ PASS ({dur:.1f}s, {len(tools_used)} tools, streaming={'YES' if has_streaming else 'NO'})")
    else:
        reason = result["error"] or f"tools={len(tools_used)}/{min_tools}, response={has_response}"
        print(f"  ❌ FAIL ({dur:.1f}s): {reason}")
    
    return result


async def run_all_tests():
    """Run all 10 test cases sequentially."""
    try:
        import websockets
    except ImportError:
        subprocess.run([PYTHON, "-m", "pip", "install", "websockets", "-q"])
        import websockets
    
    results = []
    for case in TEST_CASES:
        result = await run_single_test(case)
        results.append(result)
        
        # Brief pause between tests to let server reset
        await asyncio.sleep(2)
    
    return results


def print_summary(results):
    """Print test summary."""
    print(f"\n{'='*60}")
    print(f"  FINAL SUMMARY - 10 Complex Test Cases")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    
    for r in results:
        icon = "✅" if r["success"] else "❌"
        tools = ", ".join(r["tools_used"][:5]) if r["tools_used"] else "none"
        streaming = "iteration_start" in r["statuses"]
        print(f"  {icon} Test {r['id']:2d}: {r['name']:<30s} | {r['duration']:5.1f}s | tools: {tools} | streaming: {'YES' if streaming else 'NO'}")
    
    print(f"\n  Passed: {passed}/{len(results)}")
    print(f"  Failed: {failed}/{len(results)}")
    
    if passed == len(results):
        print(f"\n  🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n  ⚠️ {failed} test(s) failed")
        for r in results:
            if not r["success"]:
                print(f"    - Test {r['id']} ({r['name']}): {r.get('error', 'unknown')}")
    
    return passed == len(results)


def main():
    # Kill existing servers on port 8000 (but not our own process)
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', 8000))
        s.close()
        if result == 0:
            print("Port 8000 in use, waiting for release...")
            # Use netstat to find and kill the process
            subprocess.run(
                'powershell -c "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"',
                shell=True, capture_output=True,
            )
            time.sleep(3)
    except Exception:
        pass
    
    # Start server
    server_proc = start_server()
    if not server_proc:
        print("Failed to start server!")
        sys.exit(1)
    
    try:
        results = asyncio.run(run_all_tests())
        all_pass = print_summary(results)
    finally:
        print("\n🛑 Stopping server...")
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except:
            server_proc.kill()
        print("  Server stopped.")
    
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
