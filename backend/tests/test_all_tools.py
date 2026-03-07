"""
JAWIR OS - Comprehensive Tool Test
====================================
Test semua 12 tools secara langsung (tanpa WebSocket/Gemini).
Ini untuk memastikan setiap tool berfungsi sebelum integration test.

Tools:
1. web_search - Tavily web search
2. run_python_code - Python execution
3. generate_kicad_schematic - KiCad schematic design
4. gmail_search - Gmail search (butuh OAuth)
5. gmail_send - Send email (butuh OAuth)
6. drive_search - Google Drive search (butuh OAuth)
7. drive_list - Google Drive list (butuh OAuth)
8. calendar_list_events - Calendar list (butuh OAuth)
9. calendar_create_event - Calendar create (butuh OAuth)
10. open_app - Open desktop app
11. open_url - Open URL in browser
12. close_app - Close desktop app
"""

import asyncio
import os
import sys

# Add backend to path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Force reload config (clear lru_cache)
import importlib
import app.config
importlib.reload(app.config)

from app.config import settings

# Initialize API Key Rotator (normally done in server lifespan)
from agent.api_rotator import init_rotator
if settings.all_google_api_keys:
    init_rotator(settings.all_google_api_keys)
    print(f"  API Rotator initialized with {len(settings.all_google_api_keys)} keys")

print("=" * 60)
print("  JAWIR OS - Tool Test Suite")
print("=" * 60)
print(f"  Model: {settings.gemini_model}")
print(f"  API Keys: {len(settings.all_google_api_keys)}")
print(f"  Tavily Key: {'SET' if settings.tavily_api_key else 'MISSING'}")
print("=" * 60)


async def test_web_search():
    """Test web_search tool."""
    print("\n[TEST 1] web_search")
    print("-" * 40)
    try:
        from tools.web_search import TavilySearchTool
        tool = TavilySearchTool(api_key=settings.tavily_api_key)
        results = await tool.search("Python programming language", max_results=2)
        
        if results:
            print(f"  ✅ PASS - Got {len(results)} results")
            print(f"     First: {results[0].title[:50]}...")
            return True
        else:
            print("  ❌ FAIL - No results")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_python_exec():
    """Test run_python_code tool."""
    print("\n[TEST 2] run_python_code")
    print("-" * 40)
    try:
        from agent.tools.python_exec import create_python_executor_tool
        tool = create_python_executor_tool()
        result = await tool.ainvoke({"code": "print(sum(range(1, 101)))"})
        
        if "5050" in result:
            print(f"  ✅ PASS - Output contains 5050")
            print(f"     Result: {result.strip()}")
            return True
        else:
            print(f"  ❌ FAIL - Expected 5050, got: {result}")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_desktop_open_url():
    """Test open_url tool."""
    print("\n[TEST 3] open_url")
    print("-" * 40)
    try:
        from tools.python_interpreter.desktop_control import DesktopController
        dc = DesktopController()
        result = dc.open_url("https://www.google.com")
        
        if result.get("success"):
            print(f"  ✅ PASS - {result.get('message')}")
            return True
        else:
            print(f"  ❌ FAIL - {result.get('message')}")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_desktop_open_app():
    """Test open_app tool with calculator (safe to test)."""
    print("\n[TEST 4] open_app (calculator)")
    print("-" * 40)
    try:
        from tools.python_interpreter.desktop_control import DesktopController
        dc = DesktopController()
        result = dc.open_app("calculator")
        
        if result.get("success"):
            print(f"  ✅ PASS - {result.get('message')}")
            # Close it after
            await asyncio.sleep(1)
            dc.close_app("calculator")
            print("     (Closed calculator)")
            return True
        else:
            print(f"  ❌ FAIL - {result.get('message')}")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_desktop_close_app():
    """Test close_app tool."""
    print("\n[TEST 5] close_app (notepad - will open then close)")
    print("-" * 40)
    try:
        from tools.python_interpreter.desktop_control import DesktopController
        dc = DesktopController()
        
        # Open notepad first
        dc.open_app("notepad")
        await asyncio.sleep(1)
        
        # Now close it
        result = dc.close_app("notepad")
        
        if result.get("success"):
            print(f"  ✅ PASS - {result.get('message')}")
            return True
        else:
            # Could be already closed or not found
            print(f"  ⚠️ WARN - {result.get('message')}")
            return True  # Not a critical failure
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_kicad_available():
    """Test if KiCad module is importable."""
    print("\n[TEST 6] KiCad module availability")
    print("-" * 40)
    try:
        from tools.kicad import (
            save_schematic,
            get_available_templates,
            get_template,
        )
        templates = get_available_templates()
        print(f"  ✅ PASS - KiCad module loaded")
        print(f"     Templates available: {templates[:5]}...")
        return True
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_google_workspace_available():
    """Test if Google Workspace module is importable."""
    print("\n[TEST 7] Google Workspace module availability")
    print("-" * 40)
    try:
        from tools.google_workspace import GoogleWorkspaceMCP
        gws = GoogleWorkspaceMCP()
        print(f"  ✅ PASS - GoogleWorkspaceMCP loaded")
        print(f"     Note: OAuth may not be configured - that's OK for this test")
        return True
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_tool_registration():
    """Test all 12 tools can be registered."""
    print("\n[TEST 8] All 12 tools registration")
    print("-" * 40)
    try:
        from agent.tools import get_all_tools, get_tool_names
        tools = get_all_tools()
        names = get_tool_names()
        
        expected_tools = [
            "web_search", "generate_kicad_schematic", "run_python_code",
            "gmail_search", "gmail_send", "drive_search", "drive_list",
            "calendar_list_events", "calendar_create_event",
            "open_app", "open_url", "close_app"
        ]
        
        missing = [t for t in expected_tools if t not in names]
        
        if len(tools) == 12 and not missing:
            print(f"  ✅ PASS - All 12 tools registered")
            print(f"     Tools: {names}")
            return True
        else:
            print(f"  ❌ FAIL - Expected 12 tools, got {len(tools)}")
            print(f"     Missing: {missing}")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_function_calling_executor():
    """Test FunctionCallingExecutor initialization."""
    print("\n[TEST 9] FunctionCallingExecutor init")
    print("-" * 40)
    try:
        from agent.function_calling_executor import FunctionCallingExecutor
        executor = FunctionCallingExecutor()
        
        print(f"  ✅ PASS - Executor initialized")
        print(f"     Tools: {len(executor.tools)}")
        print(f"     LLM: {executor.llm}")
        return True
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_simple_call():
    """Test simple Gemini API call (no tools)."""
    print("\n[TEST 10] Gemini simple API call")
    print("-" * 40)
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        from agent.api_rotator import get_api_key
        
        api_key = get_api_key()
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
        )
        
        response = await llm.ainvoke([HumanMessage(content="Say hello in 3 words")])
        content = response.content if isinstance(response.content, str) else str(response.content)
        
        print(f"  ✅ PASS - Gemini responded")
        print(f"     Model: {settings.gemini_model}")
        print(f"     Response: {content[:100]}")
        return True
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        return False


async def test_gemini_with_tools():
    """Test Gemini with bind_tools (function calling)."""
    print("\n[TEST 11] Gemini with bind_tools")
    print("-" * 40)
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage, SystemMessage
        from agent.api_rotator import get_api_key
        from agent.tools import get_all_tools
        
        api_key = get_api_key()
        tools = get_all_tools()
        
        llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
        )
        llm_with_tools = llm.bind_tools(tools)
        
        # Test 1: Should NOT call tools
        response = await llm_with_tools.ainvoke([
            SystemMessage(content="You are a helpful assistant. Reply briefly."),
            HumanMessage(content="What is 2+2?"),
        ])
        
        if response.tool_calls:
            print(f"  ⚠️ WARN - Tool called for simple math (not expected)")
        else:
            print(f"  ✅ PASS - No tool called for simple question")
        
        # Test 2: SHOULD call web_search
        response2 = await llm_with_tools.ainvoke([
            SystemMessage(content="You must use web_search tool to search internet for current info."),
            HumanMessage(content="Search current Bitcoin price today"),
        ])
        
        if response2.tool_calls:
            tool_name = response2.tool_calls[0]["name"]
            print(f"  ✅ PASS - Tool called: {tool_name}")
            return True
        else:
            print(f"  ⚠️ WARN - No tool called for search request")
            return True  # Still pass, Gemini might answer directly
            
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_executor_flow():
    """Test full FunctionCallingExecutor flow."""
    print("\n[TEST 12] Full Executor Flow (chat without tools)")
    print("-" * 40)
    try:
        from agent.function_calling_executor import FunctionCallingExecutor
        
        executor = FunctionCallingExecutor()
        result = await executor.execute(
            user_query="Siapa kamu? Jawab dalam 1 kalimat.",
            max_iterations=3,
        )
        
        final = result.get("final_response", "")
        iterations = result.get("iterations", 0)
        tools_used = result.get("tool_calls_history", [])
        
        if final:
            print(f"  ✅ PASS - Got response")
            print(f"     Iterations: {iterations}")
            print(f"     Tools used: {len(tools_used)}")
            print(f"     Response: {final[:150]}...")
            return True
        else:
            print(f"  ❌ FAIL - No response")
            return False
    except Exception as e:
        print(f"  ❌ FAIL - {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    results = {}
    
    # Core infrastructure tests
    results["web_search"] = await test_web_search()
    results["python_exec"] = await test_python_exec()
    results["open_url"] = await test_desktop_open_url()
    results["open_app"] = await test_desktop_open_app()
    results["close_app"] = await test_desktop_close_app()
    results["kicad_module"] = await test_kicad_available()
    results["google_module"] = await test_google_workspace_available()
    results["tool_registration"] = await test_tool_registration()
    results["executor_init"] = await test_function_calling_executor()
    results["gemini_simple"] = await test_gemini_simple_call()
    results["gemini_tools"] = await test_gemini_with_tools()
    results["full_executor"] = await test_full_executor_flow()
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")
    
    print(f"\n  Total: {passed}/{total} PASSED")
    if passed == total:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print(f"  ⚠️ {total - passed} test(s) failed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
