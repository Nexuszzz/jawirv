"""
Self-contained test: starts server as subprocess, runs test, stops server.
"""
import asyncio
import json
import time
import subprocess
import sys
import os
import signal
import threading

BACKEND_DIR = r"D:\expo\jawirv3\jawirv2\jawirv2\backend"
PYTHON = os.path.join(BACKEND_DIR, "venv_fresh", "Scripts", "python.exe")


def _drain_stdout(proc, ready_event):
    """Drain server stdout in a background thread to prevent buffer deadlock."""
    for line in iter(proc.stdout.readline, ''):
        line = line.rstrip()
        if "Uvicorn running" in line:
            print(f"  [server] {line}")
            ready_event.set()
        # Just consume, don't print everything (too noisy)
    proc.stdout.close()


def start_server():
    """Start uvicorn server as subprocess."""
    print("Starting server...")
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
    
    # Wait up to 30s for server to be ready
    if not ready_event.wait(timeout=30):
        if proc.poll() is not None:
            print("  Server process died!")
        else:
            print("  Server did not report ready in 30s!")
        return None
    
    print("  Server is ready!")
    return proc


async def run_test():
    """Run the streaming test."""
    try:
        import websockets
    except ImportError:
        subprocess.run([PYTHON, "-m", "pip", "install", "websockets", "-q"])
        import websockets
    
    print("\n=== Test: Streamer Fix Verification ===")
    print("  Query: 'Cari info tentang ESP32 lalu buat dokumen Google Docs tentang ESP32'")
    start = time.time()
    
    # Connect
    for attempt in range(10):
        try:
            ws = await websockets.connect(
                'ws://localhost:8000/ws/chat',
                ping_interval=15,
                ping_timeout=30,
            )
            print(f"  Connected to WebSocket!")
            break
        except Exception as e:
            print(f"  Connection attempt {attempt+1} failed: {e}")
            await asyncio.sleep(2)
    else:
        print("  ERROR: Could not connect!")
        return False
    
    try:
        await ws.send(json.dumps({
            'type': 'user_message',
            'data': {
                'content': 'Cari info tentang ESP32 lalu buat dokumen Google Docs tentang ESP32',
                'session_id': f'stream_test_{int(time.time())}',
            }
        }))
        print("  Message sent, waiting for responses...\n")
        
        tools_used = []
        statuses = []
        
        while True:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(resp)
                mt = data.get('type', '')
                
                if mt == 'agent_status':
                    s = data.get('status', '')
                    m = data.get('message', '')
                    d = data.get('details', {})
                    e = time.time() - start
                    statuses.append(s)
                    
                    if s == 'iteration_start':
                        it = d.get("iteration", "?")
                        mx = d.get("max", "?")
                        print(f'  [{e:6.1f}s] ━━━ ReAct Loop {it}/{mx} ━━━')
                    elif s == 'thinking':
                        print(f'  [{e:6.1f}s] 🧠 THINK: {m[:100]}')
                    elif s == 'planning':
                        tools = d.get("tools", [])
                        print(f'  [{e:6.1f}s] 📋 PLAN: {tools}')
                    elif s == 'executing_tool':
                        t = d.get('tool', m)
                        tools_used.append(t)
                        print(f'  [{e:6.1f}s] ⚡ ACTION: {t}')
                    elif s == 'tool_result':
                        t = d.get('tool', '?')
                        ok = d.get('success', False)
                        icon = '✅' if ok else '❌'
                        print(f'  [{e:6.1f}s] {icon} RESULT: {t}: {m[:60]}')
                    elif s == 'observation':
                        print(f'  [{e:6.1f}s] 👁️ OBSERVE: {m[:80]}')
                    elif s == 'done':
                        print(f'  [{e:6.1f}s] ✅ DONE')
                    elif s == 'heartbeat':
                        print(f'  [{e:6.1f}s] 💓 heartbeat')
                    else:
                        print(f'  [{e:6.1f}s] [{s}]: {m[:80]}')
                
                elif mt == 'agent_response':
                    c = data.get('content', '') or data.get('data', {}).get('content', '')
                    e = time.time() - start
                    print(f'\n  [{e:6.1f}s] 📝 FINAL RESPONSE ({len(c)} chars):')
                    print(f'  {c[:300]}...' if len(c) > 300 else f'  {c}')
                    break
                
                elif mt == 'error':
                    e = time.time() - start
                    print(f'  [{e:6.1f}s] ❌ ERROR: {data.get("message", "?")}')
                    break
                    
            except asyncio.TimeoutError:
                e = time.time() - start
                if e > 300:
                    print(f'  [{e:6.1f}s] ⏰ TOTAL TIMEOUT!')
                    break
                print(f'  [{e:6.1f}s] ... waiting ...')
    finally:
        await ws.close()
    
    e = time.time() - start
    print(f'\n{"="*50}')
    print(f'  RESULTS')
    print(f'{"="*50}')
    print(f'  Duration: {e:.1f}s')
    print(f'  All statuses: {statuses}')
    print(f'  Tools detected: {tools_used}')
    
    checks = {
        'iteration_start': 'iteration_start' in statuses,
        'thinking': 'thinking' in statuses,
        'planning': 'planning' in statuses,
        'executing_tool': len(tools_used) > 0,
        'observation': 'observation' in statuses,
    }
    
    print()
    for name, ok in checks.items():
        print(f'  {"✅" if ok else "❌"} {name}: {"RECEIVED" if ok else "MISSING"}')
    
    success = checks['thinking'] and checks['executing_tool']
    print(f'\n  *** STREAMING FIX: {"WORKING ✅" if success else "BROKEN ❌"} ***\n')
    return success


def main():
    # Start server
    server_proc = start_server()
    if not server_proc:
        print("Failed to start server!")
        sys.exit(1)
    
    try:
        # Give server a moment
        time.sleep(2)
        
        # Run async test
        success = asyncio.run(run_test())
    finally:
        # Stop server
        print("Stopping server...")
        try:
            server_proc.terminate()
            server_proc.wait(timeout=5)
        except:
            server_proc.kill()
        print("Server stopped.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
