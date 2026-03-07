"""
Test JAWIR chat - kapan pakai research vs direct response
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv()

from agent.api_rotator import init_rotator
from agent.graph import invoke_agent

# Initialize API key rotator
api_keys = os.getenv("GOOGLE_API_KEYS", "").split(",")
print(f"Loaded {len(api_keys)} API keys")
init_rotator(api_keys)

async def test_chat():
    """Test berbagai jenis pertanyaan"""
    
    test_cases = [
        # Harusnya DIRECT (tanpa research)
        ("apa itu Python?", "DIRECT"),
        ("buatkan function fibonacci", "DIRECT"),
        
        # Harusnya RESEARCH (perlu search)
        ("harga RTX 5090 terbaru", "RESEARCH"),
    ]
    
    for query, expected in test_cases:
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"EXPECTED: {expected}")
        print('='*60)
        
        try:
            result = await invoke_agent(query, f'test-{hash(query) % 1000}')
            
            # Check if it used research or not
            sources = result.get('sources_used', [])
            actual = "RESEARCH" if sources else "DIRECT"
            status = "OK" if actual == expected else "WRONG"
            
            print(f"\nACTUAL: {actual} [{status}]")
            print(f"RESPONSE: {result['final_response'][:200]}...")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
