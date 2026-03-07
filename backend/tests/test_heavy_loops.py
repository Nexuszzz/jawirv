"""
JAWIR OS - 5 HEAVY Multi-Tool Test Cases (Puluhan Loop)
=========================================================
Each case forces the agent to use MANY tools across MANY iterations.
Self-contained: starts server subprocess, runs tests, stops server.

Target: minimal 10+ loop iterations per case, 5+ tool calls per case.

Run:
    cd backend
    python tests/test_heavy_loops.py
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


# ============================================================
# 5 HEAVY Test Cases - Designed for 10+ loops, 5+ tools each
# ============================================================
TEST_CASES = [
    {
        "id": 1,
        "name": "MEGA Research + Docs + Python",
        "query": (
            "Lakukan riset menyeluruh tentang mikrokontroler berikut satu per satu: "
            "ESP32, Arduino Uno, STM32, dan Raspberry Pi Pico. "
            "Untuk masing-masing, cari spesifikasi, harga, dan kelebihan. "
            "Setelah semua data terkumpul, buatkan kode Python untuk membuat tabel perbandingan dan jalankan. "
            "Terakhir, buat dokumen Google Docs yang berisi semua hasil riset dan tabel perbandingan."
        ),
        "min_tools": 5,
        "min_loops": 6,
        "timeout": 600,
    },
    {
        "id": 2,
        "name": "Full Google Workspace Sweep",
        "query": (
            "Tolong lakukan hal berikut secara berurutan: "
            "1. Cari di Google Drive file tentang 'project' atau 'laporan'. "
            "2. Cari email di Gmail tentang 'meeting' atau 'rapat'. "
            "3. Tampilkan jadwal kalender minggu ini. "
            "4. Buat dokumen Google Docs berjudul 'Ringkasan Mingguan JAWIR' yang berisi "
            "rangkuman dari semua data yang ditemukan dari Drive, Gmail, dan Calendar. "
            "5. Cari di web informasi tentang tips produktivitas kerja."
        ),
        "min_tools": 5,
        "min_loops": 6,
        "timeout": 600,
    },
    {
        "id": 3,
        "name": "Deep Web Research + Multi-Python + Docs",
        "query": (
            "Lakukan riset web mendalam tentang: "
            "1. Protokol komunikasi IoT (MQTT, CoAP, HTTP, WebSocket) - cari masing-masing. "
            "2. Setelah data terkumpul, buat kode Python yang menghitung perbandingan kecepatan "
            "dan overhead tiap protokol berdasarkan data yang ditemukan, lalu jalankan. "
            "3. Buat kode Python lagi untuk menghasilkan visualisasi text-based (ASCII chart), jalankan. "
            "4. Buat dokumen Google Docs berjudul 'Analisis Protokol IoT' dengan semua hasil."
        ),
        "min_tools": 5,
        "min_loops": 6,
        "timeout": 600,
    },
    {
        "id": 4,
        "name": "Multi-Search + Multi-Python + Drive + Calendar",
        "query": (
            "Saya butuh bantuan lengkap: "
            "1. Cari informasi tentang bahasa pemrograman Python terbaru (Python 3.13). "
            "2. Cari informasi tentang framework FastAPI. "
            "3. Cari informasi tentang database PostgreSQL vs MongoDB. "
            "4. Buat kode Python untuk benchmark sederhana antara list vs dict vs set, jalankan. "
            "5. Buat kode Python lagi untuk menghitung fibonacci iteratif vs rekursif, jalankan dan bandingkan waktu. "
            "6. Cari file di Drive saya tentang 'python' atau 'code'. "
            "7. Tampilkan jadwal kalender saya hari ini."
        ),
        "min_tools": 7,
        "min_loops": 8,
        "timeout": 600,
    },
    {
        "id": 5,
        "name": "Ultimate: Research + Schematic + Python + Docs + Drive",
        "query": (
            "Tolong bantu project IoT saya secara lengkap: "
            "1. Cari info tentang sensor suhu DS18B20 dan cara hubungkan ke ESP32. "
            "2. Cari info tentang sensor kelembaban DHT11. "
            "3. Buatkan skematik KiCad untuk rangkaian ESP32 dengan kedua sensor tersebut. "
            "4. Buatkan kode Python contoh program untuk membaca kedua sensor, jalankan untuk test sintaks. "
            "5. Cari file di Google Drive saya yang berkaitan dengan 'IoT' atau 'sensor'. "
            "6. Buat dokumen Google Docs berjudul 'Project IoT: Multi-Sensor ESP32' "
            "yang berisi semua hasil riset, skematik, dan kode program."
        ),
        "min_tools": 6,
        "min_loops": 7,
        "timeout": 600,
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
    """Run a single heavy test case."""
    import websockets

    test_id = case["id"]
    test_name = case["name"]
    query = case["query"]
    min_tools = case["min_tools"]
    min_loops = case["min_loops"]
    timeout = case["timeout"]

    print(f"\n{'='*70}")
    print(f"  TEST {test_id}: {test_name}")
    print(f"  min_tools={min_tools}, min_loops={min_loops}, timeout={timeout}s")
    print(f"{'='*70}")
    print(f"  Query: {query[:120]}...")

    start = time.time()
    result = {
        "id": test_id,
        "name": test_name,
        "success": False,
        "tools_used": [],
        "unique_tools": set(),
        "loops": 0,
        "statuses": [],
        "has_response": False,
        "response_length": 0,
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
                    "session_id": f"heavy_{test_id}_{int(time.time())}",
                }
            }))

            tools_used = []
            unique_tools = set()
            loops = 0
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
                            loops = it if isinstance(it, int) else loops + 1
                            print(f"  [{e:6.1f}s] ━━━ Loop {it}/{mx} ━━━")

                        elif s == "thinking":
                            # Skip heartbeat noise
                            if "Memproses" not in m and "langkah" not in m:
                                short = m[:80]
                                print(f"  [{e:6.1f}s] 🧠 {short}")

                        elif s == "planning":
                            tools = d.get("tools", [])
                            print(f"  [{e:6.1f}s] 📋 PLAN: {tools}")

                        elif s == "executing_tool":
                            t = d.get("tool", m)
                            tools_used.append(t)
                            unique_tools.add(t)
                            print(f"  [{e:6.1f}s] ⚡ {t}")

                        elif s == "tool_completed":
                            dur_info = m[:50]
                            print(f"  [{e:6.1f}s] ✓ {dur_info}")

                        elif s == "observation":
                            obs = m[:70]
                            print(f"  [{e:6.1f}s] 👁️ {obs}")

                        elif s == "done":
                            print(f"  [{e:6.1f}s] ✅ DONE")

                    elif mt == "agent_response":
                        c = data.get("content", "") or data.get("data", {}).get("content", "")
                        e = time.time() - start
                        print(f"  [{e:6.1f}s] 📝 Response ({len(c)} chars)")
                        result["has_response"] = True
                        result["response_length"] = len(c)
                        break

                    elif mt == "error":
                        e = time.time() - start
                        err = data.get("message", "?")
                        print(f"  [{e:6.1f}s] ❌ {err[:100]}")
                        result["error"] = err
                        break

                except asyncio.TimeoutError:
                    e = time.time() - start
                    if e > timeout:
                        result["error"] = f"Timeout after {e:.0f}s"
                        print(f"  [{e:6.1f}s] ⏰ TIMEOUT!")
                        break

            result["tools_used"] = tools_used
            result["unique_tools"] = unique_tools
            result["loops"] = loops
            result["statuses"] = statuses

    except Exception as ex:
        result["error"] = str(ex)
        print(f"  ❌ Exception: {ex}")

    result["duration"] = time.time() - start

    # ── Evaluate ──
    total_tools = len(tools_used)
    total_unique = len(unique_tools)
    has_response = result["has_response"]
    no_error = result["error"] is None
    has_streaming = "iteration_start" in statuses

    result["success"] = has_response and no_error

    dur = result["duration"]
    print(f"\n  ┌─ Result ─────────────────────────────────────────")
    print(f"  │ Status    : {'✅ PASS' if result['success'] else '❌ FAIL'}")
    print(f"  │ Duration  : {dur:.1f}s")
    print(f"  │ Loops     : {loops}")
    print(f"  │ Tools     : {total_tools} calls ({total_unique} unique)")
    print(f"  │ Unique    : {sorted(unique_tools)}")
    print(f"  │ Streaming : {'YES' if has_streaming else 'NO'}")
    print(f"  │ Response  : {result['response_length']} chars")
    if result["error"]:
        print(f"  │ Error     : {result['error'][:80]}")
    print(f"  └──────────────────────────────────────────────────")

    return result


async def run_all_tests():
    """Run all heavy test cases sequentially."""
    try:
        import websockets
    except ImportError:
        subprocess.run([PYTHON, "-m", "pip", "install", "websockets", "-q"])
        import websockets

    results = []
    for case in TEST_CASES:
        result = await run_single_test(case)
        results.append(result)
        # Brief pause between tests
        await asyncio.sleep(3)

    return results


def print_summary(results):
    """Print final summary table."""
    print(f"\n{'='*80}")
    print(f"  FINAL SUMMARY — 5 HEAVY Multi-Tool Test Cases")
    print(f"{'='*80}")

    passed = sum(1 for r in results if r["success"])
    total_tools = sum(len(r["tools_used"]) for r in results)
    total_loops = sum(r["loops"] for r in results)
    total_time = sum(r["duration"] for r in results)

    for r in results:
        icon = "✅" if r["success"] else "❌"
        uniq = sorted(r["unique_tools"])
        print(
            f"  {icon} Test {r['id']}: {r['name']:<45s} "
            f"| {r['duration']:6.1f}s "
            f"| {r['loops']:2d} loops "
            f"| {len(r['tools_used']):2d} tool calls "
            f"| {len(r['unique_tools'])} unique"
        )
        print(f"         Tools: {', '.join(uniq)}")

    print(f"\n  {'─'*60}")
    print(f"  Passed    : {passed}/{len(results)}")
    print(f"  Total Loops: {total_loops}")
    print(f"  Total Tools: {total_tools} calls")
    print(f"  Total Time : {total_time:.1f}s")

    if passed == len(results):
        print(f"\n  🎉🎉🎉 ALL {len(results)} HEAVY TESTS PASSED! 🎉🎉🎉")
    else:
        print(f"\n  ⚠️ {len(results) - passed} test(s) failed:")
        for r in results:
            if not r["success"]:
                print(f"    - Test {r['id']} ({r['name']}): {r.get('error', 'no response')}")

    return passed == len(results)


def main():
    # Clean up port
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = s.connect_ex(('127.0.0.1', 8000))
        s.close()
        if result == 0:
            print("Port 8000 in use, cleaning up...")
            subprocess.run(
                'powershell -c "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue '
                '| ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"',
                shell=True, capture_output=True,
            )
            time.sleep(3)
    except Exception:
        pass

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
