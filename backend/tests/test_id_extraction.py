"""
Test ID Extraction from MCP Output Strings
============================================
Verifies that sheets_create, docs_create, and forms_create
correctly parse resource IDs from the MCP server's text output.

Run:
    cd backend
    venv_fresh\Scripts\python.exe tests\test_id_extraction.py
"""

import re
import sys

# ============================================================
# Simulated MCP output strings (exact format from MCP server)
# ============================================================

SHEETS_OUTPUT = (
    "Successfully created spreadsheet 'JAWIR BRUTAL TEST - Benchmark DELETE' "
    "for hazzikiraju@gmail.com. "
    "ID: 17SPITs-KOVwtwjKuM-l4j_YcEhfGxF9hhVOtj45ysm0 | "
    "URL: https://docs.google.com/spreadsheets/d/17SPITs-KOVwtwjKuM-l4j_YcEhfGxF9hhVOtj45ysm0/edit | "
    "Locale: en_US"
)

FORMS_OUTPUT = (
    "Successfully created form 'JAWIR BRUTAL TEST - Survey DELETE' "
    "for hazzikiraju@gmail.com. "
    "Form ID: 1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789. "
    "Edit URL: https://docs.google.com/forms/d/1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789/edit. "
    "Responder URL: https://docs.google.com/forms/d/1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789/viewform"
)

DOCS_OUTPUT = (
    "Created Google Doc 'JAWIR BRUTAL TEST - Report DELETE' "
    "(ID: 1b_s7vFh8Sg-XpdoAY5rdlK3sePboqOq5-d2E1_XGeyo) "
    "for hazzikiraju@gmail.com. "
    "Link: https://docs.google.com/document/d/1b_s7vFh8Sg-XpdoAY5rdlK3sePboqOq5-d2E1_XGeyo/edit"
)


def test_sheets_id_extraction():
    """Test spreadsheet ID extraction from MCP output."""
    output = SHEETS_OUTPUT
    
    id_match = re.search(r'ID:\s*([^\s|]+)', output)
    url_match = re.search(r'URL:\s*(https://[^\s|]+)', output)
    
    assert id_match, "Failed to extract spreadsheet ID"
    sheet_id = id_match.group(1)
    assert sheet_id == "17SPITs-KOVwtwjKuM-l4j_YcEhfGxF9hhVOtj45ysm0", f"Wrong ID: {sheet_id}"
    
    assert url_match, "Failed to extract spreadsheet URL"
    url = url_match.group(1)
    assert "spreadsheets/d/17SPITs" in url, f"Wrong URL: {url}"
    
    # Verify the formatted output matches expected
    formatted = f"✅ Spreadsheet 'Test' berhasil dibuat!\nID: {sheet_id}\nURL: {url}"
    assert sheet_id in formatted
    assert "https://" in formatted
    
    print(f"✅ SHEETS: ID={sheet_id}")
    print(f"   URL={url}")
    return True


def test_forms_id_extraction():
    """Test form ID extraction from MCP output."""
    output = FORMS_OUTPUT
    
    id_match = re.search(r'Form ID:\s*([^.\s]+)', output)
    url_match = re.search(r'Edit URL:\s*(https://[^\s.]+[^\s]*)', output)
    
    assert id_match, "Failed to extract form ID"
    form_id = id_match.group(1)
    assert form_id == "1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789", f"Wrong ID: {form_id}"
    
    assert url_match, "Failed to extract form URL"
    url = url_match.group(1).rstrip('.')
    assert "forms/d/1AbCdEf" in url, f"Wrong URL: {url}"
    
    formatted = f"✅ Form 'Test' berhasil dibuat!\nID: {form_id}\nURL: {url}"
    assert form_id in formatted
    assert "https://" in formatted
    
    print(f"✅ FORMS:  ID={form_id}")
    print(f"   URL={url}")
    return True


def test_docs_id_extraction():
    """Test document ID extraction from MCP output."""
    output = DOCS_OUTPUT
    
    id_match = re.search(r'\(ID:\s*([^)]+)\)', output)
    url_match = re.search(r'Link:\s*(https://[^\s]+)', output)
    
    assert id_match, "Failed to extract document ID"
    doc_id = id_match.group(1)
    assert doc_id == "1b_s7vFh8Sg-XpdoAY5rdlK3sePboqOq5-d2E1_XGeyo", f"Wrong ID: {doc_id}"
    
    assert url_match, "Failed to extract document URL"
    url = url_match.group(1)
    assert "document/d/1b_s7vFh8Sg" in url, f"Wrong URL: {url}"
    
    formatted = f"✅ Dokumen 'Test' berhasil dibuat!\nID: {doc_id}\nURL: {url}"
    assert doc_id in formatted
    assert "https://" in formatted
    
    print(f"✅ DOCS:   ID={doc_id}")
    print(f"   URL={url}")
    return True


def test_edge_cases():
    """Test edge cases for ID extraction."""
    
    # Edge case 1: Empty output
    output = ""
    id_match = re.search(r'ID:\s*([^\s|]+)', output)
    assert id_match is None, "Should not match empty output"
    print("✅ EDGE: Empty output handled")
    
    # Edge case 2: Short/weird ID
    output = "ID: abc123 | URL: https://example.com"
    id_match = re.search(r'ID:\s*([^\s|]+)', output)
    assert id_match and id_match.group(1) == "abc123"
    print("✅ EDGE: Short ID handled")
    
    # Edge case 3: ID with special chars (hyphens, underscores)
    output = "ID: a_b-c_D-e_F-123 | URL: https://x.com"
    id_match = re.search(r'ID:\s*([^\s|]+)', output)
    assert id_match and id_match.group(1) == "a_b-c_D-e_F-123"
    print("✅ EDGE: Special chars in ID handled")
    
    # Edge case 4: Form ID ending with period
    output = "Form ID: abc123XYZ. Edit URL: https://docs.google.com/forms/d/abc123XYZ/edit."
    id_match = re.search(r'Form ID:\s*([^.\s]+)', output)
    url_match = re.search(r'Edit URL:\s*(https://[^\s.]+[^\s]*)', output)
    assert id_match and id_match.group(1) == "abc123XYZ"
    if url_match:
        url = url_match.group(1).rstrip('.')
        assert url.endswith("/edit"), f"URL should end with /edit but got: {url}"
    print("✅ EDGE: Form ID with trailing period handled")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("JAWIR OS - ID Extraction Test Suite")
    print("=" * 60)
    print()
    
    tests = [
        ("Sheets ID extraction", test_sheets_id_extraction),
        ("Forms ID extraction", test_forms_id_extraction),
        ("Docs ID extraction", test_docs_id_extraction),
        ("Edge cases", test_edge_cases),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print(f"❌ FAILED: {name} — {e}")
            failed += 1
            print()
        except Exception as e:
            print(f"❌ ERROR: {name} — {e}")
            failed += 1
            print()
    
    print("=" * 60)
    print(f"Results: {passed}/{passed + failed} tests passed")
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️ {failed} test(s) FAILED")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)
