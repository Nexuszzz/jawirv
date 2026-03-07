"""
Quick Test Script for Polinema Tools
Test without live scraping - uses cached data
"""
import asyncio
import sys
sys.path.insert(0, '.')

from agent.tools.polinema import (
    _get_biodata_impl,
    _get_akademik_impl,
    _get_lms_impl
)

async def test_polinema_tools():
    """Test all Polinema tools with cached data."""

    print("=" * 60)
    print("QUICK TEST: POLINEMA TOOLS (Cached Data)")
    print("=" * 60)
    print()

    # Test 1: Biodata
    print("[TEST 1] polinema_get_biodata...")
    try:
        result = await _get_biodata_impl(force_refresh=False)
        print(result)
        print("✅ PASS\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")

    # Test 2: Akademik
    print("[TEST 2] polinema_get_akademik...")
    try:
        result = await _get_akademik_impl(
            include_kehadiran=True,
            include_nilai=True,
            include_jadwal=True,
            include_kalender=True,
            force_refresh=False
        )
        print(result)
        print("✅ PASS\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")

    # Test 3: LMS
    print("[TEST 3] polinema_get_lms_assignments...")
    try:
        result = await _get_lms_impl(force_refresh=False)
        print(result)
        print("✅ PASS\n")
    except Exception as e:
        print(f"❌ FAIL: {e}\n")

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_polinema_tools())
