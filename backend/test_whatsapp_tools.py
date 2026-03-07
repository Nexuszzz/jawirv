"""
Test WhatsApp Tools Integration
=================================
Quick test untuk 5 WhatsApp tools baru.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.whatsapp import get_whatsapp_tools


async def test_whatsapp_tools():
    """Test all 5 WhatsApp tools."""
    
    tools = get_whatsapp_tools()
    
    print("=" * 60)
    print("🧪 WhatsApp Tools Integration Test")
    print("=" * 60)
    print(f"\n📦 Loaded {len(tools)} tools:\n")
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name} - {tool.description[:80]}...")
    
    print("\n" + "=" * 60)
    print("🔍 Testing Tool Execution")
    print("=" * 60)
    
    # Test 1: Check Number (dummy number)
    print("\n1️⃣ Test: whatsapp_check_number")
    try:
        check_tool = tools[0]  # whatsapp_check_number
        result = await check_tool.ainvoke({"phone": "6281234567890"})
        print(f"   Result: {result[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: List Chats
    print("\n2️⃣ Test: whatsapp_list_chats")
    try:
        list_chats_tool = tools[1]  # whatsapp_list_chats
        result = await list_chats_tool.ainvoke({})
        print(f"   Result: {result[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: List Contacts
    print("\n3️⃣ Test: whatsapp_list_contacts")
    try:
        list_contacts_tool = tools[3]  # whatsapp_list_contacts
        result = await list_contacts_tool.ainvoke({})
        print(f"   Result: {result[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: List Groups
    print("\n4️⃣ Test: whatsapp_list_groups")
    try:
        list_groups_tool = tools[4]  # whatsapp_list_groups
        result = await list_groups_tool.ainvoke({})
        print(f"   Result: {result[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_whatsapp_tools())
