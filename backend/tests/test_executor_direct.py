"""
JAWIR OS - Executor Direct Test
================================
Test FunctionCallingExecutor directly with various queries.
This bypasses WebSocket to isolate the issue.
"""

import asyncio
import os
import sys
import time

# Add backend to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Force reload config
import importlib
import app.config
importlib.reload(app.config)

from app.config import settings

# Initialize API rotator
from agent.api_rotator import init_rotator
init_rotator(settings.all_google_api_keys)

print("=" * 60)
print(f"  Model: {settings.gemini_model}")
print(f"  Keys: {len(settings.all_google_api_keys)}")
print("=" * 60)


async def test_executor(query: str, name: str):
    """Test executor with a query."""
    from agent.function_calling_executor import FunctionCallingExecutor
    
    print(f"\n[TEST] {name}")
    print(f"  Query: {query}")
    
    start = time.time()
    
    try:
        executor = FunctionCallingExecutor()
        result = await asyncio.wait_for(
            executor.execute(
                user_query=query,
                max_iterations=3,
            ),
            timeout=60,
        )
        
        duration = time.time() - start
        final = result.get("final_response", "")
        tools = result.get("tool_calls_history", [])
        iters = result.get("iterations", 0)
        
        print(f"  Duration: {duration:.1f}s")
        print(f"  Iterations: {iters}")
        print(f"  Tools used: {[t['tool_name'] for t in tools]}")
        print(f"  Response: {final[:200]}...")
        print(f"  Result: [OK] PASS")
        return True
        
    except asyncio.TimeoutError:
        print(f"  Duration: {time.time() - start:.1f}s")
        print(f"  Result: [FAIL] TIMEOUT")
        return False
    except asyncio.CancelledError:
        print(f"  Duration: {time.time() - start:.1f}s")
        print(f"  Result: [FAIL] CANCELLED")
        return False
    except Exception as e:
        print(f"  Duration: {time.time() - start:.1f}s")
        print(f"  Error: {e}")
        print(f"  Result: [FAIL] ERROR")
        import traceback
        traceback.print_exc()
        return False


async def main():
    results = {}
    
    # Test 1: Chat biasa
    results["chat"] = await test_executor(
        "Siapa kamu?",
        "Chat biasa (no tools)"
    )
    
    # Test 2: Python exec
    results["python"] = await test_executor(
        "Jalankan kode Python: print(100+200)",
        "Python Exec"
    )
    
    # Test 3: Web search  
    results["web"] = await test_executor(
        "Cari berita teknologi AI terbaru",
        "Web Search"
    )
    
    # Test 4: Open URL
    results["url"] = await test_executor(
        "Buka website https://github.com",
        "Open URL"
    )
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v)
    for name, ok in results.items():
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} {name}")
    print(f"\n  Total: {passed}/{len(results)} PASSED")


if __name__ == "__main__":
    asyncio.run(main())
