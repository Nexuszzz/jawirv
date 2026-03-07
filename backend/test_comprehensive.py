"""
JAWIR OS - Comprehensive Test Suite
Testing all flows and scenarios
"""
import asyncio
import os
import sys
import time
from datetime import datetime

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

from agent.api_rotator import init_rotator
from agent.graph import invoke_agent

# Initialize API keys
api_keys = os.getenv('GOOGLE_API_KEYS', '').split(',')
print(f"🔑 Loaded {len(api_keys)} API keys")
init_rotator(api_keys)

# Test cases
TEST_CASES = [
    # ============================================
    # Skenario 1: Direct Response (1 LLM call)
    # ============================================
    {
        "id": 1,
        "name": "Sapaan - Halo",
        "query": "halo",
        "expected_sources": 0,
        "expected_type": "direct",
        "description": "Chat sederhana, harus dijawab langsung tanpa research"
    },
    {
        "id": 2,
        "name": "Identitas - Siapa kamu",
        "query": "siapa kamu?",
        "expected_sources": 0,
        "expected_type": "direct",
        "description": "Pertanyaan identitas JAWIR"
    },
    {
        "id": 3,
        "name": "Ucapan - Terima kasih",
        "query": "terima kasih banyak ya",
        "expected_sources": 0,
        "expected_type": "direct",
        "description": "Ucapan terima kasih"
    },
    
    # ============================================
    # Skenario 2: Knowledge Response (2 LLM calls)
    # ============================================
    {
        "id": 4,
        "name": "Konsep - Apa itu JavaScript",
        "query": "apa itu JavaScript?",
        "expected_sources": 0,
        "expected_type": "knowledge",
        "description": "Penjelasan konsep tanpa perlu research"
    },
    {
        "id": 5,
        "name": "Coding - Function Python",
        "query": "buatkan function python untuk mengecek bilangan prima",
        "expected_sources": 0,
        "expected_type": "code",
        "description": "Permintaan coding, tidak perlu research"
    },
    {
        "id": 6,
        "name": "Penjelasan - Cara kerja API",
        "query": "jelaskan cara kerja REST API",
        "expected_sources": 0,
        "expected_type": "knowledge",
        "description": "Penjelasan teknis tanpa perlu data terkini"
    },
    
    # ============================================
    # Skenario 3: Web Research (4 LLM calls + search)
    # ============================================
    {
        "id": 7,
        "name": "Research - Berita terkini",
        "query": "berita teknologi AI terbaru hari ini",
        "expected_sources": None,  # Bisa 0 atau lebih
        "expected_type": "research",
        "description": "Butuh search karena data terkini"
    },
    {
        "id": 8,
        "name": "Research - Harga produk",
        "query": "harga laptop gaming terbaru 2026",
        "expected_sources": None,
        "expected_type": "research",
        "description": "Butuh search karena data harga berubah"
    },
]


async def run_test(test_case: dict) -> dict:
    """Run a single test case and return results."""
    print(f"\n{'='*60}")
    print(f"TEST #{test_case['id']}: {test_case['name']}")
    print(f"Query: \"{test_case['query']}\"")
    print(f"Expected: {test_case['expected_type']} | Sources: {test_case['expected_sources']}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        result = await invoke_agent(test_case['query'], f"test-{test_case['id']}")
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        sources = result.get('sources_used', [])
        status = result.get('status', '')
        
        # Determine pass/fail
        passed = True
        notes = []
        
        # Check sources expectation
        if test_case['expected_sources'] is not None:
            if len(sources) != test_case['expected_sources']:
                if test_case['expected_sources'] == 0 and len(sources) > 0:
                    passed = False
                    notes.append(f"Expected 0 sources but got {len(sources)}")
        
        # Check if response exists
        if not response or len(response) < 10:
            passed = False
            notes.append("Response too short or empty")
        
        # Check for error messages in response
        if "kendala" in response.lower() or "error" in response.lower():
            passed = False
            notes.append("Response contains error message")
        
        print(f"\n📝 Response ({len(response)} chars):")
        print(response[:300] + "..." if len(response) > 300 else response)
        print(f"\n📊 Stats: Sources={len(sources)} | Time={elapsed:.2f}s | Status={status}")
        print(f"{'✅ PASSED' if passed else '❌ FAILED'}")
        if notes:
            print(f"Notes: {', '.join(notes)}")
        
        return {
            "id": test_case['id'],
            "name": test_case['name'],
            "passed": passed,
            "elapsed": elapsed,
            "response_length": len(response),
            "sources_count": len(sources),
            "notes": notes,
            "error": None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "id": test_case['id'],
            "name": test_case['name'],
            "passed": False,
            "elapsed": elapsed,
            "response_length": 0,
            "sources_count": 0,
            "notes": [],
            "error": str(e)
        }


async def run_all_tests():
    """Run all test cases sequentially."""
    print("\n" + "="*60)
    print("🧪 JAWIR OS - COMPREHENSIVE TEST SUITE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 {len(api_keys)} API keys loaded")
    print("="*60)
    
    results = []
    
    for test_case in TEST_CASES:
        result = await run_test(test_case)
        results.append(result)
        
        # Small delay between tests to avoid rate limiting
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for r in results if r['passed'])
    failed = len(results) - passed
    
    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    
    if failed > 0:
        print("\n❌ Failed Tests:")
        for r in results:
            if not r['passed']:
                error_info = f" - Error: {r['error']}" if r['error'] else f" - {', '.join(r['notes'])}"
                print(f"   #{r['id']} {r['name']}{error_info}")
    
    print("\n⏱️ Timing:")
    for r in results:
        status = "✅" if r['passed'] else "❌"
        print(f"   {status} #{r['id']} {r['name']}: {r['elapsed']:.2f}s")
    
    total_time = sum(r['elapsed'] for r in results)
    print(f"\n   Total: {total_time:.2f}s")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
