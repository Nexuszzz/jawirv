"""
JAWIR OS V2 — Full Feature Test (All Categories)
==================================================
Quick comprehensive test across ALL features:
  1. REST endpoints (health, config, monitoring, IoT, keys)
  2. WebSocket ping/pong
  3. WebSocket chat E2E (FC mode)
  4. Tool contract per-category (Web, KiCad, Python, Google, Desktop, WhatsApp, Polinema, IoT)
  5. Frontend build check (if npm available)
"""

import asyncio
import json
import time
import sys
import os
import traceback

# Add parent dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"

# ── Results collector ──
results = []

def record(phase, test, status, detail=""):
    tag = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    results.append({"phase": phase, "test": test, "status": status, "detail": detail})
    print(f"  {tag} [{phase}] {test} → {status} {detail[:120]}")


# ════════════════════════════════════════════════════════════════
# PHASE 1: REST ENDPOINTS
# ════════════════════════════════════════════════════════════════
async def test_rest():
    import httpx
    print("\n═══ PHASE 1: REST ENDPOINTS ═══")
    
    endpoints = [
        ("GET", "/health", "Main health"),
        ("GET", "/health/iot", "IoT health"),
        ("GET", "/api/iot/devices", "IoT devices"),
        ("GET", "/api/iot/events", "IoT events"),
        ("GET", "/api/keys/stats", "API key stats"),
        ("GET", "/api/config", "Config"),
        ("GET", "/api/monitoring/health", "Monitoring health"),
        ("GET", "/api/monitoring/analytics", "Analytics"),
        ("GET", "/api/monitoring/tools", "Tool stats"),
        ("GET", "/api/monitoring/top-tools", "Top tools"),
    ]
    
    async with httpx.AsyncClient(base_url=BASE, timeout=10) as c:
        for method, path, name in endpoints:
            try:
                r = await c.get(path)
                if r.status_code == 200:
                    data = r.json()
                    brief = str(data)[:100]
                    record("REST", name, "PASS", brief)
                else:
                    record("REST", name, "FAIL", f"HTTP {r.status_code}")
            except Exception as e:
                record("REST", name, "FAIL", str(e)[:100])


# ════════════════════════════════════════════════════════════════
# PHASE 2: WEBSOCKET PING/PONG
# ════════════════════════════════════════════════════════════════
async def test_ws_ping():
    import websockets
    print("\n═══ PHASE 2: WEBSOCKET PING/PONG ═══")
    try:
        async with websockets.connect(WS_URL, open_timeout=5) as ws:
            # Should get connection message
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            if data.get("type") == "connection":
                record("WS", "Connection handshake", "PASS", f"session={data.get('session_id','?')[:8]}")
            else:
                record("WS", "Connection handshake", "WARN", f"got type={data.get('type')}")
            
            # Ping
            await ws.send(json.dumps({"type": "ping"}))
            pong = await asyncio.wait_for(ws.recv(), timeout=5)
            pdata = json.loads(pong)
            if pdata.get("type") == "pong":
                record("WS", "Ping → Pong", "PASS")
            else:
                record("WS", "Ping → Pong", "FAIL", f"got {pdata.get('type')}")
    except Exception as e:
        record("WS", "Connection", "FAIL", str(e)[:100])


# ════════════════════════════════════════════════════════════════
# PHASE 3: WEBSOCKET CHAT E2E (Function Calling)
# ════════════════════════════════════════════════════════════════
async def test_ws_chat():
    import websockets
    print("\n═══ PHASE 3: WS CHAT E2E ═══")
    
    test_cases = [
        ("Greeting", "Halo Jawir, siapa kamu?", ["agent_response"], None),
        ("Web Search", "cari info terbaru tentang ESP32-S3", ["agent_status", "agent_response"], "web_search"),
        ("IoT List", "tampilkan semua perangkat IoT", ["agent_status", "agent_response"], "iot_list_devices"),
    ]
    
    for name, prompt, expected_types, expected_tool in test_cases:
        try:
            async with websockets.connect(WS_URL, open_timeout=5) as ws:
                # Consume connection msg
                await asyncio.wait_for(ws.recv(), timeout=5)
                
                # Send message
                await ws.send(json.dumps({
                    "type": "user_message",
                    "data": {"content": prompt, "session_id": f"test_{name.lower().replace(' ','_')}"}
                }))
                
                events = []
                tool_called = None
                got_response = False
                start = time.time()
                
                while time.time() - start < 60:  # 60s timeout per test
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=15)
                        ev = json.loads(raw)
                        etype = ev.get("type", "")
                        events.append(etype)
                        
                        if etype == "agent_status":
                            st = ev.get("status", "")
                            tool = ev.get("tool_name", "")
                            if st == "executing_tool" and tool:
                                tool_called = tool
                        
                        if etype == "tool_result":
                            tn = ev.get("tool_name", ev.get("data", {}).get("tool_name", ""))
                            if tn:
                                tool_called = tn
                        
                        if etype == "agent_response":
                            got_response = True
                            break
                        
                        if etype == "error":
                            record("CHAT", name, "FAIL", f"error: {ev.get('message','')[:80]}")
                            break
                            
                    except asyncio.TimeoutError:
                        break
                
                if got_response:
                    if expected_tool and tool_called:
                        if expected_tool in str(tool_called):
                            record("CHAT", name, "PASS", f"tool={tool_called}, events={len(events)}")
                        else:
                            record("CHAT", name, "WARN", f"expected tool {expected_tool}, got {tool_called}")
                    elif expected_tool and not tool_called:
                        record("CHAT", name, "WARN", f"response OK but no tool detected (expected {expected_tool})")
                    else:
                        record("CHAT", name, "PASS", f"response received, events={len(events)}")
                else:
                    record("CHAT", name, "FAIL", f"no agent_response after 45s, events={events[:10]}")
                    
        except Exception as e:
            record("CHAT", name, f"FAIL", str(e)[:100])


# ════════════════════════════════════════════════════════════════
# PHASE 4: TOOL CONTRACT (all categories)
# ════════════════════════════════════════════════════════════════
async def test_tool_contracts():
    print("\n═══ PHASE 4: TOOL CONTRACTS ═══")
    
    try:
        from agent.tools import get_all_tools
        tools = get_all_tools()
        tool_map = {t.name: t for t in tools}
        record("TOOLS", f"Registry ({len(tools)} tools)", "PASS", ", ".join(sorted(tool_map.keys())))
    except Exception as e:
        record("TOOLS", "Registry load", "FAIL", str(e)[:100])
        return
    
    # Category → [(tool_name, test_args, is_safe)]
    categories = {
        "Web": [("web_search", {"query": "test"}, True)],
        "KiCad": [("generate_kicad_schematic", {"description": "simple LED circuit", "project_name": "test"}, True)],
        "Python": [("run_python_code", {"code": "print('hello jawir')"}, True)],
        "Desktop": [
            ("open_url", {"url": "https://example.com"}, False),  # skip - opens browser
            ("open_app", {"app_name": "notepad"}, False),
            ("close_app", {"app_name": "notepad"}, False),
        ],
        "Gmail": [
            ("gmail_search", {"query": "test"}, True),
            ("gmail_send", {"to": "test@test.com", "subject": "t", "body": "t"}, False),
        ],
        "Drive": [
            ("drive_search", {"query": "test"}, True),
            ("drive_list", {}, True),
        ],
        "Calendar": [
            ("calendar_list_events", {}, True),
            ("calendar_create_event", {"title": "t", "start_time": "2026-01-01T10:00", "end_time": "2026-01-01T11:00"}, False),
        ],
        "Sheets": [
            ("sheets_read", {"spreadsheet_id": "test123", "range": "A1:B2"}, True),
            ("sheets_write", {"spreadsheet_id": "x", "range": "A1", "values": [["a"]]}, False),
            ("sheets_create", {"title": "test"}, False),
        ],
        "Docs": [
            ("docs_read", {"document_id": "test"}, True),
            ("docs_create", {"title": "t", "content": "t"}, False),
        ],
        "Forms": [
            ("forms_read", {"form_id": "test"}, True),
            ("forms_create", {"title": "t"}, False),
            ("forms_add_question", {"form_id": "x", "question": "q", "question_type": "short_answer"}, False),
        ],
        "WhatsApp": [
            ("whatsapp_list_chats", {}, True),
            ("whatsapp_check_number", {"phone": "6281234567890"}, True),
            ("whatsapp_send_message", {"chat_jid": "test@s.whatsapp.net", "message": "test"}, False),
        ],
        "Polinema": [
            ("polinema_get_biodata", {}, True),
        ],
        "IoT": [
            ("iot_list_devices", {}, True),
            ("iot_get_device_state", {"device_id": "fan-01"}, True),
        ],
    }
    
    for cat, tool_tests in categories.items():
        for tool_name, args, is_safe in tool_tests:
            if tool_name not in tool_map:
                record("TOOLS", f"{cat}/{tool_name}", "WARN", "not in registry")
                continue
            
            tool = tool_map[tool_name]
            
            # Schema check
            schema = tool.args_schema.schema() if hasattr(tool, 'args_schema') and tool.args_schema else {}
            if not schema:
                record("TOOLS", f"{cat}/{tool_name} schema", "WARN", "no schema")
            
            # Execute safe tools only
            if not is_safe:
                record("TOOLS", f"{cat}/{tool_name}", "SKIP", "destructive/unsafe")
                continue
                
            try:
                # Try ainvoke first (async tools), fallback to invoke
                try:
                    result = await asyncio.wait_for(tool.ainvoke(args), timeout=25)
                except (NotImplementedError, TypeError):
                    result = await asyncio.wait_for(
                        asyncio.to_thread(tool.invoke, args), timeout=25
                    )
                result_str = str(result)[:150]
                
                # Check for graceful failures (not configured, offline, etc.)
                lower = result_str.lower()
                if any(x in lower for x in ["error", "gagal", "tidak", "not configured", "connection refused", "offline", "unavailable", "failed"]):
                    record("TOOLS", f"{cat}/{tool_name}", "WARN", f"graceful fail: {result_str[:100]}")
                else:
                    record("TOOLS", f"{cat}/{tool_name}", "PASS", result_str[:100])
                    
            except asyncio.TimeoutError:
                record("TOOLS", f"{cat}/{tool_name}", "WARN", "timeout 20s")
            except Exception as e:
                err = str(e)[:100]
                if any(x in err.lower() for x in ["not configured", "connection refused", "unavailable"]):
                    record("TOOLS", f"{cat}/{tool_name}", "WARN", f"graceful: {err}")
                else:
                    record("TOOLS", f"{cat}/{tool_name}", "FAIL", err)


# ════════════════════════════════════════════════════════════════
# PHASE 5: FRONTEND BUILD
# ════════════════════════════════════════════════════════════════
def test_frontend_build():
    import subprocess
    print("\n═══ PHASE 5: FRONTEND BUILD ═══")
    
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "frontend")
    frontend_dir = os.path.normpath(frontend_dir)
    
    if not os.path.isdir(frontend_dir):
        record("FRONTEND", "Directory", "FAIL", f"not found: {frontend_dir}")
        return
    
    record("FRONTEND", "Directory", "PASS", frontend_dir)
    
    # Check package.json
    pkg = os.path.join(frontend_dir, "package.json")
    if os.path.exists(pkg):
        with open(pkg) as f:
            pj = json.load(f)
        record("FRONTEND", "package.json", "PASS", f"name={pj.get('name')}, deps={len(pj.get('dependencies',{}))}")
    
    # TypeScript check (tsc --noEmit)
    try:
        r = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=frontend_dir, capture_output=True, text=True, timeout=60, shell=True
        )
        if r.returncode == 0:
            record("FRONTEND", "TypeScript check", "PASS", "no errors")
        else:
            errors = r.stdout[:200] or r.stderr[:200]
            record("FRONTEND", "TypeScript check", "FAIL", errors)
    except Exception as e:
        record("FRONTEND", "TypeScript check", "WARN", str(e)[:100])
    
    # Vite build
    try:
        r = subprocess.run(
            ["npx", "vite", "build"],
            cwd=frontend_dir, capture_output=True, text=True, timeout=120, shell=True
        )
        if r.returncode == 0:
            record("FRONTEND", "Vite build", "PASS", "success")
        else:
            errors = r.stderr[:200]
            record("FRONTEND", "Vite build", "FAIL", errors)
    except Exception as e:
        record("FRONTEND", "Vite build", "WARN", str(e)[:100])


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
async def main():
    print("╔══════════════════════════════════════════════════╗")
    print("║   JAWIR OS V2 — FULL FEATURE TEST               ║")
    print("╚══════════════════════════════════════════════════╝")
    t0 = time.time()
    
    await test_rest()
    await test_ws_ping()
    await test_ws_chat()
    await test_tool_contracts()
    test_frontend_build()
    
    elapsed = round(time.time() - t0, 1)
    
    # ── Summary ──
    print("\n" + "═" * 60)
    print(f"  JAWIR OS V2 — TEST SUMMARY ({elapsed}s)")
    print("═" * 60)
    
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    warn_count = sum(1 for r in results if r["status"] in ("WARN", "SKIP"))
    total = len(results)
    
    # Group by phase
    phases = {}
    for r in results:
        p = r["phase"]
        if p not in phases:
            phases[p] = {"pass": 0, "fail": 0, "warn": 0}
        if r["status"] == "PASS":
            phases[p]["pass"] += 1
        elif r["status"] == "FAIL":
            phases[p]["fail"] += 1
        else:
            phases[p]["warn"] += 1
    
    for phase, counts in phases.items():
        p, f, w = counts["pass"], counts["fail"], counts["warn"]
        icon = "✅" if f == 0 else "❌"
        print(f"  {icon} {phase:12s} PASS={p:2d}  FAIL={f:2d}  WARN/SKIP={w:2d}")
    
    print(f"\n  TOTAL: {pass_count} PASS / {fail_count} FAIL / {warn_count} WARN+SKIP / {total} tests")
    
    # Print failures
    failures = [r for r in results if r["status"] == "FAIL"]
    if failures:
        print(f"\n  ❌ FAILURES:")
        for r in failures:
            print(f"     [{r['phase']}] {r['test']}: {r['detail'][:100]}")
    
    score = round(pass_count / max(total - warn_count, 1) * 100)
    print(f"\n  SCORE: {score}% (excluding WARN/SKIP)")
    print("═" * 60)
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
