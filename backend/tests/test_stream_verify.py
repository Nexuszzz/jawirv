"""
Self-contained test: starts server, runs test, stops server.
"""
import asyncio
import json
import time
import subprocess
import sys
import os

# Paths
BACKEND_DIR = r"D:\expo\jawirv3\jawirv2\jawirv2\backend"
PYTHON = os.path.join(BACKEND_DIR, "venv_fresh", "Scripts", "python.exe")

async def run_test():
    """Run the actual test."""
    try:
        import websockets
    except ImportError:
        subprocess.run([PYTHON, "-m", "pip", "install", "websockets", "-q"])
        import websockets

    print("\n=== Test: Streamer Fix Verification ===")
    start = time.time()
    
    # Wait for server to be ready
    for attempt in range(10):
        try:
            async with websockets.connect('ws://localhost:8000/ws/chat', close_timeout=2) as ws:
                print("  Server connected!")
                break
        except Exception:
            print(f"  Waiting for server... (attempt {attempt+1})")
            await asyncio.sleep(2)
    else:
        print("  ERROR: Could not connect to server!")
        return False
    
    # Now run the actual test
    async with websockets.connect(
        'ws://localhost:8000/ws/chat',
        ping_interval=15,
        ping_timeout=30,
    ) as ws:
        await ws.send(json.dumps({
            'type': 'user_message',
            'data': {
                'content': 'Cari info tentang ESP32 lalu buat dokumen Google Docs tentang ESP32',
                'session_id': f'stream_test_{int(time.time())}',
            }
        }))
        
        tools_used = []
        statuses = []
        
        while True:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=20)
                data = json.loads(resp)
                mt = data.get('type', '')
                
                if mt == 'agent_status':
                    s = data.get('status', '')
                    m = data.get('message', '')
                    d = data.get('details', {})
                    e = time.time() - start
                    statuses.append(s)
                    
                    if s == 'iteration_start':
                        print(f'  [{e:5.1f}s] --- ITER {d.get("iteration")}/{d.get("max")} ---')
                    elif s == 'thinking':
                        print(f'  [{e:5.1f}s] THINK: {m[:80]}')
                    elif s == 'planning':
                        print(f'  [{e:5.1f}s] PLAN: {d.get("tools", [])}')
                    elif s == 'executing_tool':
                        t = d.get('tool', m)
                        tools_used.append(t)
                        print(f'  [{e:5.1f}s] ACT: {t}')
                    elif s == 'observation':
                        print(f'  [{e:5.1f}s] OBS: {m[:60]}')
                    elif s == 'done':
                        print(f'  [{e:5.1f}s] DONE: {m}')
                    else:
                        print(f'  [{e:5.1f}s] [{s}]: {m[:50]}')
                
                elif mt == 'agent_response':
                    c = data.get('content', '') or data.get('data', {}).get('content', '')
                    print(f'\n  RESPONSE ({len(c)} chars): {c[:200]}')
                    break
                
                elif mt == 'error':
                    print(f'  ERROR: {data.get("message", "?")}')
                    break
                    
            except asyncio.TimeoutError:
                e = time.time() - start
                if e > 300:
                    print('  TIMEOUT!')
                    break
                print(f'  [{e:5.1f}s] waiting...')
    
    e = time.time() - start
    print(f'\n=== Result ===')
    print(f'  Statuses received: {statuses}')
    print(f'  Tools detected: {tools_used}')
    print(f'  Duration: {e:.1f}s')
    
    has_iteration = 'iteration_start' in statuses
    has_thinking = 'thinking' in statuses
    has_tools = len(tools_used) > 0
    has_planning = 'planning' in statuses
    has_observation = 'observation' in statuses
    
    print(f'\n  iteration_start: {"YES" if has_iteration else "NO"}')
    print(f'  thinking: {"YES" if has_thinking else "NO"}')
    print(f'  planning: {"YES" if has_planning else "NO"}')
    print(f'  executing_tool: {"YES" if has_tools else "NO"}')
    print(f'  observation: {"YES" if has_observation else "NO"}')
    
    success = has_thinking and has_tools
    print(f'\n  *** STREAMING WORKS: {"YES" if success else "NO"} ***')
    return success


if __name__ == "__main__":
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1)
