# JAWIR OS - Python Interpreter Integration

## Overview
Integrasi MCP Python Interpreter ke dalam JAWIR OS untuk memberikan kemampuan seperti **Open Interpreter**.

## Features

### 🐍 Python Execution
- Execute Python code secara inline (cepat, dengan state persistence)
- Execute via subprocess (isolated, tanpa state)
- Session management untuk REPL-style interaction
- Package installation via pip

### 🖥️ Desktop Control
- Buka/tutup aplikasi desktop
- Buka URL di browser
- Take screenshot
- Keyboard automation (type text, press keys)
- List running processes

### 📄 File Generation
- **Word** (.docx) - python-docx
- **PDF** - reportlab  
- **CSV** - built-in csv module
- **Excel** (.xlsx) - openpyxl
- **JSON** - built-in json module
- **TXT** - built-in
- **Markdown** - built-in
- **Charts/Images** - matplotlib + Pillow

## File Structure
```
backend/tools/python_interpreter/
├── __init__.py          # Package exports
├── executor.py          # Python code execution
├── desktop_control.py   # Desktop app control  
├── file_generator.py    # File generation
├── interpreter.py       # Main JawirInterpreter class
└── test_interpreter.py  # Test suite
```

## CLI Commands (in kicad_cli.py)

### Python Execution
```bash
/python <code>         # Execute Python code
/py <code>             # Short alias
/pip install <package> # Install package
```

### Desktop Control
```bash
/open <app>            # Open application
/close <app>           # Close application  
/url <url>             # Open URL in browser
/screenshot            # Take screenshot
/apps                  # List running apps
```

### File Generation
```bash
/word <content>        # Create Word document
/pdf <content>         # Create PDF document
/txt <content>         # Create text file
/md <content>          # Create Markdown file
/json <data>           # Create JSON file
```

## Available Applications

| App | Command |
|-----|---------|
| Google Chrome | `/open chrome` |
| Mozilla Firefox | `/open firefox` |
| Microsoft Edge | `/open edge` |
| Spotify | `/open spotify` |
| VLC Media Player | `/open vlc` |
| Calculator | `/open calculator` |
| Notepad | `/open notepad` |
| VS Code | `/open vscode` |
| Microsoft Word | `/open word` |
| Microsoft Excel | `/open excel` |
| PowerPoint | `/open powerpoint` |
| KiCad | `/open kicad` |
| File Explorer | `/open explorer` |
| Command Prompt | `/open cmd` |
| PowerShell | `/open powershell` |
| Paint | `/open paint` |
| Photos | `/open photos` |
| Discord | `/open discord` |
| Slack | `/open slack` |

## Usage Examples

### Execute Python Code
```
JAWIR> /python print("Hello from JAWIR!")
🐍 PYTHON EXECUTION
📝 Code: print("Hello from JAWIR!")
✅ Execution successful
Output: Hello from JAWIR!
```

### Open Applications
```
JAWIR> /open chrome
🖥️ DESKTOP CONTROL
🚀 Opening: chrome
✅ Opened: chrome
```

### Generate Files
```
JAWIR> /word Laporan Project JAWIR OS untuk desain ESP32
📄 FILE GENERATION (WORD)
📝 Content: Laporan Project JAWIR OS...
✅ File created: D:\sijawir\python_workspace\output\jawir_word_abc123.docx
```

## Dependencies

Installed packages:
- `python-docx` - Word document generation
- `reportlab` - PDF generation
- `openpyxl` - Excel file generation
- `matplotlib` - Chart generation
- `Pillow` - Image processing
- `pyautogui` - Keyboard/mouse automation

## Output Directory
All generated files are saved to:
```
D:\sijawir\python_workspace\output\
```

## Integration with JAWIR OS

The Python Interpreter is integrated into JAWIR OS CLI (`kicad_cli.py`) and can be used alongside:
- 🔧 KiCad Tool (Schematic Generation)
- 🔍 Web Search Tool
- 🔬 Deep Research Tool
- 📧 Google Workspace Tools

## API Usage (Programmatic)

```python
from python_interpreter import JawirInterpreter, get_interpreter

# Get singleton instance
interp = get_interpreter()

# Execute Python code
result = interp.run_code("2 + 2")
print(result["result"])  # 4

# Open application
result = interp.open_app("chrome")
print(result["success"])  # True

# Generate file
result = interp.create_word("Hello World", "my_doc")
print(result["path"])  # D:\sijawir\...\my_doc.docx

# Take screenshot
result = interp.screenshot()
print(result["path"])  # Screenshot path
```

## Test Suite

Run tests:
```bash
cd D:\jawirv2\jawirv2\backend\tools\python_interpreter
python test_interpreter.py
```

Expected output:
```
==================================================
JAWIR Python Interpreter - Test Suite
==================================================

=== Test Python Execution ===
  2 + 2 = 4
  Print test: 
  Session persistence: x=100, x*2=200
  ✅ Python execution tests passed!

=== Test File Generation ===
  TXT: TXT created: D:\sijawir\python_workspace\output\test_txt.txt
  JSON: JSON created: D:\sijawir\python_workspace\output\test_json.json
  Markdown: Markdown created: D:\sijawir\python_workspace\output\test_md.md
  Word: Word document created: D:\sijawir\python_workspace\output\test_word.docx
  PDF: PDF created: D:\sijawir\python_workspace\output\test_pdf.pdf
  ✅ File generation tests passed!

=== Test Desktop Control ===
  Running processes: 400+
  Available apps: chrome, firefox, edge, spotify, vlc...
  ✅ Desktop control tests passed!

=== Test Interpreter Status ===
  Workspace: D:\sijawir\python_workspace
  Output dir: D:\sijawir\python_workspace\output
  Current session: default
  Available apps: 19
  ✅ Status tests passed!

==================================================
✅ ALL TESTS PASSED!
==================================================
```

---
**JAWIR OS © 2026 - AI Assistant Jawa Terkuat dari Ngawi 🇮🇩**
