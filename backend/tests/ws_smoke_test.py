"""
JAWIR OS — WebSocket Smoke Test
Tests: connect, send user_message, validate full response flow
"""
import asyncio
import websockets
import json
import time
import sys

WS_URI = "ws://127.0.0.1:8000/ws/chat"
TIMEOUT_TOTAL = 60
TIMEOUT_MSG = 30


async def ws_smoke_test():
    """Core WS E2E test."""
    received = []
    try:
        async with websockets.connect(WS_URI) as ws:
            # 1) Wait for connection welcome
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            received.append(data)
            print(f"[1] RECV type={data.get('type')}: {str(data.get('message',''))[:80]}")

            # 2) Send user_message — backend expects nested data.content
            payload = {
                "type": "user_message",
                "data": {
                    "content": "Halo, list semua tools yang kamu punya",
                    "session_id": "smoke-test-001"
                }
            }
            await ws.send(json.dumps(payload))
            print("[2] SENT: user_message")

            # 3) Collect all responses
            start = time.time()
            while time.time() - start < TIMEOUT_TOTAL:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT_MSG)
                    data = json.loads(msg)
                    received.append(data)
                    mtype = data.get("type", "")

                    if mtype == "agent_status":
                        print(f"  [status] {data.get('status')} — {str(data.get('message',''))[:60]}")
                    elif mtype == "tool_result":
                        print(f"  [tool_result] {data.get('tool_name','?')} status={data.get('status')}")
                    elif mtype == "agent_response":
                        content = data.get("content", "")
                        print(f"  [agent_response] len={len(content)}, preview: {content[:150]}")
                        break  # Final response received
                    elif mtype == "error":
                        print(f"  [ERROR] {data.get('message','')}")
                        break
                    elif mtype == "stream":
                        pass  # Ignore stream chunks in summary
                    else:
                        print(f"  [{mtype}] {str(data)[:100]}")

                except asyncio.TimeoutError:
                    print(f"  [!] Timeout after {TIMEOUT_MSG}s waiting for next message")
                    break

            # 4) Summary
            types = [r.get("type") for r in received]
            has_response = "agent_response" in types
            has_error = "error" in types
            has_status = "agent_status" in types

            print(f"\n{'='*50}")
            print(f"Total messages received: {len(received)}")
            print(f"Message types: {types}")
            print(f"Has agent_status: {has_status}")
            print(f"Has agent_response: {has_response}")
            print(f"Has error: {has_error}")
            print(f"{'='*50}")

            if has_response:
                print("RESULT: PASS ✅ — Full response received")
                return 0
            elif has_error:
                # Check if error is recoverable
                err_msgs = [r for r in received if r.get("type") == "error"]
                recoverable = all(e.get("recoverable", False) for e in err_msgs)
                if recoverable:
                    print("RESULT: PARTIAL ⚠️ — Recoverable error (structured)")
                    return 1
                else:
                    print("RESULT: FAIL ❌ — Non-recoverable error")
                    return 2
            else:
                print("RESULT: FAIL ❌ — No response received (possible disconnect)")
                return 2

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"RESULT: FAIL ❌ — WS closed unexpectedly: {e}")
        return 2
    except Exception as e:
        print(f"RESULT: FAIL ❌ — Exception: {e}")
        return 2


async def ws_ping_test():
    """Test that ping/pong works."""
    try:
        async with websockets.connect(WS_URI) as ws:
            # Consume welcome
            await asyncio.wait_for(ws.recv(), timeout=5)
            # Send ping
            await ws.send(json.dumps({"type": "ping"}))
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            if data.get("type") == "pong":
                print("PING/PONG: PASS ✅")
                return 0
            else:
                print(f"PING/PONG: FAIL ❌ — got {data.get('type')}")
                return 1
    except Exception as e:
        print(f"PING/PONG: FAIL ❌ — {e}")
        return 2


async def main():
    print("=" * 50)
    print("JAWIR OS — WebSocket Smoke Test Suite")
    print("=" * 50)

    print("\n--- Test 1: Ping/Pong ---")
    r1 = await ws_ping_test()

    print("\n--- Test 2: Full Chat E2E ---")
    r2 = await ws_smoke_test()

    print(f"\n{'='*50}")
    print(f"FINAL: Ping={'PASS' if r1==0 else 'FAIL'}, Chat={'PASS' if r2==0 else 'FAIL'}")
    sys.exit(max(r1, r2))


if __name__ == "__main__":
    asyncio.run(main())
