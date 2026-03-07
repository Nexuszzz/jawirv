"""
JAWIR OS - Complex ReAct Loop Test Suite
Tests the agentic workflow: Plan → Act → Observe → Loop

This test proves JAWIR can:
1. Break down complex queries into sub-tasks (Planning)
2. Execute multiple searches iteratively (Acting)
3. Validate results and retry if needed (Observing + Looping)
4. Synthesize comprehensive answers (Final Output)
"""

import asyncio
import json
import time
from datetime import datetime
import websockets

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_phase(phase, emoji):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{emoji} [{phase}]{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")

def print_status(status, message):
    color = {
        'thinking': Colors.YELLOW,
        'planning': Colors.BLUE,
        'searching': Colors.CYAN,
        'reading': Colors.CYAN,
        'writing': Colors.GREEN,
        'done': Colors.GREEN,
        'error': Colors.RED,
    }.get(status, Colors.ENDC)
    
    emoji = {
        'thinking': '🧠',
        'planning': '📋',
        'searching': '🔍',
        'reading': '📖',
        'writing': '✍️',
        'done': '✅',
        'error': '❌',
    }.get(status, '📌')
    
    print(f"  {emoji} {color}{status.upper():12}{Colors.ENDC} │ {message}")

def print_tool_result(title, sources_count):
    print(f"  🔧 {Colors.GREEN}TOOL RESULT{Colors.ENDC}  │ {title} ({sources_count} sources)")

def print_metric(name, value, unit=""):
    print(f"  📊 {name:20} │ {Colors.BOLD}{value}{Colors.ENDC} {unit}")


# =============================================================================
# TEST CASES - Complex queries to test ReAct capabilities
# =============================================================================

TEST_CASES = [
    {
        "id": "TC001",
        "name": "Multi-Step Comparison Query",
        "query": "Bandingkan ESP32 vs STM32 vs Arduino Nano untuk proyek IoT rumah pintar. Mana yang terbaik dari segi harga, performa, dan kemudahan pemrograman? Berikan tabel perbandingan lengkap.",
        "expected": {
            "min_steps": 3,          # Should plan at least 3 steps
            "min_sources": 5,        # Should gather at least 5 sources
            "must_contain": ["ESP32", "STM32", "Arduino", "tabel", "perbandingan"],
            "description": "Tests multi-step planning and comparison synthesis"
        }
    },
    {
        "id": "TC002", 
        "name": "Deep Technical Research",
        "query": "Jelaskan arsitektur internal ESP32-S3 secara mendalam, termasuk dual-core Xtensa LX7, AI acceleration, dan USB OTG. Bagaimana cara mengoptimalkan konsumsi daya untuk aplikasi baterai?",
        "expected": {
            "min_steps": 4,
            "min_sources": 5,
            "must_contain": ["Xtensa", "dual-core", "AI", "daya", "baterai"],
            "description": "Tests deep technical research with multiple facets"
        }
    },
    {
        "id": "TC003",
        "name": "Practical Implementation Query",
        "query": "Bagaimana cara membuat sistem monitoring suhu dan kelembaban menggunakan ESP32 dan sensor DHT22 yang data-nya bisa diakses via web dashboard? Jelaskan komponen yang dibutuhkan, wiring diagram, dan kode program.",
        "expected": {
            "min_steps": 4,
            "min_sources": 4,
            "must_contain": ["ESP32", "DHT22", "web", "kode", "komponen"],
            "description": "Tests practical implementation guidance"
        }
    },
]


async def run_test_case(test_case: dict) -> dict:
    """Run a single test case and collect metrics."""
    
    uri = "ws://localhost:8000/ws/chat"
    results = {
        "test_id": test_case["id"],
        "test_name": test_case["name"],
        "query": test_case["query"],
        "start_time": None,
        "end_time": None,
        "duration_seconds": 0,
        "phases": [],
        "plan_steps": 0,
        "sources_found": 0,
        "retry_count": 0,
        "validation_result": None,
        "final_response": None,
        "response_length": 0,
        "sources_used": [],
        "thinking_process": [],
        "success": False,
        "error": None,
    }
    
    print_header(f"TEST: {test_case['id']} - {test_case['name']}")
    print(f"{Colors.YELLOW}Query:{Colors.ENDC} {test_case['query'][:100]}...")
    print(f"{Colors.BLUE}Expected:{Colors.ENDC} {test_case['expected']['description']}")
    
    start_time = time.time()
    results["start_time"] = datetime.now().isoformat()
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            # Skip welcome message
            welcome = await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send query
            print_phase("SENDING QUERY", "📤")
            await websocket.send(json.dumps({
                "type": "user_message",
                "data": {"content": test_case["query"]}
            }))
            print(f"  📤 Query sent ({len(test_case['query'])} chars)")
            
            # Collect responses
            print_phase("REACT LOOP EXECUTION", "🔄")
            
            current_phase = None
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=120)
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        print_status(status, message)
                        results["phases"].append({
                            "status": status,
                            "message": message,
                            "timestamp": data.get("timestamp")
                        })
                        
                        # Track planning steps
                        if status == "planning" and "plan" in details:
                            results["plan_steps"] = len(details["plan"])
                            print(f"      └─ {Colors.BLUE}Plan has {results['plan_steps']} steps{Colors.ENDC}")
                            for i, step in enumerate(details["plan"], 1):
                                print(f"         {i}. {step[:60]}...")
                        
                        # Track validation
                        if "validation" in message.lower() or "retry" in message.lower():
                            results["retry_count"] += 1
                    
                    elif msg_type == "tool_result":
                        tool_data = data.get("data", {})
                        title = tool_data.get("title", "Research")
                        sources = tool_data.get("sources", [])
                        results["sources_found"] += len(sources)
                        print_tool_result(title, len(sources))
                    
                    elif msg_type == "agent_response":
                        # Final response received
                        content = data.get("content", "")
                        results["final_response"] = content
                        results["response_length"] = len(content)
                        results["sources_used"] = data.get("sources_used", [])
                        results["thinking_process"] = data.get("thinking_process", [])
                        
                        print_phase("FINAL RESPONSE RECEIVED", "🎯")
                        print(f"  📝 Response length: {len(content)} characters")
                        print(f"  📚 Sources used: {len(results['sources_used'])}")
                        print(f"  🧠 Thinking steps: {len(results['thinking_process'])}")
                        break
                    
                    elif msg_type == "error":
                        error_msg = data.get("message", "Unknown error")
                        results["error"] = error_msg
                        print(f"  {Colors.RED}❌ ERROR: {error_msg}{Colors.ENDC}")
                        break
                        
                except asyncio.TimeoutError:
                    results["error"] = "Timeout waiting for response"
                    print(f"  {Colors.RED}⏱️ TIMEOUT{Colors.ENDC}")
                    break
        
        # Calculate duration
        end_time = time.time()
        results["end_time"] = datetime.now().isoformat()
        results["duration_seconds"] = round(end_time - start_time, 2)
        
        # Validate results
        print_phase("VALIDATION", "✅")
        
        expected = test_case["expected"]
        validations = []
        
        # Check plan steps
        if results["plan_steps"] >= expected["min_steps"]:
            validations.append(("Plan Steps", True, f"{results['plan_steps']} >= {expected['min_steps']}"))
        else:
            validations.append(("Plan Steps", False, f"{results['plan_steps']} < {expected['min_steps']}"))
        
        # Check sources
        if results["sources_found"] >= expected["min_sources"]:
            validations.append(("Sources Found", True, f"{results['sources_found']} >= {expected['min_sources']}"))
        else:
            validations.append(("Sources Found", False, f"{results['sources_found']} < {expected['min_sources']}"))
        
        # Check content keywords
        response_lower = (results["final_response"] or "").lower()
        for keyword in expected["must_contain"]:
            if keyword.lower() in response_lower:
                validations.append((f"Contains '{keyword}'", True, "Found"))
            else:
                validations.append((f"Contains '{keyword}'", False, "Not found"))
        
        # Print validation results
        all_passed = True
        for name, passed, detail in validations:
            status = f"{Colors.GREEN}PASS{Colors.ENDC}" if passed else f"{Colors.RED}FAIL{Colors.ENDC}"
            print(f"  {status} │ {name}: {detail}")
            if not passed:
                all_passed = False
        
        results["success"] = all_passed and results["final_response"] is not None
        
        # Print metrics
        print_phase("METRICS", "📊")
        print_metric("Duration", results["duration_seconds"], "seconds")
        print_metric("Plan Steps", results["plan_steps"])
        print_metric("Sources Found", results["sources_found"])
        print_metric("Retry Count", results["retry_count"])
        print_metric("Response Length", results["response_length"], "chars")
        print_metric("Sources Cited", len(results["sources_used"]))
        
        # Print response preview
        if results["final_response"]:
            print_phase("RESPONSE PREVIEW", "📜")
            preview = results["final_response"][:500]
            print(f"{Colors.GREEN}{preview}...{Colors.ENDC}")
        
    except Exception as e:
        results["error"] = str(e)
        results["end_time"] = datetime.now().isoformat()
        results["duration_seconds"] = round(time.time() - start_time, 2)
        print(f"\n{Colors.RED}❌ TEST ERROR: {e}{Colors.ENDC}")
    
    return results


async def run_all_tests():
    """Run all test cases and generate report."""
    
    print_header("JAWIR OS - ReAct Agentic Workflow Test Suite")
    print(f"{Colors.CYAN}Testing iterative planning, research, validation, and synthesis{Colors.ENDC}")
    print(f"{Colors.YELLOW}Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    
    all_results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{Colors.BOLD}Running Test {i}/{len(TEST_CASES)}...{Colors.ENDC}")
        result = await run_test_case(test_case)
        all_results.append(result)
        
        # Brief pause between tests
        if i < len(TEST_CASES):
            print(f"\n{Colors.YELLOW}⏳ Waiting 3 seconds before next test...{Colors.ENDC}")
            await asyncio.sleep(3)
    
    # =========================================================================
    # FINAL REPORT
    # =========================================================================
    print_header("FINAL TEST REPORT")
    
    passed = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - passed
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Tests: {len(all_results)}")
    print(f"  {Colors.GREEN}Passed: {passed}{Colors.ENDC}")
    print(f"  {Colors.RED}Failed: {failed}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Individual Results:{Colors.ENDC}")
    for r in all_results:
        status = f"{Colors.GREEN}✅ PASS{Colors.ENDC}" if r["success"] else f"{Colors.RED}❌ FAIL{Colors.ENDC}"
        print(f"  {status} │ {r['test_id']}: {r['test_name']} ({r['duration_seconds']}s)")
    
    # Aggregate metrics
    print(f"\n{Colors.BOLD}Aggregate Metrics:{Colors.ENDC}")
    total_duration = sum(r["duration_seconds"] for r in all_results)
    avg_duration = total_duration / len(all_results) if all_results else 0
    total_sources = sum(r["sources_found"] for r in all_results)
    avg_steps = sum(r["plan_steps"] for r in all_results) / len(all_results) if all_results else 0
    
    print_metric("Total Duration", round(total_duration, 2), "seconds")
    print_metric("Avg Duration/Query", round(avg_duration, 2), "seconds")
    print_metric("Total Sources Found", total_sources)
    print_metric("Avg Plan Steps", round(avg_steps, 1))
    
    # ReAct Pattern Analysis
    print(f"\n{Colors.BOLD}ReAct Pattern Analysis:{Colors.ENDC}")
    print(f"  🧠 {Colors.YELLOW}REASON{Colors.ENDC}  │ Supervisor creates multi-step plans")
    print(f"  ⚡ {Colors.CYAN}ACT{Colors.ENDC}     │ Researcher executes web searches")
    print(f"  👁️ {Colors.GREEN}OBSERVE{Colors.ENDC} │ Validator checks if research is sufficient")
    print(f"  🔄 {Colors.BLUE}LOOP{Colors.ENDC}    │ Retry if validation fails (retry count tracked)")
    
    # Conclusion
    if passed == len(all_results):
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! JAWIR OS ReAct workflow is working correctly.{Colors.ENDC}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ Some tests failed. Review the results above.{Colors.ENDC}")
    
    # Save report
    report_path = "test_results_react.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n📁 Full report saved to: {report_path}")
    
    return all_results


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" JAWIR OS - Agentic ReAct Workflow Test")
    print(" Testing: Plan → Act → Observe → Loop")
    print("="*60 + "\n")
    
    asyncio.run(run_all_tests())
