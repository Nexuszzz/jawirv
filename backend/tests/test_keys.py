"""Quick test: Which API key works with gemini-3-pro-preview + bind_tools?"""
import os, sys, asyncio, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from agent.tools import get_all_tools

tools = get_all_tools()
print(f"Tools: {len(tools)} loaded")

# Load API keys from environment (set GOOGLE_API_KEYS=key1,key2,key3 di .env)
_raw_keys = os.environ.get("GOOGLE_API_KEYS", os.environ.get("GOOGLE_API_KEY", ""))
_key_list = [k.strip() for k in _raw_keys.split(",") if k.strip()]
if not _key_list:
    raise ValueError("GOOGLE_API_KEY atau GOOGLE_API_KEYS harus di-set di .env")

KEYS = [(f"Key{i+1}", k) for i, k in enumerate(_key_list)]


MODELS = ["gemini-3-pro-preview", "gemini-3-flash-preview"]


async def test_key_model(key_name, api_key, model_name):
    """Test one key+model combo."""
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            request_timeout=30,
        )
        llm_tools = llm.bind_tools(tools)
        
        t0 = time.time()
        resp = await llm_tools.ainvoke([
            SystemMessage(content="You are JAWIR. Reply briefly."),
            HumanMessage(content="What is 2+2? Answer in one word."),
        ])
        dt = time.time() - t0
        
        content = resp.content
        tc = resp.tool_calls
        
        # Normalize content
        if isinstance(content, list):
            parts = [item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in content]
            content = " ".join(parts)
        
        print(f"  [{key_name}] {model_name}: OK ({dt:.1f}s) tc={len(tc)} content='{content[:80]}'")
        return True
    except Exception as e:
        err = str(e)[:150]
        print(f"  [{key_name}] {model_name}: FAIL - {err}")
        return False


async def main():
    for model in MODELS:
        print(f"\n=== Model: {model} ===")
        for key_name, api_key in KEYS:
            await test_key_model(key_name, api_key, model)
    
    # Also test web_search tool directly
    print("\n=== Direct Tavily Search Test ===")
    try:
        from agent.tools.web import _web_search
        result = await _web_search.ainvoke({"query": "test"})
        print(f"  Tavily: OK - {str(result)[:100]}")
    except Exception as e:
        print(f"  Tavily: FAIL - {e}")


asyncio.run(main())
