"""
JAWIR OS - Open Interpreter Integration
========================================
Integrasi lengkap Python Interpreter untuk JAWIR OS.
Fitur mirip Open Interpreter dengan kemampuan:
- Eksekusi kode Python
- Kontrol desktop apps
- Generasi file (Word, PDF, CSV, Excel, JSON, TXT, Markdown, Images)
"""

import os
import sys
import asyncio
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

# Import komponen
from .executor import PythonExecutor, ReplSession
from .desktop_control import DesktopController
from .file_generator import FileGenerator


class JawirInterpreter:
    """
    JAWIR Interpreter - Open Interpreter untuk JAWIR OS.
    
    Kemampuan:
    1. Execute Python code (inline & subprocess)
    2. Control desktop applications
    3. Generate various file formats
    4. Manage REPL sessions
    """
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir or "D:/sijawir/python_workspace").absolute()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.executor = PythonExecutor(working_dir=str(self.workspace_dir))
        self.desktop = DesktopController()
        self.file_gen = FileGenerator(output_dir=str(self.workspace_dir / "output"))
        
        # Default session
        self.current_session = "default"
        
    # ==================== PYTHON EXECUTION ====================
    
    def run_code(
        self,
        code: str,
        session: str = None,
        use_subprocess: bool = False,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code.
        
        Args:
            code: Python code to execute
            session: Session name for persistent state
            use_subprocess: Use subprocess for isolation
            timeout: Timeout in seconds
            
        Returns:
            Dict with output, errors, and result
        """
        session = session or self.current_session
        
        if use_subprocess:
            return self.executor.execute_subprocess(code, timeout=timeout)
        else:
            return self.executor.execute_inline(code, session_id=session)
    
    def run_file(self, filepath: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a Python file.
        
        Args:
            filepath: Path to Python file
            timeout: Timeout in seconds
            
        Returns:
            Dict with output and errors
        """
        path = Path(filepath)
        if not path.exists():
            return {"success": False, "message": f"File not found: {filepath}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        return self.executor.execute_subprocess(code, timeout=timeout)
    
    def install_package(self, package: str) -> Dict[str, Any]:
        """Install a Python package."""
        return self.executor.install_package(package)
    
    def install_packages(self, packages: List[str]) -> Dict[str, Any]:
        """Install multiple Python packages."""
        results = []
        for pkg in packages:
            result = self.executor.install_package(pkg)
            results.append({pkg: result})
        
        success_count = sum(1 for r in results for k, v in r.items() if v.get("success"))
        return {
            "success": success_count == len(packages),
            "message": f"Installed {success_count}/{len(packages)} packages",
            "details": results
        }
    
    # ==================== DESKTOP CONTROL ====================
    
    def open_app(self, app_name: str) -> Dict[str, Any]:
        """Open a desktop application."""
        return self.desktop.open_app(app_name)
    
    def open_url(self, url: str, browser: str = None) -> Dict[str, Any]:
        """Open a URL in browser."""
        return self.desktop.open_url(url, browser)
    
    def close_app(self, app_name: str) -> Dict[str, Any]:
        """Close a desktop application."""
        return self.desktop.close_app(app_name)
    
    def list_running_apps(self) -> Dict[str, Any]:
        """List running applications."""
        processes = self.desktop.get_running_processes()
        return {
            "success": True,
            "processes": processes,
            "count": len(processes)
        }
    
    def type_text(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        """Type text using keyboard."""
        return self.desktop.type_text(text, interval)
    
    def press_key(self, key: str, modifiers: List[str] = None) -> Dict[str, Any]:
        """Press keyboard key."""
        return self.desktop.press_key(key, modifiers)
    
    def screenshot(self, filename: str = None) -> Dict[str, Any]:
        """Take a screenshot."""
        return self.desktop.take_screenshot(filename)
    
    def search_youtube(self, query: str, browser: str = None) -> Dict[str, Any]:
        """Search YouTube with a query."""
        return self.desktop.search_youtube(query, browser)
    
    def search_google(self, query: str, browser: str = None) -> Dict[str, Any]:
        """Search Google with a query."""
        return self.desktop.search_google(query, browser)
    
    def browse(self, url: str, browser: str = None) -> Dict[str, Any]:
        """Open a website in browser."""
        return self.desktop.browse_website(url, browser)
    
    def play_youtube(self, query: str, browser: str = None) -> Dict[str, Any]:
        """Search YouTube and play the first video result."""
        return self.desktop.search_and_play_youtube(query, browser)
    
    def play_youtube_url(self, video_url: str, browser: str = None) -> Dict[str, Any]:
        """Play a YouTube video by URL or video ID."""
        return self.desktop.play_youtube_video(video_url, browser)
    
    def youtube_results(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Get YouTube search results without playing."""
        return self.desktop.get_youtube_search_results(query, limit)
    
    # ==================== SPOTIFY CONTROL ====================
    
    def play_spotify(self, query: str, content_type: str = "track") -> Dict[str, Any]:
        """Search and play music on Spotify."""
        return self.desktop.search_and_play_spotify(query, content_type)
    
    def spotify_control(self, action: str) -> Dict[str, Any]:
        """Control Spotify playback (play, pause, next, previous, stop)."""
        return self.desktop.spotify_control(action)
    
    def open_spotify(self) -> Dict[str, Any]:
        """Open Spotify application."""
        return self.desktop.open_spotify()
    
    def close_spotify(self) -> Dict[str, Any]:
        """Close Spotify application."""
        return self.desktop.close_spotify()
    
    def play_spotify_uri(self, uri: str) -> Dict[str, Any]:
        """Play Spotify content by URI."""
        return self.desktop.play_spotify_uri(uri)
    
    # ==================== FILE GENERATION ====================
    
    def create_word(self, content: str, filename: str = "document", title: str = None) -> Dict[str, Any]:
        """Create a Word document."""
        return self.file_gen.create_word(content, filename, title)
    
    def create_pdf(self, content: str, filename: str = "document", title: str = None) -> Dict[str, Any]:
        """Create a PDF document."""
        return self.file_gen.create_pdf(content, filename, title)
    
    def create_csv(self, data: List[Dict], filename: str = "data") -> Dict[str, Any]:
        """Create a CSV file."""
        return self.file_gen.create_csv(data, filename)
    
    def create_excel(self, data: Union[List[Dict], Dict[str, List[Dict]]], filename: str = "workbook") -> Dict[str, Any]:
        """Create an Excel file."""
        return self.file_gen.create_excel(data, filename)
    
    def create_json(self, data: Any, filename: str = "data") -> Dict[str, Any]:
        """Create a JSON file."""
        return self.file_gen.create_json(data, filename)
    
    def create_txt(self, content: str, filename: str = "document") -> Dict[str, Any]:
        """Create a text file."""
        return self.file_gen.create_txt(content, filename)
    
    def create_markdown(self, content: str, filename: str = "document", title: str = None) -> Dict[str, Any]:
        """Create a Markdown file."""
        return self.file_gen.create_markdown(content, filename, title)
    
    def create_chart(
        self,
        data: Dict[str, List],
        chart_type: str = "line",
        filename: str = "chart",
        title: str = None,
        xlabel: str = None,
        ylabel: str = None
    ) -> Dict[str, Any]:
        """Create a chart/graph."""
        return self.file_gen.create_chart(data, chart_type, filename, title, xlabel, ylabel)
    
    def create_image(
        self,
        width: int = 800,
        height: int = 600,
        color: str = "white",
        filename: str = "image",
        text: str = None
    ) -> Dict[str, Any]:
        """Create a simple image."""
        return self.file_gen.create_image(width, height, color, filename, text)
    
    # ==================== SESSION MANAGEMENT ====================
    
    def new_session(self, session_id: str = None) -> str:
        """Create a new REPL session."""
        import uuid
        session_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        self.current_session = session_id
        return session_id
    
    def clear_session(self, session_id: str = None) -> Dict[str, Any]:
        """Clear a REPL session."""
        return self.executor.clear_session(session_id or self.current_session)
    
    def list_sessions(self) -> List[str]:
        """List all REPL sessions."""
        return self.executor.list_sessions()
    
    def get_session_history(self, session_id: str = None) -> List[Dict]:
        """Get session execution history."""
        session_id = session_id or self.current_session
        if session_id in self.executor.sessions:
            return self.executor.sessions[session_id].history
        return []
    
    # ==================== HELPER COMMANDS ====================
    
    def help(self) -> str:
        """Get help text."""
        return """
╔═══════════════════════════════════════════════════════════════════════╗
║                        JAWIR INTERPRETER HELP                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  PYTHON EXECUTION                                                     ║
║  ─────────────────                                                    ║
║  /python <code>          - Execute Python code                        ║
║  /python file <path>     - Run Python file                           ║
║  /pip install <package>  - Install package                           ║
║                                                                       ║
║  DESKTOP CONTROL                                                      ║
║  ───────────────                                                      ║
║  /open <app>             - Open application (chrome, spotify, etc)   ║
║  /close <app>            - Close application                         ║
║  /url <url>              - Open URL in browser                       ║
║  /screenshot             - Take screenshot                           ║
║                                                                       ║
║  FILE GENERATION                                                      ║
║  ───────────────                                                      ║
║  /word <content>         - Create Word document                      ║
║  /pdf <content>          - Create PDF document                       ║
║  /csv <data>             - Create CSV file                           ║
║  /excel <data>           - Create Excel file                         ║
║  /json <data>            - Create JSON file                          ║
║  /txt <content>          - Create text file                          ║
║  /md <content>           - Create Markdown file                      ║
║  /chart <data>           - Create chart/graph                        ║
║                                                                       ║
║  AVAILABLE APPS: chrome, firefox, edge, spotify, vlc, calculator,    ║
║                  notepad, vscode, word, excel, powerpoint, kicad,    ║
║                  explorer, cmd, powershell, paint, photos            ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

    def get_status(self) -> Dict[str, Any]:
        """Get interpreter status."""
        return {
            "workspace": str(self.workspace_dir),
            "current_session": self.current_session,
            "active_sessions": len(self.executor.sessions),
            "output_dir": str(self.file_gen.output_dir),
            "available_apps": list(self.desktop.APPS.keys())
        }


# ==================== SINGLETON INSTANCE ====================

_interpreter_instance = None

def get_interpreter() -> JawirInterpreter:
    """Get or create the global JAWIR Interpreter instance."""
    global _interpreter_instance
    if _interpreter_instance is None:
        _interpreter_instance = JawirInterpreter()
    return _interpreter_instance


# ==================== CONVENIENCE FUNCTIONS ====================

def run_python(code: str, use_subprocess: bool = False) -> Dict[str, Any]:
    """Run Python code."""
    return get_interpreter().run_code(code, use_subprocess=use_subprocess)

def open_app(app_name: str) -> Dict[str, Any]:
    """Open desktop application."""
    return get_interpreter().open_app(app_name)

def open_url(url: str) -> Dict[str, Any]:
    """Open URL in browser."""
    return get_interpreter().open_url(url)

def create_file(file_type: str, content: Any, filename: str = None) -> Dict[str, Any]:
    """
    Create a file of specified type.
    
    Args:
        file_type: "word", "pdf", "csv", "excel", "json", "txt", "md", "chart"
        content: File content
        filename: Optional filename
    """
    interp = get_interpreter()
    filename = filename or "output"
    
    type_map = {
        "word": interp.create_word,
        "docx": interp.create_word,
        "pdf": interp.create_pdf,
        "csv": interp.create_csv,
        "excel": interp.create_excel,
        "xlsx": interp.create_excel,
        "json": interp.create_json,
        "txt": interp.create_txt,
        "text": interp.create_txt,
        "md": interp.create_markdown,
        "markdown": interp.create_markdown,
    }
    
    if file_type.lower() in type_map:
        return type_map[file_type.lower()](content, filename)
    else:
        return {"success": False, "message": f"Unknown file type: {file_type}"}
