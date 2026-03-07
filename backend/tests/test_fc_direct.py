"""Direct test: FunctionCallingExecutor without WebSocket/server.
This tests the core FC loop directly to isolate issues.
"""
import os, sys, asyncio, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Initialize API key rotator
from app.config import settings
from agent.api_rotator import init_rotator
init_rotator(settings.all_google_api_keys)

from agent.function_calling_executor import FunctionCallingExecutor

async def main():
    print("Initializing FunctionCallingExecutor...")
    executor = FunctionCallingExecutor()
    print(f"Tools: {[t.name for t in executor.tools]}")
    print(f"Model: {os.environ.get('GEMINI_MODEL', 'gemini-3-pro-preview')}")
    print()
    
    tests = [
        ("Chat biasa", "Halo JAWIR, siapa kamu?"),
        ("Chat konsep", "Apa itu ESP32? Jelaskan singkat 2 kalimat."),
        ("Web Search", "Cari informasi terbaru tentang AI 2026"),
        ("Python Exec", "Jalankan kode Python: print(sum(range(1, 101)))"),
        ("Open URL", "Bukakan URL https://www.google.com"),
    ]
    
    results = {}
    for name, query in tests:
        print(f"{'='*50}")
        print(f"TEST: {name}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        t0 = time.time()
        try:
            result = await executor.execute(query, max_iterations=3)
            dt = time.time() - t0
            
            resp = result.get("final_response", "(none)")
            tc_hist = result.get("tool_calls_history", [])
            iters = result.get("iterations", 0)
            
            print(f"  Time: {dt:.1f}s")
            print(f"  Iterations: {iters}")
            print(f"  Tool calls: {len(tc_hist)}")
            for tc in tc_hist:
                print(f"    -> {tc['tool_name']}: {tc['status']} ({tc['result'][:80]})")
            print(f"  Response: {resp[:200]}")
            
            ok = bool(resp) and not resp.startswith("Mohon maaf")
            results[name] = ok
            print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
        except Exception as e:
            dt = time.time() - t0
            print(f"  Time: {dt:.1f}s")
            print(f"  ERROR: {e}")
            results[name] = False
            print(f"  RESULT: FAIL")
        print()
    
    print(f"\n{'#'*50}")
    print("SUMMARY")
    print(f"{'#'*50}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n  {passed}/{total} PASSED")
    print(f"{'#'*50}")

asyncio.run(main())
