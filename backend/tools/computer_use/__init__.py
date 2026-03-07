# Copyright 2025-2026 JAWIR OS
# Computer Use Module - Browser Automation dengan Gemini Vision
"""
JAWIR OS Computer Use Module
============================
Browser automation menggunakan Google Gemini Computer Use Preview.

Fitur:
- Vision-based browser automation (model "melihat" screenshot)
- Natural language browser control
- Multi-step task execution
- Auto-retry & error handling

Usage:
    from tools.computer_use import BrowserAgent, PlaywrightComputer
    
    with PlaywrightComputer() as browser:
        agent = BrowserAgent(browser, "Search Python tutorials on YouTube")
        agent.run()
"""

from .computer import Computer, EnvState
from .playwright_computer import PlaywrightComputer
from .browser_agent import BrowserAgent, run_browser_task, browse_and_search, fill_web_form

__all__ = [
    "Computer",
    "EnvState",
    "PlaywrightComputer",
    "BrowserAgent",
    "run_browser_task",
    "browse_and_search",
    "fill_web_form",
]
