import asyncio, json, time, websockets

async def test():
    print('=== Test: Streamer Fix ===')
    start = time.time()
    async with websockets.connect('ws://localhost:8000/ws/chat', ping_interval=15, ping_timeout=30) as ws:
        await ws.send(json.dumps({'type':'user_message','data':{'content':'Cari info tentang ESP32 lalu buat dokumen Google Docs tentang ESP32','session_id':'fix_test_005'}}))
        tools_used = []
        statuses = []
        while True:
            try:
                resp = await asyncio.wait_for(ws.recv(), timeout=20)
                data = json.loads(resp)
                mt = data.get('type','')
                if mt == 'agent_status':
                    s = data.get('status','')
                    m = data.get('message','')
                    d = data.get('details',{})
                    e = time.time()-start
                    statuses.append(s)
                    if s == 'iteration_start': print(f'  [{e:5.1f}s] --- ITER {d.get("iteration")}/{d.get("max")} ---')
                    elif s == 'thinking': print(f'  [{e:5.1f}s] THINK: {m[:80]}')
                    elif s == 'planning': print(f'  [{e:5.1f}s] PLAN: {d.get("tools",[])}')
                    elif s == 'executing_tool':
                        t = d.get('tool',m)
                        tools_used.append(t)
                        print(f'  [{e:5.1f}s] ACT: {t}')
                    elif s == 'observation': print(f'  [{e:5.1f}s] OBS: {m[:60]}')
                    elif s == 'done': print(f'  [{e:5.1f}s] DONE: {m}')
                    else: print(f'  [{e:5.1f}s] [{s}]: {m[:50]}')
                elif mt == 'agent_response':
                    c = data.get('content','') or data.get('data',{}).get('content','')
                    print(f'\n  RESP ({len(c)} chars): {c[:200]}')
                    break
                elif mt == 'error':
                    print(f'  ERR: {data.get("message","?")}')
                    break
            except asyncio.TimeoutError:
                e = time.time()-start
                if e > 300: print('TIMEOUT'); break
                print(f'  [{e:5.1f}s] waiting...')
    e = time.time()-start
    print(f'\n=== Result ===')
    print(f'Statuses: {statuses}')
    print(f'Tools: {tools_used}')
    print(f'Duration: {e:.1f}s')
    print(f'STREAMING WORKS: {len(tools_used)>0}')

asyncio.run(test())
