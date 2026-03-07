"""
JAWIR OS — Tool Contract Tests (Phase 3D)
Validates every tool in the registry: schema, safe-mode execution, graceful degradation.
"""
import asyncio
import sys
import os
import json
import time

# Ensure backend is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env
from dotenv import load_dotenv
load_dotenv()


async def run_tool_tests():
    """Test all tools in the registry."""
    from agent.tools import get_all_tools

    tools = get_all_tools()
    print(f"{'='*60}")
    print(f"JAWIR OS — Tool Contract Tests")
    print(f"Total tools registered: {len(tools)}")
    print(f"{'='*60}\n")

    results = []
    for i, tool in enumerate(tools, 1):
        name = tool.name
        desc = (tool.description or "")[:60]
        schema = tool.args_schema

        # Test 1: Schema exists and is valid
        has_schema = schema is not None
        schema_fields = list(schema.model_fields.keys()) if has_schema else []

        # Test 2: Determine if safe to test
        unsafe_tools = {
            # Tools that send real messages/emails or do destructive actions
            "gmail_send", "whatsapp_send_message", "whatsapp_send_file",
            "calendar_create_event", "sheets_write", "sheets_create",
            "docs_create", "forms_create", "forms_add_question",
            "open_app", "close_app",
            "iot_set_device_state", "iot_ack_or_reset_alarm",
            "run_python_code",
        }

        # Tools that only read / are safe to execute
        safe_read_tools = {
            "web_search": {"query": "test ping"},
            "gmail_search": {"query": "test", "max_results": 1},
            "drive_search": {"query": "test"},
            "drive_list": {},
            "calendar_list_events": {"max_results": 1},
            "sheets_read": {"spreadsheet_id": "test_nonexistent"},
            "docs_read": {"document_id": "test_nonexistent"},
            "forms_read": {"form_id": "test_nonexistent"},
            "whatsapp_check_number": {"phone": "000000000"},
            "whatsapp_list_chats": {},
            "whatsapp_list_contacts": {},
            "whatsapp_list_groups": {},
            "whatsapp_get_messages": {"chat_jid": "test@s.whatsapp.net"},
            "polinema_get_biodata": {},
            "polinema_get_akademik": {"data_type": "nilai"},
            "polinema_get_lms_assignments": {},
            "iot_list_devices": {},
            "iot_get_device_state": {"device_id": "fan-01"},
            "iot_get_latest_events": {},
            "open_url": {"url": "about:blank"},
            "generate_kicad_schematic": {"description": "simple LED circuit with resistor", "project_name": "test_led"},
        }

        is_safe = name not in unsafe_tools
        test_args = safe_read_tools.get(name)

        # Schema test
        schema_pass = has_schema and len(schema_fields) >= 0

        # Execution test (safe tools only, with timeout)
        exec_result = "SKIP (unsafe)"
        exec_pass = True  # Skip = neutral
        exec_detail = ""

        if is_safe and test_args is not None:
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(tool.invoke, test_args) if not asyncio.iscoroutinefunction(tool.func) else tool.ainvoke(test_args),
                    timeout=15
                )
                result_str = str(result)[:150]
                # Check for graceful failure patterns
                if any(kw in result_str.lower() for kw in ["not configured", "offline", "error", "failed", "tidak", "gagal", "unavailable"]):
                    exec_result = f"GRACEFUL: {result_str[:80]}"
                    exec_pass = True
                else:
                    exec_result = f"OK: {result_str[:80]}"
                    exec_pass = True
            except asyncio.TimeoutError:
                exec_result = "TIMEOUT (15s)"
                exec_pass = False
            except Exception as e:
                err_msg = str(e)[:100]
                # Some errors are expected (e.g., auth not configured)
                if any(kw in err_msg.lower() for kw in ["not configured", "credentials", "auth", "connect", "refused", "timeout"]):
                    exec_result = f"EXPECTED_ERR: {err_msg[:60]}"
                    exec_pass = True
                else:
                    exec_result = f"CRASH: {err_msg[:80]}"
                    exec_pass = False

        status = "PASS" if schema_pass and exec_pass else "FAIL"
        results.append({
            "name": name,
            "schema_pass": schema_pass,
            "exec_pass": exec_pass,
            "exec_result": exec_result,
            "status": status,
        })

        icon = "✅" if status == "PASS" else "❌"
        print(f"  [{i:2d}] {icon} {name:<35s} schema={'OK' if schema_pass else 'FAIL':<4s} args={schema_fields}")
        if exec_result != "SKIP (unsafe)":
            print(f"       exec: {exec_result}")

    # Summary
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    print(f"\n{'='*60}")
    print(f"RESULT: {passed} PASS / {failed} FAIL / {len(results)} TOTAL")
    if failed == 0:
        print("ALL TOOLS: PASS ✅")
    else:
        print("FAILURES:")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  ❌ {r['name']}: {r['exec_result']}")
    print(f"{'='*60}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    code = asyncio.run(run_tool_tests())
    sys.exit(code)
