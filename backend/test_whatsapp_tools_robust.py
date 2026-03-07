"""
Robust integration test untuk WhatsApp tools.
Tests semua 5 tools dengan proper error handling dan device status checking.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.gowa_client import GoWAClient, GoWAConnectionError, DeviceNotLoggedInError
from agent.tools.whatsapp import get_whatsapp_tools

# Get tools
tools = get_whatsapp_tools()
whatsapp_check_number = next((t for t in tools if t.name == "whatsapp_check_number"), None)
whatsapp_list_chats = next((t for t in tools if t.name == "whatsapp_list_chats"), None)
whatsapp_list_contacts = next((t for t in tools if t.name == "whatsapp_list_contacts"), None)
whatsapp_list_groups = next((t for t in tools if t.name == "whatsapp_list_groups"), None)
whatsapp_send_message = next((t for t in tools if t.name == "whatsapp_send_message"), None)


def print_separator(title: str = ""):
    """Print formatted separator"""
    print("\n" + "=" * 80)
    if title:
        print(f"  {title}")
        print("=" * 80)
    print()


def print_result(test_name: str, success: bool, message: str = ""):
    """Print test result with colors"""
    emoji = "✅" if success else "❌"
    status = "SUCCESS" if success else "FAILED"
    print(f"{emoji} {test_name}: {status}")
    if message:
        print(f"   {message}")


async def test_health_check():
    """Test 0: Health check GoWA server"""
    print_separator("Test 0: Health Check")
    
    client = GoWAClient()
    is_healthy, message = client.check_health()
    
    print_result("Health Check", is_healthy, message)
    
    if not is_healthy:
        print("\n⚠️  GoWA server tidak dapat diakses!")
        print("Pastikan:")
        print("  1. VPS GoWA service running: sudo systemctl status gowa.service")
        print("  2. Firewall allow port 3000: sudo ufw status")
        print("  3. URL benar: http://13.55.23.245:3000")
        return False
    
    return True


async def test_device_status():
    """Test 1: Check device login status"""
    print_separator("Test 1: Device Status")
    
    client = GoWAClient()
    is_logged_in, device_jid = client.is_device_logged_in()
    
    if is_logged_in:
        print_result("Device Status", True, f"Device JID: {device_jid}")
    else:
        print_result("Device Status", False, "No device logged in")
        print("\n⚠️  Device belum login ke WhatsApp!")
        print("Action required:")
        print("  1. Buka browser: http://13.55.23.245:3000")
        print("  2. Login: admin / jawir2026")
        print("  3. Generate QR code")
        print("  4. Scan dengan WhatsApp mobile")
        print("  5. Re-run test ini")
        print("\nNote: Tests akan tetap dilanjutkan untuk verify endpoints...")
    
    return is_logged_in


async def test_check_number():
    """Test 2: Check if number is registered on WhatsApp"""
    print_separator("Test 2: Check Number")
    
    # Test dengan nomor example (tidak akan terkirim ke siapa-siapa)
    test_phone = "628123456789"
    
    try:
        result = await whatsapp_check_number.ainvoke({"phone": test_phone})
        
        if "✅" in result or "terdaftar" in result.lower():
            print_result("Check Number", True, result[:200])
        elif "Device not logged in" in result or "DEVICE_NOT_LOGGED_IN" in result:
            print_result("Check Number", False, "Device not logged in (expected)")
        else:
            print_result("Check Number", False, result[:200])
    
    except Exception as e:
        print_result("Check Number", False, f"Exception: {str(e)}")


async def test_list_contacts():
    """Test 3: List all WhatsApp contacts"""
    print_separator("Test 3: List Contacts")
    
    try:
        result = await whatsapp_list_contacts.ainvoke({})
        
        if "✅" in result or "kontak" in result.lower():
            # Extract contact count
            lines = result.split("\n")
            contact_count = len([l for l in lines if l.strip().startswith("-")])
            print_result("List Contacts", True, f"Found {contact_count} contacts")
            print(f"\nFirst 5 lines:\n{chr(10).join(lines[:5])}")
        elif "Device not logged in" in result or "DEVICE_NOT_LOGGED_IN" in result:
            print_result("List Contacts", False, "Device not logged in (expected)")
        else:
            print_result("List Contacts", False, result[:200])
    
    except Exception as e:
        print_result("List Contacts", False, f"Exception: {str(e)}")


async def test_list_groups():
    """Test 4: List all WhatsApp groups"""
    print_separator("Test 4: List Groups")
    
    try:
        result = await whatsapp_list_groups.ainvoke({})
        
        if "✅" in result or "grup" in result.lower():
            # Extract group count
            lines = result.split("\n")
            group_count = len([l for l in lines if l.strip().startswith("-")])
            print_result("List Groups", True, f"Found {group_count} groups")
            print(f"\nFirst 5 lines:\n{chr(10).join(lines[:5])}")
        elif "Device not logged in" in result or "DEVICE_NOT_LOGGED_IN" in result:
            print_result("List Groups", False, "Device not logged in (expected)")
        else:
            print_result("List Groups", False, result[:200])
    
    except Exception as e:
        print_result("List Groups", False, f"Exception: {str(e)}")


async def test_list_chats():
    """Test 5: List all conversations"""
    print_separator("Test 5: List Chats")
    
    try:
        result = await whatsapp_list_chats.ainvoke({})
        
        if "✅" in result or "percakapan" in result.lower():
            # Extract chat count
            lines = result.split("\n")
            chat_count = len([l for l in lines if l.strip().startswith("-")])
            print_result("List Chats", True, f"Found {chat_count} chats")
            print(f"\nFirst 5 lines:\n{chr(10).join(lines[:5])}")
        elif "Device not logged in" in result or "DEVICE_NOT_LOGGED_IN" in result:
            print_result("List Chats", False, "Device not logged in (expected)")
        else:
            print_result("List Chats", False, result[:200])
    
    except Exception as e:
        print_result("List Chats", False, f"Exception: {str(e)}")


async def test_send_message():
    """Test 6: Send message (skipped for safety)"""
    print_separator("Test 6: Send Message")
    
    print("⏭️  SKIPPED: Send message test requires manual approval")
    print("   To test manually, uncomment code in test file")
    print("   Example: await whatsapp_send_message.acoroutine(")
    print("              phone='628xxx',")
    print("              message='Test from JAWIR'")
    print("            )")


async def main():
    """Run all tests"""
    print_separator("WhatsApp Tools Robust Integration Test")
    print("Testing 5 WhatsApp tools dengan GoWA API")
    print("VPS: http://13.55.23.245:3000")
    
    # Test 0: Health check first
    is_healthy = await test_health_check()
    if not is_healthy:
        print("\n❌ Health check failed. Aborting tests.")
        return
    
    # Test 1: Device status
    is_device_logged_in = await test_device_status()
    
    # Continue with other tests even if device not logged in
    # (to verify endpoints exist)
    await test_check_number()
    await test_list_contacts()
    await test_list_groups()
    await test_list_chats()
    await test_send_message()
    
    # Summary
    print_separator("Test Summary")
    
    if is_device_logged_in:
        print("✅ All systems ready!")
        print("\nNext steps:")
        print("  1. Run JAWIR CLI: python jawir_cli.py")
        print("  2. Test commands:")
        print("     /ask 'cek nomor 628xxx ada WA?'")
        print("     /ask 'list kontak WA saya'")
        print("     /ask 'list grup WA saya'")
        print("     /ask 'kirim WA ke 628xxx: test message'")
    else:
        print("⚠️  Device not logged in!")
        print("\nAction required:")
        print("  1. Open: http://13.55.23.245:3000")
        print("  2. Login: admin / jawir2026")
        print("  3. Scan QR code with WhatsApp mobile")
        print("  4. Re-run this test: python test_whatsapp_tools_robust.py")


if __name__ == "__main__":
    asyncio.run(main())
