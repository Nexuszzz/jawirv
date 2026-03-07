"""
JAWIR OS - FULL Real Integration Test (Self-Contained)
========================================================
Script ini:
1. Start server backend di subprocess  
2. Test semua tool via WebSocket
3. Print hasil lengkap dengan server log capture

Pakai: python test_real_full.py
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import io

# Fix Windows console encoding for emoji
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

PYTHON_EXE = os.path.join(BACKEND_DIR, "venv_new", "Scripts", "python.exe")
PORT = 8765
WS_URL = f"ws://localhost:{PORT}/ws/chat"
TIMEOUT = 120  # 2 minutes per test (Gemini can be slow)


def flush():
    """Force flush stdout."""
    sys.stdout.flush()
    sys.stderr.flush()


def log(msg):
    """Print with flush."""
    print(msg)
    flush()


async def send_and_collect(ws, content: str, timeout: int = TIMEOUT):
    """Send user message and collect all responses until agent_response."""
    msg = json.dumps({
        "type": "user_message",
        "data": {"content": content},
    })
    await ws.send(msg)

    responses = []
    final_response = None
    start = time.time()

    while time.time() - start < timeout:
        remaining = timeout - (time.time() - start)
        if remaining <= 0:
            final_response = "TIMEOUT"
            break
        try:
            raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 30))
            data = json.loads(raw)
            responses.append(data)

            msg_type = data.get("type", "")
            if msg_type == "agent_response":
                final_response = data.get("content", "")
                break
            elif msg_type == "agent_status":
                status = data.get("status", "")
                message = data.get("message", "")
                if status == "error":
                    final_response = f"ERROR: {message}"
                    break
                # Print live status
                log(f"    [{status}] {message}")
        except asyncio.TimeoutError:
            # Not a fatal timeout - just no message in 30s, keep waiting
            elapsed = time.time() - start
            if elapsed >= timeout:
                final_response = "TIMEOUT"
                break
            log(f"    ... waiting ({int(elapsed)}s elapsed)")
        except Exception as e:
            final_response = f"ERROR: {e}"
            break

    return final_response, responses


def print_test(test_num, name, query, response, all_msgs, extra_check=None):
    """Print test result."""
    log(f"\n{'='*60}")
    log(f"  TEST {test_num}: {name}")
    log(f"{'='*60}")
    log(f"  Query: {query}")

    # Show tools used
    tool_names = []
    for m in all_msgs:
        if m.get("type") == "agent_status":
            s = m.get("status", "")
            if s == "executing_tool":
                details = m.get("details", {})
                tn = details.get("tool_name", "")
                if tn:
                    tool_names.append(tn)
                tools_list = details.get("tools", [])
                if tools_list:
                    tool_names.extend(tools_list)

    if tool_names:
        log(f"  Tools used: {', '.join(tool_names)}")

    resp_preview = (response or "NONE")[:300]
    log(f"  Response: {resp_preview}")

    has_response = response and response != "TIMEOUT" and not response.startswith("ERROR")

    if extra_check is not None:
        passed = has_response and extra_check
    else:
        passed = has_response

    status_str = "PASS" if passed else "FAIL"
    log(f"  Result: {status_str}")
    flush()
    return passed


async def run_tests():
    """Run all tests against running server."""
    import websockets

    log("=" * 60)
    log("  JAWIR OS - Real Integration Test")
    log(f"  Server: {WS_URL}")
    log(f"  Timeout per test: {TIMEOUT}s")
    log("=" * 60)
    flush()

    results = {}

    # Wait for server to be ready
    log("\n... Waiting for server to be ready...")
    flush()
    for i in range(20):
        try:
            async with websockets.connect(WS_URL, open_timeout=3, ping_interval=None) as ws:
                _ = await asyncio.wait_for(ws.recv(), timeout=5)
                log("[OK] Server ready!")
                flush()
                break
        except Exception:
            if i % 5 == 0:
                log(f"    retry {i+1}...")
                flush()
            await asyncio.sleep(1)
    else:
        log("[FAIL] Server did not start in time!")
        flush()
        return {}

    try:
        async with websockets.connect(
            WS_URL,
            close_timeout=10,
            ping_interval=None,
            ping_timeout=None,
            max_size=10 * 1024 * 1024,  # 10MB max message
        ) as ws:
            # Consume connection message
            conn_raw = await asyncio.wait_for(ws.recv(), timeout=10)
            conn = json.loads(conn_raw)
            log(f"Connected: {conn.get('message', 'OK')}\n")
            flush()

            # -------- TEST 1: Chat biasa (no tool needed) --------
            query = "Halo JAWIR, siapa kamu?"
            resp, msgs = await send_and_collect(ws, query, timeout=60)
            results["1_chat_biasa"] = print_test(1, "Chat Biasa (tanpa tool)", query, resp, msgs)

            # -------- TEST 2: Chat konsep (no tool needed) --------
            query = "Apa itu ESP32?"
            resp, msgs = await send_and_collect(ws, query, timeout=60)
            results["2_chat_konsep"] = print_test(2, "Chat Konsep (tanpa tool)", query, resp, msgs)

            # -------- TEST 3: Web Search --------
            query = "Carikan informasi terbaru tentang artificial intelligence 2026"
            resp, msgs = await send_and_collect(ws, query, timeout=TIMEOUT)
            results["3_web_search"] = print_test(3, "Web Search Tool", query, resp, msgs)

            # -------- TEST 4: Python Code Execution --------
            query = "Jalankan kode Python: print(sum(range(1, 101)))"
            resp, msgs = await send_and_collect(ws, query, timeout=TIMEOUT)
            has_5050 = resp is not None and "5050" in str(resp)
            results["4_python_exec"] = print_test(4, "Python Code Execution", query, resp, msgs, extra_check=has_5050)

            # -------- TEST 5: Open URL (Desktop) --------
            query = "Bukakan URL https://www.google.com"
            resp, msgs = await send_and_collect(ws, query, timeout=TIMEOUT)
            results["5_open_url"] = print_test(5, "Desktop - Open URL", query, resp, msgs)

            # -------- TEST 6: KiCad Schematic --------
            query = "Buatkan skematik LED blink sederhana dengan resistor 330 ohm"
            resp, msgs = await send_and_collect(ws, query, timeout=TIMEOUT)
            results["6_kicad"] = print_test(6, "KiCad Schematic", query, resp, msgs)

    except Exception as e:
        log(f"\n[ERROR] Connection error: {e}")
        import traceback
        traceback.print_exc()
        flush()

    # -------- SUMMARY --------
    log(f"\n{'#'*60}")
    log("  SUMMARY")
    log(f"{'#'*60}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, ok in results.items():
        icon = "PASS" if ok else "FAIL"
        log(f"  [{icon}] {name}")

    log(f"\n  Total: {passed}/{total} PASSED")
    if passed == total and total > 0:
        log("  ALL TESTS PASSED!")
    elif total > 0:
        log(f"  {total - passed} test(s) failed")
    log(f"{'#'*60}")
    flush()

    return results


def kill_port(port):
    """Kill any process on the given port (Windows)."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = int(parts[-1])
                try:
                    os.kill(pid, signal.SIGTERM)
                    log(f"  Killed PID {pid} on port {port}")
                except Exception:
                    pass
    except Exception:
        pass


def main():
    """Start server, run tests, stop server."""
    log(f"Starting JAWIR server on port {PORT} ...")
    flush()

    # Kill any existing process on the port
    kill_port(PORT)
    time.sleep(1)

    env = os.environ.copy()
    env["WS_PORT"] = str(PORT)
    env["PYTHONIOENCODING"] = "utf-8"

    # Start server with log output to file
    log_file = os.path.join(BACKEND_DIR, "tests", "server_test.log")

    with open(log_file, "w", encoding="utf-8") as lf:
        server_proc = subprocess.Popen(
            [
                PYTHON_EXE, "-m", "uvicorn",
                "app.main:app",
                "--host", "0.0.0.0",
                "--port", str(PORT),
                "--log-level", "info",
                "--timeout-keep-alive", "120",
            ],
            cwd=BACKEND_DIR,
            env=env,
            stdout=lf,
            stderr=subprocess.STDOUT,
        )

    try:
        # Give server time to start
        time.sleep(4)

        if server_proc.poll() is not None:
            # Server died
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    server_log = f.read()
                log(f"[FAIL] Server crashed!\n{server_log[:1000]}")
            except Exception:
                log("[FAIL] Server crashed! Could not read log.")
            flush()
            return

        log(f"[OK] Server started (PID={server_proc.pid})")
        flush()

        # Run tests
        asyncio.run(run_tests())

    finally:
        log("\nStopping server...")
        flush()
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
            server_proc.wait(timeout=3)
        log("[OK] Server stopped.")

        # Show server logs
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                server_log = f.read()
            if server_log:
                log(f"\n--- Server Logs (last 2000 chars) ---")
                log(server_log[-2000:])
                log("--- End Server Logs ---")
        except Exception:
            pass
        flush()


if __name__ == "__main__":
    main()
