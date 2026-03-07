#!/usr/bin/env python
# JAWIR OS Computer Use - Setup Script
"""
Setup Computer Use Module
=========================
Script untuk install dependencies dan setup Playwright browser.

Usage:
    python setup_computer_use.py
"""

import subprocess
import sys
import os


def run_command(command: str, description: str) -> bool:
    """Run a shell command."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"$ {command}\n")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        return True
    else:
        print(f"❌ {description} - FAILED")
        return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     JAWIR OS - Computer Use Module Setup                      ║
║     Browser Automation dengan Gemini Vision                   ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    requirements_file = os.path.join(script_dir, "requirements_computer_use.txt")
    
    steps = [
        # Step 1: Install Python packages
        (
            f'pip install -r "{requirements_file}"',
            "Installing Python dependencies"
        ),
        # Step 2: Install Playwright system dependencies
        (
            "playwright install-deps chromium",
            "Installing Playwright system dependencies"
        ),
        # Step 3: Install Chromium browser
        (
            "playwright install chromium",
            "Installing Chromium browser for Playwright"
        ),
    ]
    
    success_count = 0
    for command, description in steps:
        if run_command(command, description):
            success_count += 1
    
    print(f"""
{'='*60}
                    SETUP COMPLETE
{'='*60}

Results: {success_count}/{len(steps)} steps successful

Next Steps:
1. Set GEMINI_API_KEY environment variable:
   
   Windows (PowerShell):
   $env:GEMINI_API_KEY="your-api-key-here"
   
   Linux/Mac:
   export GEMINI_API_KEY="your-api-key-here"

2. Test the module:
   python -c "from computer_use import PlaywrightComputer; print('OK')"

3. Use in JAWIR OS:
   /browse search python tutorials on youtube
   /webfill https://example.com/form name=John email=john@email.com
   /websearch youtube arduino tutorial

{'='*60}
    """)
    
    return success_count == len(steps)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
