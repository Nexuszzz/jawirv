"""
JAWIR OS - Complex Multi-Step Research Test
Tests Web Research & Deep Research with complex queries that require many steps.
Uses ReAct pattern: Reason → Act → Observe → Loop
"""

import asyncio
import json
import time
from datetime import datetime
import websockets


async def test_research(query: str, mode: str, test_name: str):
    """Test a complex research query."""
    
    uri = "ws://localhost:8000/ws/chat"
    
    print("\n" + "=" * 100)
    print(f"🧪 TEST: {test_name}")
    print("=" * 100)
    print(f"📝 QUERY:\n{query[:500]}...")
    print(f"\n🔬 MODE: {mode.upper()} RESEARCH")
    print("=" * 100)
    
    # Metrics
    phases = []
    plan_steps = 0
    sources_found = 0
    research_iterations = 0
    validation_iterations = 0
    start_time = time.time()
    
    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=120) as websocket:
            # Skip welcome
            await asyncio.wait_for(websocket.recv(), timeout=10)
            
            # Send query
            print("\n📤 Sending to JAWIR ReAct Agent...\n")
            await websocket.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": query,
                    "research_mode": mode
                }
            }))
            
            print("-" * 100)
            print("🔄 REACT LOOP EXECUTION (Reason → Act → Observe → Loop)")
            print("-" * 100)
            
            current_step = 0
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=600)
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        emoji = {
                            'thinking': '🧠',
                            'planning': '📋',
                            'searching': '🔍',
                            'reading': '📖',
                            'validating': '✅',
                            'iterating': '🔄',
                            'writing': '✍️',
                            'done': '🏁',
                        }.get(status, '📌')
                        
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] {emoji} {status.upper():12} │ {message}")
                        phases.append(status)
                        
                        if status == "searching":
                            research_iterations += 1
                        elif status == "validating":
                            validation_iterations += 1
                        
                        if status == "planning" and "plan" in details:
                            plan_steps = len(details["plan"])
                            print(f"             📋 PLAN ({plan_steps} steps):")
                            for i, step in enumerate(details["plan"], 1):
                                print(f"                {i}. {step[:80]}...")
                    
                    elif msg_type == "tool_result":
                        tool_data = data.get("data", {})
                        title = tool_data.get("title", "Research")
                        sources = tool_data.get("sources", [])
                        count = len(sources) if isinstance(sources, list) else 0
                        sources_found += count
                        current_step += 1
                        print(f"             🔧 Step {current_step}: {title} (+{count} sources)")
                    
                    elif msg_type == "agent_response":
                        content = data.get("content", "")
                        sources_used = data.get("sources_used", [])
                        thinking = data.get("thinking_process", [])
                        
                        duration = round(time.time() - start_time, 2)
                        
                        print("\n" + "=" * 100)
                        print("🎯 FINAL RESPONSE")
                        print("=" * 100)
                        
                        # ReAct Metrics
                        print(f"\n📊 REACT AGENT METRICS:")
                        print(f"   ┌─────────────────────────────────────────────────────┐")
                        print(f"   │ Mode:               {mode.upper():>30} │")
                        print(f"   │ Duration:           {duration:>27} sec │")
                        print(f"   │ Plan Steps:         {plan_steps:>30} │")
                        print(f"   │ Search Iterations:  {research_iterations:>30} │")
                        print(f"   │ Validation Checks:  {validation_iterations:>30} │")
                        print(f"   │ Total Sources:      {sources_found:>30} │")
                        print(f"   │ Sources Cited:      {len(sources_used):>30} │")
                        print(f"   │ Thinking Steps:     {len(thinking):>30} │")
                        print(f"   │ Response Length:    {len(content):>26} chars │")
                        print(f"   └─────────────────────────────────────────────────────┘")
                        
                        # ReAct Loop Proof
                        print(f"\n🔄 REACT PATTERN PROOF:")
                        print(f"   🧠 REASON  → Supervisor analyzed query, created {plan_steps}-step plan")
                        print(f"   ⚡ ACT     → Researcher executed {research_iterations} search operations")
                        print(f"   👁️ OBSERVE → Validator checked {validation_iterations}x, found {sources_found} sources")
                        print(f"   ✍️ OUTPUT  → Synthesizer created comprehensive response")
                        if research_iterations > 1 or validation_iterations > 1:
                            print(f"   🔄 LOOP    → Multi-iteration research completed!")
                        
                        # Response Preview
                        print(f"\n📜 RESPONSE PREVIEW (first 2000 chars):")
                        print("-" * 100)
                        print(content[:2000])
                        if len(content) > 2000:
                            print("\n... [TRUNCATED - full response is", len(content), "chars] ...")
                        print("-" * 100)
                        
                        # Sources
                        if sources_used:
                            print(f"\n📚 SOURCES ({len(sources_used)} cited):")
                            for i, s in enumerate(sources_used[:15], 1):
                                if isinstance(s, dict):
                                    url = s.get('url', s.get('title', 'N/A'))
                                    print(f"   {i:2}. {url[:85]}")
                                else:
                                    print(f"   {i:2}. {str(s)[:85]}")
                            if len(sources_used) > 15:
                                print(f"   ... and {len(sources_used) - 15} more sources")
                        
                        return {
                            "success": True,
                            "duration": duration,
                            "plan_steps": plan_steps,
                            "search_iterations": research_iterations,
                            "validation_iterations": validation_iterations,
                            "sources_found": sources_found,
                            "sources_cited": len(sources_used),
                            "response_length": len(content)
                        }
                    
                    elif msg_type == "error":
                        print(f"\n❌ ERROR: {data.get('message', 'Unknown')}")
                        return {"success": False, "error": data.get('message')}
                        
                except asyncio.TimeoutError:
                    print("\n⏱️ TIMEOUT after 10 minutes")
                    return {"success": False, "error": "timeout"}
                    
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def main():
    """Run complex multi-step research tests."""
    
    print("\n" + "#" * 100)
    print("#" + " " * 98 + "#")
    print("#" + "  JAWIR OS - COMPLEX MULTI-STEP RESEARCH TEST".center(98) + "#")
    print("#" + "  Testing ReAct Agent with Web Research & Deep Research".center(98) + "#")
    print("#" + " " * 98 + "#")
    print("#" * 100)
    print(f"\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Goal: Test complex queries requiring multiple research steps and iterations")
    
    # Complex test cases
    test_cases = [
        # ===== TEST 1: WEB RESEARCH - Complex Technical Comparison =====
        {
            "name": "Web Research - Multi-Factor Technical Analysis",
            "mode": "web",
            "query": """Saya sedang membangun sistem Smart Home untuk rumah 2 lantai dengan 15 ruangan.
            
Tolong lakukan riset dan analisis LENGKAP untuk memilih protokol komunikasi terbaik:

1. **ANALISIS PROTOKOL**
   - Matter/Thread vs Zigbee vs Z-Wave vs WiFi
   - Untuk setiap protokol, jelaskan: range, throughput, latency, mesh capability, power consumption
   
2. **KOMPATIBILITAS HARDWARE**
   - Chip mana yang support setiap protokol? (ESP32, nRF52, CC2652, dll)
   - Harga module di Indonesia untuk setiap opsi
   
3. **CASE STUDY**
   - Contoh implementasi smart home skala besar yang sukses
   - Lesson learned dan best practices
   
4. **REKOMENDASI ARSITEKTUR**
   - Gambarkan arsitektur jaringan untuk 15 ruangan
   - Hub/gateway apa yang diperlukan?
   - Estimasi biaya total untuk semua komponen
   
5. **DEVELOPMENT ROADMAP**
   - Langkah-langkah implementasi dari awal sampai jadi
   - Timeline realistis untuk proyek ini

PENTING: Sertakan SEMUA sumber dan link untuk setiap informasi teknis!"""
        },
        
        # ===== TEST 2: DEEP RESEARCH - Comprehensive Technical Deep Dive =====
        {
            "name": "Deep Research - AI Edge Computing Analysis",
            "mode": "deep",
            "query": """Saya menulis thesis tentang "Edge AI untuk IoT: Perbandingan Platform dan Implementasi".

Lakukan RISET MENDALAM dan KOMPREHENSIF mencakup:

1. **LANDASAN TEORI**
   - Definisi Edge AI vs Cloud AI vs Fog Computing
   - Sejarah perkembangan Edge Computing (2015-2025)
   - Teori utama: latency optimization, bandwidth efficiency, privacy preservation
   
2. **ANALISIS PLATFORM EDGE AI**
   Bandingkan secara detail:
   - NVIDIA Jetson (Nano, TX2, Xavier, Orin)
   - Google Coral (Dev Board, USB Accelerator)
   - Intel Neural Compute Stick
   - ESP32-S3 dengan ESP-DL
   - Raspberry Pi dengan Coral/Hailo
   
   Untuk setiap platform, analisis:
   - Spesifikasi (TOPS, memory, power draw)
   - Framework yang didukung (TensorFlow Lite, ONNX, dll)
   - Benchmark performa (inferensi/detik untuk model umum)
   - Harga dan ketersediaan
   
3. **STUDI KASUS IMPLEMENTASI**
   - Minimal 3 case study dari jurnal/paper terbaru
   - Analisis methodology dan hasil
   
4. **FRAMEWORK DAN TOOLS**
   - TensorFlow Lite vs ONNX Runtime vs OpenVINO vs TensorRT
   - Quantization techniques (INT8, FP16)
   - Model optimization untuk edge
   
5. **BENCHMARKING METHODOLOGY**
   - Bagaimana cara benchmark yang proper?
   - Metrics yang digunakan (latency, throughput, power efficiency)
   
6. **GAP ANALYSIS DAN FUTURE DIRECTIONS**
   - Apa yang masih kurang dari solusi saat ini?
   - Trend riset 2024-2026
   
KEBUTUHAN OUTPUT:
- Format akademis dengan proper citations
- Minimal 20 sumber dari jurnal, dokumentasi official, dan artikel teknis
- Tabel perbandingan untuk semua platform
- Rekomendasi untuk thesis saya"""
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n\n{'#' * 100}")
        print(f"# TEST {i}/{len(test_cases)}: {test['name']}")
        print(f"{'#' * 100}")
        
        result = await test_research(test["query"], test["mode"], test["name"])
        result["name"] = test["name"]
        result["mode"] = test["mode"]
        results.append(result)
        
        if i < len(test_cases):
            print(f"\n⏳ Cooling down 10 seconds before next test...")
            await asyncio.sleep(10)
    
    # Final Summary
    print("\n\n" + "=" * 100)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 100)
    
    total_sources = 0
    total_duration = 0
    
    for r in results:
        status = "✅ PASS" if r.get("success") else "❌ FAIL"
        print(f"\n{status} {r['name']}")
        print(f"   Mode: {r['mode'].upper()}")
        
        if r.get("success"):
            print(f"   Duration: {r['duration']}s")
            print(f"   Plan Steps: {r['plan_steps']}")
            print(f"   Search Iterations: {r['search_iterations']}")
            print(f"   Validation Iterations: {r['validation_iterations']}")
            print(f"   Sources Found: {r['sources_found']}")
            print(f"   Sources Cited: {r['sources_cited']}")
            print(f"   Response Length: {r['response_length']} chars")
            total_sources += r['sources_found']
            total_duration += r['duration']
        else:
            print(f"   Error: {r.get('error', 'Unknown')}")
    
    print("\n" + "-" * 100)
    print(f"📈 TOTALS:")
    print(f"   Total Duration: {total_duration:.2f} seconds")
    print(f"   Total Sources Found: {total_sources}")
    print(f"   Tests Passed: {sum(1 for r in results if r.get('success'))}/{len(results)}")
    print("=" * 100)
    print("\n✅ Complex Multi-Step Research Tests Complete!\n")


if __name__ == "__main__":
    asyncio.run(main())
