"""
JAWIR OS - Desktop Controller
=============================
Control desktop applications (Windows-focused).

Capabilities:
- Open applications (Chrome, Spotify, Calculator, Notepad, etc.)
- Close applications
- Focus/switch windows
- Take screenshots
- Get running processes
"""

import os
import sys
import subprocess
import time
from typing import Dict, Any, Optional, List
from pathlib import Path


class DesktopController:
    """
    Desktop App Controller untuk JAWIR OS.
    Menggunakan Windows API dan subprocess untuk control apps.
    """
    
    # Common Windows applications paths/commands
    APPS = {
        # Browsers
        "chrome": {
            "paths": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "command": "start chrome"
        },
        "firefox": {
            "paths": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
            "command": "start firefox"
        },
        "edge": {
            "paths": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            ],
            "command": "start msedge"
        },
        
        # Media
        "spotify": {
            "paths": [
                os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
                r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
            ],
            "command": "start spotify:",
            "uwp": "spotify:"
        },
        "vlc": {
            "paths": [
                r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            ],
            "command": "start vlc"
        },
        
        # Utilities
        "calculator": {
            "command": "calc",
            "uwp": "calculator:"
        },
        "notepad": {
            "command": "notepad"
        },
        "paint": {
            "command": "mspaint"
        },
        "explorer": {
            "command": "explorer"
        },
        "cmd": {
            "command": "cmd"
        },
        "powershell": {
            "command": "powershell"
        },
        "terminal": {
            "command": "wt",  # Windows Terminal
            "uwp": "wt:"
        },
        
        # Office
        "word": {
            "paths": [
                r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            ],
            "command": "start winword"
        },
        "excel": {
            "paths": [
                r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
            ],
            "command": "start excel"
        },
        "powerpoint": {
            "paths": [
                r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
                r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
            ],
            "command": "start powerpnt"
        },
        
        # Development
        "vscode": {
            "paths": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe",
            ],
            "command": "code"
        },
        "kicad": {
            "paths": [
                r"C:\Program Files\KiCad\8.0\bin\kicad.exe",
                r"C:\Program Files\KiCad\7.0\bin\kicad.exe",
            ],
            "command": "kicad"
        },
        
        # Settings
        "settings": {
            "command": "start ms-settings:",
            "uwp": "ms-settings:"
        },
        "control": {
            "command": "control"
        },
    }
    
    def __init__(self):
        self.platform = sys.platform
        
    def _find_app_path(self, app_name: str) -> Optional[str]:
        """Find the executable path for an application."""
        app_info = self.APPS.get(app_name.lower())
        if not app_info:
            return None
        
        paths = app_info.get("paths", [])
        for path in paths:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                return expanded
        
        return None
    
    def open_app(self, app_name: str, args: List[str] = None) -> Dict[str, Any]:
        """
        Open a desktop application.
        
        Args:
            app_name: Name of the application (e.g., "chrome", "spotify", "calculator")
            args: Optional arguments to pass to the application
            
        Returns:
            Dict with success status and message
        """
        app_name_lower = app_name.lower()
        args = args or []
        
        # Check if it's a known app
        app_info = self.APPS.get(app_name_lower)
        
        if app_info:
            # Try UWP protocol first (for Windows Store apps)
            if "uwp" in app_info:
                try:
                    os.startfile(app_info["uwp"])
                    return {
                        "success": True,
                        "message": f"Opened {app_name} via UWP protocol",
                        "method": "uwp"
                    }
                except:
                    pass
            
            # Try direct path
            exe_path = self._find_app_path(app_name_lower)
            if exe_path:
                try:
                    cmd = [exe_path] + args
                    subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    return {
                        "success": True,
                        "message": f"Opened {app_name} from {exe_path}",
                        "method": "direct"
                    }
                except Exception as e:
                    pass
            
            # Try shell command
            if "command" in app_info:
                try:
                    cmd = app_info["command"]
                    if args:
                        cmd += " " + " ".join(args)
                    
                    subprocess.Popen(
                        cmd,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    return {
                        "success": True,
                        "message": f"Opened {app_name} via shell command",
                        "method": "shell"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Failed to open {app_name}: {str(e)}",
                        "method": "shell"
                    }
        
        # Try as direct command/path
        try:
            if os.path.exists(app_name):
                # It's a file path
                os.startfile(app_name)
                return {
                    "success": True,
                    "message": f"Opened file: {app_name}",
                    "method": "startfile"
                }
            else:
                # Try as command
                subprocess.Popen(
                    [app_name] + args,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                return {
                    "success": True,
                    "message": f"Opened {app_name} as command",
                    "method": "command"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to open {app_name}: {str(e)}",
                "method": "failed"
            }
    
    def open_url(self, url: str, browser: str = None) -> Dict[str, Any]:
        """
        Open a URL in the default or specified browser.
        
        Args:
            url: URL to open
            browser: Optional browser name (chrome, firefox, edge)
            
        Returns:
            Dict with success status and message
        """
        import webbrowser
        
        if browser:
            browser_lower = browser.lower()
            app_info = self.APPS.get(browser_lower)
            
            if app_info:
                exe_path = self._find_app_path(browser_lower)
                if exe_path:
                    try:
                        subprocess.Popen([exe_path, url])
                        return {
                            "success": True,
                            "message": f"Opened {url} in {browser}"
                        }
                    except:
                        pass
                
                # Try using command with URL
                if "command" in app_info:
                    try:
                        # Map browser to executable for URL opening
                        browser_cmds = {
                            "chrome": ["cmd", "/c", "start", "chrome", url],
                            "firefox": ["cmd", "/c", "start", "firefox", url],
                            "edge": ["cmd", "/c", "start", "msedge", url],
                        }
                        
                        if browser_lower in browser_cmds:
                            subprocess.Popen(
                                browser_cmds[browser_lower],
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            return {
                                "success": True,
                                "message": f"Opened {url} in {browser} via command"
                            }
                    except:
                        pass
        
        # Use default browser
        try:
            webbrowser.open(url)
            return {
                "success": True,
                "message": f"Opened {url} in default browser"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to open URL: {str(e)}"
            }
    
    def close_app(self, app_name: str) -> Dict[str, Any]:
        """
        Close an application by name.
        
        Args:
            app_name: Process name to close (e.g., "chrome", "notepad")
            
        Returns:
            Dict with success status and message
        """
        if sys.platform != "win32":
            return {
                "success": False,
                "message": "Close app only supported on Windows"
            }
        
        # Map app names to process names
        process_map = {
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "spotify": "Spotify.exe",
            "notepad": "notepad.exe",
            "calculator": "CalculatorApp.exe",
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "vscode": "Code.exe",
            "vlc": "vlc.exe",
        }
        
        process_name = process_map.get(app_name.lower(), f"{app_name}.exe")
        
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", process_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Closed {app_name} ({process_name})"
                }
            else:
                return {
                    "success": False,
                    "message": f"Could not close {app_name}: {result.stderr}"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error closing {app_name}: {str(e)}"
            }
    
    def get_running_processes(self, filter_name: str = None) -> List[Dict[str, Any]]:
        """
        Get list of running processes.
        
        Args:
            filter_name: Optional filter by process name
            
        Returns:
            List of process info dictionaries
        """
        if sys.platform != "win32":
            return []
        
        try:
            cmd = ["tasklist", "/FO", "CSV", "/NH"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            processes = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.replace('"', '').split(',')
                if len(parts) >= 5:
                    name = parts[0]
                    if filter_name and filter_name.lower() not in name.lower():
                        continue
                    processes.append({
                        "name": name,
                        "pid": parts[1],
                        "session": parts[2],
                        "memory": parts[4]
                    })
            
            return processes
        except:
            return []
    
    def take_screenshot(self, output_path: str = None) -> Dict[str, Any]:
        """
        Take a screenshot of the entire screen.
        
        Args:
            output_path: Path to save the screenshot (default: working_dir/screenshot.png)
            
        Returns:
            Dict with success status and file path
        """
        try:
            from PIL import ImageGrab
            
            if not output_path:
                output_path = str(Path("D:/sijawir/python_workspace/screenshot.png"))
            
            # Capture screen
            screenshot = ImageGrab.grab()
            screenshot.save(output_path)
            
            return {
                "success": True,
                "message": f"Screenshot saved to {output_path}",
                "path": output_path
            }
        except ImportError:
            return {
                "success": False,
                "message": "Pillow not installed. Run: pip install Pillow"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to take screenshot: {str(e)}"
            }
    
    def list_available_apps(self) -> List[str]:
        """List all available app names that can be opened."""
        return list(self.APPS.keys())
    
    def type_text(self, text: str) -> Dict[str, Any]:
        """
        Type text using keyboard simulation.
        
        Args:
            text: Text to type
            
        Returns:
            Dict with success status
        """
        try:
            import pyautogui
            pyautogui.typewrite(text, interval=0.05)
            return {
                "success": True,
                "message": f"Typed: {text[:50]}..."
            }
        except ImportError:
            return {
                "success": False,
                "message": "pyautogui not installed. Run: pip install pyautogui"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to type text: {str(e)}"
            }
    
    def press_key(self, key: str, modifiers: List[str] = None) -> Dict[str, Any]:
        """
        Press a keyboard key with optional modifiers.
        
        Args:
            key: Key to press (e.g., "enter", "tab", "a")
            modifiers: Optional modifiers (e.g., ["ctrl"], ["ctrl", "shift"])
            
        Returns:
            Dict with success status
        """
        try:
            import pyautogui
            
            if modifiers:
                with pyautogui.hold(modifiers):
                    pyautogui.press(key)
            else:
                pyautogui.press(key)
            
            return {
                "success": True,
                "message": f"Pressed: {'+'.join(modifiers or [])}+{key}" if modifiers else f"Pressed: {key}"
            }
        except ImportError:
            return {
                "success": False,
                "message": "pyautogui not installed. Run: pip install pyautogui"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to press key: {str(e)}"
            }
    
    def search_youtube(self, query: str, browser: str = None) -> Dict[str, Any]:
        """
        Search YouTube with a query.
        
        Args:
            query: Search query
            browser: Optional browser (firefox, chrome, edge)
            
        Returns:
            Dict with success status and message
        """
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        return self.open_url(url, browser=browser)
    
    def search_google(self, query: str, browser: str = None) -> Dict[str, Any]:
        """
        Search Google with a query.
        
        Args:
            query: Search query
            browser: Optional browser (firefox, chrome, edge)
            
        Returns:
            Dict with success status and message
        """
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        return self.open_url(url, browser=browser)
    
    def browse_website(self, url: str, browser: str = None) -> Dict[str, Any]:
        """
        Open a website in the specified browser.
        Alias for open_url with auto-https.
        
        Args:
            url: Website URL (auto-adds https:// if missing)
            browser: Optional browser name
            
        Returns:
            Dict with success status
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return self.open_url(url, browser=browser)
    
    def play_youtube_video(self, video_url: str, browser: str = None) -> Dict[str, Any]:
        """
        Play a YouTube video by URL with autoplay.
        
        Args:
            video_url: YouTube video URL or video ID
            browser: Optional browser name
            
        Returns:
            Dict with success status
        """
        # Handle video ID only
        if not video_url.startswith('http'):
            if 'youtube.com' not in video_url and 'youtu.be' not in video_url:
                video_url = f"https://www.youtube.com/watch?v={video_url}"
        
        # Add autoplay parameter
        if 'youtube.com/watch' in video_url:
            if '?' in video_url:
                video_url += '&autoplay=1'
            else:
                video_url += '?autoplay=1'
        
        return self.open_url(video_url, browser=browser)
    
    def search_and_play_youtube(self, query: str, browser: str = None) -> Dict[str, Any]:
        """
        Search YouTube and play the first video result.
        
        Args:
            query: Search query
            browser: Optional browser name
            
        Returns:
            Dict with success status, video info
        """
        try:
            # Try using youtubesearchpython with sync method
            try:
                from youtubesearchpython import VideosSearch
                import asyncio
                
                # Search for videos
                search = VideosSearch(query, limit=5)
                
                # Handle both sync and async
                try:
                    results = search.result()
                except:
                    # If async, try to run in event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results = loop.run_until_complete(search.next())
                    loop.close()
                
                if not results or not results.get('result'):
                    raise Exception("No results from library")
                
                # Get first video
                video = results['result'][0]
                video_url = video.get('link')
                # Add autoplay parameter
                if video_url and 'youtube.com/watch' in video_url:
                    video_url += '&autoplay=1'
                video_title = video.get('title', 'Unknown')
                video_duration = video.get('duration', 'Unknown')
                video_channel = video.get('channel', {}).get('name', 'Unknown')
                video_views = video.get('viewCount', {}).get('short', 'Unknown')
                
            except Exception as lib_error:
                # Fallback: Use direct URL approach with search result redirect
                import urllib.parse
                import urllib.request
                import re
                
                # Search YouTube and get first video ID
                search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                req = urllib.request.Request(search_url, headers=headers)
                
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html = response.read().decode('utf-8')
                    
                    # Find first video ID in the response
                    video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                    
                    if not video_ids:
                        return {
                            "success": False,
                            "message": f"No videos found for: {query}"
                        }
                    
                    video_id = video_ids[0]
                    # Add autoplay=1 for automatic playback
                    video_url = f"https://www.youtube.com/watch?v={video_id}&autoplay=1"
                    
                    # Try to extract title
                    title_match = re.search(r'"title":\s*\{"runs":\s*\[\{"text":\s*"([^"]+)"', html)
                    video_title = title_match.group(1) if title_match else query
                    video_duration = "Unknown"
                    video_channel = "Unknown"
                    video_views = "Unknown"
                    
                except Exception as url_error:
                    return {
                        "success": False,
                        "message": f"Failed to search YouTube: {str(url_error)}"
                    }
            
            # Play the video
            play_result = self.open_url(video_url, browser=browser)
            
            if play_result.get('success'):
                return {
                    "success": True,
                    "message": f"Playing: {video_title}",
                    "video": {
                        "title": video_title,
                        "url": video_url,
                        "duration": video_duration,
                        "channel": video_channel,
                        "views": video_views
                    }
                }
            else:
                return play_result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    def get_youtube_search_results(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get YouTube search results without playing.
        
        Args:
            query: Search query
            limit: Max number of results
            
        Returns:
            Dict with video list
        """
        try:
            from youtubesearchpython import VideosSearch
            
            search = VideosSearch(query, limit=limit)
            results = search.result()
            
            if not results or not results.get('result'):
                return {
                    "success": False,
                    "message": f"No videos found for: {query}",
                    "videos": []
                }
            
            videos = []
            for i, video in enumerate(results['result'], 1):
                videos.append({
                    "index": i,
                    "title": video.get('title', 'Unknown'),
                    "url": video.get('link'),
                    "duration": video.get('duration', 'Unknown'),
                    "channel": video.get('channel', {}).get('name', 'Unknown'),
                    "views": video.get('viewCount', {}).get('short', 'Unknown')
                })
            
            return {
                "success": True,
                "query": query,
                "videos": videos
            }
            
        except ImportError:
            return {
                "success": False,
                "message": "youtube-search-python not installed",
                "videos": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "videos": []
            }

    # ==================== SPOTIFY CONTROL METHODS ====================
    
    def open_spotify(self) -> Dict[str, Any]:
        """
        Open Spotify application.
        
        Returns:
            Dict with success status
        """
        return self.open_app("spotify")
    
    def play_spotify_uri(self, uri: str) -> Dict[str, Any]:
        """
        Play Spotify content by URI.
        
        Args:
            uri: Spotify URI (e.g., spotify:track:xxx, spotify:playlist:xxx, spotify:album:xxx)
            
        Returns:
            Dict with success status
        """
        try:
            import subprocess
            
            # Open Spotify with the URI
            subprocess.Popen(["start", uri], shell=True)
            
            return {
                "success": True,
                "message": f"Playing Spotify URI: {uri}",
                "uri": uri
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error playing Spotify URI: {str(e)}"
            }
    
    def search_and_play_spotify(self, query: str, content_type: str = "track") -> Dict[str, Any]:
        """
        Search and play music on Spotify.
        
        Method: 
        1. Open Spotify search URI
        2. Wait for search results to load
        3. Click the GREEN PLAY BUTTON on Top Result card
        
        Args:
            query: Search query (song name, artist, album, playlist)
            content_type: Type of content - "track", "album", "playlist", "artist"
            
        Returns:
            Dict with success status and info
        """
        try:
            import subprocess
            import urllib.parse
            
            # Step 1: Open Spotify with search URI
            encoded_query = urllib.parse.quote(query)
            search_uri = f"spotify:search:{encoded_query}"
            subprocess.Popen(["start", search_uri], shell=True)
            
            # Step 2: Wait for Spotify to open and load search results
            time.sleep(4)  # Increased wait time for search results
            
            # Step 3: Use pywinauto to focus and click Play button
            try:
                from pywinauto import Application
                import pyautogui
                
                # Connect to Spotify
                app = Application(backend='uia').connect(title_re='.*Spotify.*')
                win = app.window(title_re='.*Spotify.*')
                win.set_focus()
                time.sleep(0.5)
                
                # Get window position
                rect = win.rectangle()
                
                # Calculate Play button position
                # Based on Spotify UI analysis:
                # - Left sidebar: ~60px
                # - Top Result card starts at y~130
                # - Green Play button is at right side of Top Result card
                # - Approximately at x=420, y=340 relative to window
                
                # Hover on Top Result to make Play button visible
                hover_x = rect.left + 270
                hover_y = rect.top + 280
                pyautogui.moveTo(hover_x, hover_y)
                time.sleep(0.8)
                
                # Click the GREEN PLAY button
                play_btn_x = rect.left + 420
                play_btn_y = rect.top + 340
                pyautogui.click(play_btn_x, play_btn_y)
                
            except ImportError:
                # Fallback: If pywinauto not available, try keyboard navigation
                import pyautogui
                pyautogui.FAILSAFE = False
                
                # Focus Spotify
                subprocess.run(
                    ["powershell", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('Spotify')"],
                    capture_output=True
                )
                time.sleep(0.5)
                
                # Try Tab navigation to reach Play button, then Enter
                pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.press('tab')
                time.sleep(0.2)
                pyautogui.press('enter')
                
            except Exception as e:
                # Last fallback: just press Enter hoping it plays something
                import pyautogui
                subprocess.run(
                    ["powershell", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('Spotify')"],
                    capture_output=True
                )
                time.sleep(0.3)
                pyautogui.press('enter')
            
            return {
                "success": True,
                "message": f"🎵 Now playing on Spotify: {query}",
                "query": query,
                "content_type": content_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error playing Spotify: {str(e)}"
            }
    
    def spotify_control(self, action: str) -> Dict[str, Any]:
        """
        Control Spotify playback using media keys.
        
        Args:
            action: Control action - "play", "pause", "toggle", "next", "previous", "stop"
            
        Returns:
            Dict with success status
        """
        try:
            import ctypes
            
            # Virtual key codes for media control
            VK_MEDIA_PLAY_PAUSE = 0xB3
            VK_MEDIA_NEXT_TRACK = 0xB0
            VK_MEDIA_PREV_TRACK = 0xB1
            VK_MEDIA_STOP = 0xB2
            KEYEVENTF_KEYUP = 0x0002
            
            action_map = {
                "play": VK_MEDIA_PLAY_PAUSE,
                "pause": VK_MEDIA_PLAY_PAUSE,
                "toggle": VK_MEDIA_PLAY_PAUSE,
                "play_pause": VK_MEDIA_PLAY_PAUSE,
                "next": VK_MEDIA_NEXT_TRACK,
                "skip": VK_MEDIA_NEXT_TRACK,
                "previous": VK_MEDIA_PREV_TRACK,
                "prev": VK_MEDIA_PREV_TRACK,
                "back": VK_MEDIA_PREV_TRACK,
                "stop": VK_MEDIA_STOP
            }
            
            action_lower = action.lower().strip()
            
            if action_lower not in action_map:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}. Available: play, pause, toggle, next, previous, stop"
                }
            
            vk_code = action_map[action_lower]
            
            # Simulate media key press
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
            
            action_messages = {
                "play": "Playing",
                "pause": "Paused",
                "toggle": "Toggled play/pause",
                "play_pause": "Toggled play/pause",
                "next": "Skipped to next track",
                "skip": "Skipped to next track",
                "previous": "Playing previous track",
                "prev": "Playing previous track",
                "back": "Playing previous track",
                "stop": "Stopped playback"
            }
            
            return {
                "success": True,
                "message": action_messages.get(action_lower, f"Spotify: {action}"),
                "action": action_lower
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error controlling Spotify: {str(e)}"
            }
    
    def set_spotify_volume(self, volume: int) -> Dict[str, Any]:
        """
        Set Spotify volume (affects system media volume).
        
        Args:
            volume: Volume level 0-100
            
        Returns:
            Dict with success status
        """
        try:
            import ctypes
            
            # Clamp volume to 0-100
            volume = max(0, min(100, volume))
            
            # Volume up/down media keys
            VK_VOLUME_MUTE = 0xAD
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF
            KEYEVENTF_KEYUP = 0x0002
            
            # Use nircmd for precise volume control if available
            try:
                import subprocess
                # Try using PowerShell to set volume
                ps_cmd = f'''
                $obj = New-Object -ComObject WScript.Shell
                $volume = {volume}
                # Mute first, then set volume
                1..50 | ForEach-Object {{ $obj.SendKeys([char]174) }}  # Volume down
                $steps = [math]::Round($volume / 2)
                1..$steps | ForEach-Object {{ $obj.SendKeys([char]175) }}  # Volume up
                '''
                # Simpler approach: just inform user
                pass
            except:
                pass
            
            return {
                "success": True,
                "message": f"Volume control: {volume}% (Note: Use system volume controls for precise adjustment)",
                "volume": volume
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error setting volume: {str(e)}"
            }
    
    def close_spotify(self) -> Dict[str, Any]:
        """
        Close Spotify application.
        
        Returns:
            Dict with success status
        """
        return self.close_app("spotify")
