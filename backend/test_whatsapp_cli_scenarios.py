"""
Test 5 Scenario Campuran: WhatsApp Tools + Other Tools
========================================================
Test via JAWIR CLI dengan skenario realistis yang menggabungkan
WhatsApp tools dengan tools lain (web search, Python, Gmail, Sheets, dll).
"""

import asyncio
import websockets
import json
import uuid
from pathlib import Path
from datetime import datetime

# Session management
SESSION_FILE = Path.home() / ".jawir" / "session_id"

def get_session_id() -> str:
    """Get or create session ID"""
    if SESSION_FILE.exists():
        return SESSION_FILE.read_text().strip()
    
    session_id = str(uuid.uuid4())
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(session_id)
    return session_id


async def send_message_to_jawir(prompt: str, timeout: int = 120) -> list:
    """Send message to JAWIR and collect responses"""
    session_id = get_session_id()
    uri = "ws://localhost:8000/ws/chat"
    
    responses = []
    
    try:
        async with websockets.connect(uri, ping_interval=20, ping_timeout=120) as ws:
            # Send message
            message = {
                "type": "user_message",
                "data": {
                    "content": prompt,
                    "session_id": session_id,
                }
            }
            await ws.send(json.dumps(message))
            print(f"📤 Sent: {prompt[:100]}...")
            
            # Collect responses
            async for msg in ws:
                data = json.loads(msg)
                responses.append(data)
                
                msg_type = data.get("type", "")
                
                # Print progress
                if msg_type == "thinking":
                    thought = data.get("data", {}).get("thought", "")
                    print(f"💭 Thinking: {thought[:100]}")
                elif msg_type == "executing_tool":
                    tool = data.get("data", {}).get("tool", "")
                    print(f"🔧 Tool: {tool}")
                elif msg_type == "final_response":
                    response = data.get("data", {}).get("text", "")
                    print(f"✅ Response: {response[:200]}")
                    break
                elif msg_type == "error":
                    error = data.get("data", {}).get("message", "")
                    print(f"❌ Error: {error}")
                    break
                    
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        
    return responses


def print_separator(title: str):
    """Print formatted separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def analyze_responses(responses: list, expected_tools: list) -> dict:
    """Analyze responses and check if expected tools were called"""
    tools_called = []
    final_response = ""
    
    for resp in responses:
        if resp.get("type") == "executing_tool":
            tool_name = resp.get("data", {}).get("tool", "")
            tools_called.append(tool_name)
        elif resp.get("type") == "final_response":
            final_response = resp.get("data", {}).get("text", "")
    
    # Check if expected tools were called
    tools_matched = all(tool in tools_called for tool in expected_tools)
    
    return {
        "tools_called": tools_called,
        "expected_tools": expected_tools,
        "tools_matched": tools_matched,
        "final_response": final_response,
    }


async def test_scenario_1():
    """
    Scenario 1: Cek Nomor WhatsApp + Web Search Info
    Expected tools: whatsapp_check_number, web_search
    """
    print_separator("Scenario 1: Cek Nomor WA + Search Info")
    
    prompt = """
    Tolong cek apakah nomor 6287853462867 terdaftar di WhatsApp.
    Kalau terdaftar, cari info tentang kode area 6287853 itu dari mana.
    """
    
    responses = await send_message_to_jawir(prompt, timeout=60)
    result = analyze_responses(responses, ["whatsapp_check_number"])
    
    print(f"\n📊 Analysis:")
    print(f"  Tools called: {result['tools_called']}")
    print(f"  Expected: {result['expected_tools']}")
    print(f"  Match: {'✅' if result['tools_matched'] else '❌'}")
    
    return result


async def test_scenario_2():
    """
    Scenario 2: List Kontak WA + Hitung Jumlah (Python)
    Expected tools: whatsapp_list_contacts, run_python_code
    """
    print_separator("Scenario 2: List Kontak WA + Analisis Python")
    
    prompt = """
    Tampilkan list kontak WhatsApp saya, 
    lalu hitung ada berapa total kontak menggunakan Python code.
    """
    
    responses = await send_message_to_jawir(prompt, timeout=60)
    result = analyze_responses(responses, ["whatsapp_list_contacts"])
    
    print(f"\n📊 Analysis:")
    print(f"  Tools called: {result['tools_called']}")
    print(f"  Expected: {result['expected_tools']}")
    print(f"  Match: {'✅' if result['tools_matched'] else '❌'}")
    
    return result


async def test_scenario_3():
    """
    Scenario 3: Search Info + Kirim via WhatsApp
    Expected tools: web_search, whatsapp_send_message
    """
    print_separator("Scenario 3: Web Search + Kirim WA")
    
    prompt = """
    Cari info tentang cuaca Jakarta hari ini dari web,
    lalu kirimkan ringkasan singkatnya ke nomor WhatsApp 6287853462867.
    """
    
    responses = await send_message_to_jawir(prompt, timeout=60)
    result = analyze_responses(responses, ["web_search", "whatsapp_send_message"])
    
    print(f"\n📊 Analysis:")
    print(f"  Tools called: {result['tools_called']}")
    print(f"  Expected: {result['expected_tools']}")
    print(f"  Match: {'✅' if result['tools_matched'] else '❌'}")
    
    return result


async def test_scenario_4():
    """
    Scenario 4: List Chats WA + Hitung (No External Tools)
    Expected tools: whatsapp_list_chats
    """
    print_separator("Scenario 4: List Chats WA")
    
    prompt = """
    Tampilkan list percakapan WhatsApp saya.
    Berapa jumlah total chat yang saya punya?
    """
    
    responses = await send_message_to_jawir(prompt, timeout=60)
    result = analyze_responses(responses, ["whatsapp_list_chats"])
    
    print(f"\n📊 Analysis:")
    print(f"  Tools called: {result['tools_called']}")
    print(f"  Expected: {result['expected_tools']}")
    print(f"  Match: {'✅' if result['tools_matched'] else '❌'}")
    
    return result


async def test_scenario_5():
    """
    Scenario 5: List Grup WA + Analisis
    Expected tools: whatsapp_list_groups
    """
    print_separator("Scenario 5: List Grup WA + Info")
    
    prompt = """
    List semua grup WhatsApp yang saya ikuti.
    Berapa total grup yang ada?
    """
    
    responses = await send_message_to_jawir(prompt, timeout=60)
    result = analyze_responses(responses, ["whatsapp_list_groups"])
    
    print(f"\n📊 Analysis:")
    print(f"  Tools called: {result['tools_called']}")
    print(f"  Expected: {result['expected_tools']}")
    print(f"  Match: {'✅' if result['tools_matched'] else '❌'}")
    
    return result


async def main():
    """Run all test scenarios"""
    print_separator("JAWIR CLI WhatsApp Integration Test")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: http://localhost:8000")
    print(f"Session: {get_session_id()}")
    
    results = []
    
    # Run all scenarios
    scenarios = [
        test_scenario_1,
        test_scenario_2,
        test_scenario_3,
        test_scenario_4,
        test_scenario_5,
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        try:
            result = await scenario()
            results.append({
                "scenario": i,
                "name": scenario.__doc__.split("\n")[1].strip(),
                "success": result["tools_matched"],
                "tools_called": result["tools_called"],
            })
        except Exception as e:
            print(f"❌ Scenario {i} failed: {str(e)}")
            results.append({
                "scenario": i,
                "success": False,
                "error": str(e),
            })
        
        # Wait between tests
        if i < len(scenarios):
            print("\n⏳ Waiting 3s before next test...\n")
            await asyncio.sleep(3)
    
    # Final Summary
    print_separator("Final Summary")
    
    success_count = sum(1 for r in results if r.get("success", False))
    total_count = len(results)
    
    print(f"✅ Passed: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    print(f"Success Rate: {success_count/total_count*100:.1f}%")
    
    print("\nDetailed Results:")
    for r in results:
        scenario = r.get("scenario", "?")
        name = r.get("name", "Unknown")
        success = r.get("success", False)
        tools = r.get("tools_called", [])
        
        emoji = "✅" if success else "❌"
        print(f"{emoji} Scenario {scenario}: {name}")
        if tools:
            print(f"   Tools: {', '.join(tools)}")
        if not success and "error" in r:
            print(f"   Error: {r['error']}")
    
    print("\n" + "="*80)
    print("Test complete! Check logs above for details.")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
