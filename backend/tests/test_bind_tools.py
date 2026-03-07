"""Test bind_tools with minimal tool to isolate the issue."""
import os, sys, asyncio, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# Simple test tool
class SearchInput(BaseModel):
    query: str = Field(description="Search query")

def dummy_search(query: str) -> str:
    return f"Search result for: {query}"

test_tool = StructuredTool.from_function(
    func=dummy_search,
    name="web_search",
    description="Search the internet for current information",
    args_schema=SearchInput,
)

API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEYS", "").split(",")[0]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

async def main():
    print(f"Model: {MODEL}")
    print(f"Key: {API_KEY[:10]}...")
    
    # Test 1: Minimal tool (1 tool)
    print("\n--- Test 1: bind_tools with 1 simple tool ---")
    llm = ChatGoogleGenerativeAI(model=MODEL, google_api_key=API_KEY, temperature=0.7, convert_system_message_to_human=True)
    llm_tools = llm.bind_tools([test_tool])
    
    t0 = time.time()
    try:
        resp = await asyncio.wait_for(
            llm_tools.ainvoke([
                SystemMessage(content="You are JAWIR. Use web_search to find current info when asked."),
                HumanMessage(content="Cari harga Bitcoin hari ini"),
            ]),
            timeout=30,
        )
        dt = time.time() - t0
        print(f"  Time: {dt:.1f}s")
        print(f"  Tool calls: {resp.tool_calls}")
        content = resp.content[:100] if resp.content else "(none)"
        print(f"  Content: {content}")
        print(f"  RESULT: OK")
    except asyncio.TimeoutError:
        print(f"  TIMEOUT after {time.time()-t0:.1f}s!")
        print(f"  RESULT: FAIL (timeout)")
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  RESULT: FAIL")

    # Test 2: All 12 tools
    print("\n--- Test 2: bind_tools with all 12 JAWIR tools ---")
    from agent.tools import get_all_tools
    all_tools = get_all_tools()
    print(f"  Tools: {len(all_tools)}")
    
    llm2 = ChatGoogleGenerativeAI(model=MODEL, google_api_key=API_KEY, temperature=0.7, convert_system_message_to_human=True)
    llm2_tools = llm2.bind_tools(all_tools)
    
    t0 = time.time()
    try:
        resp2 = await asyncio.wait_for(
            llm2_tools.ainvoke([
                SystemMessage(content="You are JAWIR. Use web_search tool when asked to search."),
                HumanMessage(content="Cari harga Bitcoin hari ini"),
            ]),
            timeout=60,
        )
        dt = time.time() - t0
        print(f"  Time: {dt:.1f}s")
        print(f"  Tool calls: {resp2.tool_calls}")
        content = resp2.content[:100] if resp2.content else "(none)"
        print(f"  Content: {content}")
        print(f"  RESULT: OK")
    except asyncio.TimeoutError:
        print(f"  TIMEOUT after {time.time()-t0:.1f}s!")
        print(f"  RESULT: FAIL (timeout)")
    except Exception as e:
        print(f"  ERROR: {e}")
        print(f"  RESULT: FAIL")

asyncio.run(main())
