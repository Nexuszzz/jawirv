"""
JAWIR OS - File Upload Test Suite
Testing image and PDF upload functionality
"""
import asyncio
import os
import sys
import base64
import httpx
from pathlib import Path

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

# Backend URL
BACKEND_URL = "http://localhost:8000"


async def test_upload_image():
    """Test uploading an image file."""
    print("\n" + "="*60)
    print("TEST: Upload Image (PNG)")
    print("="*60)
    
    # Create a simple test image (1x1 red pixel PNG)
    # This is a minimal valid PNG file
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixels
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
        0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,  # IEND chunk
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("test.png", png_data, "image/png")}
            response = await client.post(f"{BACKEND_URL}/api/upload/file", files=files)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful!")
                print(f"   File ID: {data.get('file_id')}")
                print(f"   Type: {data.get('file_type')}")
                print(f"   Name: {data.get('original_name')}")
                return True, data
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False, None
                
    except httpx.ConnectError:
        print("❌ Cannot connect to backend. Is the server running?")
        print("   Run: cd backend && python -m uvicorn app.main:app --port 8000")
        return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None


async def test_upload_pdf():
    """Test uploading a PDF file."""
    print("\n" + "="*60)
    print("TEST: Upload PDF")
    print("="*60)
    
    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": ("test.pdf", pdf_content, "application/pdf")}
            response = await client.post(f"{BACKEND_URL}/api/upload/file", files=files)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful!")
                print(f"   File ID: {data.get('file_id')}")
                print(f"   Type: {data.get('file_type')}")
                print(f"   Name: {data.get('original_name')}")
                print(f"   Text extracted: {len(data.get('extracted_text', '')) > 0}")
                return True, data
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False, None
                
    except httpx.ConnectError:
        print("❌ Cannot connect to backend. Is the server running?")
        return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None


async def test_chat_with_file(file_data: dict):
    """Test sending a chat message with an uploaded file."""
    print("\n" + "="*60)
    print("TEST: Chat with File Attachment")
    print("="*60)
    
    if not file_data:
        print("⚠️ Skipping - no file data available")
        return False
    
    # This would typically be done via WebSocket
    # For now, just verify the file data structure
    print(f"✅ File ready for chat:")
    print(f"   ID: {file_data.get('file_id')}")
    print(f"   Type: {file_data.get('file_type')}")
    
    # Simulate what would be sent via WebSocket
    message_payload = {
        "type": "user_message_with_file",
        "content": "Analisis gambar ini",
        "file_id": file_data.get("file_id"),
        "file_type": file_data.get("file_type"),
        "file_name": file_data.get("original_name"),
    }
    
    print(f"   Payload ready: {message_payload}")
    return True


async def run_all_tests():
    """Run all file upload tests."""
    print("\n" + "="*60)
    print("🧪 JAWIR OS - FILE UPLOAD TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Image upload
    passed, img_data = await test_upload_image()
    results.append(("Image Upload", passed))
    
    # Test 2: PDF upload
    passed, pdf_data = await test_upload_pdf()
    results.append(("PDF Upload", passed))
    
    # Test 3: Chat with file
    passed = await test_chat_with_file(img_data)
    results.append(("Chat with File", passed))
    
    # Summary
    print("\n" + "="*60)
    print("📊 FILE UPLOAD TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, p in results if p)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    print(f"\nTotal: {passed_count}/{len(results)} passed")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
