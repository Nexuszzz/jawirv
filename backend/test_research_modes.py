"""
JAWIR OS - Web Research & Deep Research Test
Tests both research modes with ReAct agent pattern.
"""

import asyncio
import json
import time
from datetime import datetime
import websockets


async def test_research_mode(query: str, mode: str = "web"):
    """Test a research query with specified mode."""
    
    uri = "ws://localhost:8000/ws/chat"
    
    print("\n" + "=" * 80)
    print(f" JAWIR OS - {mode.upper()} RESEARCH TEST")
    print("=" * 80)
    print(f"\n📝 QUERY: {query[:100]}...")
    print(f"🔬 MODE: {mode.upper()}")
    
    # Metrics
    phases = []
    plan_steps = 0
    sources_found = 0
    research_iterations = 0
    start_time = time.time()
    
    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=60) as websocket:
            # Skip welcome
            await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send query with research mode
            print("\n📤 Sending query to JAWIR...\n")
            await websocket.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": query,
                    "research_mode": mode  # "web" or "deep"
                }
            }))
            
            print("-" * 80)
            print("🔄 REACT LOOP EXECUTION:")
            print("-" * 80)
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=300)
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        # Map emoji
                        emoji = {
                            'thinking': '🧠',
                            'planning': '📋',
                            'searching': '🔍',
                            'reading': '📖',
                            'validating': '✅',
                            'writing': '✍️',
                            'done': '✅',
                        }.get(status, '📌')
                        
                        print(f"{emoji} [{status.upper():12}] {message}")
                        phases.append(status)
                        
                        # Track iterations
                        if status == "searching":
                            research_iterations += 1
                        
                        # Extract plan details
                        if status == "planning" and "plan" in details:
                            plan_steps = len(details["plan"])
                            print(f"   └─ 📋 Plan created with {plan_steps} steps:")
                            for i, step in enumerate(details["plan"], 1):
                                print(f"      {i}. {step[:70]}...")
                    
                    elif msg_type == "tool_result":
                        tool_data = data.get("data", {})
                        title = tool_data.get("title", "Research")
                        sources = tool_data.get("sources", [])
                        sources_found += len(sources) if isinstance(sources, list) else 0
                        print(f"🔧 [TOOL RESULT  ] {title}")
                        if isinstance(sources, list):
                            for s in sources[:3]:
                                if isinstance(s, dict):
                                    print(f"      - {s.get('title', 'N/A')[:50]}...")
                                else:
                                    print(f"      - {str(s)[:50]}...")
                    
                    elif msg_type == "agent_response":
                        content = data.get("content", "")
                        sources_used = data.get("sources_used", [])
                        thinking = data.get("thinking_process", [])
                        
                        end_time = time.time()
                        duration = round(end_time - start_time, 2)
                        
                        print("\n" + "=" * 80)
                        print("🎯 FINAL RESPONSE RECEIVED")
                        print("=" * 80)
                        
                        # Metrics
                        print(f"\n📊 REACT WORKFLOW METRICS:")
                        print(f"   • Mode:            {mode.upper()} RESEARCH")
                        print(f"   • Duration:        {duration} seconds")
                        print(f"   • Plan Steps:      {plan_steps}")
                        print(f"   • Research Iters:  {research_iterations}")
                        print(f"   • Sources Found:   {sources_found}")
                        print(f"   • Sources Cited:   {len(sources_used)}")
                        print(f"   • Thinking Steps:  {len(thinking)}")
                        print(f"   • Response Length: {len(content)} chars")
                        
                        # Phase breakdown
                        print(f"\n🔄 PHASE BREAKDOWN:")
                        phase_counts = {}
                        for p in phases:
                            phase_counts[p] = phase_counts.get(p, 0) + 1
                        for phase, count in phase_counts.items():
                            print(f"   • {phase}: {count} times")
                        
                        # Response preview
                        print(f"\n📜 RESPONSE PREVIEW:")
                        print("-" * 80)
                        print(content[:1500])
                        if len(content) > 1500:
                            print("\n... [TRUNCATED] ...")
                        print("-" * 80)
                        
                        # Sources
                        if sources_used:
                            print(f"\n📚 SOURCES CITED ({len(sources_used)} total):")
                            for i, s in enumerate(sources_used[:10], 1):
                                if isinstance(s, dict):
                                    url = s.get('url', s.get('title', 'N/A'))
                                    print(f"   {i}. {url[:70]}")
                                else:
                                    print(f"   {i}. {str(s)[:70]}")
                        
                        # ReAct proof
                        print("\n" + "=" * 80)
                        print("✅ REACT PATTERN PROOF:")
                        print("=" * 80)
                        print(f"   🧠 REASON   → Supervisor created {plan_steps}-step plan")
                        print(f"   ⚡ ACT      → Researcher executed {research_iterations} search iterations")
                        print(f"   👁️ OBSERVE  → Validator checked results, sources: {sources_found}")
                        print(f"   ✍️ WRITE    → Synthesizer created {len(content)} char response")
                        if research_iterations > 1:
                            print(f"   🔄 LOOP     → ReAct loop iterated {research_iterations} times!")
                        print("=" * 80)
                        
                        return {
                            "success": True,
                            "duration": duration,
                            "plan_steps": plan_steps,
                            "sources": sources_found,
                            "response_length": len(content),
                            "iterations": research_iterations
                        }
                    
                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {data.get('message', 'Unknown')}")
                        return {"success": False, "error": data.get('message')}
                        
                except asyncio.TimeoutError:
                    print("\n⏱️ TIMEOUT - no response within 300 seconds")
                    return {"success": False, "error": "timeout"}
                    
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        return {"success": False, "error": str(e)}


async def run_all_tests():
    """Run comprehensive research tests."""
    
    print("\n" + "=" * 80)
    print(" JAWIR OS - COMPREHENSIVE RESEARCH TEST SUITE")
    print(" Testing: Web Research & Deep Research with ReAct Pattern")
    print("=" * 80)
    print(f" Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test cases
    test_cases = [
        {
            "name": "Web Research - Technical Comparison",
            "mode": "web",
            "query": """Bandingkan ESP32-S3 vs Raspberry Pi Pico W vs STM32 untuk proyek IoT.
            
            Saya butuh analisis mendalam tentang:
            1. Spesifikasi teknis lengkap (CPU, RAM, Flash, GPIO)
            2. Fitur konektivitas (WiFi, Bluetooth, dll)
            3. Harga di pasaran Indonesia
            4. Kemudahan pemrograman dan ekosistem
            5. Konsumsi daya untuk aplikasi baterai
            
            Berikan tabel perbandingan lengkap dan rekomendasi untuk smart home project.
            SERTAKAN LINK SUMBER untuk setiap klaim."""
        },
        {
            "name": "Deep Research - Complex Analysis",
            "mode": "deep",
            "query": """Lakukan riset mendalam tentang teknologi Matter/Thread untuk Smart Home.
            
            Saya perlu memahami:
            1. Apa itu Matter dan Thread? Sejarah dan latar belakang
            2. Arsitektur teknis dan cara kerjanya
            3. Perbandingan dengan Zigbee, Z-Wave, dan WiFi
            4. Chip/module yang mendukung (ESP32, nRF52, dll)
            5. Contoh implementasi dan project open source
            6. Prospek masa depan dan adopsi industri
            
            Ini untuk thesis saya, jadi perlu analisis komprehensif dengan SEMUA SUMBER tercantum."""
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 80}")
        print(f"# TEST {i}/{len(test_cases)}: {test['name']}")
        print(f"{'#' * 80}")
        
        result = await test_research_mode(test["query"], test["mode"])
        results.append({
            "name": test["name"],
            "mode": test["mode"],
            **result
        })
        
        if i < len(test_cases):
            print(f"\n⏳ Waiting 5 seconds before next test...")
            await asyncio.sleep(5)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print(" FINAL TEST SUMMARY")
    print("=" * 80)
    
    for r in results:
        status = "✅ PASS" if r.get("success") else "❌ FAIL"
        print(f"\n{status} | {r['name']}")
        if r.get("success"):
            print(f"      Mode: {r['mode'].upper()}")
            print(f"      Duration: {r['duration']}s")
            print(f"      Plan Steps: {r['plan_steps']}")
            print(f"      Sources: {r['sources']}")
            print(f"      Iterations: {r['iterations']}")
        else:
            print(f"      Error: {r.get('error', 'Unknown')}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n🚀 Starting JAWIR OS Research Tests...\n")
    asyncio.run(run_all_tests())
