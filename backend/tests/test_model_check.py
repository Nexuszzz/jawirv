"""Quick test: does Gemini model + bind_tools work?"""
import os, sys, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent.tools import get_all_tools

tools = get_all_tools()
print(f"Tools loaded: {len(tools)}")
print(f"Tool names: {[t.name for t in tools]}")

MODELS_TO_TEST = ["gemini-2.0-flash", "gemini-2.5-flash-preview-05-20"]
API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEYS", "").split(",")[0]

async def test():
    for model_name in MODELS_TO_TEST:
        print(f"\n--- Testing model: {model_name} ---")
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=API_KEY,
                temperature=0.7,
                convert_system_message_to_human=True,
            )
            llm_with_tools = llm.bind_tools(tools)
            
            # Test 1: Simple chat (should NOT call tools)
            resp = await llm_with_tools.ainvoke([
                SystemMessage(content="You are JAWIR. Reply briefly in one sentence."),
                HumanMessage(content="What is 2+2?"),
            ])
            tc = resp.tool_calls
            content = resp.content[:200] if resp.content else "(no content)"
            print(f"  Chat test: tool_calls={len(tc)}, content={content}")
            
            # Test 2: Search trigger (SHOULD call web_search tool)
            resp2 = await llm_with_tools.ainvoke([
                SystemMessage(content="You are JAWIR. Use web_search tool to search for info."),
                HumanMessage(content="Cari harga Bitcoin hari ini"),
            ])
            tc2 = resp2.tool_calls
            content2 = resp2.content[:200] if resp2.content else "(no content)"
            print(f"  Search test: tool_calls={len(tc2)}, content={content2}")
            if tc2:
                for call in tc2:
                    print(f"    -> tool={call['name']}, args={call['args']}")
            
            print(f"  RESULT: OK")
        except Exception as e:
            print(f"  RESULT: FAILED - {e}")

asyncio.run(test())
