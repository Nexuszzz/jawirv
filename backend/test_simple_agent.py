"""
Simple direct test for the agent - bypass WebSocket.
"""

import asyncio
import logging
import os
import sys
import traceback

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test")

async def test_agent():
    """Direct test of agent invoke."""
    # Initialize rotator before importing agent
    from dotenv import load_dotenv
    load_dotenv()
    
    from app.config import settings
    from agent.api_rotator import init_rotator, get_rotator
    
    # Initialize rotator with keys
    init_rotator(settings.all_google_api_keys)
    print(f"✅ Rotator initialized with {len(settings.all_google_api_keys)} keys")
    
    from agent.graph import invoke_agent
    
    query = "Apa itu ESP32? Jelaskan fitur utamanya."
    session_id = "test-direct-001"
    
    print("\n" + "=" * 60)
    print("DIRECT AGENT TEST")
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)
    
    result = await invoke_agent(
        user_query=query,
        session_id=session_id,
        streamer=None,  # No streaming
    )
    
    print("\n=== RESULT ===")
    print(f"Response length: {len(result.get('final_response', ''))}")
    print(f"Thinking steps: {len(result.get('thinking_process', []))}")
    print(f"Sources: {len(result.get('sources_used', []))}")
    
    print("\n=== RESPONSE ===")
    print(result.get("final_response", "NO RESPONSE")[:2000])
    
    print("\n=== SOURCES ===")
    for s in result.get("sources_used", [])[:5]:
        print(f"  - {s}")


if __name__ == "__main__":
    asyncio.run(test_agent())
