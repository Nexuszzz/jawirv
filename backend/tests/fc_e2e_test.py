"""
JAWIR OS — V2 Function Calling E2E Test (Phase 3C)
Sends prompts that SHOULD trigger tool calls via Gemini FC.
Validates: tool_result events + agent_response arrive.
"""
import asyncio
import websockets
import json
import time
import sys

WS_URI = "ws://127.0.0.1:8000/ws/chat"


async def fc_test(prompt: str, expect_tool: str = None, timeout: int = 90):
    """
    Send a prompt, collect all WS events, check for tool_result + agent_response.
    """
    received = []
    tool_results = []
    agent_response = None
    error_msg = None

    try:
        async with websockets.connect(WS_URI) as ws:
            # Consume welcome
            await asyncio.wait_for(ws.recv(), timeout=5)

            # Send user message
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": prompt,
                    "session_id": f"fc-test-{int(time.time())}"
                }
            }))
            print(f"  SENT: {prompt[:60]}")

            start = time.time()
            while time.time() - start < timeout:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=60)
                    data = json.loads(msg)
                    received.append(data)
                    mtype = data.get("type", "")

                    if mtype == "agent_status":
                        status = data.get("status", "")
                        if status not in ("thinking", "idle"):
                            print(f"    [status] {status}: {str(data.get('message',''))[:50]}")
                    elif mtype == "tool_result":
                        tn = data.get("tool_name", "?")
                        ts = data.get("status", "?")
                        tool_results.append(data)
                        print(f"    [tool_result] {tn} -> {ts}")
                    elif mtype == "agent_response":
                        agent_response = data.get("content", "")
                        print(f"    [agent_response] len={len(agent_response)}")
                        break
                    elif mtype == "error":
                        error_msg = data.get("message", "")
                        print(f"    [ERROR] {error_msg}")
                        break

                except asyncio.TimeoutError:
                    print(f"    [!] Timeout after 60s")
                    break

    except Exception as e:
        error_msg = str(e)
        print(f"    [EXCEPTION] {e}")

    # Evaluate
    has_tool = len(tool_results) > 0
    has_response = agent_response is not None
    has_error = error_msg is not None

    if expect_tool:
        tool_names = [tr.get("tool_name") for tr in tool_results]
        matched = expect_tool in tool_names
    else:
        matched = True  # No specific tool expected

    if has_response and (not expect_tool or matched):
        return "PASS", tool_results, agent_response
    elif has_error:
        return "FAIL_ERROR", tool_results, error_msg
    elif has_response and not matched:
        return "PARTIAL", tool_results, agent_response
    else:
        return "FAIL_TIMEOUT", tool_results, None


async def main():
    print("=" * 60)
    print("JAWIR OS — V2 Function Calling E2E Tests")
    print("=" * 60)

    tests = [
        {
            "name": "FC-1: IoT list devices",
            "prompt": "Tolong tampilkan semua perangkat IoT yang terhubung",
            "expect_tool": "iot_list_devices",
        },
        {
            "name": "FC-2: Web search",
            "prompt": "Cari di internet: harga Raspberry Pi 5 terbaru 2026",
            "expect_tool": "web_search",
        },
        {
            "name": "FC-3: IoT device state",
            "prompt": "Berapa suhu ruangan dari sensor kipas fan-01?",
            "expect_tool": "iot_get_device_state",
        },
    ]

    results = []
    for tc in tests:
        print(f"\n--- {tc['name']} ---")
        status, tools, resp = await fc_test(tc["prompt"], tc.get("expect_tool"))
        icon = "✅" if status == "PASS" else ("⚠️" if status == "PARTIAL" else "❌")
        print(f"  RESULT: {icon} {status}")
        if tools:
            print(f"  Tools called: {[t.get('tool_name') for t in tools]}")
        results.append({"name": tc["name"], "status": status})

    # Summary
    print(f"\n{'='*60}")
    passed = sum(1 for r in results if r["status"] == "PASS")
    partial = sum(1 for r in results if r["status"] == "PARTIAL")
    failed = sum(1 for r in results if r["status"].startswith("FAIL"))
    print(f"PASS: {passed} / PARTIAL: {partial} / FAIL: {failed} / TOTAL: {len(results)}")
    for r in results:
        icon = "✅" if r["status"] == "PASS" else ("⚠️" if r["status"] == "PARTIAL" else "❌")
        print(f"  {icon} {r['name']}: {r['status']}")

    if failed > 0:
        print("\nOVERALL: FAIL ❌")
        sys.exit(1)
    else:
        print("\nOVERALL: PASS ✅")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
