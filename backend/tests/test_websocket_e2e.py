"""
JAWIR OS - WebSocket End-to-End Test
======================================
Test full flow: WS connection -> Agent -> Gemini -> Tools -> Response

Tests:
1. Chat biasa (tanpa tool)
2. Web search (dengan tool)
3. Python exec (dengan tool)
4. Open URL (dengan tool)
5. KiCad (dengan tool)
"""

import asyncio
import json
import os
import subprocess
import sys
import time

# Add backend to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

PYTHON_EXE = os.path.join(BACKEND_DIR, "venv_new", "Scripts", "python.exe")
PORT = 8765
WS_URL = f"ws://localhost:{PORT}/ws/chat"
TIMEOUT = 90  # Gemini Pro takes ~8-10s per call


async def send_and_wait(ws, content: str, timeout: int = TIMEOUT):
    """Send message and wait for agent_response."""
    import websockets
    
    msg = json.dumps({
        "type": "user_message",
        "data": {"content": content},
    })
    await ws.send(msg)
    
    responses = []
    final_response = None
    tools_used = []
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            remaining = timeout - (time.time() - start)
            raw = await asyncio.wait_for(ws.recv(), timeout=max(1, remaining))
            data = json.loads(raw)
            responses.append(data)
            
            msg_type = data.get("type", "")
            
            if msg_type == "agent_status":
                status = data.get("status", "")
                if status == "executing_tool":
                    tool_name = data.get("details", {}).get("tool_name", "")
                    if tool_name:
                        tools_used.append(tool_name)
                elif status == "error":
                    final_response = f"ERROR: {data.get('message', 'unknown')}"
                    break
            
            elif msg_type == "agent_response":
                final_response = data.get("content", "")
                break
                
        except asyncio.TimeoutError:
            final_response = "TIMEOUT"
            break
        except Exception as e:
            final_response = f"ERROR: {e}"
            break
    
    return final_response, tools_used, responses


def print_result(test_num, name, query, response, tools_used, passed):
    """Print test result."""
    print(f"\n{'─' * 60}")
    print(f"  TEST {test_num}: {name}")
    print(f"{'─' * 60}")
    print(f"  Query: {query}")
    if tools_used:
        print(f"  Tools: {', '.join(tools_used)}")
    resp_preview = (response or "NONE")[:300]
    print(f"  Response: {resp_preview}")
    status = "PASS" if passed else "FAIL"
    icon = "[OK]" if passed else "[FAIL]"
    print(f"  Result: {icon} {status}")
    return passed


async def run_tests():
    """Run all WebSocket tests."""
    import websockets
    
    print("=" * 60)
    print("  JAWIR OS - WebSocket E2E Test")
    print(f"  Server: {WS_URL}")
    print("=" * 60)
    
    results = {}
    
    # Wait for server
    print("\n... Waiting for server...")
    for _ in range(20):
        try:
            async with websockets.connect(WS_URL, open_timeout=3, ping_interval=None):
                print("[OK] Server ready!")
                break
        except Exception:
            await asyncio.sleep(1)
    else:
        print("[FAIL] Server not ready after 20s")
        return {}
    
    try:
        async with websockets.connect(
            WS_URL, 
            close_timeout=10, 
            ping_interval=None, 
            ping_timeout=None
        ) as ws:
            # Consume welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=10)
            print(f"Connected: {json.loads(welcome).get('message', '')[:50]}...")
            
            # TEST 1: Chat biasa
            query = "Halo JAWIR, siapa kamu?"
            resp, tools, _ = await send_and_wait(ws, query)
            has_response = resp and not resp.startswith("ERROR") and resp != "TIMEOUT"
            results["1_chat"] = print_result(1, "Chat Biasa", query, resp, tools, has_response)
            
            # TEST 2: Web Search
            query = "Cari berita teknologi AI terbaru"
            resp, tools, _ = await send_and_wait(ws, query)
            has_response = resp and not resp.startswith("ERROR") and resp != "TIMEOUT"
            results["2_web_search"] = print_result(2, "Web Search", query, resp, tools, has_response)
            
            # TEST 3: Python Exec
            query = "Jalankan kode Python: print(2**10)"
            resp, tools, _ = await send_and_wait(ws, query)
            has_1024 = resp and "1024" in resp
            results["3_python"] = print_result(3, "Python Exec", query, resp, tools, has_1024)
            
            # TEST 4: Open URL
            query = "Buka website https://github.com"
            resp, tools, _ = await send_and_wait(ws, query)
            has_response = resp and not resp.startswith("ERROR") and resp != "TIMEOUT"
            results["4_open_url"] = print_result(4, "Open URL", query, resp, tools, has_response)
            
            # TEST 5: KiCad
            query = "Buatkan skematik LED blink sederhana dengan resistor"
            resp, tools, _ = await send_and_wait(ws, query, timeout=120)
            has_response = resp and not resp.startswith("ERROR") and resp != "TIMEOUT"
            results["5_kicad"] = print_result(5, "KiCad Schematic", query, resp, tools, has_response)
            
    except Exception as e:
        print(f"\n[ERROR] Connection error: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, ok in results.items():
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} {name}")
    
    print(f"\n  Total: {passed}/{total} PASSED")
    if passed == total:
        print("  [SUCCESS] ALL TESTS PASSED!")
    else:
        print(f"  [WARNING] {total - passed} test(s) failed")
    print(f"{'=' * 60}")
    
    return results


def main():
    """Start server, run tests, stop server."""
    print("[INFO] Starting JAWIR server on port", PORT, "...")
    
    env = os.environ.copy()
    env["WS_PORT"] = str(PORT)
    env["GEMINI_MODEL"] = "gemini-3-pro-preview"
    env["PYTHONIOENCODING"] = "utf-8"
    
    server_proc = subprocess.Popen(
        [
            PYTHON_EXE, "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", str(PORT),
            "--log-level", "warning",
        ],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    
    try:
        time.sleep(3)
        
        if server_proc.poll() is not None:
            output = server_proc.stdout.read().decode() if server_proc.stdout else ""
            print(f"[FAIL] Server failed to start!")
            print(f"Output: {output[:500]}")
            return
        
        print(f"[OK] Server started (PID={server_proc.pid})")
        
        # Run tests
        asyncio.run(run_tests())
        
    finally:
        print("\n[INFO] Stopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("[OK] Server stopped.")


if __name__ == "__main__":
    main()
