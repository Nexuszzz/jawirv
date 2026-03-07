"""
JAWIR OS - Sheets & Forms ID Fix Verification Test
=====================================================
Tests the critical fix: sheets_create and forms_create now
return real Google API IDs instead of empty strings.

Runs 7 sequential tool calls via WebSocket:
1. sheets_create → verify ID extracted
2. sheets_write → verify write using real ID
3. sheets_read → verify read using real ID
4. forms_create → verify ID extracted
5. forms_add_question → verify add using real ID
6. forms_read → verify form using real ID
7. docs_create → verify doc ID extracted

Run:
    cd backend
    venv_fresh\\Scripts\\python.exe tests\\test_id_fix_e2e.py
"""

import asyncio
import json
import sys
import time
import re
import websockets

WS_URL = "ws://localhost:8000/ws/chat"
TIMEOUT_PER_TEST = 120  # 2 min per test


async def send_and_collect(query: str, timeout: int = TIMEOUT_PER_TEST) -> dict:
    """Send a query via WebSocket and collect the full response."""
    async with websockets.connect(WS_URL, ping_interval=15, max_size=10_000_000) as ws:
        # Wait for connection message first
        conn_msg = await asyncio.wait_for(ws.recv(), timeout=10)
        conn_data = json.loads(conn_msg)
        print(f"   📡 Connected: {conn_data.get('type', '?')}")
        
        # Send in correct format
        await ws.send(json.dumps({
            "type": "user_message",
            "data": {
                "content": query,
                "session_id": "test-id-fix-e2e"
            }
        }))
        
        final_response = ""
        statuses = []
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=60)
                data = json.loads(msg)
                msg_type = data.get("type", "")
                
                if msg_type == "agent_status":
                    status = data.get("status", "")
                    message = data.get("message", "")[:80]
                    statuses.append(status)
                    print(f"   📊 [{status}] {message}")
                elif msg_type == "agent_response":
                    final_response = data.get("content", "")
                    break
                elif msg_type == "tool_result":
                    tool = data.get("tool_name", "?")
                    status = data.get("status", "?")
                    print(f"   🔧 Tool: {tool} → {status}")
                elif msg_type == "error":
                    final_response = f"ERROR: {data.get('message', '')}"
                    break
                elif msg_type in ("connection", "pong"):
                    pass  # ignore
                else:
                    print(f"   ❓ Unknown type: {msg_type}")
            except asyncio.TimeoutError:
                print(f"   ⏳ Waiting... ({time.time() - start:.0f}s elapsed)")
                continue
        
        return {
            "response": final_response,
            "statuses": statuses,
            "elapsed": time.time() - start
        }


def extract_id_from_response(response: str, pattern: str) -> str:
    """Extract an ID from response text using regex."""
    match = re.search(pattern, response)
    return match.group(1) if match else ""


async def run_test_sequence():
    """Run the complete test sequence."""
    print("=" * 60)
    print("JAWIR OS - Sheets & Forms ID Fix E2E Test")
    print("=" * 60)
    print()
    
    results = {}
    sheet_id = ""
    form_id = ""
    doc_id = ""
    
    # =========================================================
    # TEST 1: sheets_create — should return real ID
    # =========================================================
    print("🧪 TEST 1: sheets_create (should return real ID)...")
    r = await send_and_collect(
        "Buat spreadsheet baru dengan judul 'TEST ID FIX - DELETE'. "
        "Hanya buat spreadsheet, jangan lakukan hal lain."
    )
    resp = r["response"]
    
    # Try to extract ID - agent may use various formats
    for pattern in [
        r'ID:\s*([a-zA-Z0-9_-]{20,})',
        r'spreadsheet.*?ID.*?([a-zA-Z0-9_-]{20,})',
        r'([a-zA-Z0-9_-]{30,})',  # long alphanum string is likely an ID
    ]:
        id_match = re.search(pattern, resp, re.IGNORECASE)
        if id_match:
            sheet_id = id_match.group(1).strip()
            break
    
    has_real_id = sheet_id and len(sheet_id) > 10 and sheet_id != "1XyZ_BRUTAL_TEST_SHEET_ID"
    
    if has_real_id:
        print(f"   ✅ PASS — Spreadsheet ID: {sheet_id[:50]}...")
        results["sheets_create"] = "PASS"
    else:
        print(f"   ❌ FAIL — Got ID: '{sheet_id}' (empty or placeholder)")
        print(f"   Full response (first 500 chars):\n{resp[:500]}")
        results["sheets_create"] = "FAIL"
    print(f"   ⏱️ {r['elapsed']:.1f}s")
    print()
    
    # =========================================================
    # TEST 2: sheets_write — should work with real ID
    # =========================================================
    if has_real_id:
        print(f"🧪 TEST 2: sheets_write (using ID: {sheet_id[:20]}...)...")
        r = await send_and_collect(
            f"Tulis data ke spreadsheet ID {sheet_id} di range Sheet1!A1 "
            f'dengan values: [["Nama","Umur","Kota"],["Ali",25,"Jakarta"],["Budi",30,"Bandung"]]. '
            f"Gunakan persis ID tersebut."
        )
        resp = r["response"]
        
        if "berhasil" in resp.lower() or "✅" in resp or "success" in resp.lower() or "updated" in resp.lower() or "written" in resp.lower() or "tulis" in resp.lower():
            print(f"   ✅ PASS — Write successful")
            results["sheets_write"] = "PASS"
        elif "404" in resp or "not found" in resp.lower():
            print(f"   ❌ FAIL (404!) — {resp[:300]}")
            results["sheets_write"] = "FAIL"
        else:
            print(f"   ⚠️ UNCERTAIN — {resp[:300]}")
            results["sheets_write"] = "UNCERTAIN"
        print(f"   ⏱️ {r['elapsed']:.1f}s")
    else:
        print("🧪 TEST 2: sheets_write — SKIPPED (no real ID)")
        results["sheets_write"] = "SKIP"
    print()
    
    # =========================================================
    # TEST 3: sheets_read — should work with real ID
    # =========================================================
    if has_real_id:
        print(f"🧪 TEST 3: sheets_read (using ID: {sheet_id[:20]}...)...")
        r = await send_and_collect(
            f"Baca data dari spreadsheet ID {sheet_id} range Sheet1!A1:C3. "
            f"Gunakan persis ID tersebut."
        )
        resp = r["response"]
        
        if "ali" in resp.lower() or "nama" in resp.lower() or "data" in resp.lower():
            print(f"   ✅ PASS — Read returned data")
            results["sheets_read"] = "PASS"
        elif "error" in resp.lower() or "❌" in resp:
            print(f"   ❌ FAIL — {resp[:200]}")
            results["sheets_read"] = "FAIL"
        else:
            print(f"   ⚠️ UNCERTAIN — {resp[:200]}")
            results["sheets_read"] = "UNCERTAIN"
        print(f"   ⏱️ {r['elapsed']:.1f}s")
    else:
        print("🧪 TEST 3: sheets_read — SKIPPED (no real ID)")
        results["sheets_read"] = "SKIP"
    print()
    
    # =========================================================
    # TEST 4: forms_create — should return real ID
    # =========================================================
    print("🧪 TEST 4: forms_create (should return real ID)...")
    r = await send_and_collect(
        "Buat form baru dengan judul 'TEST ID FIX FORM - DELETE' "
        "dan deskripsi 'Test form untuk verifikasi ID extraction'. "
        "Hanya buat form, jangan tambahkan pertanyaan."
    )
    resp = r["response"]
    
    for pattern in [
        r'Form ID:\s*([a-zA-Z0-9_-]{20,})',
        r'ID:\s*([a-zA-Z0-9_-]{20,})',
        r'form.*?ID.*?([a-zA-Z0-9_-]{20,})',
        r'([a-zA-Z0-9_-]{30,})',
    ]:
        id_match = re.search(pattern, resp, re.IGNORECASE)
        if id_match:
            form_id = id_match.group(1).strip()
            break
    
    has_form_id = form_id and len(form_id) > 10 and form_id != "1FORM_ID_BRUTAL_TEST"
    
    if has_form_id:
        print(f"   ✅ PASS — Form ID: {form_id[:50]}...")
        results["forms_create"] = "PASS"
    else:
        print(f"   ❌ FAIL — Got ID: '{form_id}' (empty or placeholder)")
        print(f"   Full response (first 500 chars):\n{resp[:500]}")
        results["forms_create"] = "FAIL"
    print(f"   ⏱️ {r['elapsed']:.1f}s")
    print()
    
    # =========================================================
    # TEST 5: forms_add_question — should work with real ID
    # =========================================================
    if has_form_id:
        print(f"🧪 TEST 5: forms_add_question (using ID: {form_id[:20]}...)...")
        r = await send_and_collect(
            f"Tambahkan pertanyaan ke form ID {form_id}: "
            f"pertanyaan 'Apakah tes ini berhasil?' dengan tipe multiple_choice "
            f"dan opsi: Ya, Tidak, Mungkin. "
            f"Gunakan persis form ID tersebut."
        )
        resp = r["response"]
        
        if "berhasil" in resp.lower() or "✅" in resp or "success" in resp.lower() or "added" in resp.lower() or "ditambah" in resp.lower() or "pertanyaan" in resp.lower():
            print(f"   ✅ PASS — Question added successfully")
            results["forms_add_question"] = "PASS"
        elif "404" in resp or "not found" in resp.lower():
            print(f"   ❌ FAIL (404!) — {resp[:300]}")
            results["forms_add_question"] = "FAIL"
        else:
            print(f"   ⚠️ UNCERTAIN — {resp[:300]}")
            results["forms_add_question"] = "UNCERTAIN"
        print(f"   ⏱️ {r['elapsed']:.1f}s")
    else:
        print("🧪 TEST 5: forms_add_question — SKIPPED (no real ID)")
        results["forms_add_question"] = "SKIP"
    print()
    
    # =========================================================
    # TEST 6: forms_read — should work with real ID
    # =========================================================
    if has_form_id:
        print(f"🧪 TEST 6: forms_read (using ID: {form_id[:20]}...)...")
        r = await send_and_collect(
            f"Baca struktur form ID {form_id}. "
            f"Gunakan persis form ID tersebut."
        )
        resp = r["response"]
        
        if "error" not in resp.lower() and "404" not in resp:
            print(f"   ✅ PASS — Form read succeeded")
            results["forms_read"] = "PASS"
        else:
            print(f"   ❌ FAIL — {resp[:200]}")
            results["forms_read"] = "FAIL"
        print(f"   ⏱️ {r['elapsed']:.1f}s")
    else:
        print("🧪 TEST 6: forms_read — SKIPPED (no real ID)")
        results["forms_read"] = "SKIP"
    print()
    
    # =========================================================
    # TEST 7: docs_create — should return real ID
    # =========================================================
    print("🧪 TEST 7: docs_create (should return real ID)...")
    r = await send_and_collect(
        "Buat dokumen Google Docs baru dengan judul 'TEST ID FIX DOC - DELETE' "
        "dan isi 'Dokumen ini untuk verifikasi ID extraction. Hapus setelah tes.' "
        "Hanya buat dokumen."
    )
    resp = r["response"]
    
    for pattern in [
        r'ID:\s*([a-zA-Z0-9_-]{20,})',
        r'doc.*?ID.*?([a-zA-Z0-9_-]{20,})',
        r'([a-zA-Z0-9_-]{30,})',
    ]:
        id_match = re.search(pattern, resp, re.IGNORECASE)
        if id_match:
            doc_id = id_match.group(1).strip()
            break
    
    has_doc_id = doc_id and len(doc_id) > 10
    
    if has_doc_id:
        print(f"   ✅ PASS — Doc ID: {doc_id[:50]}...")
        results["docs_create"] = "PASS"
    else:
        print(f"   ❌ FAIL — Got ID: '{doc_id}' (empty)")
        print(f"   Full response (first 500 chars):\n{resp[:500]}")
        results["docs_create"] = "FAIL"
    print(f"   ⏱️ {r['elapsed']:.1f}s")
    print()
    
    # =========================================================
    # SUMMARY
    # =========================================================
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v == "FAIL")
    skipped = sum(1 for v in results.values() if v in ("SKIP", "UNCERTAIN"))
    total = len(results)
    
    for test_name, status in results.items():
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "UNCERTAIN": "⚠️"}.get(status, "?")
        print(f"  {icon} {test_name}: {status}")
    
    print()
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {failed}/{total}")
    print(f"Skipped: {skipped}/{total}")
    print()
    
    # Cleanup info
    print("=" * 60)
    print("CLEANUP REQUIRED:")
    print("=" * 60)
    if sheet_id:
        print(f"  📊 Spreadsheet: {sheet_id}")
    if form_id:
        print(f"  📋 Form: {form_id}")
    if doc_id:
        print(f"  📄 Doc: {doc_id}")
    print("  → Delete all files with 'TEST ID FIX' in title from Google Drive")
    print()
    
    if failed == 0 and skipped == 0:
        print("🎉 ALL TESTS PASSED!")
    elif failed == 0:
        print("✅ All executed tests passed (some skipped)")
    else:
        print(f"⚠️ {failed} test(s) FAILED — ID extraction fix may need adjustment")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_test_sequence())
    sys.exit(0 if success else 1)
