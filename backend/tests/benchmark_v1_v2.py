"""
JAWIR OS - Performance Benchmark: V1 vs V2
============================================
Script benchmark yang membandingkan response time V1 (manual routing)
vs V2 (Gemini native function calling) untuk 10 query standar.

Usage:
    cd backend
    venv_new\\Scripts\\python.exe tests/benchmark_v1_v2.py

Requirements:
    - GOOGLE_API_KEY dan TAVILY_API_KEY di .env
    - Server TIDAK perlu running (direct invocation)

Output:
    - Response time per query (V1 dan V2)
    - Average, median, min, max
    - Comparison table
    - Winner per query
"""

import asyncio
import sys
import os
import time
import statistics
from dataclasses import dataclass, field
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================
# Benchmark Data Structures
# ============================================

@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    query: str
    version: str  # "V1" or "V2"
    response_time_ms: float
    success: bool
    response_length: int = 0
    tool_calls: int = 0
    error: str = ""


@dataclass
class BenchmarkSummary:
    """Summary of all benchmark runs."""
    version: str
    total_queries: int = 0
    successful: int = 0
    failed: int = 0
    avg_ms: float = 0.0
    median_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    total_ms: float = 0.0
    times: list = field(default_factory=list)


# ============================================
# Test Queries
# ============================================

BENCHMARK_QUERIES = [
    # 1. Simple greeting (no tool needed)
    "Halo JAWIR, apa kabar?",
    # 2. Simple knowledge question (no tool)
    "Apa itu resistor?",
    # 3. Web search query
    "Berapa harga ESP32 terbaru?",
    # 4. KiCad design request
    "Buatkan skematik LED blink dengan resistor 330 ohm",
    # 5. Python code execution
    "Hitung 2 pangkat 20",
    # 6. Calendar query
    "Cek jadwal hari ini",
    # 7. Gmail query
    "Cari email dari boss@company.com",
    # 8. Complex reasoning (no tool)
    "Jelaskan perbedaan antara Arduino dan ESP32 untuk proyek IoT",
    # 9. Desktop control
    "Buka aplikasi calculator",
    # 10. Multi-step question
    "Carikan informasi tentang sensor DHT22 dan buatkan skematik koneksinya ke ESP32",
]


# ============================================
# Benchmark Runner
# ============================================

async def run_single_benchmark(
    query: str,
    version: str,
    session_id: str,
) -> BenchmarkResult:
    """
    Run a single benchmark query.
    
    Args:
        query: The user query
        version: "V1" or "V2"
        session_id: Session identifier
    
    Returns:
        BenchmarkResult with timing data
    """
    try:
        # Set feature flag
        os.environ["USE_FUNCTION_CALLING"] = "true" if version == "V2" else "false"
        
        # Reimport to pick up flag change
        # (In production this would use the config system)
        from agent.graph import invoke_agent
        
        start = time.perf_counter()
        
        result = await invoke_agent(
            user_query=query,
            session_id=session_id,
        )
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        final_response = result.get("final_response", "")
        tool_history = result.get("tool_calls_history", [])
        
        return BenchmarkResult(
            query=query,
            version=version,
            response_time_ms=round(elapsed_ms, 2),
            success=True,
            response_length=len(final_response),
            tool_calls=len(tool_history) if isinstance(tool_history, list) else 0,
        )
        
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return BenchmarkResult(
            query=query,
            version=version,
            response_time_ms=round(elapsed_ms, 2),
            success=False,
            error=str(e)[:200],
        )


async def run_benchmark_suite(
    version: str,
    queries: list[str] = None,
) -> tuple[list[BenchmarkResult], BenchmarkSummary]:
    """
    Run full benchmark suite for one version.
    
    Args:
        version: "V1" or "V2"
        queries: List of queries (default: BENCHMARK_QUERIES)
    
    Returns:
        Tuple of (results list, summary)
    """
    queries = queries or BENCHMARK_QUERIES
    results = []
    
    print(f"\n{'='*60}")
    print(f"  BENCHMARK: {version} ({len(queries)} queries)")
    print(f"{'='*60}")
    
    for i, query in enumerate(queries, 1):
        print(f"\n  [{i}/{len(queries)}] {query[:60]}...")
        
        result = await run_single_benchmark(
            query=query,
            version=version,
            session_id=f"benchmark-{version.lower()}-{i}",
        )
        results.append(result)
        
        status = "✅" if result.success else "❌"
        print(f"    {status} {result.response_time_ms}ms "
              f"(len={result.response_length}, tools={result.tool_calls})")
        
        if not result.success:
            print(f"    Error: {result.error}")
    
    # Calculate summary
    times = [r.response_time_ms for r in results if r.success]
    summary = BenchmarkSummary(
        version=version,
        total_queries=len(queries),
        successful=len([r for r in results if r.success]),
        failed=len([r for r in results if not r.success]),
        times=times,
    )
    
    if times:
        summary.avg_ms = round(statistics.mean(times), 2)
        summary.median_ms = round(statistics.median(times), 2)
        summary.min_ms = round(min(times), 2)
        summary.max_ms = round(max(times), 2)
        summary.total_ms = round(sum(times), 2)
    
    return results, summary


def print_comparison(
    v1_results: list[BenchmarkResult],
    v1_summary: BenchmarkSummary,
    v2_results: list[BenchmarkResult],
    v2_summary: BenchmarkSummary,
):
    """Print comparison table between V1 and V2."""
    
    print(f"\n\n{'='*80}")
    print(f"  PERFORMANCE COMPARISON: V1 (Manual Routing) vs V2 (Function Calling)")
    print(f"{'='*80}")
    
    # Per-query comparison
    print(f"\n{'Query':<45} {'V1 (ms)':<12} {'V2 (ms)':<12} {'Winner':<10}")
    print(f"{'-'*45} {'-'*12} {'-'*12} {'-'*10}")
    
    v1_wins = 0
    v2_wins = 0
    
    for v1r, v2r in zip(v1_results, v2_results):
        query_short = v1r.query[:42] + "..." if len(v1r.query) > 42 else v1r.query
        
        v1_time = f"{v1r.response_time_ms}" if v1r.success else "FAIL"
        v2_time = f"{v2r.response_time_ms}" if v2r.success else "FAIL"
        
        if v1r.success and v2r.success:
            if v1r.response_time_ms < v2r.response_time_ms:
                winner = "V1 ⚡"
                v1_wins += 1
            elif v2r.response_time_ms < v1r.response_time_ms:
                winner = "V2 ⚡"
                v2_wins += 1
            else:
                winner = "TIE"
        else:
            winner = "N/A"
        
        print(f"  {query_short:<43} {v1_time:<12} {v2_time:<12} {winner:<10}")
    
    # Summary comparison
    print(f"\n\n{'Metric':<25} {'V1':<15} {'V2':<15} {'Diff':<15}")
    print(f"{'-'*25} {'-'*15} {'-'*15} {'-'*15}")
    
    metrics = [
        ("Avg Response Time", v1_summary.avg_ms, v2_summary.avg_ms, "ms"),
        ("Median Response Time", v1_summary.median_ms, v2_summary.median_ms, "ms"),
        ("Min Response Time", v1_summary.min_ms, v2_summary.min_ms, "ms"),
        ("Max Response Time", v1_summary.max_ms, v2_summary.max_ms, "ms"),
        ("Total Time", v1_summary.total_ms, v2_summary.total_ms, "ms"),
        ("Success Rate", v1_summary.successful, v2_summary.successful, f"/{v1_summary.total_queries}"),
    ]
    
    for name, v1_val, v2_val, unit in metrics:
        diff = round(v2_val - v1_val, 2)
        diff_str = f"{'+' if diff > 0 else ''}{diff}{unit}"
        print(f"  {name:<23} {v1_val}{unit:<13} {v2_val}{unit:<13} {diff_str}")
    
    # Overall winner
    print(f"\n\n🏆 OVERALL WINNER:")
    print(f"   V1 wins: {v1_wins}/{len(v1_results)}")
    print(f"   V2 wins: {v2_wins}/{len(v2_results)}")
    
    if v2_summary.avg_ms > 0 and v1_summary.avg_ms > 0:
        speedup = round(v1_summary.avg_ms / v2_summary.avg_ms, 2)
        if speedup > 1:
            print(f"   V2 is {speedup}x faster on average")
        else:
            print(f"   V1 is {round(1/speedup, 2)}x faster on average")


# ============================================
# Offline Benchmark (Mock-based)
# ============================================

async def run_offline_benchmark():
    """
    Run benchmark with mocked LLM calls for testing the benchmark framework itself.
    Doesn't require API keys or running server.
    """
    import random
    
    print("\n" + "="*60)
    print("  OFFLINE BENCHMARK (Mock Mode)")
    print("  Testing benchmark framework without live API calls")
    print("="*60)
    
    v1_results = []
    v2_results = []
    
    for i, query in enumerate(BENCHMARK_QUERIES, 1):
        # Simulate V1 (usually slower due to multi-node traversal)
        v1_time = random.uniform(800, 3000)
        v1_results.append(BenchmarkResult(
            query=query,
            version="V1",
            response_time_ms=round(v1_time, 2),
            success=True,
            response_length=random.randint(100, 2000),
            tool_calls=0,
        ))
        
        # Simulate V2 (usually faster, single FC loop)
        v2_time = random.uniform(500, 2000)
        v2_results.append(BenchmarkResult(
            query=query,
            version="V2",
            response_time_ms=round(v2_time, 2),
            success=True,
            response_length=random.randint(100, 2000),
            tool_calls=random.randint(0, 3),
        ))
    
    # Calculate summaries
    v1_times = [r.response_time_ms for r in v1_results]
    v2_times = [r.response_time_ms for r in v2_results]
    
    v1_summary = BenchmarkSummary(
        version="V1",
        total_queries=len(BENCHMARK_QUERIES),
        successful=len(BENCHMARK_QUERIES),
        avg_ms=round(statistics.mean(v1_times), 2),
        median_ms=round(statistics.median(v1_times), 2),
        min_ms=round(min(v1_times), 2),
        max_ms=round(max(v1_times), 2),
        total_ms=round(sum(v1_times), 2),
        times=v1_times,
    )
    
    v2_summary = BenchmarkSummary(
        version="V2",
        total_queries=len(BENCHMARK_QUERIES),
        successful=len(BENCHMARK_QUERIES),
        avg_ms=round(statistics.mean(v2_times), 2),
        median_ms=round(statistics.median(v2_times), 2),
        min_ms=round(min(v2_times), 2),
        max_ms=round(max(v2_times), 2),
        total_ms=round(sum(v2_times), 2),
        times=v2_times,
    )
    
    print_comparison(v1_results, v1_summary, v2_results, v2_summary)
    print("\n✅ Offline benchmark complete (mock data)")
    return True


# ============================================
# Test Integration (pytest)
# ============================================

def test_benchmark_data_structures():
    """Test BenchmarkResult and BenchmarkSummary dataclasses."""
    result = BenchmarkResult(
        query="test query",
        version="V2",
        response_time_ms=1234.56,
        success=True,
        response_length=500,
        tool_calls=2,
    )
    assert result.query == "test query"
    assert result.version == "V2"
    assert result.response_time_ms == 1234.56
    assert result.success is True
    assert result.tool_calls == 2


def test_benchmark_summary():
    """Test BenchmarkSummary computation."""
    summary = BenchmarkSummary(
        version="V2",
        total_queries=10,
        successful=9,
        failed=1,
        avg_ms=1500.0,
        median_ms=1400.0,
        min_ms=800.0,
        max_ms=3000.0,
        total_ms=15000.0,
        times=[800, 1000, 1200, 1400, 1500, 1600, 1700, 1800, 3000],
    )
    assert summary.version == "V2"
    assert summary.total_queries == 10
    assert summary.successful == 9
    assert len(summary.times) == 9


def test_benchmark_queries_count():
    """Should have exactly 10 benchmark queries."""
    assert len(BENCHMARK_QUERIES) == 10


def test_benchmark_queries_non_empty():
    """All benchmark queries should be non-empty strings."""
    for q in BENCHMARK_QUERIES:
        assert isinstance(q, str)
        assert len(q.strip()) > 0


def test_offline_benchmark_runs():
    """Offline benchmark should complete successfully."""
    result = asyncio.run(run_offline_benchmark())
    assert result is True


# ============================================
# Main Entry Point
# ============================================

async def main():
    """Main benchmark entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="JAWIR OS Performance Benchmark")
    parser.add_argument(
        "--mode",
        choices=["offline", "live", "v1-only", "v2-only"],
        default="offline",
        help="Benchmark mode: offline (mock), live (real API), v1-only, v2-only",
    )
    parser.add_argument(
        "--queries",
        type=int,
        default=10,
        help="Number of queries to benchmark (1-10)",
    )
    
    args = parser.parse_args()
    queries = BENCHMARK_QUERIES[:args.queries]
    
    if args.mode == "offline":
        await run_offline_benchmark()
    
    elif args.mode == "live":
        print("🔥 LIVE BENCHMARK - Using real API calls")
        print("   Make sure GOOGLE_API_KEY and TAVILY_API_KEY are set in .env")
        
        v1_results, v1_summary = await run_benchmark_suite("V1", queries)
        v2_results, v2_summary = await run_benchmark_suite("V2", queries)
        print_comparison(v1_results, v1_summary, v2_results, v2_summary)
    
    elif args.mode == "v2-only":
        print("🔥 V2-ONLY BENCHMARK")
        v2_results, v2_summary = await run_benchmark_suite("V2", queries)
        
        print(f"\n\nV2 Summary:")
        print(f"  Avg: {v2_summary.avg_ms}ms")
        print(f"  Median: {v2_summary.median_ms}ms")
        print(f"  Min: {v2_summary.min_ms}ms")
        print(f"  Max: {v2_summary.max_ms}ms")
    
    elif args.mode == "v1-only":
        print("🔥 V1-ONLY BENCHMARK")
        v1_results, v1_summary = await run_benchmark_suite("V1", queries)
        
        print(f"\n\nV1 Summary:")
        print(f"  Avg: {v1_summary.avg_ms}ms")
        print(f"  Median: {v1_summary.median_ms}ms")
        print(f"  Min: {v1_summary.min_ms}ms")
        print(f"  Max: {v1_summary.max_ms}ms")


if __name__ == "__main__":
    asyncio.run(main())
