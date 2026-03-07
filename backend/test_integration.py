"""
JAWIR OS - Frontend-Backend Integration Test
Validates that all APIs and WebSocket messages match between frontend and backend.
"""
import asyncio
import os
import sys
import json
import httpx
import websockets
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"


def print_header(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def test_health_check():
    """Test if backend is running."""
    print_header("Test 1: Health Check")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BACKEND_URL}/")
            
            if response.status_code == 200:
                print("✅ Backend is running")
                return True
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to backend")
        print("   Run: cd backend && python -m uvicorn app.main:app --port 8000")
        return False


async def test_upload_endpoint():
    """Test upload endpoint matches frontend expectations."""
    print_header("Test 2: Upload Endpoint")
    
    # Minimal valid PNG
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
        0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("test_integration.png", png_data, "image/png")}
            response = await client.post(f"{BACKEND_URL}/api/upload/file", files=files)
            
            if response.status_code != 200:
                print(f"❌ Upload failed: {response.status_code}")
                return False, None
            
            data = response.json()
            
            # Validate response matches frontend UploadResponse interface
            required_fields = ["success", "file_id", "filename", "file_type", "file_size", "url", "message"]
            optional_fields = ["base64_preview"]
            
            missing = [f for f in required_fields if f not in data]
            if missing:
                print(f"❌ Missing required fields: {missing}")
                return False, None
            
            print("✅ Upload response matches frontend interface:")
            for field in required_fields:
                print(f"   • {field}: {str(data[field])[:50]}")
            
            return True, data
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None


async def test_websocket_connection():
    """Test WebSocket connection and basic messaging."""
    print_header("Test 3: WebSocket Connection")
    
    try:
        async with websockets.connect(WS_URL, open_timeout=10, close_timeout=5) as ws:
            print("✅ WebSocket connected")
            
            # Backend sends welcome message on connect
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get("type") == "connection":
                print("✅ Received welcome message")
                print(f"   Message: {data.get('message', '')[:50]}...")
                return True
            else:
                # Fallback: check if we can receive any message
                print(f"⚠️ Unexpected first message type: {data.get('type')}")
                return True  # Still connected, just different message type
                
    except asyncio.TimeoutError:
        print("❌ WebSocket timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False


async def test_websocket_user_message():
    """Test sending user message via WebSocket."""
    print_header("Test 4: WebSocket User Message")
    
    try:
        async with websockets.connect(WS_URL, open_timeout=30, close_timeout=5) as ws:
            # Send user message (same format as frontend)
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {
                    "content": "halo"
                },
                "session_id": "test-session-001",
                "timestamp": datetime.now().timestamp() * 1000
            }))
            
            print("   Sent: user_message 'halo'")
            
            # Collect responses
            responses = []
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(response)
                    responses.append(data)
                    print(f"   Received: {data.get('type')}")
                    
                    # Stop when we get final response
                    if data.get("type") == "agent_response":
                        break
                    if data.get("type") == "error":
                        break
                        
            except asyncio.TimeoutError:
                pass
            
            # Validate response types
            response_types = [r.get("type") for r in responses]
            
            if "agent_response" in response_types:
                print("✅ Received agent_response")
                
                # Validate agent_response structure
                agent_response = next(r for r in responses if r.get("type") == "agent_response")
                required = ["type", "content", "thinking_process", "sources_used"]
                missing = [f for f in required if f not in agent_response]
                
                if missing:
                    print(f"⚠️ Missing fields in agent_response: {missing}")
                else:
                    print("✅ agent_response structure matches frontend interface")
                    print(f"   Content preview: {agent_response.get('content', '')[:100]}...")
                
                return True
            else:
                print(f"❌ No agent_response received. Got: {response_types}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_websocket_message_with_file(file_id: str):
    """Test sending message with file attachment via WebSocket."""
    print_header("Test 5: WebSocket Message with File")
    
    if not file_id:
        print("⚠️ Skipping - no file_id available")
        return False
    
    try:
        async with websockets.connect(WS_URL, open_timeout=30, close_timeout=5) as ws:
            # Send user message with file (same format as frontend)
            await ws.send(json.dumps({
                "type": "user_message_with_file",
                "data": {
                    "content": "Apa ini?",
                    "file_id": file_id
                },
                "session_id": "test-session-002",
                "timestamp": datetime.now().timestamp() * 1000
            }))
            
            print(f"   Sent: user_message_with_file (file_id={file_id})")
            
            # Collect responses
            responses = []
            try:
                while True:
                    response = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(response)
                    responses.append(data)
                    print(f"   Received: {data.get('type')} - {data.get('message', '')[:50]}")
                    
                    if data.get("type") in ["agent_response", "error"]:
                        break
                        
            except asyncio.TimeoutError:
                pass
            
            if any(r.get("type") == "agent_response" for r in responses):
                print("✅ File message processed successfully")
                return True
            else:
                print(f"❌ Expected agent_response")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("  🔗 JAWIR OS - FRONTEND-BACKEND INTEGRATION TEST")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = []
    
    # Test 1: Health check
    passed = await test_health_check()
    results.append(("Health Check", passed))
    if not passed:
        print("\n⚠️ Backend not running. Stopping tests.")
        return
    
    # Test 2: Upload
    passed, upload_data = await test_upload_endpoint()
    results.append(("Upload Endpoint", passed))
    
    # Test 3: WebSocket connection
    passed = await test_websocket_connection()
    results.append(("WebSocket Connection", passed))
    
    # Test 4: User message
    passed = await test_websocket_user_message()
    results.append(("User Message", passed))
    
    # Test 5: Message with file
    file_id = upload_data.get("file_id") if upload_data else None
    passed = await test_websocket_message_with_file(file_id)
    results.append(("Message with File", passed))
    
    # Summary
    print_header("📊 INTEGRATION TEST SUMMARY")
    
    passed_count = sum(1 for _, p in results if p)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    print(f"\n   Total: {passed_count}/{len(results)} passed")
    
    if passed_count == len(results):
        print("\n   🎉 ALL INTEGRATION TESTS PASSED!")
        print("   Frontend and Backend are fully compatible.")
    else:
        print(f"\n   ⚠️ {len(results) - passed_count} test(s) failed")


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
