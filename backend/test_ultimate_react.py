"""
JAWIR OS - ULTIMATE Complex ReAct Test
Tests extreme multi-step planning with source verification
"""

import asyncio
import json
import time
from datetime import datetime
import websockets


# Ultra-complex queries that require extensive research
COMPLEX_QUERIES = [
    {
        "name": "Deep Technical Comparison",
        "query": """Buatkan analisis komprehensif dan mendalam tentang perbandingan arsitektur mikrokontroler untuk sistem IoT industri:

1. ESP32-S3 vs ESP32-C6 vs ESP32-H2 - Jelaskan perbedaan arsitektur RISC-V vs Xtensa
2. STM32F4 vs STM32H7 vs STM32U5 - Bandingkan fitur low-power dan performa
3. Nordic nRF52840 vs nRF5340 - Analisis untuk aplikasi BLE mesh
4. RP2040 (Raspberry Pi Pico) - Keunggulan PIO dan dual-core

Untuk SETIAP mikrokontroler, saya butuh:
- Spesifikasi lengkap (Clock speed, RAM, Flash, GPIO, ADC resolution)
- Harga estimasi di Indonesia (Tokopedia/Shopee)
- Konsumsi daya (active mode, deep sleep, light sleep)
- Protokol komunikasi yang didukung (SPI, I2C, UART, CAN, USB)
- Ketersediaan library dan framework (Arduino, ESP-IDF, Zephyr, FreeRTOS)
- Use case terbaik untuk masing-masing
- Kelebihan dan kekurangan

Berikan dalam format tabel perbandingan yang sistematis dengan sumber referensi yang jelas."""
    },
    {
        "name": "Multi-Domain Research", 
        "query": """Saya ingin membangun sistem Smart Agriculture (Pertanian Pintar) skala menengah. Tolong riset mendalam:

HARDWARE:
1. Sensor yang dibutuhkan: soil moisture, pH tanah, suhu udara, kelembaban, intensitas cahaya, curah hujan
2. Mikrokontroler terbaik untuk outdoor (waterproof, low power, solar-powered)
3. Komunikasi: LoRa vs NB-IoT vs Sigfox untuk area pertanian luas
4. Panel surya dan sistem baterai yang optimal

SOFTWARE:
1. Platform IoT: ThingsBoard vs Blynk vs Home Assistant vs custom
2. Database time-series: InfluxDB vs TimescaleDB vs QuestDB
3. Machine Learning untuk prediksi panen dan deteksi penyakit tanaman
4. Dashboard monitoring real-time

INTEGRASI:
1. API cuaca (BMKG, OpenWeatherMap)
2. Sistem irigasi otomatis
3. Notifikasi WhatsApp/Telegram
4. Integrasi dengan drone untuk pemetaan

Berikan estimasi biaya total, timeline implementasi, dan sumber referensi lengkap dengan URL."""
    }
]


async def run_ultimate_test():
    """Run ultimate complex test."""
    
    uri = "ws://localhost:8000/ws/chat"
    query = COMPLEX_QUERIES[0]  # Use first complex query
    
    print("=" * 80)
    print(" JAWIR OS - ULTIMATE ReAct Complexity Test")
    print(" Testing: Multi-step Planning with Source Verification")
    print("=" * 80)
    print(f"\n🎯 TEST: {query['name']}")
    print(f"\n📝 QUERY (Length: {len(query['query'])} chars):")
    print("-" * 80)
    print(query['query'][:500] + "...")
    print("-" * 80)
    
    # Metrics tracking
    metrics = {
        "start_time": time.time(),
        "plan_steps": 0,
        "plan_details": [],
        "sources_found": 0,
        "source_urls": [],
        "validation_loops": 0,
        "tool_calls": 0,
        "phases": [],
    }
    
    try:
        async with websockets.connect(uri, ping_interval=30, ping_timeout=60) as websocket:
            # Skip welcome
            await asyncio.wait_for(websocket.recv(), timeout=5)
            
            # Send complex query
            print(f"\n📤 Sending query to JAWIR...")
            await websocket.send(json.dumps({
                "type": "user_message",
                "data": {"content": query['query']}
            }))
            
            print("\n" + "=" * 80)
            print("🔄 REACT LOOP EXECUTION (Live Tracking)")
            print("=" * 80)
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=300)
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        # Emoji mapping
                        emoji = {
                            'thinking': '🧠',
                            'planning': '📋',
                            'searching': '🔍',
                            'reading': '📖',
                            'writing': '✍️',
                            'validating': '✅',
                            'done': '🎉',
                        }.get(status, '📌')
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"\n{emoji} [{timestamp}] {status.upper()}: {message}")
                        
                        metrics["phases"].append({
                            "status": status,
                            "message": message,
                            "time": timestamp
                        })
                        
                        # Track planning details
                        if status == "planning" and "plan" in details:
                            metrics["plan_steps"] = len(details["plan"])
                            metrics["plan_details"] = details["plan"]
                            
                            print(f"\n   📋 PLAN CREATED: {metrics['plan_steps']} STEPS")
                            print("   " + "-" * 60)
                            for i, step in enumerate(details["plan"], 1):
                                step_text = step[:80] + "..." if len(step) > 80 else step
                                print(f"   {i:2}. {step_text}")
                            print("   " + "-" * 60)
                        
                        # Track validation
                        if "validation" in message.lower() or "retry" in message.lower():
                            metrics["validation_loops"] += 1
                            print(f"   🔄 Validation loop #{metrics['validation_loops']}")
                    
                    elif msg_type == "tool_result":
                        tool_data = data.get("data", {})
                        title = tool_data.get("title", "Research")
                        sources = tool_data.get("sources", [])
                        
                        metrics["tool_calls"] += 1
                        metrics["sources_found"] += len(sources)
                        
                        print(f"\n   🔧 TOOL RESULT #{metrics['tool_calls']}: {title}")
                        print(f"   📚 Found {len(sources)} sources:")
                        
                        for src in sources:
                            if isinstance(src, dict):
                                url = src.get("url", "N/A")
                                src_title = src.get("title", "Unknown")[:50]
                                metrics["source_urls"].append(url)
                                print(f"      • {src_title}")
                                print(f"        🔗 {url}")
                    
                    elif msg_type == "agent_response":
                        # Final response!
                        content = data.get("content", "")
                        sources_used = data.get("sources_used", [])
                        thinking_process = data.get("thinking_process", [])
                        
                        metrics["end_time"] = time.time()
                        metrics["duration"] = round(metrics["end_time"] - metrics["start_time"], 2)
                        metrics["response_length"] = len(content)
                        
                        # Print final results
                        print("\n" + "=" * 80)
                        print("🎯 FINAL RESPONSE RECEIVED")
                        print("=" * 80)
                        
                        # Metrics Summary
                        print(f"\n📊 EXECUTION METRICS:")
                        print(f"   ├─ Duration:           {metrics['duration']} seconds")
                        print(f"   ├─ Plan Steps:         {metrics['plan_steps']}")
                        print(f"   ├─ Tool Calls:         {metrics['tool_calls']}")
                        print(f"   ├─ Sources Found:      {metrics['sources_found']}")
                        print(f"   ├─ Unique URLs:        {len(set(metrics['source_urls']))}")
                        print(f"   ├─ Validation Loops:   {metrics['validation_loops']}")
                        print(f"   ├─ Response Length:    {metrics['response_length']} chars")
                        print(f"   └─ Thinking Steps:     {len(thinking_process)}")
                        
                        # Response Preview
                        print(f"\n📜 RESPONSE PREVIEW (first 1500 chars):")
                        print("-" * 80)
                        print(content[:1500])
                        if len(content) > 1500:
                            print("... [truncated]")
                        print("-" * 80)
                        
                        # All Sources with URLs
                        print(f"\n🔗 ALL SOURCE URLS ({len(set(metrics['source_urls']))} unique):")
                        print("-" * 80)
                        for i, url in enumerate(sorted(set(metrics['source_urls'])), 1):
                            print(f"   {i:2}. {url}")
                        print("-" * 80)
                        
                        # Sources from response
                        if sources_used:
                            print(f"\n📚 SOURCES IN RESPONSE ({len(sources_used)}):")
                            for s in sources_used:
                                if isinstance(s, dict):
                                    print(f"   • {s.get('title', 'N/A')}")
                                    print(f"     🔗 {s.get('url', 'N/A')}")
                                elif isinstance(s, str):
                                    print(f"   • {s}")
                        
                        # ReAct Pattern Analysis
                        print("\n" + "=" * 80)
                        print("🔄 REACT PATTERN ANALYSIS")
                        print("=" * 80)
                        
                        # Count phase types
                        phase_counts = {}
                        for p in metrics["phases"]:
                            status = p["status"]
                            phase_counts[status] = phase_counts.get(status, 0) + 1
                        
                        print("\n   Phase Breakdown:")
                        for status, count in sorted(phase_counts.items()):
                            bar = "█" * count
                            print(f"   {status:12} │ {bar} ({count})")
                        
                        # Verdict
                        print("\n" + "=" * 80)
                        print("✅ REACT WORKFLOW VERIFICATION")
                        print("=" * 80)
                        
                        checks = [
                            ("Planning (multi-step)", metrics["plan_steps"] >= 3, f"{metrics['plan_steps']} steps"),
                            ("Acting (tool use)", metrics["tool_calls"] >= 1, f"{metrics['tool_calls']} tool calls"),
                            ("Observing (sources)", metrics["sources_found"] >= 3, f"{metrics['sources_found']} sources"),
                            ("Response quality", metrics["response_length"] >= 500, f"{metrics['response_length']} chars"),
                        ]
                        
                        all_passed = True
                        for name, passed, detail in checks:
                            status = "✅ PASS" if passed else "❌ FAIL"
                            print(f"   {status} │ {name}: {detail}")
                            if not passed:
                                all_passed = False
                        
                        if all_passed:
                            print("\n   🎉 ALL CHECKS PASSED! JAWIR ReAct workflow verified!")
                        
                        break
                    
                    elif msg_type == "error":
                        print(f"\n   ❌ ERROR: {data.get('message', 'Unknown')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("\n   ⏱️ TIMEOUT - Query took too long")
                    break
                    
    except Exception as e:
        print(f"\n❌ CONNECTION ERROR: {e}")
    
    return metrics


async def run_multi_query_test():
    """Run multiple complex queries in sequence."""
    
    print("\n" + "=" * 80)
    print(" JAWIR OS - MULTI-QUERY STRESS TEST")
    print("=" * 80)
    
    all_metrics = []
    
    for i, query in enumerate(COMPLEX_QUERIES, 1):
        print(f"\n\n{'#' * 80}")
        print(f"# QUERY {i}/{len(COMPLEX_QUERIES)}: {query['name']}")
        print(f"{'#' * 80}")
        
        metrics = await run_ultimate_test()
        all_metrics.append(metrics)
        
        if i < len(COMPLEX_QUERIES):
            print("\n⏳ Waiting 5 seconds before next query...")
            await asyncio.sleep(5)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print(" FINAL SUMMARY - ALL QUERIES")
    print("=" * 80)
    
    total_duration = sum(m.get("duration", 0) for m in all_metrics)
    total_sources = sum(m.get("sources_found", 0) for m in all_metrics)
    total_steps = sum(m.get("plan_steps", 0) for m in all_metrics)
    
    print(f"\n   Total Queries:      {len(COMPLEX_QUERIES)}")
    print(f"   Total Duration:     {total_duration} seconds")
    print(f"   Total Plan Steps:   {total_steps}")
    print(f"   Total Sources:      {total_sources}")
    print(f"   Avg Time/Query:     {total_duration/len(COMPLEX_QUERIES):.1f} seconds")


if __name__ == "__main__":
    print("\n🚀 Starting JAWIR OS Ultimate Complexity Test...\n")
    
    # Run single ultimate test first
    asyncio.run(run_ultimate_test())
