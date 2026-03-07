#!/usr/bin/env python
"""
JAWIR OS - 10 Complex Multi-Tool Test Cases
============================================
Tests yang melibatkan multiple tools dan iterasi berulang.
"""

import asyncio
import json
import sys
import time
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Installing websockets...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets


# Test cases dengan kompleksitas berbeda
TEST_CASES = [
    {
        "name": "Test 1: Web Search + Docs Create",
        "query": "Cari info tentang Arduino Uno dan buat dokumen ringkasannya",
        "expected_tools": ["web_search", "docs_create"],
        "timeout": 180,
    },
    {
        "name": "Test 2: Multiple Web Searches",
        "query": "Bandingkan harga Raspberry Pi 4 dan Raspberry Pi 5 di marketplace Indonesia",
        "expected_tools": ["web_search"],
        "timeout": 120,
    },
    {
        "name": "Test 3: Python Execution",
        "query": "Hitung bilangan prima dari 1 sampai 100 menggunakan Python",
        "expected_tools": ["execute_python"],
        "timeout": 60,
    },
    {
        "name": "Test 4: Gmail + Drive Search",
        "query": "Tampilkan daftar label Gmail dan list 5 file terbaru di Drive",
        "expected_tools": ["gmail_get_labels", "drive_list_files"],
        "timeout": 120,
    },
    {
        "name": "Test 5: Docs + Forms Create",
        "query": "Buat dokumen tentang Bahasa Python dasar dengan judul 'Pengenalan Python'",
        "expected_tools": ["docs_create"],
        "timeout": 120,
    },
    {
        "name": "Test 6: Calendar List",
        "query": "Tampilkan daftar kalender Google saya",
        "expected_tools": ["calendar_list"],
        "timeout": 60,
    },
    {
        "name": "Test 7: Desktop Control - Open App",
        "query": "Buka aplikasi notepad",
        "expected_tools": ["open_application"],
        "timeout": 30,
    },
    {
        "name": "Test 8: Web Search Intensif",
        "query": "Cari tutorial lengkap tentang penggunaan sensor DHT22 dengan ESP32, cara wiringnya, dan contoh kodenya",
        "expected_tools": ["web_search"],
        "timeout": 180,
    },
    {
        "name": "Test 9: Multi-step Research + Docs",
        "query": "Cari kelebihan dan kekurangan STM32 vs ESP32, lalu buat dokumen perbandingannya",
        "expected_tools": ["web_search", "docs_create"],
        "timeout": 240,
    },
    {
        "name": "Test 10: Complex Query - Materi + Form",
        "query": "Cari info tentang LED RGB, cara kerjanya dan contoh project dengan Arduino. Buat jadi dokumen materi pembelajaran.",
        "expected_tools": ["web_search", "docs_create"],
        "timeout": 300,
    },
]


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[35m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


async def run_test(test_case: dict, test_num: int) -> dict:
    """Run a single test case."""
    name = test_case["name"]
    query = test_case["query"]
    timeout = test_case["timeout"]
    expected_tools = test_case.get("expected_tools", [])
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}[{test_num}/10] {name}{Colors.ENDC}")
    print(f"{Colors.DIM}Query: {query[:80]}...{Colors.ENDC}")
    print(f"{Colors.DIM}Expected tools: {', '.join(expected_tools)}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.ENDC}")
    
    result = {
        "name": name,
        "query": query,
        "success": False,
        "tools_used": [],
        "response_received": False,
        "response_preview": "",
        "duration": 0,
        "error": None,
    }
    
    start_time = time.time()
    
    try:
        async with websockets.connect(
            "ws://localhost:8000/ws/chat",
            ping_interval=15,
            ping_timeout=30,
            close_timeout=10
        ) as ws:
            # Send message
            msg = {
                "type": "user_message",
                "data": {
                    "content": query,
                    "session_id": f"test_{test_num}_{int(time.time())}",
                }
            }
            await ws.send(json.dumps(msg))
            
            tools_executed = []
            final_response = None
            iterations = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=20)
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        if status == "iteration_start":
                            iterations += 1
                            print(f"  {Colors.BLUE}📍 Iteration {iterations}{Colors.ENDC}")
                        elif status == "thinking":
                            thought = message[:60] + "..." if len(message) > 60 else message
                            print(f"  {Colors.YELLOW}💭 {thought}{Colors.ENDC}")
                        elif status == "planning":
                            tools = details.get("tools", [])
                            print(f"  {Colors.CYAN}📋 Planning: {', '.join(tools)}{Colors.ENDC}")
                        elif status == "executing_tool":
                            tool = details.get("tool", message)
                            tools_executed.append(tool)
                            print(f"  {Colors.GREEN}🔧 Executing: {tool}{Colors.ENDC}")
                        elif status == "observation":
                            obs = message[:50] + "..." if len(message) > 50 else message
                            print(f"  {Colors.MAGENTA}👁️ Observe: {obs}{Colors.ENDC}")
                        elif status == "done":
                            print(f"  {Colors.GREEN}✅ Done{Colors.ENDC}")
                    
                    elif msg_type == "agent_response":
                        content = data.get("content", "") or data.get("data", {}).get("content", "")
                        final_response = content
                        break
                    
                    elif msg_type == "error":
                        error = data.get("message", "Unknown error")
                        result["error"] = error
                        print(f"  {Colors.RED}❌ Error: {error}{Colors.ENDC}")
                        break
                        
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        result["error"] = f"Timeout after {elapsed:.0f}s"
                        print(f"  {Colors.YELLOW}⏳ Timeout after {elapsed:.0f}s{Colors.ENDC}")
                        break
                    print(f"  {Colors.DIM}⏳ Waiting... ({elapsed:.0f}s){Colors.ENDC}")
                    continue
            
            result["duration"] = time.time() - start_time
            result["tools_used"] = tools_executed
            result["response_received"] = final_response is not None
            
            if final_response:
                result["response_preview"] = final_response[:200] + "..." if len(final_response) > 200 else final_response
                # Check if any expected tools were used
                if expected_tools:
                    tools_matched = any(
                        any(exp.lower() in tool.lower() for exp in expected_tools)
                        for tool in tools_executed
                    )
                    result["success"] = tools_matched and result["response_received"]
                else:
                    result["success"] = result["response_received"]
            
    except ConnectionRefusedError:
        result["error"] = "Cannot connect to server"
    except Exception as e:
        result["error"] = str(e)
        result["duration"] = time.time() - start_time
    
    # Print result summary
    if result["success"]:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}✅ PASSED{Colors.ENDC} ({result['duration']:.1f}s)")
        print(f"  {Colors.DIM}Tools: {', '.join(result['tools_used'])}{Colors.ENDC}")
    else:
        print(f"\n  {Colors.RED}{Colors.BOLD}❌ FAILED{Colors.ENDC} ({result['duration']:.1f}s)")
        if result["error"]:
            print(f"  {Colors.RED}Error: {result['error']}{Colors.ENDC}")
    
    return result


async def run_all_tests():
    """Run all 10 test cases."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}  JAWIR OS - 10 Complex Multi-Tool Test Cases{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.ENDC}")
    
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        result = await run_test(test_case, i)
        results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    # Print summary
    passed = sum(1 for r in results if r["success"])
    failed = 10 - passed
    total_duration = sum(r["duration"] for r in results)
    
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}  TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*70}{Colors.ENDC}")
    
    for i, r in enumerate(results, 1):
        status = f"{Colors.GREEN}✅ PASS{Colors.ENDC}" if r["success"] else f"{Colors.RED}❌ FAIL{Colors.ENDC}"
        print(f"  {i:2}. {status} {r['name'][:40]:<40} ({r['duration']:.1f}s)")
    
    print(f"\n{Colors.BOLD}Results:{Colors.ENDC}")
    print(f"  {Colors.GREEN}Passed: {passed}/10{Colors.ENDC}")
    print(f"  {Colors.RED}Failed: {failed}/10{Colors.ENDC}")
    print(f"  Total time: {total_duration:.1f}s")
    print(f"  Success rate: {(passed/10)*100:.0f}%")
    
    if failed > 0:
        print(f"\n{Colors.YELLOW}Failed tests:{Colors.ENDC}")
        for r in results:
            if not r["success"]:
                print(f"  - {r['name']}: {r.get('error', 'No response')}")
    
    return passed == 10


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
