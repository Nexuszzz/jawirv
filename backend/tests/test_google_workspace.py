#!/usr/bin/env python
"""
Test Google Workspace Tools setelah OAuth
"""

import os
import sys

# Setup path
current_dir = os.path.dirname(__file__)
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from tools.google_workspace import GoogleWorkspaceMCP

def test_google_workspace():
    """Test semua Google Workspace tools."""
    
    print("=" * 60)
    print("🧪 GOOGLE WORKSPACE INTEGRATION TEST")
    print("=" * 60)
    
    # Initialize client
    try:
        mcp = GoogleWorkspaceMCP(user_email="hazzikiraju@gmail.com")
        print(f"✅ MCP Client initialized")
        print(f"   Path: {mcp.mcp_path}")
        print(f"   Email: {mcp.user_email}")
    except Exception as e:
        print(f"❌ Failed to init MCP: {e}")
        return
    
    tests = []
    
    # Test 1: Gmail Labels
    print("\n📧 Test 1: Gmail - List Labels")
    print("-" * 40)
    try:
        result = mcp.list_gmail_labels()
        if result.get("success"):
            print(f"✅ PASS - Got labels")
            output = result.get("output", "")[:200]
            print(f"   Output: {output}...")
            tests.append(("Gmail Labels", True))
        else:
            print(f"❌ FAIL - {result.get('error')}")
            tests.append(("Gmail Labels", False))
    except Exception as e:
        print(f"❌ ERROR - {e}")
        tests.append(("Gmail Labels", False))
    
    # Test 2: Gmail Search
    print("\n📧 Test 2: Gmail - Search")
    print("-" * 40)
    try:
        result = mcp.search_gmail("in:inbox", max_results=3)
        if result.get("success"):
            print(f"✅ PASS - Search completed")
            output = result.get("output", "")[:300]
            print(f"   Output: {output}...")
            tests.append(("Gmail Search", True))
        else:
            print(f"❌ FAIL - {result.get('error')}")
            tests.append(("Gmail Search", False))
    except Exception as e:
        print(f"❌ ERROR - {e}")
        tests.append(("Gmail Search", False))
    
    # Test 3: Drive List
    print("\n📁 Test 3: Drive - List Files")
    print("-" * 40)
    try:
        result = mcp.search_drive_files("*")
        if result.get("success"):
            print(f"✅ PASS - Got files")
            output = result.get("output", "")[:300]
            print(f"   Output: {output}...")
            tests.append(("Drive List", True))
        else:
            print(f"❌ FAIL - {result.get('error')}")
            tests.append(("Drive List", False))
    except Exception as e:
        print(f"❌ ERROR - {e}")
        tests.append(("Drive List", False))
    
    # Test 4: Calendar List
    print("\n📅 Test 4: Calendar - List")
    print("-" * 40)
    try:
        result = mcp.list_calendars()
        if result.get("success"):
            print(f"✅ PASS - Got calendars")
            output = result.get("output", "")[:300]
            print(f"   Output: {output}...")
            tests.append(("Calendar List", True))
        else:
            print(f"❌ FAIL - {result.get('error')}")
            tests.append(("Calendar List", False))
    except Exception as e:
        print(f"❌ ERROR - {e}")
        tests.append(("Calendar List", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    
    for name, ok in tests:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL GOOGLE WORKSPACE TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
    
    return passed == total


def test_sheets_docs():
    """Test Sheets and Docs tools."""
    
    print("\n" + "=" * 60)
    print("📊 SHEETS & DOCS TEST")
    print("=" * 60)
    
    from tools.google_workspace import GoogleWorkspaceMCP
    mcp = GoogleWorkspaceMCP(user_email="hazzikiraju@gmail.com")
    
    tests = []
    
    # Test Sheets Create
    print("\n📊 Test: Sheets - Create Spreadsheet")
    print("-" * 40)
    try:
        result = mcp.create_spreadsheet("JAWIR Test Sheet")
        if result.get("success"):
            print(f"✅ PASS - Created spreadsheet")
            output = result.get("output", "")[:200]
            print(f"   Output: {output}...")
            tests.append(("Sheets Create", True))
        else:
            print(f"❌ FAIL - {result.get('error', '')[:200]}")
            tests.append(("Sheets Create", False))
    except Exception as e:
        print(f"❌ ERROR - {e}")
        tests.append(("Sheets Create", False))
    
    # Test Docs Create
    print("\n📝 Test: Docs - Create Document")
    print("-" * 40)
    try:
        result = mcp.create_doc("JAWIR Test Doc", "This is a test document from JAWIR OS")
        if result.get("success"):
            print(f"✅ PASS - Created document")
            output = result.get("output", "")[:200]
            print(f"   Output: {output}...")
            tests.append(("Docs Create", True))
        else:
            print(f"❌ FAIL - {result.get('error', '')[:200]}")
            tests.append(("Docs Create", False))
    except Exception as e:
        print(f"❌ ERROR - {e}")
        tests.append(("Docs Create", False))
    
    # Summary
    print("\n" + "-" * 40)
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    for name, ok in tests:
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    print(f"\n  Sheets/Docs: {passed}/{total} passed")
    
    return passed, total


if __name__ == "__main__":
    test_google_workspace()
    test_sheets_docs()
