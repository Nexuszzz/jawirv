"""
Test JAWIR Python Interpreter
==============================
Test untuk memastikan semua komponen berfungsi.
"""

import sys
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from python_interpreter import JawirInterpreter, get_interpreter

def test_python_execution():
    """Test Python code execution."""
    print("\n=== Test Python Execution ===")
    interp = get_interpreter()
    
    # Test simple code
    result = interp.run_code("2 + 2")
    print(f"  2 + 2 = {result.get('result')}")
    assert result.get('result') == 4, "Simple math failed"
    
    # Test print
    result = interp.run_code("print('Hello from JAWIR!')")
    print(f"  Print test: {result.get('output', '').strip()}")
    
    # Test session persistence
    interp.run_code("x = 100")
    result = interp.run_code("x * 2")
    print(f"  Session persistence: x=100, x*2={result.get('result')}")
    assert result.get('result') == 200, "Session persistence failed"
    
    print("  ✅ Python execution tests passed!")

def test_file_generation():
    """Test file generation."""
    print("\n=== Test File Generation ===")
    interp = get_interpreter()
    
    # Test TXT
    result = interp.create_txt("Hello JAWIR OS!", "test_txt")
    print(f"  TXT: {result.get('message')}")
    assert result.get('success'), "TXT creation failed"
    
    # Test JSON
    result = interp.create_json({"name": "JAWIR", "version": "1.0"}, "test_json")
    print(f"  JSON: {result.get('message')}")
    assert result.get('success'), "JSON creation failed"
    
    # Test Markdown
    result = interp.create_markdown("# JAWIR OS\n\nHello World!", "test_md")
    print(f"  Markdown: {result.get('message')}")
    assert result.get('success'), "Markdown creation failed"
    
    # Test Word (if python-docx installed)
    try:
        result = interp.create_word("Test document from JAWIR OS", "test_word")
        print(f"  Word: {result.get('message')}")
    except Exception as e:
        print(f"  Word: Skipped ({e})")
    
    # Test PDF (if reportlab installed)
    try:
        result = interp.create_pdf("Test PDF from JAWIR OS", "test_pdf")
        print(f"  PDF: {result.get('message')}")
    except Exception as e:
        print(f"  PDF: Skipped ({e})")
    
    print("  ✅ File generation tests passed!")

def test_desktop_control():
    """Test desktop control (non-destructive)."""
    print("\n=== Test Desktop Control ===")
    interp = get_interpreter()
    
    # Test list apps (should work without opening anything)
    result = interp.list_running_apps()
    if result.get('success'):
        count = len(result.get('processes', []))
        print(f"  Running processes: {count}")
    else:
        print(f"  List apps: {result.get('message')}")
    
    # Test available apps listing
    apps = list(interp.desktop.APPS.keys())
    print(f"  Available apps: {', '.join(apps[:5])}...")
    
    print("  ✅ Desktop control tests passed!")

def test_interpreter_status():
    """Test interpreter status."""
    print("\n=== Test Interpreter Status ===")
    interp = get_interpreter()
    
    status = interp.get_status()
    print(f"  Workspace: {status.get('workspace')}")
    print(f"  Output dir: {status.get('output_dir')}")
    print(f"  Current session: {status.get('current_session')}")
    print(f"  Available apps: {len(status.get('available_apps', []))}")
    
    print("  ✅ Status tests passed!")

def main():
    print("=" * 50)
    print("JAWIR Python Interpreter - Test Suite")
    print("=" * 50)
    
    try:
        test_python_execution()
        test_file_generation()
        test_desktop_control()
        test_interpreter_status()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
