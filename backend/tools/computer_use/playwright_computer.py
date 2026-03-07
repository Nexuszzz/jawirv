# Copyright 2025-2026 JAWIR OS
# Playwright Computer - Browser automation via Playwright
"""
Playwright Computer
===================
Browser automation menggunakan Playwright untuk control Chrome.

Features:
- Headless atau visible mode
- Screenshot capture
- Mouse/keyboard simulation
- Full browser control
"""

import os
import time
from typing import Literal, Optional

try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright not installed. Run: pip install playwright && playwright install chrome")

from .computer import Computer, EnvState


# Key mapping untuk Playwright
KEY_MAP = {
    "control": "Control",
    "ctrl": "Control",
    "alt": "Alt",
    "shift": "Shift",
    "meta": "Meta",
    "command": "Meta",
    "win": "Meta",
    "enter": "Enter",
    "return": "Enter",
    "tab": "Tab",
    "escape": "Escape",
    "esc": "Escape",
    "backspace": "Backspace",
    "delete": "Delete",
    "space": " ",
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
}


class PlaywrightComputer(Computer):
    """Browser automation menggunakan Playwright."""

    def __init__(
        self,
        screen_size: tuple[int, int] = (1440, 900),
        initial_url: str = "https://www.google.com",
        search_engine_url: str = "https://www.google.com",
        headless: bool = False,
        highlight_mouse: bool = False,
        download_folder: str = None,
    ):
        """
        Initialize PlaywrightComputer.
        
        Args:
            screen_size: Browser viewport size (width, height)
            initial_url: Starting URL
            search_engine_url: URL for search() function
            headless: Run browser in headless mode
            highlight_mouse: Show visual cursor highlight (for debugging)
            download_folder: Folder to save downloaded files (default: ./downloads)
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chrome")
        
        self._screen_size = screen_size
        self._initial_url = initial_url
        self._search_engine_url = search_engine_url
        self._headless = headless
        self._highlight_mouse = highlight_mouse
        
        # Download folder setup
        self._download_folder = download_folder or os.path.join(os.getcwd(), "downloads")
        os.makedirs(self._download_folder, exist_ok=True)
        self._last_download = None  # Track last downloaded file
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page: Optional[Page] = None

    def _handle_new_page(self, new_page: Page):
        """Handle new tab - redirect to main page (single tab support)."""
        try:
            new_url = new_page.url
            new_page.close()
            if self._page:
                self._page.goto(new_url)
        except Exception:
            pass

    def __enter__(self):
        """Start browser session."""
        print("🌐 Starting browser session...")
        
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-extensions",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--no-first-run",
            ],
        )
        
        self._context = self._browser.new_context(
            viewport={
                "width": self._screen_size[0],
                "height": self._screen_size[1],
            },
            accept_downloads=True,  # Enable download support
        )
        
        self._page = self._context.new_page()
        self._page.goto(self._initial_url)
        self._context.on("page", self._handle_new_page)
        
        print(f"✅ Browser started at {self._initial_url}")
        print(f"📁 Download folder: {self._download_folder}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close browser session."""
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
            print("🔴 Browser session closed")
        except Exception:
            pass

    def _highlight_cursor(self, x: int, y: int):
        """Show visual cursor highlight for debugging."""
        if self._highlight_mouse and self._page:
            try:
                self._page.evaluate(f"""
                    (function() {{
                        let existing = document.getElementById('jawir-cursor-highlight');
                        if (existing) existing.remove();
                        
                        const div = document.createElement('div');
                        div.id = 'jawir-cursor-highlight';
                        div.style.cssText = `
                            position: fixed;
                            left: {x - 10}px;
                            top: {y - 10}px;
                            width: 20px;
                            height: 20px;
                            border-radius: 50%;
                            background: rgba(255, 0, 0, 0.5);
                            border: 2px solid red;
                            pointer-events: none;
                            z-index: 999999;
                            transition: all 0.1s ease;
                        `;
                        document.body.appendChild(div);
                        
                        setTimeout(() => div.remove(), 2000);
                    }})();
                """)
            except Exception:
                pass

    def screen_size(self) -> tuple[int, int]:
        """Get screen size."""
        if self._page:
            viewport = self._page.viewport_size
            if viewport:
                return viewport["width"], viewport["height"]
        return self._screen_size

    def open_web_browser(self) -> EnvState:
        """Open browser (already open, return current state)."""
        return self.current_state()

    def click_at(self, x: int, y: int) -> EnvState:
        """Click at coordinates."""
        self._highlight_cursor(x, y)
        self._page.mouse.click(x, y)
        self._page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(0.3)
        return self.current_state()

    def hover_at(self, x: int, y: int) -> EnvState:
        """Hover at coordinates."""
        self._highlight_cursor(x, y)
        self._page.mouse.move(x, y)
        self._page.wait_for_load_state("domcontentloaded", timeout=5000)
        time.sleep(0.2)
        return self.current_state()

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        """Type text at coordinates."""
        self._highlight_cursor(x, y)
        self._page.mouse.click(x, y)
        time.sleep(0.1)
        
        if clear_before_typing:
            self._page.keyboard.press("Control+A")
            self._page.keyboard.press("Backspace")
            time.sleep(0.1)
        
        self._page.keyboard.type(text, delay=20)
        
        if press_enter:
            time.sleep(0.1)
            self._page.keyboard.press("Enter")
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
        
        time.sleep(0.3)
        return self.current_state()

    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        """Scroll entire page."""
        scroll_map = {
            "up": (0, -500),
            "down": (0, 500),
            "left": (-500, 0),
            "right": (500, 0),
        }
        dx, dy = scroll_map.get(direction, (0, 0))
        self._page.mouse.wheel(dx, dy)
        time.sleep(0.3)
        return self.current_state()

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int = 800,
    ) -> EnvState:
        """Scroll at specific position."""
        self._highlight_cursor(x, y)
        self._page.mouse.move(x, y)
        
        dx, dy = 0, 0
        if direction == "up":
            dy = -magnitude
        elif direction == "down":
            dy = magnitude
        elif direction == "left":
            dx = -magnitude
        elif direction == "right":
            dx = magnitude
        
        self._page.mouse.wheel(dx, dy)
        time.sleep(0.3)
        return self.current_state()

    def wait_seconds(self, seconds: int = 5) -> EnvState:
        """Wait for specified seconds."""
        time.sleep(seconds)
        return self.current_state()

    def go_back(self) -> EnvState:
        """Navigate back."""
        self._page.go_back()
        self._page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(0.3)
        return self.current_state()

    def go_forward(self) -> EnvState:
        """Navigate forward."""
        self._page.go_forward()
        self._page.wait_for_load_state("domcontentloaded", timeout=10000)
        time.sleep(0.3)
        return self.current_state()

    def search(self) -> EnvState:
        """Go to search engine."""
        return self.navigate(self._search_engine_url)

    def navigate(self, url: str) -> EnvState:
        """Navigate to URL."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        self._page.goto(url)
        self._page.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(0.5)
        return self.current_state()

    def key_combination(self, keys: list[str]) -> EnvState:
        """Press key combination."""
        # Convert key names
        mapped_keys = []
        for key in keys:
            mapped = KEY_MAP.get(key.lower(), key)
            mapped_keys.append(mapped)
        
        key_string = "+".join(mapped_keys)
        self._page.keyboard.press(key_string)
        time.sleep(0.2)
        return self.current_state()

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        """Drag and drop."""
        self._highlight_cursor(x, y)
        self._page.mouse.move(x, y)
        self._page.mouse.down()
        time.sleep(0.1)
        
        self._highlight_cursor(destination_x, destination_y)
        self._page.mouse.move(destination_x, destination_y)
        time.sleep(0.1)
        self._page.mouse.up()
        
        time.sleep(0.3)
        return self.current_state()

    def current_state(self) -> EnvState:
        """Get current screenshot and URL."""
        self._page.wait_for_load_state("domcontentloaded", timeout=5000)
        time.sleep(0.2)
        
        screenshot = self._page.screenshot(type="png", full_page=False)
        url = self._page.url
        
        return EnvState(screenshot=screenshot, url=url)
    
    # ==========================================
    # JAWIR ENHANCED METHODS
    # ==========================================
    
    def type_and_submit(self, selector: str, text: str) -> EnvState:
        """Type text into element by selector and submit."""
        try:
            self._page.fill(selector, text)
            self._page.press(selector, "Enter")
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ type_and_submit error: {e}")
        return self.current_state()
    
    def click_element(self, selector: str) -> EnvState:
        """Click element by selector."""
        try:
            self._page.click(selector, timeout=5000)
            self._page.wait_for_load_state("domcontentloaded", timeout=10000)
            time.sleep(0.3)
        except Exception as e:
            print(f"⚠️ click_element error: {e}")
        return self.current_state()
    
    def get_text(self, selector: str) -> str:
        """Get text content from element."""
        try:
            return self._page.text_content(selector, timeout=5000) or ""
        except Exception:
            return ""
    
    def screenshot_to_file(self, filepath: str) -> str:
        """Save screenshot to file."""
        try:
            self._page.screenshot(path=filepath, full_page=False)
            return filepath
        except Exception as e:
            return f"Error: {e}"
    
    def download_file(self, url: str = None, filename: str = None, timeout: int = 60000) -> dict:
        """
        Download a file from URL or wait for current download to complete.
        
        Args:
            url: Optional URL to navigate to for download (e.g., PDF link)
            filename: Optional custom filename for the download
            timeout: Download timeout in milliseconds (default: 60s)
        
        Returns:
            dict with download info: {success, filepath, filename, error}
        """
        try:
            if url:
                # Navigate to URL and wait for download
                with self._page.expect_download(timeout=timeout) as download_info:
                    self._page.goto(url)
                
                download = download_info.value
            else:
                # Wait for any download to start
                with self._page.expect_download(timeout=timeout) as download_info:
                    pass
                download = download_info.value
            
            # Determine filename
            suggested_name = download.suggested_filename
            final_filename = filename or suggested_name
            
            # Save to download folder
            save_path = os.path.join(self._download_folder, final_filename)
            download.save_as(save_path)
            
            self._last_download = save_path
            print(f"✅ Downloaded: {final_filename}")
            print(f"📁 Saved to: {save_path}")
            
            return {
                "success": True,
                "filepath": save_path,
                "filename": final_filename,
                "error": None
            }
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return {
                "success": False,
                "filepath": None,
                "filename": None,
                "error": str(e)
            }
    
    def click_and_download(self, x: int, y: int, filename: str = None, timeout: int = 60000) -> dict:
        """
        Click at position and wait for download to complete.
        
        Args:
            x, y: Click position
            filename: Optional custom filename
            timeout: Download timeout in milliseconds
        
        Returns:
            dict with download info
        """
        try:
            with self._page.expect_download(timeout=timeout) as download_info:
                self._highlight_cursor(x, y)
                self._page.mouse.click(x, y)
            
            download = download_info.value
            suggested_name = download.suggested_filename
            final_filename = filename or suggested_name
            
            save_path = os.path.join(self._download_folder, final_filename)
            download.save_as(save_path)
            
            self._last_download = save_path
            print(f"✅ Downloaded: {final_filename}")
            print(f"📁 Saved to: {save_path}")
            
            return {
                "success": True,
                "filepath": save_path,
                "filename": final_filename,
                "error": None
            }
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return {
                "success": False,
                "filepath": None,
                "filename": None,
                "error": str(e)
            }
    
    def get_last_download(self) -> str:
        """Get path of last downloaded file."""
        return self._last_download
    
    def download_pdf_from_page(self, timeout: int = 30000) -> dict:
        """
        Download PDF from current page using browser's print-to-PDF.
        Useful when the page IS a PDF or you want to save page as PDF.
        
        Args:
            timeout: Timeout in ms
        
        Returns:
            dict with download info
        """
        try:
            # Generate filename from page title
            title = self._page.title() or "document"
            # Clean filename
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_title = clean_title[:100]  # Limit length
            filename = f"{clean_title}.pdf"
            
            save_path = os.path.join(self._download_folder, filename)
            
            # Use Playwright's PDF generation
            self._page.pdf(path=save_path)
            
            self._last_download = save_path
            print(f"✅ PDF saved: {filename}")
            print(f"📁 Saved to: {save_path}")
            
            return {
                "success": True,
                "filepath": save_path,
                "filename": filename,
                "error": None
            }
        except Exception as e:
            # If PDF fails (non-headless), try screenshot method
            print(f"⚠️ PDF generation not available in headed mode, trying alternative...")
            return self._download_pdf_alternative(timeout)
    
    def _download_pdf_alternative(self, timeout: int = 30000) -> dict:
        """
        Alternative PDF download - wait for actual file download.
        Works when clicking a PDF link that triggers download.
        """
        try:
            # Check if current URL is a PDF
            current_url = self._page.url
            if current_url.endswith('.pdf') or '/pdf/' in current_url:
                # It's a PDF URL, download directly
                import urllib.request
                
                title = self._page.title() or "document"
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                clean_title = clean_title[:100] if clean_title else "document"
                filename = f"{clean_title}.pdf"
                save_path = os.path.join(self._download_folder, filename)
                
                # Download via urllib
                urllib.request.urlretrieve(current_url, save_path)
                
                self._last_download = save_path
                print(f"✅ PDF downloaded: {filename}")
                print(f"📁 Saved to: {save_path}")
                
                return {
                    "success": True,
                    "filepath": save_path,
                    "filename": filename,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "filepath": None,
                    "filename": None,
                    "error": "Current page is not a PDF"
                }
        except Exception as e:
            return {
                "success": False,
                "filepath": None,
                "filename": None,
                "error": str(e)
            }
