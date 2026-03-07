#!/usr/bin/env python
"""
JAWIR OS - AI Assistant dari Ngawi 
==========================================================
JAWIR adalah AI Assistant Jawa Terkuat.

AVAILABLE TOOLS:
- 🔧 KiCad Tool      : Generate schematic dari natural language
- 🔍 Web Search Tool : Cari info komponen, datasheet, tutorial
- 🔬 Research Tool   : Deep research sebelum desain rangkaian
- 📧 Google Workspace: Gmail, Drive, Calendar, Sheets, Forms

Usage:
    python kicad_cli.py -i                              (interactive mode)
    python kicad_cli.py "Buat ESP32 dengan LED"         (KiCad tool)
    python kicad_cli.py -s "ESP32 pinout"               (Web Search tool)
    python kicad_cli.py -r "IoT weather station"        (Research + KiCad)
    python kicad_cli.py -g                              (Google Workspace mode)

Commands in Interactive Mode:
    /search <query>   - 🔍 Web Search tool
    /research <topic> - 🔬 Research tool + generate schematic
    /google           - 📧 Switch to Google Workspace mode
    /gmail <action>   - 📧 Gmail (labels, search, send)
    /drive <action>   - 📁 Drive (list, search, upload)
    /calendar <action>- 📅 Calendar (list, events, add)
    /help             - Show help
    /clear            - Clear screen
    <description>     - 🔧 KiCad tool (direct generation)
    exit              - Exit
"""

import os
import sys
import asyncio
import argparse
import time
import re

# Setup path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
backend_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, backend_dir)

# Add gpt-researcher to path
gpt_researcher_path = os.path.join(os.path.dirname(backend_dir), 'gpt-researcher')
sys.path.insert(0, gpt_researcher_path)

# Environment setup
try:
    from dotenv import load_dotenv
    env_paths = [
        os.path.join(backend_dir, '.env'),
        os.path.join(os.path.dirname(backend_dir), '.env'),
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            break
except ImportError:
    pass


# ============================================
# COLORS FOR TERMINAL OUTPUT
# ============================================

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_banner():
    """Print JAWIR banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
     ██╗ █████╗ ██╗    ██╗██╗██████╗      ██████╗ ███████╗
     ██║██╔══██╗██║    ██║██║██╔══██╗    ██╔═══██╗██╔════╝
     ██║███████║██║ █╗ ██║██║██████╔╝    ██║   ██║███████╗
██   ██║██╔══██║██║███╗██║██║██╔══██╗    ██║   ██║╚════██║
╚█████╔╝██║  ██║╚███╔███╔╝██║██║  ██║    ╚██████╔╝███████║
 ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝
{Colors.ENDC}
{Colors.YELLOW}          AI Assistant dari Ngawi - Jawa Terkuat!{Colors.ENDC}
{Colors.DIM}  ════════════════════════════════════════════════════════════{Colors.ENDC}
{Colors.DIM}  🔧 KiCad  |  🔍 Search  |  🔬 Research  |  📧 Google  |  🐍 Python{Colors.ENDC}
{Colors.DIM}  🖥️ Computer Use  |  📚 Journal  |  🎬 YouTube  |  ⬇️ Download{Colors.ENDC}
"""
    print(banner)


def print_status(icon: str, message: str, color: str = Colors.ENDC):
    """Print status message with icon."""
    print(f"{color}{icon} {message}{Colors.ENDC}")


def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'═' * 60}{Colors.ENDC}\n")


def print_react_step(step_type: str, content: str, step_num: int = None):
    """Print ReAct step with formatting."""
    if step_type == "thought":
        prefix = f"{Colors.CYAN}💭 THOUGHT"
        if step_num:
            prefix += f" #{step_num}"
        print(f"{prefix}:{Colors.ENDC}")
        print(f"   {Colors.DIM}{content}{Colors.ENDC}\n")
    elif step_type == "action":
        prefix = f"{Colors.YELLOW}⚡ ACTION"
        if step_num:
            prefix += f" #{step_num}"
        print(f"{prefix}:{Colors.ENDC}")
        print(f"   {content}\n")
    elif step_type == "observation":
        prefix = f"{Colors.GREEN}👁️ OBSERVATION"
        if step_num:
            prefix += f" #{step_num}"
        print(f"{prefix}:{Colors.ENDC}")
        # Truncate long observations
        if len(content) > 500:
            content = content[:500] + "..."
        print(f"   {Colors.DIM}{content}{Colors.ENDC}\n")
    elif step_type == "final":
        print(f"{Colors.GREEN}{Colors.BOLD}✅ FINAL ANSWER:{Colors.ENDC}")
        print(f"   {content}\n")


# ============================================
# ReAct AGENT - Unified Reasoning + Acting Pattern
# ============================================
# JAWIR OS menggunakan konsep AGENTIC ReAct:
# Thought → Action → Observation (loop)
# Gemini sebagai OTAK UTAMA yang memutuskan tool mana yang dipakai
# ============================================

class ReActAgent:
    """
    UNIFIED ReAct Agent untuk JAWIR OS.
    Menggunakan pattern: Thought → Action → Observation (loop)
    
    SEMUA TOOLS terintegrasi disini:
    - KiCad Tools (schematic generation)
    - Web Search Tools (search internet)
    - Desktop Control Tools (open apps, browser)
    - YouTube Tools (search, play)
    - Python Interpreter (execute code)
    - File Generation Tools (word, pdf, etc)
    
    Gemini 3 Pro/Flash sebagai OTAK yang memutuskan action.
    """
    
    def __init__(self, gemini_client):
        self.gemini = gemini_client
        self.web_search = None
        self.interpreter = None
        
        # Initialize Web Search
        try:
            self.web_search = WebSearchTool()
        except:
            pass
        
        # Initialize Python Interpreter (lazy load)
        self._interpreter_initialized = False
        
        self.max_iterations = 6  # Lebih banyak untuk multi-tool tasks
        self.conversation_history = []
    
    def _get_interpreter(self):
        """Lazy load Python Interpreter."""
        if not self._interpreter_initialized:
            try:
                # Add python_interpreter to path
                tools_dir = os.path.dirname(current_dir)
                py_interp_dir = os.path.join(tools_dir, 'python_interpreter')
                
                if os.path.exists(py_interp_dir):
                    # Add both paths to ensure imports work
                    if py_interp_dir not in sys.path:
                        sys.path.insert(0, py_interp_dir)
                    if tools_dir not in sys.path:
                        sys.path.insert(0, tools_dir)
                    
                    # Import modules directly to avoid relative import issues
                    import importlib.util
                    
                    # Load executor
                    executor_spec = importlib.util.spec_from_file_location(
                        "executor", 
                        os.path.join(py_interp_dir, "executor.py")
                    )
                    executor_module = importlib.util.module_from_spec(executor_spec)
                    sys.modules["executor"] = executor_module
                    executor_spec.loader.exec_module(executor_module)
                    
                    # Load desktop_control
                    desktop_spec = importlib.util.spec_from_file_location(
                        "desktop_control",
                        os.path.join(py_interp_dir, "desktop_control.py")
                    )
                    desktop_module = importlib.util.module_from_spec(desktop_spec)
                    sys.modules["desktop_control"] = desktop_module
                    desktop_spec.loader.exec_module(desktop_module)
                    
                    # Load file_generator
                    file_gen_spec = importlib.util.spec_from_file_location(
                        "file_generator",
                        os.path.join(py_interp_dir, "file_generator.py")
                    )
                    file_gen_module = importlib.util.module_from_spec(file_gen_spec)
                    sys.modules["file_generator"] = file_gen_module
                    file_gen_spec.loader.exec_module(file_gen_module)
                    
                    # Now create interpreter manually
                    from pathlib import Path
                    workspace_dir = Path("D:/sijawir/python_workspace").absolute()
                    workspace_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Create a simple interpreter-like object
                    class SimpleInterpreter:
                        def __init__(self):
                            self.workspace_dir = workspace_dir
                            self.executor = executor_module.PythonExecutor(working_dir=str(workspace_dir))
                            self.desktop = desktop_module.DesktopController()
                            self.file_gen = file_gen_module.FileGenerator(output_dir=str(workspace_dir / "output"))
                            self.current_session = "default"
                        
                        def run_code(self, code, session=None, use_subprocess=False, timeout=30):
                            session = session or self.current_session
                            if use_subprocess:
                                return self.executor.execute_subprocess(code, timeout=timeout)
                            return self.executor.execute_inline(code, session_id=session)
                        
                        def open_app(self, app_name):
                            return self.desktop.open_app(app_name)
                        
                        def close_app(self, app_name):
                            return self.desktop.close_app(app_name)
                        
                        def open_url(self, url, browser=None):
                            return self.desktop.open_url(url, browser)
                        
                        def screenshot(self, filename=None, region=None):
                            return self.desktop.take_screenshot(filename, region)
                        
                        def search_youtube(self, query, browser=None):
                            return self.desktop.search_youtube(query, browser)
                        
                        def search_google(self, query, browser=None):
                            return self.desktop.search_google(query, browser)
                        
                        def browse(self, url, browser=None):
                            return self.desktop.browse_website(url, browser)
                        
                        def play_youtube(self, query, browser=None):
                            return self.desktop.search_and_play_youtube(query, browser)
                        
                        def play_youtube_url(self, video_url, browser=None):
                            return self.desktop.play_youtube_video(video_url, browser)
                        
                        def youtube_results(self, query, limit=5):
                            return self.desktop.get_youtube_search_results(query, limit)
                        
                        # ========== SPOTIFY METHODS ==========
                        def open_spotify(self):
                            """Open Spotify application"""
                            return self.desktop.open_spotify()
                        
                        def play_spotify(self, query, content_type="track"):
                            """Search and play music on Spotify"""
                            return self.desktop.search_and_play_spotify(query, content_type)
                        
                        def spotify_control(self, action):
                            """Control Spotify: play, pause, next, previous, stop"""
                            return self.desktop.spotify_control(action)
                        
                        def close_spotify(self):
                            """Close Spotify application"""
                            return self.desktop.close_spotify()
                        
                        def play_spotify_uri(self, uri):
                            """Play Spotify content by URI"""
                            return self.desktop.play_spotify_uri(uri)
                        # =====================================
                        
                        def install_package(self, package):
                            return self.executor.install_package(package)
                        
                        def create_word(self, content, filename="document", title=None):
                            return self.file_gen.create_word(content, filename, title)
                        
                        def create_pdf(self, content, filename="document", title=None):
                            return self.file_gen.create_pdf(content, filename, title)
                        
                        def create_txt(self, content, filename="document"):
                            return self.file_gen.create_txt(content, filename)
                        
                        def create_markdown(self, content, filename="document", title=None):
                            return self.file_gen.create_markdown(content, filename, title)
                        
                        def create_json(self, data, filename="data"):
                            return self.file_gen.create_json(data, filename)
                        
                        def create_excel(self, data, filename="workbook"):
                            return self.file_gen.create_excel(data, filename)
                    
                    self.interpreter = SimpleInterpreter()
                    self._interpreter_initialized = True
                    print_status("✅", "Python Interpreter initialized", Colors.GREEN)
                    
            except Exception as e:
                print_status("⚠️", f"Python Interpreter not available: {e}", Colors.YELLOW)
                import traceback
                traceback.print_exc()
        return self.interpreter
    
    def _get_gws_client(self):
        """Lazy load Google Workspace client."""
        if not hasattr(self, '_gws_client'):
            self._gws_client = None
        if self._gws_client is None:
            try:
                tools_dir = os.path.dirname(current_dir)
                if tools_dir not in sys.path:
                    sys.path.insert(0, tools_dir)
                from google_workspace import GoogleWorkspaceMCP
                self._gws_client = GoogleWorkspaceMCP()
                print_status("✅", f"Google Workspace connected: {self._gws_client.user_email}", Colors.GREEN)
            except Exception as e:
                print_status("⚠️", f"Google Workspace not available: {e}", Colors.YELLOW)
                return None
        return self._gws_client
    
    def get_react_system_prompt(self, task_type: str = "general") -> str:
        """
        System prompt untuk ReAct reasoning.
        Berisi SEMUA TOOLS yang tersedia untuk Gemini.
        """
        
        # Base prompt
        base_prompt = """Kamu adalah JAWIR OS - AI Assistant Jawa Terkuat dari Ngawi.
Kamu menggunakan ReAct (Reasoning + Acting) pattern untuk menyelesaikan SEMUA tugas.

═══════════════════════════════════════════════════════════════════
🛠️ AVAILABLE TOOLS - Gunakan sesuai kebutuhan!
═══════════════════════════════════════════════════════════════════

📋 GENERAL TOOLS:
• finish(answer) - WAJIB dipanggil untuk menyelesaikan tugas dengan jawaban final
• respond(message) - Balas user dengan pesan tanpa selesai (untuk percakapan)

🔍 WEB SEARCH TOOLS:
• web_search(query) - Cari informasi di internet
• search_component(name) - Cari info komponen elektronik (pinout, datasheet)

🖥️ DESKTOP CONTROL TOOLS:
• open_app(app_name) - Buka aplikasi (chrome, firefox, spotify, vscode, notepad, dll)
• close_app(app_name) - Tutup aplikasi
• screenshot() - Ambil screenshot layar

🎬 YOUTUBE TOOLS:
• play_youtube(query) - Cari dan PUTAR video YouTube (autoplay!)
• search_youtube(query) - Cari YouTube dan buka halaman hasil
• youtube_results(query) - Dapatkan list hasil pencarian

� SPOTIFY TOOLS (PRIORITAS untuk musik!):
• open_spotify() - Buka aplikasi Spotify
• play_spotify(query) - Cari dan PUTAR musik di Spotify (GUNAKAN INI untuk request musik!)
• spotify_control(action) - Kontrol playback: "play", "pause", "next", "previous", "stop"
• close_spotify() - Tutup Spotify
• play_spotify_uri(uri) - Play langsung via Spotify URI (spotify:track:xxx)

🌐 BROWSER TOOLS:
• browse(url) - Buka website di browser
• search_google(query) - Cari di Google

🐍 PYTHON TOOLS:
• run_python(code) - Eksekusi kode Python
• install_package(package) - Install pip package

📄 FILE GENERATION TOOLS:
• create_word(content) - Buat dokumen Word
• create_pdf(content) - Buat dokumen PDF
• create_txt(content) - Buat file teks
• create_markdown(content) - Buat file Markdown
• create_json(data) - Buat file JSON
• create_excel(data) - Buat file Excel

🔧 KICAD TOOLS (untuk desain elektronik):
• generate_schematic(spec) - Generate skematik KiCad

🖥️ COMPUTER USE TOOLS (Browser Automation dengan AI Vision):
• journal_search(query) - Download paper akademik dari arXiv (AI akan browse & download otomatis)
• ytplay_vision(query) - Play YouTube dengan AI vision (lebih akurat dari play_youtube)
• browse_interact(url|task) - AI browse website dan lakukan task tertentu
• download_file(url|filename) - Download file dari URL ke folder downloads

📧 GOOGLE WORKSPACE TOOLS:
• gmail_search(query) - Cari email di Gmail
• gmail_send(to|subject|body) - Kirim email (format: email@domain|Subjek|Isi pesan)
• gmail_draft(to|subject|body) - Buat draft email
• drive_list(query) - List/cari file di Google Drive
• drive_create(filename|content) - Buat file di Drive
• calendar_list() - List event kalender
• calendar_add(text) - Tambah event dengan natural language (misal: "Meeting besok jam 3 sore")
• sheets_read(spreadsheetId|range) - Baca data dari Google Sheets
• sheets_write(spreadsheetId|range|values) - Tulis data ke Sheets (values dalam format JSON)

═══════════════════════════════════════════════════════════════════
📝 FORMAT WAJIB - Selalu gunakan format ini:
═══════════════════════════════════════════════════════════════════

Thought: [Analisis apa yang user minta, rencanakan langkah]
Action: [nama_tool(parameter)]

Tunggu Observation dari tool, lalu lanjutkan dengan Thought berikutnya.
Selesaikan dengan finish(jawaban) ketika tugas selesai.

═══════════════════════════════════════════════════════════════════
📌 CONTOH PENGGUNAAN:
═══════════════════════════════════════════════════════════════════

🎵 User: "putar musik jazz di spotify" atau "nyalakan lagu jazz"
Thought: User mau dengar musik jazz. Saya akan putar di Spotify.
Action: play_spotify(jazz relaxing music)

🎧 User: "pause musiknya" atau "stop"
Thought: User mau pause musik yang sedang diputar.
Action: spotify_control(pause)

🎵 User: "next song" atau "skip lagu"
Thought: User mau skip ke lagu berikutnya.
Action: spotify_control(next)

🎬 User: "putarkan video tutorial python di youtube"
Thought: User mau VIDEO tutorial, bukan musik. Putar di YouTube.
Action: play_youtube(python tutorial)
[Observation: Chrome opened]
Thought: Chrome sudah terbuka. Sekarang cari di Google.
Action: search_google(tutorial python untuk pemula)

🐍 User: "hitung faktorial 10"
Thought: User mau hitung faktorial. Saya akan jalankan Python.
Action: run_python(import math; print(f"Faktorial 10 = {math.factorial(10)}"))

📄 User: "buatkan laporan tentang IoT"
Thought: User mau laporan. Saya akan cari info dulu lalu buat dokumen.
Action: web_search(IoT Internet of Things penjelasan lengkap)
[Observation: info IoT...]
Thought: Info cukup. Buat dokumen Word.
Action: create_word(# Laporan IoT\\n\\nInternet of Things adalah...)

📚 User: "carikan paper tentang machine learning" atau "download journal AI"
Thought: User mau paper akademik. Gunakan AI vision untuk browse arXiv.
Action: journal_search(machine learning deep neural network)
[Observation: ✅ Paper downloaded: paper.pdf]
Thought: Paper berhasil didownload!
Action: finish(Paper "machine learning" sudah didownload ke folder journals)

🎬 User: "putarkan video lofi di youtube" (untuk video yang perlu AI vision)
Thought: User mau video spesifik. Gunakan ytplay_vision untuk akurasi.
Action: ytplay_vision(lofi hip hop beats to relax study)

🌐 User: "buka github terus cari repository python terbaru"
Thought: User mau AI browse dan interaksi. Gunakan browse_interact.
Action: browse_interact(https://github.com|cari trending python repos)

⬇️ User: "download gambar dari url ini"
Thought: User mau download file. Gunakan download_file.
Action: download_file(https://example.com/image.png|gambar_baru.png)

📧 User: "kirim email ke boss tentang progress project"
Thought: User mau kirim email. Gunakan gmail_send.
Action: gmail_send(boss@company.com|Progress Project|Halo, berikut update progress project hari ini...)

📅 User: "tambahkan meeting besok jam 3 sore"
Thought: User mau buat event kalender. Gunakan calendar_add dengan natural language.
Action: calendar_add(Meeting besok jam 3 sore)

📁 User: "cari file proposal di drive"
Thought: User mau cari file di Google Drive.
Action: drive_list(proposal)

═══════════════════════════════════════════════════════════════════
⚡ ATURAN PENTING:
═══════════════════════════════════════════════════════════════════
1. SELALU mulai dengan Thought untuk analisis
2. Gunakan tool yang TEPAT sesuai permintaan user
3. Untuk multimedia (YouTube), langsung pakai play_youtube()
4. Untuk browsing, pakai browse() atau search_google()
5. **SETELAH action BERHASIL (✅), LANGSUNG panggil finish() dengan ringkasan!**
6. Jika ada error, coba alternatif lain ATAU finish dengan error message
7. JANGAN ulangi action yang sudah berhasil!

📌 CONTOH FLOW YANG BENAR:
User: "putarkan musik jazz"
Thought: User mau dengar jazz. Putar di YouTube.
Action: play_youtube(jazz music relaxing)
[Observation: ✅ Now playing: Jazz Music...]
Thought: Musik sudah diputar. Selesai!
Action: finish(Musik jazz sudah diputar di YouTube: Jazz Music Relaxing)

📌 FLOW SALAH (JANGAN LAKUKAN):
❌ Mengulangi action yang sudah berhasil
❌ Tidak memanggil finish() setelah berhasil
❌ Lebih dari 2 iterasi untuk task sederhana"""

        # Add KiCad-specific rules for schematic tasks
        if task_type == "schematic":
            base_prompt += """

═══════════════════════════════════════════════════════════════════
🔧 ATURAN KHUSUS KICAD (Desain Elektronik):
═══════════════════════════════════════════════════════════════════

🔴 ATURAN POWER WIRING - SANGAT KRITIS!!!
- VCC sensor → HANYA ke VCC/3V3 (ESP32.pin2), BUKAN ke GPIO!
- GND sensor → HANYA ke GND (ESP32.pin1), BUKAN ke GPIO!
- DATA sensor → ke GPIO yang sesuai (GPIO4, GPIO16, dll)

CONTOH KONEKSI DHT11 YANG BENAR:
- pin1 (VCC) → 3V3 atau VCC.pin1  ✅
- pin2 (DATA) → GPIO4 (U1.pin26)  ✅
- pin4 (GND) → GND atau U1.pin1   ✅

FLOW DESAIN SKEMATIK:
1. search_component() untuk dapat info pinout
2. generate_schematic() dengan spesifikasi lengkap
3. finish() dengan ringkasan koneksi"""

        return base_prompt

    async def run(self, user_request: str, task_type: str = "general") -> dict:
        """
        Jalankan ReAct loop untuk menyelesaikan request.
        
        Args:
            user_request: Permintaan user
            task_type: "general", "schematic", "search", atau "research"
        
        Returns:
            dict dengan hasil dan history
        """
        from pydantic import BaseModel, Field
        from typing import Optional, Literal
        from langchain_core.messages import HumanMessage, SystemMessage
        
        print_section("🧠 ReAct REASONING MODE")
        print_status("📝", f"Request: {user_request}", Colors.CYAN)
        print_status("🔄", f"Task Type: {task_type}", Colors.DIM)
        print()
        
        # Schema untuk ReAct response
        class ReActStep(BaseModel):
            thought: str = Field(description="Analisis dan reasoning tentang permintaan user")
            action: str = Field(description="Nama tool yang akan digunakan (web_search, play_youtube, open_app, run_python, create_word, finish, dll)")
            action_input: str = Field(description="Parameter/argumen untuk action")
        
        # Initialize
        iteration = 0
        observations = []
        final_result = None
        collected_info = {
            "components_info": [],
            "search_results": [],
            "design_specs": {},
            "files_created": [],
            "actions_performed": [],
        }
        
        # Build initial prompt
        messages = [
            SystemMessage(content=self.get_react_system_prompt(task_type)),
            HumanMessage(content=f"User Request: {user_request}\n\nMulai dengan Thought untuk menganalisis permintaan ini.")
        ]
        
        # ReAct Loop
        while iteration < self.max_iterations:
            iteration += 1
            print(f"{Colors.BOLD}{'─' * 50}{Colors.ENDC}")
            print(f"{Colors.BOLD}Iteration {iteration}/{self.max_iterations}{Colors.ENDC}\n")
            
            try:
                # Get Thought + Action from LLM (Gemini as the brain!)
                step: ReActStep = await self.gemini.invoke_with_rotation(messages, ReActStep)
                
                # Print Thought
                print_react_step("thought", step.thought, iteration)
                
                # Print Action
                print_react_step("action", f"{step.action}({step.action_input})", iteration)
                
                # Execute Action and get Observation
                observation = await self._execute_action(
                    step.action, 
                    step.action_input, 
                    collected_info,
                    user_request
                )
                
                # Print Observation
                print_react_step("observation", observation, iteration)
                
                # Track action performed
                collected_info["actions_performed"].append({
                    "iteration": iteration,
                    "action": step.action,
                    "input": step.action_input,
                    "observation": observation[:200] + "..." if len(observation) > 200 else observation
                })
                
                # Check if finished
                if step.action.lower() == "finish":
                    final_result = {
                        "success": True,
                        "answer": step.action_input,
                        "observation": observation,
                        "iterations": iteration,
                        "collected_info": collected_info,
                    }
                    print_react_step("final", step.action_input)
                    break
                
                # Determine if action was successful (check for ✅ in observation)
                action_success = observation.startswith("✅")
                
                # AUTO-FINISH untuk single-action tasks yang BERHASIL
                # TAPI TIDAK untuk multi-step requests (yang mengandung "dan", "lalu", "kemudian", dll)
                simple_actions = ["play_youtube", "search_youtube", "close_app", 
                                 "browse", "search_google", "screenshot", "run_python",
                                 "create_word", "create_pdf", "create_txt", "create_markdown",
                                 "create_json", "create_excel", "install_package",
                                 # Spotify actions - ONLY play_spotify and spotify_control auto-finish
                                 "play_spotify", "spotify_control", 
                                 "close_spotify", "play_spotify_uri",
                                 # Web search actions
                                 "web_search", "search_component",
                                 # Google Workspace actions
                                 "gmail_search", "gmail_send", "gmail_draft",
                                 "drive_list", "drive_create",
                                 "calendar_list", "calendar_add",
                                 "sheets_read", "sheets_write"]
                
                # Detect multi-step keywords in original request
                multi_step_keywords = [" dan ", " lalu ", " kemudian ", " terus ", " setelah itu ",
                                       " then ", " and then ", " after that "]
                is_multi_step = any(kw in user_request.lower() for kw in multi_step_keywords)
                
                # Actions that should NOT auto-finish in multi-step context
                no_auto_finish_in_multistep = ["open_app", "open_spotify", "browse"]
                
                # Determine if we should auto-finish
                should_auto_finish = (
                    action_success and 
                    step.action.lower() in simple_actions and
                    not (is_multi_step and step.action.lower() in no_auto_finish_in_multistep) and
                    iteration == 1  # Only on first iteration
                )
                
                # For multi-step: auto-finish after final action (play_spotify, play_youtube, etc.)
                final_actions_in_multistep = ["play_spotify", "play_youtube", "play_spotify_uri"]
                if is_multi_step and iteration > 1 and step.action.lower() in final_actions_in_multistep and action_success:
                    should_auto_finish = True
                
                if should_auto_finish:
                    # Auto-finish dengan ringkasan
                    summary = f"Tugas selesai! {observation}"
                    final_result = {
                        "success": True,
                        "answer": summary,
                        "observation": observation,
                        "iterations": iteration,
                        "collected_info": collected_info,
                        "auto_finished": True
                    }
                    print_react_step("final", summary)
                    break
                
                # Build next message based on success
                if action_success:
                    # Check if there's more to do (multi-step)
                    if is_multi_step and iteration == 1:
                        next_message = f"""
Observation: {observation}

✅ Langkah pertama BERHASIL! Tapi request user masih ada lanjutannya.

Request asli: "{user_request}"

Langkah yang sudah dilakukan: {step.action}({step.action_input})
Hasil: {observation}

LANJUTKAN ke langkah berikutnya sesuai request user!
Jangan finish() dulu sampai SEMUA langkah selesai.

Thought: [Apa langkah selanjutnya dari request user?]
Action: [tool untuk langkah berikutnya]"""
                    else:
                        next_message = f"""
Observation: {observation}

🎉 ACTION BERHASIL! Tugas sudah selesai.
SEKARANG WAJIB panggil finish() dengan ringkasan hasil.

Contoh: finish(Musik sudah diputar!)

Thought: Semua langkah sudah selesai. Sekarang finish.
Action: finish([ringkasan singkat untuk user])"""
                else:
                    next_message = f"""
Observation: {observation}

Berdasarkan observation di atas, lanjutkan dengan Thought berikutnya.
Jika ada error, coba cara lain. Jika berhasil, panggil finish()."""
                
                messages.append(HumanMessage(content=next_message))
                
                observations.append({
                    "iteration": iteration,
                    "thought": step.thought,
                    "action": step.action,
                    "action_input": step.action_input,
                    "observation": observation,
                })
                
            except Exception as e:
                print_status("❌", f"Error in iteration {iteration}: {e}", Colors.RED)
                observations.append({"error": str(e)})
                break
        
        # If max iterations reached without finish
        if not final_result:
            final_result = {
                "success": False,
                "message": "Max iterations reached",
                "iterations": iteration,
                "observations": observations,
                "collected_info": collected_info,
            }
        
        return final_result
    
    async def _execute_action(self, action: str, action_input: str, collected_info: dict, original_request: str) -> str:
        """
        Execute action dan return observation.
        
        UNIFIED handler untuk SEMUA tools JAWIR OS.
        """
        action = action.lower().strip()
        
        # ============================================
        # WEB SEARCH TOOLS
        # ============================================
        if action == "web_search":
            if self.web_search:
                # Detect apakah query tentang elektronik atau umum
                electronics_keywords = ["esp32", "arduino", "sensor", "relay", "led", "resistor", 
                                       "capacitor", "transistor", "pinout", "schematic", "circuit",
                                       "microcontroller", "gpio", "i2c", "spi", "uart", "pwm",
                                       "voltage", "current", "power", "pcb", "kicad", "datasheet"]
                is_electronics = any(kw in action_input.lower() for kw in electronics_keywords)
                
                results = self.web_search.search(action_input, max_results=5, electronics_only=is_electronics)
                if results:
                    formatted = []
                    for r in results[:3]:
                        formatted.append(f"- {r.get('title', 'No title')}: {r.get('content', '')[:200]}...")
                    collected_info["search_results"].extend(results)
                    return "✅ Search results:\n" + "\n".join(formatted)
                return "❌ No results found for this query."
            return "❌ Web search not available (TAVILY_API_KEY not set)"
        
        elif action == "search_component":
            if self.web_search:
                info = self.web_search.search_component(action_input)
                if info:
                    collected_info["components_info"].append({
                        "component": action_input,
                        "info": info
                    })
                    return f"✅ Component info for {action_input}:\n{info[:500]}..."
                return f"❌ No detailed info found for {action_input}"
            return "❌ Web search not available"
        
        # ============================================
        # DESKTOP CONTROL TOOLS
        # ============================================
        elif action == "open_app":
            interp = self._get_interpreter()
            if interp:
                result = interp.open_app(action_input)
                if result.get("success"):
                    return f"✅ Opened application: {action_input}"
                return f"❌ Failed to open {action_input}: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "close_app":
            interp = self._get_interpreter()
            if interp:
                result = interp.close_app(action_input)
                if result.get("success"):
                    return f"✅ Closed application: {action_input}"
                return f"❌ Failed to close {action_input}: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "screenshot":
            interp = self._get_interpreter()
            if interp:
                result = interp.screenshot()
                if result.get("success"):
                    path = result.get("path", "unknown")
                    return f"✅ Screenshot saved to: {path}"
                return f"❌ Failed to take screenshot: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        # ============================================
        # YOUTUBE TOOLS
        # ============================================
        elif action == "play_youtube":
            interp = self._get_interpreter()
            if interp:
                result = interp.play_youtube(action_input)
                if result.get("success"):
                    video = result.get("video", {})
                    title = video.get("title", "Unknown")
                    url = video.get("url", "")
                    return f"✅ Now playing: {title}\n🔗 {url}"
                return f"❌ Failed to play YouTube: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "search_youtube":
            interp = self._get_interpreter()
            if interp:
                result = interp.search_youtube(action_input)
                if result.get("success"):
                    return f"✅ YouTube search opened for: {action_input}"
                return f"❌ Failed to search YouTube: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "youtube_results":
            interp = self._get_interpreter()
            if interp:
                result = interp.youtube_results(action_input, limit=5)
                if result.get("success"):
                    videos = result.get("videos", [])
                    formatted = []
                    for v in videos:
                        formatted.append(f"[{v.get('index')}] {v.get('title')} - {v.get('channel')}")
                    return "✅ YouTube results:\n" + "\n".join(formatted)
                return f"❌ No videos found: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        # ============================================
        # SPOTIFY TOOLS
        # ============================================
        elif action == "open_spotify":
            interp = self._get_interpreter()
            if interp:
                result = interp.open_spotify()
                if result.get("success"):
                    return "✅ Spotify opened!"
                return f"❌ Failed to open Spotify: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "play_spotify":
            interp = self._get_interpreter()
            if interp:
                result = interp.play_spotify(action_input)
                if result.get("success"):
                    query = result.get("query", action_input)
                    return f"✅ Now playing on Spotify: {query}"
                return f"❌ Failed to play Spotify: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "spotify_control":
            interp = self._get_interpreter()
            if interp:
                result = interp.spotify_control(action_input)
                if result.get("success"):
                    msg = result.get("message", f"Spotify: {action_input}")
                    return f"✅ {msg}"
                return f"❌ Failed to control Spotify: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "close_spotify":
            interp = self._get_interpreter()
            if interp:
                result = interp.close_spotify()
                if result.get("success"):
                    return "✅ Spotify closed!"
                return f"❌ Failed to close Spotify: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "play_spotify_uri":
            interp = self._get_interpreter()
            if interp:
                result = interp.play_spotify_uri(action_input)
                if result.get("success"):
                    uri = result.get("uri", action_input)
                    return f"✅ Playing Spotify URI: {uri}"
                return f"❌ Failed to play URI: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        # ============================================
        # BROWSER TOOLS
        # ============================================
        elif action == "browse":
            interp = self._get_interpreter()
            if interp:
                result = interp.browse(action_input)
                if result.get("success"):
                    return f"✅ Opened website: {action_input}"
                return f"❌ Failed to open website: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "search_google":
            interp = self._get_interpreter()
            if interp:
                result = interp.search_google(action_input)
                if result.get("success"):
                    return f"✅ Google search opened for: {action_input}"
                return f"❌ Failed to search Google: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        # ============================================
        # PYTHON TOOLS
        # ============================================
        elif action == "run_python":
            interp = self._get_interpreter()
            if interp:
                result = interp.run_code(action_input)
                # executor returns: stdout, stderr, status, result
                status = result.get("status", 0)
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                
                if status == 0:
                    output = stdout.strip() if stdout else ""
                    return f"✅ Python executed:\n{output}" if output else "✅ Python code executed successfully (no output)"
                else:
                    error = stderr.strip() if stderr else "Execution failed"
                    return f"❌ Python error:\n{error}"
            return "❌ Python Interpreter not available"
        
        elif action == "install_package":
            interp = self._get_interpreter()
            if interp:
                result = interp.install_package(action_input)
                if result.get("success"):
                    return f"✅ Package installed: {action_input}"
                return f"❌ Failed to install {action_input}: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        # ============================================
        # FILE GENERATION TOOLS
        # ============================================
        elif action == "create_word":
            interp = self._get_interpreter()
            if interp:
                result = interp.create_word(action_input, "document")
                if result.get("success"):
                    path = result.get("path", "unknown")
                    collected_info["files_created"].append({"type": "word", "path": path})
                    return f"✅ Word document created: {path}"
                return f"❌ Failed to create Word: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "create_pdf":
            interp = self._get_interpreter()
            if interp:
                result = interp.create_pdf(action_input, "document")
                if result.get("success"):
                    path = result.get("path", "unknown")
                    collected_info["files_created"].append({"type": "pdf", "path": path})
                    return f"✅ PDF document created: {path}"
                return f"❌ Failed to create PDF: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "create_txt":
            interp = self._get_interpreter()
            if interp:
                result = interp.create_txt(action_input, "document")
                if result.get("success"):
                    path = result.get("path", "unknown")
                    collected_info["files_created"].append({"type": "txt", "path": path})
                    return f"✅ Text file created: {path}"
                return f"❌ Failed to create text file: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "create_markdown":
            interp = self._get_interpreter()
            if interp:
                result = interp.create_markdown(action_input, "document")
                if result.get("success"):
                    path = result.get("path", "unknown")
                    collected_info["files_created"].append({"type": "markdown", "path": path})
                    return f"✅ Markdown file created: {path}"
                return f"❌ Failed to create Markdown: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "create_json":
            interp = self._get_interpreter()
            if interp:
                import json
                try:
                    data = json.loads(action_input)
                except:
                    data = {"content": action_input}
                result = interp.create_json(data, "data")
                if result.get("success"):
                    path = result.get("path", "unknown")
                    collected_info["files_created"].append({"type": "json", "path": path})
                    return f"✅ JSON file created: {path}"
                return f"❌ Failed to create JSON: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        elif action == "create_excel":
            interp = self._get_interpreter()
            if interp:
                import json
                try:
                    data = json.loads(action_input)
                except:
                    data = [{"content": action_input}]
                result = interp.create_excel(data, "workbook")
                if result.get("success"):
                    path = result.get("path", "unknown")
                    collected_info["files_created"].append({"type": "excel", "path": path})
                    return f"✅ Excel file created: {path}"
                return f"❌ Failed to create Excel: {result.get('message', 'Unknown error')}"
            return "❌ Python Interpreter not available"
        
        # ============================================
        # KICAD TOOLS
        # ============================================
        elif action == "generate_schematic":
            collected_info["design_specs"]["final_spec"] = action_input
            collected_info["design_specs"]["original_request"] = original_request
            return f"✅ Design specification recorded:\n{action_input}\n\nSekarang gunakan finish() untuk menyelesaikan dengan ringkasan koneksi."
        
        # ============================================
        # COMPUTER USE TOOLS (Browser Automation)
        # ============================================
        elif action == "journal_search":
            if COMPUTER_USE_AVAILABLE:
                try:
                    print(f"\n🔍 Searching for journal: {action_input}")
                    # Run sync in thread pool to avoid event loop issues
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: asyncio.run(search_and_download_journal(action_input))
                    )
                    if result.get("success"):
                        return f"✅ Journal downloaded: {result.get('file_path', 'journals folder')}"
                    return f"❌ Journal search failed: {result.get('error', 'Unknown error')}"
                except Exception as e:
                    return f"❌ Journal search error: {str(e)}"
            return "❌ Computer Use not available. Install playwright: pip install playwright && playwright install chromium"
        
        elif action == "ytplay_vision":
            if COMPUTER_USE_AVAILABLE:
                try:
                    print(f"\n🎬 Playing YouTube with AI Vision: {action_input}")
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: asyncio.run(play_youtube_video(action_input))
                    )
                    if result.get("success"):
                        return f"✅ YouTube playing: {result.get('video_title', action_input)}"
                    return f"❌ YouTube play failed: {result.get('error', 'Unknown error')}"
                except Exception as e:
                    return f"❌ YouTube play error: {str(e)}"
            return "❌ Computer Use not available. Install playwright: pip install playwright && playwright install chromium"
        
        elif action == "browse_interact":
            if COMPUTER_USE_AVAILABLE:
                try:
                    # Parse url|task format
                    parts = action_input.split("|", 1)
                    url = parts[0].strip()
                    task = parts[1].strip() if len(parts) > 1 else "browse and summarize"
                    
                    print(f"\n🌐 AI Browsing: {url} | Task: {task}")
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: asyncio.run(browse_and_interact(url, task))
                    )
                    if result.get("success"):
                        return f"✅ Browse completed: {result.get('summary', 'Task done')}"
                    return f"❌ Browse failed: {result.get('error', 'Unknown error')}"
                except Exception as e:
                    return f"❌ Browse error: {str(e)}"
            return "❌ Computer Use not available. Install playwright: pip install playwright && playwright install chromium"
        
        elif action == "download_file":
            if COMPUTER_USE_AVAILABLE:
                try:
                    # Parse url|filename format
                    parts = action_input.split("|", 1)
                    url = parts[0].strip()
                    filename = parts[1].strip() if len(parts) > 1 else None
                    
                    print(f"\n⬇️ Downloading: {url}")
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: asyncio.run(download_file_from_web(url, filename))
                    )
                    if result.get("success"):
                        return f"✅ File downloaded: {result.get('file_path', 'downloads folder')}"
                    return f"❌ Download failed: {result.get('error', 'Unknown error')}"
                except Exception as e:
                    return f"❌ Download error: {str(e)}"
            return "❌ Computer Use not available. Install playwright: pip install playwright && playwright install chromium"
        
        # ============================================
        # GOOGLE WORKSPACE TOOLS
        # ============================================
        elif action == "gmail_search":
            try:
                gws = self._get_gws_client()
                if gws:
                    result = gws.search_gmail(action_input)
                    if result.get("success"):
                        return f"✅ Gmail search results:\n{result.get('output', 'No results')}"
                    return f"❌ Gmail search failed: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Gmail search error: {str(e)}"
        
        elif action == "gmail_send":
            try:
                # Parse to|subject|body format
                parts = action_input.split("|", 2)
                if len(parts) < 3:
                    return "❌ Format salah. Gunakan: gmail_send(to@email.com|Subject|Body)"
                to = parts[0].strip()
                subject = parts[1].strip()
                body = parts[2].strip()
                
                gws = self._get_gws_client()
                if gws:
                    result = gws.send_email(to, subject, body)
                    if result.get("success"):
                        return f"✅ Email sent to {to}: {subject}"
                    return f"❌ Failed to send email: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Gmail send error: {str(e)}"
        
        elif action == "gmail_draft":
            try:
                # Parse to|subject|body format
                parts = action_input.split("|", 2)
                if len(parts) < 3:
                    return "❌ Format salah. Gunakan: gmail_draft(to@email.com|Subject|Body)"
                to = parts[0].strip()
                subject = parts[1].strip()
                body = parts[2].strip()
                
                gws = self._get_gws_client()
                if gws:
                    result = gws.create_gmail_draft(to, subject, body)
                    if result.get("success"):
                        return f"✅ Draft created: {subject}"
                    return f"❌ Failed to create draft: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Gmail draft error: {str(e)}"
        
        elif action == "drive_list":
            try:
                gws = self._get_gws_client()
                if gws:
                    result = gws.search_drive_files(action_input or "*")
                    if result.get("success"):
                        return f"✅ Drive files:\n{result.get('output', 'No files found')}"
                    return f"❌ Drive list failed: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Drive list error: {str(e)}"
        
        elif action == "drive_create":
            try:
                # Parse filename|content format
                parts = action_input.split("|", 1)
                if len(parts) < 2:
                    return "❌ Format salah. Gunakan: drive_create(filename.txt|content)"
                filename = parts[0].strip()
                content = parts[1].strip()
                
                gws = self._get_gws_client()
                if gws:
                    result = gws.create_drive_file(filename, content)
                    if result.get("success"):
                        return f"✅ File created in Drive: {filename}"
                    return f"❌ Failed to create file: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Drive create error: {str(e)}"
        
        elif action == "calendar_list":
            try:
                gws = self._get_gws_client()
                if gws:
                    result = gws.list_events()
                    if result.get("success"):
                        return f"✅ Calendar events:\n{result.get('output', 'No events')}"
                    return f"❌ Calendar list failed: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Calendar list error: {str(e)}"
        
        elif action == "calendar_add":
            try:
                gws = self._get_gws_client()
                if gws:
                    result = gws.quick_add_event(action_input)
                    if result.get("success"):
                        return f"✅ Event added: {action_input}"
                    return f"❌ Failed to add event: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Calendar add error: {str(e)}"
        
        elif action == "sheets_read":
            try:
                # Parse spreadsheetId|range format
                parts = action_input.split("|", 1)
                if len(parts) < 2:
                    return "❌ Format salah. Gunakan: sheets_read(spreadsheetId|A1:D10)"
                spreadsheet_id = parts[0].strip()
                range_str = parts[1].strip()
                
                gws = self._get_gws_client()
                if gws:
                    result = gws.read_sheet_values(spreadsheet_id, range_str)
                    if result.get("success"):
                        return f"✅ Sheet data:\n{result.get('output', 'No data')}"
                    return f"❌ Sheets read failed: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Sheets read error: {str(e)}"
        
        elif action == "sheets_write":
            try:
                # Parse spreadsheetId|range|values format
                parts = action_input.split("|", 2)
                if len(parts) < 3:
                    return "❌ Format salah. Gunakan: sheets_write(spreadsheetId|A1|[[\"data1\",\"data2\"]])"
                spreadsheet_id = parts[0].strip()
                range_str = parts[1].strip()
                values_str = parts[2].strip()
                
                import json
                try:
                    values = json.loads(values_str)
                except:
                    values = [[values_str]]
                
                gws = self._get_gws_client()
                if gws:
                    result = gws.write_sheet_values(spreadsheet_id, range_str, values)
                    if result.get("success"):
                        return f"✅ Data written to sheet at {range_str}"
                    return f"❌ Sheets write failed: {result.get('error', 'Unknown error')}"
                return "❌ Google Workspace not available"
            except Exception as e:
                return f"❌ Sheets write error: {str(e)}"
        
        # ============================================
        # FINISH / RESPOND TOOLS
        # ============================================
        elif action == "finish":
            return f"✅ Task completed: {action_input}"
        
        elif action == "respond":
            return f"📝 Response: {action_input}"
        
        # ============================================
        # UNKNOWN ACTION
        # ============================================
        else:
            available_tools = [
                "web_search", "search_component", 
                "open_app", "close_app", "screenshot",
                "play_youtube", "search_youtube", "youtube_results",
                "browse", "search_google",
                "run_python", "install_package",
                "create_word", "create_pdf", "create_txt", "create_markdown", "create_json", "create_excel",
                "generate_schematic", 
                "journal_search", "ytplay_vision", "browse_interact", "download_file",  # Computer Use
                "gmail_search", "gmail_send", "gmail_draft", "drive_list", "drive_create",  # Google Workspace
                "calendar_list", "calendar_add", "sheets_read", "sheets_write",  # Google Workspace
                "finish", "respond"
            ]
            return f"❌ Unknown action: {action}\nAvailable tools: {', '.join(available_tools)}"


# ============================================
# WEB SEARCH TOOL
# ============================================

class WebSearchTool:
    """Web search using Tavily API."""
    
    # Domain untuk pencarian elektronik
    ELECTRONICS_DOMAINS = [
        "electronics-tutorials.ws", "sparkfun.com", 
        "adafruit.com", "arduino.cc", "espressif.com",
        "randomnerdtutorials.com", "instructables.com",
        "hackaday.com", "allaboutcircuits.com",
        "electronicshub.org", "circuitdigest.com"
    ]
    
    def __init__(self):
        from tavily import TavilyClient
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5, electronics_only: bool = True) -> list[dict]:
        """Perform web search.
        
        Args:
            query: Search query
            max_results: Max results to return
            electronics_only: If True, filter to electronics domains. If False, search all web.
        """
        try:
            search_params = {
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            }
            
            # Hanya filter domain jika electronics_only=True
            if electronics_only:
                search_params["include_domains"] = self.ELECTRONICS_DOMAINS
            
            response = self.client.search(**search_params)
            return response.get("results", [])
        except Exception as e:
            print_status("❌", f"Search error: {e}", Colors.RED)
            return []
    
    def search_general(self, query: str, max_results: int = 5) -> list[dict]:
        """Perform general web search tanpa filter domain."""
        return self.search(query, max_results, electronics_only=False)
    
    def search_component(self, component: str) -> str:
        """Search for component info, pinout, datasheet."""
        queries = [
            f"{component} pinout diagram connections",
            f"{component} circuit schematic example",
        ]
        
        all_results = []
        for q in queries:
            results = self.search(q, max_results=3)
            all_results.extend(results)
        
        # Format results
        context = []
        seen_urls = set()
        for r in all_results:
            if r.get("url") not in seen_urls:
                seen_urls.add(r.get("url"))
                context.append(f"• {r.get('title', 'No title')}\n  {r.get('content', '')[:300]}...")
        
        return "\n\n".join(context[:6])
    
    def search_circuit(self, description: str) -> str:
        """Search for circuit design info."""
        query = f"circuit schematic design {description} tutorial example"
        results = self.search(query, max_results=8)
        
        context = []
        for r in results:
            context.append(f"• {r.get('title', '')}\n  URL: {r.get('url', '')}\n  {r.get('content', '')[:400]}")
        
        return "\n\n".join(context)


# ============================================
# DEEP RESEARCH TOOL
# ============================================

class DeepResearchTool:
    """Deep research using multi-step search and analysis."""
    
    def __init__(self, gemini_client):
        self.gemini = gemini_client
        self.search = None
        try:
            self.search = WebSearchTool()
        except Exception as e:
            print_status("⚠️", f"Web search not available: {e}", Colors.YELLOW)
    
    async def research_circuit(self, topic: str) -> dict:
        """
        Deep research a circuit design topic.
        Returns comprehensive research with components, connections, best practices.
        """
        from pydantic import BaseModel, Field
        from typing import Optional
        from langchain_core.messages import HumanMessage, SystemMessage
        
        print_section("🔬 DEEP RESEARCH MODE")
        print_status("📋", f"Topic: {topic}", Colors.CYAN)
        
        # Step 1: Generate sub-questions
        print_status("📋", "Generating research questions...", Colors.YELLOW)
        
        class ResearchQuestions(BaseModel):
            questions: list[str] = Field(description="List of specific research questions")
            components_to_research: list[str] = Field(description="Components to look up")
        
        question_prompt = f"""Kamu adalah peneliti elektronika. Untuk topik berikut, generate:
1. 3-5 pertanyaan spesifik yang perlu dijawab untuk merancang rangkaian
2. Daftar komponen yang perlu diteliti

Topik: {topic}

Fokus pada:
- Komponen apa saja yang dibutuhkan
- Bagaimana koneksi antar komponen
- Best practices dan common mistakes
- Spesifikasi tegangan/arus yang tepat"""
        
        try:
            questions: ResearchQuestions = await self.gemini.invoke_with_rotation(
                [HumanMessage(content=question_prompt)],
                ResearchQuestions
            )
            
            print(f"\n{Colors.BOLD}Research Questions:{Colors.ENDC}")
            for i, q in enumerate(questions.questions, 1):
                print(f"   {i}. {q}")
            
            print(f"\n{Colors.BOLD}Components to Research:{Colors.ENDC}")
            for c in questions.components_to_research:
                print(f"   • {c}")
            
        except Exception as e:
            print_status("⚠️", f"Question generation failed: {e}", Colors.YELLOW)
            questions = ResearchQuestions(
                questions=[f"How to design {topic}?"],
                components_to_research=[]
            )
        
        # Step 2: Web search for each question
        search_context = ""
        if self.search:
            print_status("🌐", "Searching web for information...", Colors.YELLOW)
            
            all_search_results = []
            
            # Search main topic
            results = self.search.search_circuit(topic)
            if results:
                all_search_results.append(f"=== Circuit Design: {topic} ===\n{results}")
            
            # Search each component
            for comp in questions.components_to_research[:4]:
                print_status("🔍", f"Researching: {comp}", Colors.DIM)
                comp_info = self.search.search_component(comp)
                if comp_info:
                    all_search_results.append(f"=== Component: {comp} ===\n{comp_info}")
            
            search_context = "\n\n".join(all_search_results)
            
            if search_context:
                print_status("✅", f"Collected {len(all_search_results)} research sections", Colors.GREEN)
        else:
            print_status("⚠️", "Web search unavailable, using AI knowledge only", Colors.YELLOW)
        
        # Step 3: Synthesize research into design recommendations
        print_status("🧠", "Synthesizing research...", Colors.YELLOW)
        
        class ResearchReport(BaseModel):
            summary: str = Field(description="Ringkasan hasil riset")
            recommended_components: list[dict] = Field(
                description="Komponen yang direkomendasikan [{name, value, reason}]"
            )
            connection_guidelines: list[str] = Field(
                description="Panduan koneksi penting"
            )
            best_practices: list[str] = Field(
                description="Best practices dari riset"
            )
            warnings: list[str] = Field(
                description="Peringatan dan common mistakes"
            )
            schematic_recommendation: str = Field(
                description="Rekomendasi final untuk desain skematik"
            )
        
        synthesis_prompt = f"""Kamu adalah ahli elektronika yang sedang menganalisis hasil riset.

TOPIK RISET: {topic}

RESEARCH QUESTIONS:
{chr(10).join(questions.questions)}

WEB SEARCH RESULTS:
{search_context if search_context else "No web search results available - use your knowledge"}

TUGAS: Berdasarkan riset di atas, berikan:
1. Ringkasan temuan penting
2. Komponen yang direkomendasikan beserta nilainya (resistor value, capacitor value, dll)
3. Panduan koneksi yang benar
4. Best practices
5. Peringatan/common mistakes yang harus dihindari
6. Rekomendasi final untuk desain skematik

Pastikan rekomendasi SPESIFIK dan ACTIONABLE untuk membuat rangkaian."""
        
        try:
            report: ResearchReport = await self.gemini.invoke_with_rotation(
                [HumanMessage(content=synthesis_prompt)],
                ResearchReport
            )
            
            # Print report
            print_section("📊 RESEARCH REPORT")
            
            print(f"{Colors.BOLD}📋 Summary:{Colors.ENDC}")
            print(f"   {report.summary}\n")
            
            print(f"{Colors.BOLD}📦 Recommended Components:{Colors.ENDC}")
            for comp in report.recommended_components:
                name = comp.get('name', 'Unknown')
                value = comp.get('value', '')
                reason = comp.get('reason', '')
                print(f"   • {name} ({value}): {reason}")
            
            print(f"\n{Colors.BOLD}🔌 Connection Guidelines:{Colors.ENDC}")
            for g in report.connection_guidelines:
                print(f"   • {g}")
            
            print(f"\n{Colors.BOLD}✅ Best Practices:{Colors.ENDC}")
            for bp in report.best_practices:
                print(f"   • {bp}")
            
            print(f"\n{Colors.BOLD}⚠️ Warnings:{Colors.ENDC}")
            for w in report.warnings:
                print(f"   {Colors.YELLOW}• {w}{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}🎯 Schematic Recommendation:{Colors.ENDC}")
            print(f"   {report.schematic_recommendation}")
            
            return {
                "report": report,
                "search_context": search_context,
                "questions": questions,
            }
            
        except Exception as e:
            print_status("❌", f"Synthesis failed: {e}", Colors.RED)
            return {"error": str(e)}

# ============================================
# GEMINI WITH ROTATION
# ============================================

class GeminiWithRotation:
    """Wrapper untuk ChatGoogleGenerativeAI dengan API key rotation."""
    
    def __init__(self, api_keys: list[str], model: str = "gemini-3-flash-preview"):
        self.api_keys = api_keys
        self.model = model
        self.current_index = 0
        self.rate_limited_keys: dict[str, float] = {}
        self.max_retries = len(api_keys) * 2
        
    def get_next_key(self) -> str:
        """Get next available API key."""
        now = time.time()
        attempts = 0
        
        while attempts < len(self.api_keys):
            key = self.api_keys[self.current_index]
            
            if key in self.rate_limited_keys:
                if now < self.rate_limited_keys[key]:
                    self.current_index = (self.current_index + 1) % len(self.api_keys)
                    attempts += 1
                    continue
                else:
                    del self.rate_limited_keys[key]
            
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            return key
        
        if self.rate_limited_keys:
            min_key = min(self.rate_limited_keys, key=self.rate_limited_keys.get)
            wait_time = self.rate_limited_keys[min_key] - now
            if wait_time > 0:
                print_status("⏳", f"Semua key rate-limited. Menunggu {wait_time:.0f}s...", Colors.YELLOW)
                time.sleep(wait_time + 1)
            return min_key
        
        raise RuntimeError("No API keys available")
    
    def mark_rate_limited(self, key: str, cooldown_seconds: int = 60):
        """Mark key as rate-limited."""
        self.rate_limited_keys[key] = time.time() + cooldown_seconds
        key_index = self.api_keys.index(key) + 1
        print_status("🔒", f"Key #{key_index} rate-limited, trying another...", Colors.YELLOW)
    
    def create_llm(self, api_key: str):
        """Create LLM instance."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=self.model,
            google_api_key=api_key,
            temperature=0.3,
            convert_system_message_to_human=True,
        )
    
    async def invoke_with_rotation(self, messages, output_schema, max_retries: int = None):
        """Invoke AI with automatic key rotation."""
        from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
        import re
        
        max_retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            api_key = self.get_next_key()
            key_num = self.api_keys.index(api_key) + 1
            
            try:
                llm = self.create_llm(api_key)
                structured_llm = llm.with_structured_output(output_schema)
                result = await structured_llm.ainvoke(messages)
                return result
                
            except ChatGoogleGenerativeAIError as e:
                error_str = str(e)
                last_error = e
                
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    retry_match = re.search(r'retry.*?(\d+\.?\d*)s', error_str.lower())
                    cooldown = int(float(retry_match.group(1))) + 5 if retry_match else 60
                    self.mark_rate_limited(api_key, cooldown)
                    continue
                elif "API_KEY_INVALID" in error_str:
                    self.rate_limited_keys[api_key] = float('inf')
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                continue
        
        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")
    
    async def invoke_raw(self, messages, max_retries: int = None) -> str:
        """Invoke AI for raw text response (no structured output)."""
        from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
        import re
        
        max_retries = max_retries or self.max_retries
        last_error = None
        
        for attempt in range(max_retries):
            api_key = self.get_next_key()
            
            try:
                llm = self.create_llm(api_key)
                result = await llm.ainvoke(messages)
                return result.content
                
            except ChatGoogleGenerativeAIError as e:
                error_str = str(e)
                last_error = e
                
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    retry_match = re.search(r'retry.*?(\d+\.?\d*)s', error_str.lower())
                    cooldown = int(float(retry_match.group(1))) + 5 if retry_match else 60
                    self.mark_rate_limited(api_key, cooldown)
                    continue
                elif "API_KEY_INVALID" in error_str:
                    self.rate_limited_keys[api_key] = float('inf')
                    continue
                else:
                    raise
            except Exception as e:
                last_error = e
                continue
        
        raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")


# ============================================
# ENHANCED SYSTEM PROMPT WITH RESEARCH
# ============================================

def get_system_prompt(research_context: str = "") -> str:
    """Get enhanced system prompt, optionally with research context."""
    
    research_section = ""
    if research_context:
        research_section = f"""
═══════════════════════════════════════════════════════════════════
RESEARCH CONTEXT (USE THIS INFORMATION FOR ACCURATE DESIGN):
═══════════════════════════════════════════════════════════════════
{research_context}

PENTING: Gunakan informasi dari research di atas untuk menentukan:
- Nilai komponen yang tepat (resistor, capacitor values)
- Best practices untuk koneksi
- Hindari common mistakes yang disebutkan

"""

    return f"""Kamu adalah JAWIR OS - AI Assistant Jawa Terkuat dari Ngawi.
Kamu ahli desain elektronika dan hardware.

Kamu memiliki berbagai TOOLS:
- KiCad Tool: Generate schematic dari natural language
- Web Search Tool: Cari informasi komponen dan tutorial
- Research Tool: Deep research sebelum desain

SEKARANG kamu menggunakan KiCad Tool.
TUGAS: Desain skematik KiCad yang BENAR secara elektrikal dan sesuai kaidah.
{research_section}
═══════════════════════════════════════════════════════════════════
ATURAN REFERENCE NAMING (SANGAT WAJIB - TIDAK BOLEH DILANGGAR):
═══════════════════════════════════════════════════════════════════
🚨 KRITIS: SETIAP komponen HARUS punya reference UNIK dengan NOMOR!
🚨 DILARANG KERAS menggunakan "?" dalam reference!

PREFIX BERDASARKAN TIPE:
• Resistor     → R1, R2, R3, dst (BUKAN R?, R??, atau hanya R)
• Kapasitor    → C1, C2, C3, dst
• LED          → D1, D2, D3, dst (BUKAN D? atau LED1)
• IC/MCU       → U1, U2, dst
• Transistor   → Q1, Q2, dst
• Connector    → J1, J2, dst
• Button/Switch→ SW1, SW2, dst
• Sensor       → U1, U2, dst (gunakan prefix U untuk sensor module)
• VCC          → #PWR01 atau langsung "VCC" (khusus power symbol)
• GND          → #PWR02 atau langsung "GND" (khusus power symbol)

CONTOH BENAR vs SALAH:
✅ BENAR: R1, R2, D1, D2, U1, C1, SW1
❌ SALAH: R?, D?, R, D, resistor1, LED1

═══════════════════════════════════════════════════════════════════
LANGKAH WAJIB SEBELUM DESAIN (Chain of Thought):
═══════════════════════════════════════════════════════════════════
1. ANALISIS permintaan user - apa tujuan rangkaian?
2. IDENTIFIKASI komponen yang dibutuhkan DAN tentukan REFERENCE-nya
3. TENTUKAN koneksi berdasarkan datasheet/spesifikasi
4. VALIDASI setiap reference UNIK dan tidak ada "?"

═══════════════════════════════════════════════════════════════════
KOMPONEN TERSEDIA & PIN MAPPING DETAIL:
═══════════════════════════════════════════════════════════════════

📦 RESISTOR (type: "resistor", prefix: R)
   • 2-pin komponen VERTIKAL
   • pin1 = terminal ATAS (posisi relatif: y=-3.81mm dari center)
   • pin2 = terminal BAWAH (posisi relatif: y=+3.81mm dari center)
   • Value: ohm (contoh: "330", "1k", "10k", "4.7k")
   • Gunakan: R1, R2, R3, dst

📦 LED (type: "led", prefix: D)
   • 2-pin komponen HORIZONTAL
   • pin1 = CATHODE (K, terminal negatif) - di KIRI (x=-3.81mm)
   • pin2 = ANODE (A, terminal positif) - di KANAN (x=+3.81mm)
   • Value: warna (contoh: "Red", "Green", "Blue", "Yellow")
   • Arus mengalir: Anode(+/pin2) → Cathode(-/pin1)
   • Gunakan: D1, D2, D3, dst

📦 CAPACITOR (type: "capacitor", prefix: C)
   • 2-pin komponen VERTIKAL
   • pin1 = terminal ATAS, pin2 = terminal BAWAH
   • Value: farad (contoh: "100nF", "10uF", "100uF")
   • Gunakan: C1, C2, C3, dst

📦 DHT11 (type: "dht11", prefix: U)
   • 4-pin sensor, pins di sisi KIRI
   • pin1 = VCC (3.3V-5V)
   • pin2 = DATA (digital output ke GPIO)
   • pin3 = NC (tidak digunakan)
   • pin4 = GND
   • Gunakan: U2 (setelah ESP32 yang U1)

📦 HC-SR04 (type: "hcsr04", prefix: U)
   • 4-pin ultrasonic sensor, pins di sisi KIRI
   • pin1 = VCC (5V saja!)
   • pin2 = TRIG (GPIO output untuk trigger)
   • pin3 = ECHO (GPIO input untuk echo)
   • pin4 = GND
   • Gunakan: U2, U3, dst

📦 BUTTON (type: "button", prefix: SW)
   • 2-pin momentary switch HORIZONTAL
   • pin1 = terminal KIRI (x=-5.08mm)
   • pin2 = terminal KANAN (x=+5.08mm)
   • Gunakan: SW1, SW2, dst

📦 NPN TRANSISTOR (type: "npn", prefix: Q)
   • 3-pin transistor
   • pin1 = BASE (B) - kontrol input
   • pin2 = COLLECTOR (C) - ke load/VCC
   • pin3 = EMITTER (E) - ke GND
   • Gunakan: Q1, Q2, dst

📦 ESP32 (type: "esp32", prefix: U)
   • Microcontroller 38 pins
   • Reference: selalu U1
   • PINS KIRI (masuk dari x=-15.24mm):
     - pin1=GND, pin2=3V3, pin3=EN
     - pin4=VP(GPIO36), pin5=VN(GPIO39)
     - pin6=IO34, pin7=IO35, pin8=IO32, pin9=IO33
     - pin10=IO25, pin11=IO26, pin12=IO27
     - pin13=IO14, pin14=IO12, pin15=GND2, pin16=IO13
   • PINS KANAN (masuk dari x=+15.24mm):
     - pin24=IO2, pin25=IO0, pin26=IO4
     - pin27=IO16, pin28=IO17, pin29=IO5
     - pin30=IO18, pin31=IO19, pin33=IO21
     - pin34=RXD0, pin35=TXD0, pin36=IO22(SCL), pin37=IO23(SDA)

📦 POWER SYMBOLS:
   • VCC (type: "vcc"): pin1 = power output (+3.3V/+5V)
   • GND (type: "gnd"): pin1 = ground (0V)
   • Reference: gunakan "VCC" dan "GND" langsung

═══════════════════════════════════════════════════════════════════
KOMPONEN TAMBAHAN (IOT SENSORS & MODULES):
═══════════════════════════════════════════════════════════════════

📦 DHT22 (type: "dht22", prefix: U) - Higher precision temp/humidity
   • pin1=VCC (3.3V-5V), pin2=DATA, pin3=NC, pin4=GND
   • Sama seperti DHT11 tapi lebih akurat

📦 BMP280 (type: "bmp280", prefix: U) - Pressure/Temperature I2C
   • pin1=VCC, pin2=GND, pin3=SCL, pin4=SDA
   • I2C Address: 0x76 atau 0x77

📦 PIR (type: "pir", prefix: U) - Motion Sensor HC-SR501
   • pin1=VCC (5V), pin2=OUT (ke GPIO), pin3=GND

📦 LDR (type: "ldr", prefix: R) - Light Sensor
   • 2-pin seperti resistor, gunakan dengan voltage divider
   • pin1=terminal ATAS, pin2=terminal BAWAH

📦 OLED_SSD1306 (type: "oled_ssd1306", prefix: U) - 0.96" Display
   • pin1=GND, pin2=VCC, pin3=SCL, pin4=SDA
   • I2C Address: 0x3C

📦 SERVO (type: "servo", prefix: M) - SG90/MG996R
   • pin1=GND (coklat), pin2=VCC (merah), pin3=SIG (oranye/PWM)

📦 BUZZER (type: "buzzer", prefix: BZ)
   • 2-pin, pin1=+ (ke GPIO/VCC), pin2=- (ke GND)

📦 RELAY (type: "relay", prefix: K) - 1 Channel Module
   • pin1=VCC, pin2=GND, pin3=IN (trigger dari GPIO)
   • pin4=COM, pin5=NO (normally open), pin6=NC (normally closed)

📦 L298N (type: "l298n", prefix: U) - Motor Driver
   • pin1=VCC, pin2=GND, pin3=5V (output)
   • pin4=ENA, pin5=IN1, pin6=IN2, pin7=IN3, pin8=IN4, pin9=ENB
   • pin10=OUT1, pin11=OUT2, pin12=OUT3, pin13=OUT4

📦 SOIL_MOISTURE (type: "soil_moisture", prefix: U)
   • pin1=VCC, pin2=GND, pin3=DO (digital), pin4=AO (analog)

📦 MQ2 (type: "mq2", prefix: U) - Gas/Smoke Sensor
   • pin1=VCC, pin2=GND, pin3=DO (digital), pin4=AO (analog)

📦 POTENTIOMETER (type: "potentiometer", prefix: RV)
   • 3-pin variable resistor
   • pin1=bottom (GND), pin2=wiper (ke ADC), pin3=top (VCC)

📦 IR_RECEIVER (type: "ir_receiver", prefix: U) - VS1838B
   • pin1=OUT (ke GPIO), pin2=GND, pin3=VCC

═══════════════════════════════════════════════════════════════════
KAIDAH RANGKAIAN LED (SANGAT PENTING):
═══════════════════════════════════════════════════════════════════
LED WAJIB pakai RESISTOR untuk membatasi arus!

URUTAN KONEKSI LED:
  ESP32 GPIO (pin10=IO25) → R1.pin1 → R1.pin2 → D1.pin2(Anode) → D1.pin1(Cathode) → GND

Dalam bentuk wires:
  1. U1.pin10 → R1.pin1 (GPIO ke resistor atas)
  2. R1.pin2 → D1.pin2 (resistor bawah ke LED anode)  
  3. D1.pin1 → GND.pin1 (LED cathode ke ground)

RUMUS RESISTOR: R = (Vcc - Vled) / Iled
  - LED Merah: Vled=2V, Iled=20mA → R=(3.3-2)/0.02=65Ω → pakai 220Ω
  - LED Hijau: Vled=2.2V → pakai 220Ω
  - Aman: 220-330 ohm untuk 3.3V, 330-1K untuk 5V

═══════════════════════════════════════════════════════════════════
CONTOH LENGKAP - ESP32 + 2 LED (MERAH & HIJAU):
═══════════════════════════════════════════════════════════════════

DESIGN GOAL: ESP32 mengendalikan 2 LED (merah di GPIO25, hijau di GPIO26)

components: [
  {{"type": "esp32", "reference": "U1", "value": "ESP32-WROOM-32", "position": {{"x": 180, "y": 100}}}},
  {{"type": "resistor", "reference": "R1", "value": "220", "position": {{"x": 100, "y": 60}}}},
  {{"type": "resistor", "reference": "R2", "value": "220", "position": {{"x": 100, "y": 100}}}},
  {{"type": "led", "reference": "D1", "value": "Red", "position": {{"x": 60, "y": 60}}}},
  {{"type": "led", "reference": "D2", "value": "Green", "position": {{"x": 60, "y": 100}}}},
  {{"type": "vcc", "reference": "VCC", "value": "3.3V", "position": {{"x": 180, "y": 30}}}},
  {{"type": "gnd", "reference": "GND", "value": "GND", "position": {{"x": 60, "y": 140}}}}
]

wires: [
  {{"from": {{"component": "U1", "pin": 2}}, "to": {{"component": "VCC", "pin": 1}}}},
  {{"from": {{"component": "U1", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}},
  {{"from": {{"component": "U1", "pin": 10}}, "to": {{"component": "R1", "pin": 1}}}},
  {{"from": {{"component": "R1", "pin": 2}}, "to": {{"component": "D1", "pin": 2}}}},
  {{"from": {{"component": "D1", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}},
  {{"from": {{"component": "U1", "pin": 11}}, "to": {{"component": "R2", "pin": 1}}}},
  {{"from": {{"component": "R2", "pin": 2}}, "to": {{"component": "D2", "pin": 2}}}},
  {{"from": {{"component": "D2", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}}
]

═══════════════════════════════════════════════════════════════════
🎯 CONTOH LENGKAP - ESP32 + DHT11 SENSOR (WIRING BENAR):
═══════════════════════════════════════════════════════════════════

components: [
  {{"type": "esp32", "reference": "U1", "value": "ESP32-WROOM-32", "position": {{"x": 180, "y": 100}}}},
  {{"type": "dht11", "reference": "U2", "value": "DHT11", "position": {{"x": 80, "y": 80}}}},
  {{"type": "resistor", "reference": "R1", "value": "10k", "position": {{"x": 50, "y": 50}}}},
  {{"type": "vcc", "reference": "VCC", "value": "3.3V", "position": {{"x": 80, "y": 30}}}},
  {{"type": "gnd", "reference": "GND", "value": "GND", "position": {{"x": 80, "y": 130}}}}
]

wires: [
  // POWER CONNECTIONS - VCC/GND ke sensor (SANGAT PENTING!)
  {{"from": {{"component": "VCC", "pin": 1}}, "to": {{"component": "U2", "pin": 1}}}},   // VCC → DHT11.VCC ✅
  {{"from": {{"component": "U2", "pin": 4}}, "to": {{"component": "GND", "pin": 1}}}},   // DHT11.GND → GND ✅
  // PULL-UP RESISTOR untuk DATA
  {{"from": {{"component": "VCC", "pin": 1}}, "to": {{"component": "R1", "pin": 1}}}},   // VCC → Resistor
  {{"from": {{"component": "R1", "pin": 2}}, "to": {{"component": "U2", "pin": 2}}}},    // Resistor → DATA
  // DATA CONNECTION ke GPIO
  {{"from": {{"component": "U2", "pin": 2}}, "to": {{"component": "U1", "pin": 26}}}},   // DHT11.DATA → GPIO4 ✅
  // ESP32 POWER
  {{"from": {{"component": "VCC", "pin": 1}}, "to": {{"component": "U1", "pin": 2}}}},   // VCC → ESP32.3V3
  {{"from": {{"component": "U1", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}}    // ESP32.GND → GND
]

═══════════════════════════════════════════════════════════════════
🎯 CONTOH LENGKAP - ESP32 + PIR SENSOR (WIRING BENAR):
═══════════════════════════════════════════════════════════════════

components: [
  {{"type": "esp32", "reference": "U1", "value": "ESP32-WROOM-32", "position": {{"x": 180, "y": 100}}}},
  {{"type": "pir", "reference": "U2", "value": "HC-SR501", "position": {{"x": 80, "y": 80}}}},
  {{"type": "vcc", "reference": "VCC", "value": "5V", "position": {{"x": 80, "y": 30}}}},
  {{"type": "gnd", "reference": "GND", "value": "GND", "position": {{"x": 80, "y": 130}}}}
]

wires: [
  // POWER CONNECTIONS
  {{"from": {{"component": "VCC", "pin": 1}}, "to": {{"component": "U2", "pin": 1}}}},   // VCC 5V → PIR.VCC ✅
  {{"from": {{"component": "U2", "pin": 3}}, "to": {{"component": "GND", "pin": 1}}}},   // PIR.GND → GND ✅
  // DATA CONNECTION
  {{"from": {{"component": "U2", "pin": 2}}, "to": {{"component": "U1", "pin": 26}}}},   // PIR.OUT → GPIO4 ✅
  // ESP32 POWER
  {{"from": {{"component": "VCC", "pin": 1}}, "to": {{"component": "U1", "pin": 2}}}},   // VCC → ESP32.3V3
  {{"from": {{"component": "U1", "pin": 1}}, "to": {{"component": "GND", "pin": 1}}}}    // ESP32.GND → GND
]

═══════════════════════════════════════════════════════════════════
🔴🔴🔴 ATURAN KONEKSI POWER - SANGAT KRITIS!!! 🔴🔴🔴
═══════════════════════════════════════════════════════════════════
KESALAHAN UMUM: VCC/GND terhubung ke GPIO → SALAH TOTAL!
VCC dan GND adalah POWER SUPPLY, BUKAN sinyal kontrol!

📌 ATURAN EMAS KONEKSI POWER:

1️⃣ PIN VCC SENSOR → HANYA ke power supply (VCC symbol atau ESP32.pin2=3V3)
   ✅ BENAR: DHT11.pin1(VCC) → VCC.pin1  (power ke power)
   ✅ BENAR: DHT11.pin1(VCC) → U1.pin2   (ke 3V3 ESP32)
   ❌ SALAH: DHT11.pin1(VCC) → U1.pin26  (GPIO4 bukan power!)
   ❌ SALAH: DHT11.pin1(VCC) → U1.pin10  (GPIO25 bukan power!)

2️⃣ PIN GND SENSOR → HANYA ke GND symbol atau ESP32.pin1(GND)
   ✅ BENAR: DHT11.pin4(GND) → GND.pin1  (ground ke ground)
   ✅ BENAR: DHT11.pin4(GND) → U1.pin1   (ke GND ESP32)
   ❌ SALAH: DHT11.pin4(GND) → U1.pin26  (GPIO bukan GND!)
   ❌ SALAH: DHT11.pin4(GND) → U1.pin10  (IO25 bukan GND!)

3️⃣ PIN DATA/SIGNAL → HANYA ke GPIO
   ✅ BENAR: DHT11.pin2(DATA) → U1.pin26  (DATA ke GPIO4)
   ❌ SALAH: DHT11.pin2(DATA) → VCC.pin1  (signal ke power!)
   ❌ SALAH: DHT11.pin2(DATA) → GND.pin1  (signal ke ground!)

═══════════════════════════════════════════════════════════════════
🔌 REFERENSI PIN POWER ESP32 (HAFAL INI!):
═══════════════════════════════════════════════════════════════════
• ESP32.pin1  = GND   (untuk ground semua sensor)
• ESP32.pin2  = 3V3   (untuk VCC sensor 3.3V)
• ESP32.pin15 = GND2  (alternatif ground)
• ESP32.pin38 = GND3  (alternatif ground)

🚫 ESP32.pin10 s.d pin14, pin24-pin37 = GPIO (BUKAN POWER!)
🚫 JANGAN PERNAH hubungkan VCC sensor ke GPIO!
🚫 JANGAN PERNAH hubungkan GND sensor ke GPIO!

═══════════════════════════════════════════════════════════════════
📋 TABEL KONEKSI SENSOR STANDAR (GUNAKAN INI):
═══════════════════════════════════════════════════════════════════

🌡️ DHT11/DHT22 (Suhu & Kelembaban):
   • pin1 (VCC)  → VCC.pin1 atau U1.pin2 (3V3)
   • pin2 (DATA) → U1.pin26 (GPIO4) + pull-up resistor 10K
   • pin3 (NC)   → tidak dihubungkan
   • pin4 (GND)  → GND.pin1 atau U1.pin1 (GND)

📏 HC-SR04 (Ultrasonik - BUTUH 5V!):
   • pin1 (VCC)  → VCC.pin1 (5V - bukan 3V3!)
   • pin2 (TRIG) → U1.pin26 (GPIO4 - output)
   • pin3 (ECHO) → U1.pin27 (GPIO16 - input, pakai voltage divider!)
   • pin4 (GND)  → GND.pin1

🔴 PIR HC-SR501 (Gerakan - BUTUH 5V!):
   • pin1 (VCC)  → VCC.pin1 (5V)
   • pin2 (OUT)  → U1.pin26 (GPIO4 - output 3.3V aman)
   • pin3 (GND)  → GND.pin1

🖥️ OLED SSD1306 (Display I2C):
   • pin1 (GND)  → GND.pin1
   • pin2 (VCC)  → VCC.pin1 atau U1.pin2 (3V3)
   • pin3 (SCL)  → U1.pin36 (GPIO22 - I2C clock)
   • pin4 (SDA)  → U1.pin37 (GPIO23 - I2C data)

🔧 SERVO SG90 (Motor):
   • pin1 (GND)  → GND.pin1
   • pin2 (VCC)  → VCC.pin1 (5V - eksternal lebih baik)
   • pin3 (SIG)  → U1.pin26 (GPIO4 - PWM capable)

═══════════════════════════════════════════════════════════════════
ATURAN POSISI & LAYOUT:
═══════════════════════════════════════════════════════════════════
• Canvas center = (127, 100) mm
• ESP32 (U1) di KANAN (x=160-180, y=100) - butuh area 60x60mm
• Komponen peripheral di KIRI ESP32 (x=40-120)
• VCC di ATAS (y=20-40)
• GND di BAWAH (y=140-180)
• Spacing minimum 30mm antar komponen
• LED disusun vertikal dengan spacing 40mm

═══════════════════════════════════════════════════════════════════
⚠️ VALIDATION CHECKLIST POWER (WAJIB CEK SEBELUM OUTPUT!):
═══════════════════════════════════════════════════════════════════
☑ SEMUA reference punya NOMOR (R1 bukan R?, D1 bukan D?)
☑ Reference UNIK (tidak ada duplikat)
☑ ESP32.pin2 (3V3) → terhubung ke VCC atau sensor VCC pins?
☑ ESP32.pin1 (GND) → terhubung ke GND atau sensor GND pins?
☑ SETIAP sensor VCC → ke power (VCC/3V3/5V), BUKAN ke GPIO!
☑ SETIAP sensor GND → ke ground (GND), BUKAN ke GPIO!
☑ SETIAP sensor DATA → ke GPIO yang sesuai
☑ Pin number sesuai mapping di atas?
☑ Posisi komponen tidak overlap (minimum 25mm)?

⚡ QUICK CHECK: Jika ada wire dari sensor.VCC ke U1.pin10+ → SALAH!
⚡ QUICK CHECK: Jika ada wire dari sensor.GND ke U1.pin10+ → SALAH!

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON):
═══════════════════════════════════════════════════════════════════
1. project: nama project (lowercase, underscore, contoh: "esp32_led_blink")
2. description: deskripsi singkat rangkaian
3. components: array komponen dengan reference BERNOMOR
4. wires: array koneksi dengan pin numbers
5. explanation: penjelasan edukatif (fungsi komponen, GPIO yang dipakai, cara kerja)

INGAT: JANGAN gunakan "?" dalam reference! Selalu R1, R2, D1, D2, dst."""


# ============================================
# UNIFIED ReAct RUNNER - Entry Point for ALL Requests
# ============================================

async def run_jawir_react(user_request: str, task_type: str = "auto") -> dict:
    """
    Run JAWIR dengan ReAct Agent untuk SEMUA jenis request.
    
    Ini adalah entry point utama dimana Gemini sebagai OTAK
    memutuskan tool mana yang akan digunakan.
    
    Args:
        user_request: Permintaan user dalam bahasa natural
        task_type: "auto" (detect otomatis), "schematic", "general"
    
    Returns:
        dict dengan hasil eksekusi
    """
    # Get API keys
    api_keys = []
    google_api_keys = os.getenv("GOOGLE_API_KEYS", "")
    if google_api_keys:
        api_keys = [k.strip() for k in google_api_keys.split(",") if k.strip()]
    if not api_keys:
        single_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if single_key:
            api_keys = [single_key]
    
    if not api_keys:
        print_status("❌", "API Key not found! Set GOOGLE_API_KEYS in .env", Colors.RED)
        return {"success": False, "error": "No API key"}
    
    # ============================================
    # CONVERSATIONAL MODE DETECTION
    # Gemini bisa chat biasa tanpa tools!
    # ============================================
    request_lower = user_request.lower().strip()
    
    # Pola percakapan casual yang TIDAK butuh tools
    casual_patterns = [
        # Sapaan
        r"^(hai|halo|hi|hello|hey|selamat pagi|selamat siang|selamat sore|selamat malam)",
        # Pertanyaan tentang JAWIR
        r"^(siapa kamu|kamu siapa|apa itu jawir|tentang jawir|perkenalkan dirimu)",
        # Pertanyaan umum
        r"^(gimana kabar|apa kabar|bagaimana kabarmu|lagi ngapain)",
        # Terima kasih
        r"^(terima kasih|makasih|thanks|thank you|mantap|keren|oke|ok|baik)",
        # Pertanyaan pendapat tanpa action
        r"^(menurutmu|pendapatmu|gimana menurut kamu)",
        # Curhat/sharing
        r"^(aku lagi|gue lagi|saya lagi|pengen cerita)",
    ]
    
    # Keyword yang PASTI butuh tools (override casual detection)
    tool_keywords = [
        "putar", "play", "buka", "open", "cari", "search", "download", "kirim", 
        "send", "buatkan", "create", "generate", "tolong", "please", "run", 
        "jalankan", "execute", "hitung", "rangkaian", "skematik", "youtube",
        "spotify", "email", "gmail", "drive", "calendar", "jadwal", "file",
        "screenshot", "browser", "chrome", "python", "code", "kode"
    ]
    
    # Check if it's a casual conversation
    import re
    is_casual = any(re.search(pattern, request_lower) for pattern in casual_patterns)
    needs_tools = any(kw in request_lower for kw in tool_keywords)
    
    # Jika casual DAN tidak butuh tools → langsung chat
    if is_casual and not needs_tools:
        print_status("💬", "Mode: Percakapan Biasa", Colors.CYAN)
        
        # Setup simple chat response
        gemini = GeminiWithRotation(api_keys, model="gemini-3-flash-preview")
        
        chat_prompt = """Kamu adalah JAWIR OS - AI Assistant Jawa Terkuat dari Ngawi.
Kamu ramah, santai, dan bisa diajak ngobrol biasa.
Kalau user menyapa atau chat casual, jawab dengan friendly tanpa perlu pakai tools.
Gunakan bahasa Indonesia yang natural, bisa dicampur Jawa sedikit.
Jawab singkat tapi hangat."""
        
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            response = await gemini.invoke_raw([
                SystemMessage(content=chat_prompt),
                HumanMessage(content=user_request)
            ])
            
            print(f"\n{Colors.CYAN}💬 JAWIR:{Colors.ENDC} {response}\n")
            return {
                "success": True,
                "mode": "conversational",
                "answer": response,
                "iterations": 0
            }
        except Exception as e:
            print_status("⚠️", f"Chat error: {e}", Colors.YELLOW)
            # Fall back to ReAct if chat fails
    
    # ============================================
    # TOOL MODE - Use ReAct Agent
    # ============================================
    print_status("🔧", "Mode: ReAct Agent (Tools)", Colors.CYAN)
    
    # Auto-detect task type
    if task_type == "auto":
        # Schematic keywords
        schematic_keywords = ["rangkaian", "skematik", "schematic", "esp32", "arduino", "sensor",
                           "led", "resistor", "capacitor", "transistor", "circuit", "wiring",
                           "kicad", "pcb", "desain elektronik", "buat rangkaian"]
        
        if any(kw in request_lower for kw in schematic_keywords):
            task_type = "schematic"
        else:
            task_type = "general"
    
    print_status("🔑", f"{len(api_keys)} API key(s) available", Colors.GREEN)
    print_status("🎯", f"Task type: {task_type}", Colors.DIM)
    
    # Setup LLM with rotation
    gemini = GeminiWithRotation(api_keys, model="gemini-3-flash-preview")
    
    # Run ReAct Agent
    react_agent = ReActAgent(gemini)
    result = await react_agent.run(user_request, task_type=task_type)
    
    # If this is a schematic task and we have design specs, generate the schematic
    if task_type == "schematic":
        collected = result.get("collected_info", {})
        if collected.get("design_specs", {}).get("final_spec"):
            print_status("🔧", "Design spec collected, generating schematic...", Colors.CYAN)
            # Call the actual schematic generation
            success = await generate_schematic(user_request, research_mode=False, use_react=False)
            result["schematic_generated"] = success
    
    return result


# ============================================
# MAIN GENERATION FUNCTION WITH ReAct
# ============================================

async def generate_schematic(user_request: str, research_mode: bool = False, use_react: bool = True) -> bool:
    """
    Generate KiCad schematic from user request.
    
    Args:
        user_request: Deskripsi rangkaian dari user
        research_mode: Jika True, lakukan deep research dulu
        use_react: Jika True, gunakan ReAct pattern untuk reasoning
    """
    from pydantic import BaseModel, Field
    from typing import Optional
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # Import KiCad tools
    from library_v2 import get_component_info_for_ai
    from generator_bridge import save_schematic_v2 as save_schematic, open_in_kicad
    from schemas import Position, PinReference, ComponentPlacement, WireConnection, SchematicPlan
    
    # Get API keys
    api_keys = []
    google_api_keys = os.getenv("GOOGLE_API_KEYS", "")
    if google_api_keys:
        api_keys = [k.strip() for k in google_api_keys.split(",") if k.strip()]
    if not api_keys:
        single_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if single_key:
            api_keys = [single_key]
    
    if not api_keys:
        print_status("❌", "API Key not found! Set GOOGLE_API_KEYS in .env", Colors.RED)
        return False
    
    print_status("✅", f"{len(api_keys)} API key(s) available", Colors.GREEN)
    
    # Setup LLM
    gemini = GeminiWithRotation(api_keys, model="gemini-3-flash-preview")
    
    # =========================================
    # PHASE 1: ReAct Reasoning (if enabled)
    # =========================================
    react_context = ""
    if use_react:
        react_agent = ReActAgent(gemini)
        react_result = await react_agent.run(user_request, task_type="schematic")
        
        if react_result.get("success"):
            # Collect info from ReAct reasoning
            collected = react_result.get("collected_info", {})
            
            if collected.get("components_info"):
                react_context += "\n=== COMPONENT INFO FROM RESEARCH ===\n"
                for comp in collected["components_info"]:
                    react_context += f"\n{comp['component']}:\n{comp['info'][:300]}...\n"
            
            if collected.get("search_results"):
                react_context += "\n=== WEB SEARCH RESULTS ===\n"
                for r in collected["search_results"][:3]:
                    react_context += f"- {r.get('title', '')}: {r.get('content', '')[:150]}...\n"
            
            if collected.get("design_specs", {}).get("final_spec"):
                react_context += f"\n=== DESIGN SPECIFICATION ===\n{collected['design_specs']['final_spec']}\n"
    
    # =========================================
    # PHASE 2: Deep Research (if enabled)
    # =========================================
    research_context = ""
    if research_mode:
        researcher = DeepResearchTool(gemini)
        research_result = await researcher.research_circuit(user_request)
        
        if "report" in research_result:
            report = research_result["report"]
            research_context = f"""
RESEARCH SUMMARY: {report.summary}

RECOMMENDED COMPONENTS:
{chr(10).join(f"- {c.get('name')}: {c.get('value')} ({c.get('reason')})" for c in report.recommended_components)}

CONNECTION GUIDELINES:
{chr(10).join(f"- {g}" for g in report.connection_guidelines)}

BEST PRACTICES:
{chr(10).join(f"- {bp}" for bp in report.best_practices)}

WARNINGS:
{chr(10).join(f"- {w}" for w in report.warnings)}

SCHEMATIC RECOMMENDATION: {report.schematic_recommendation}
"""
        
        print_status("✅", "Research complete, generating schematic...", Colors.GREEN)
    
    # =========================================
    # PHASE 3: Generate Schematic
    # =========================================
    
    # Schema output
    class KicadDesignOutput(BaseModel):
        project: str = Field(description="Nama project (lowercase, underscore)")
        description: Optional[str] = Field(default=None, description="Deskripsi rangkaian")
        components: list[dict] = Field(default=[], description="List komponen")
        wires: list[dict] = Field(default=[], description="List koneksi")
        explanation: str = Field(description="Penjelasan rangkaian")
    
    # Combine all context
    full_context = ""
    if react_context:
        full_context += f"\n{react_context}"
    if research_context:
        full_context += f"\n{research_context}"
    
    # Messages
    messages = [
        SystemMessage(content=get_system_prompt(full_context)),
        HumanMessage(content=f"Desain skematik: {user_request}"),
    ]
    
    print_section("🔧 GENERATING SCHEMATIC")
    print_status("📝", f"Request: {user_request}", Colors.CYAN)
    print_status("⏳", "Sending to Gemini AI...", Colors.YELLOW)
    
    try:
        # Invoke AI
        start_time = time.time()
        design: KicadDesignOutput = await gemini.invoke_with_rotation(
            messages, KicadDesignOutput
        )
        elapsed = time.time() - start_time
        
        print_status("✅", f"AI Response in {elapsed:.1f}s", Colors.GREEN)
        
        # Print results
        print_section("DESIGN RESULT")
        print(f"{Colors.BOLD}Project:{Colors.ENDC} {design.project}")
        print(f"{Colors.BOLD}Components:{Colors.ENDC} {len(design.components)}")
        print(f"{Colors.BOLD}Wires:{Colors.ENDC} {len(design.wires)}")
        
        print(f"\n{Colors.BOLD}📦 Components:{Colors.ENDC}")
        for comp in design.components:
            ref = comp.get('reference', '?')
            ctype = comp.get('type', '?')
            value = comp.get('value', '')
            print(f"   • {ref}: {ctype} ({value})")
        
        print(f"\n{Colors.BOLD}🔌 Connections:{Colors.ENDC}")
        for wire in design.wires[:8]:
            f = wire.get('from', {})
            t = wire.get('to', {})
            print(f"   • {f.get('component', '?')}.{f.get('pin', '?')} → {t.get('component', '?')}.{t.get('pin', '?')}")
        if len(design.wires) > 8:
            print(f"   ... and {len(design.wires) - 8} more connections")
        
        print_section("EXPLANATION")
        print(f"{Colors.DIM}{design.explanation}{Colors.ENDC}")
        
        # =========================================
        # POST-PROCESSING: Fix Reference Names
        # =========================================
        def fix_references(components: list[dict]) -> list[dict]:
            """Auto-fix references yang masih menggunakan '?' atau tidak ada nomor."""
            counters = {}  # Track counter per prefix
            ref_mapping = {}  # Map old ref to new ref for wire fixing
            
            fixed_components = []
            for comp in components:
                ref = comp.get("reference", "")
                comp_type = comp.get("type", "")
                
                # Determine prefix based on type
                prefix_map = {
                    "resistor": "R", "capacitor": "C", "led": "D",
                    "esp32": "U", "dht11": "U", "hcsr04": "U",
                    "npn": "Q", "pnp": "Q",
                    "button": "SW", "rotary_encoder": "SW",
                    "conn_2pin": "J", "conn_3pin": "J", "conn_4pin": "J",
                    "vcc": "VCC", "gnd": "GND"
                }
                prefix = prefix_map.get(comp_type, "U")
                
                # Check if reference needs fixing
                needs_fix = False
                if "?" in ref:
                    needs_fix = True
                elif prefix not in ["VCC", "GND"]:
                    # Check if has number suffix
                    import re
                    if not re.search(r'\d+$', ref):
                        needs_fix = True
                
                if needs_fix and prefix not in ["VCC", "GND"]:
                    # Generate new reference
                    if prefix not in counters:
                        counters[prefix] = 1
                    new_ref = f"{prefix}{counters[prefix]}"
                    counters[prefix] += 1
                    
                    ref_mapping[ref] = new_ref
                    comp["reference"] = new_ref
                    print_status("🔧", f"Fixed reference: {ref} → {new_ref}", Colors.YELLOW)
                
                fixed_components.append(comp)
            
            return fixed_components, ref_mapping
        
        def fix_wires(wires: list[dict], ref_mapping: dict) -> list[dict]:
            """Update wire references based on mapping."""
            fixed_wires = []
            for wire in wires:
                new_wire = wire.copy()
                
                # Fix 'from' reference
                from_ref = wire.get("from", {}).get("component", "")
                if from_ref in ref_mapping:
                    new_wire["from"] = wire["from"].copy()
                    new_wire["from"]["component"] = ref_mapping[from_ref]
                
                # Fix 'to' reference
                to_ref = wire.get("to", {}).get("component", "")
                if to_ref in ref_mapping:
                    new_wire["to"] = wire["to"].copy()
                    new_wire["to"]["component"] = ref_mapping[to_ref]
                
                fixed_wires.append(new_wire)
            
            return fixed_wires
        
        # Apply fixes
        design.components, ref_mapping = fix_references(design.components)
        if ref_mapping:
            design.wires = fix_wires(design.wires, ref_mapping)
            print_status("✅", f"Fixed {len(ref_mapping)} reference(s)", Colors.GREEN)
        
        # =========================================
        # POST-PROCESSING: Validate Power Wiring
        # =========================================
        def validate_and_fix_power_wiring(components: list[dict], wires: list[dict]) -> tuple[list[dict], list[str]]:
            """
            Validate power connections and warn about incorrect wiring.
            VCC/GND pins should connect to power symbols or ESP32 power pins, NOT GPIO!
            """
            warnings = []
            
            # Build component type map
            comp_types = {c.get("reference"): c.get("type") for c in components}
            
            # ESP32 pin classification
            ESP32_POWER_PINS = {1, 2, 15, 38}  # GND, 3V3, GND2, GND3
            ESP32_GPIO_PINS = set(range(3, 39)) - ESP32_POWER_PINS  # All other pins are GPIO
            
            # Sensor VCC pins (must connect to power, not GPIO)
            SENSOR_VCC_PINS = {
                "dht11": 1, "dht22": 1,  # pin 1 = VCC
                "hcsr04": 1,  # pin 1 = VCC
                "pir": 1,  # pin 1 = VCC
                "bmp280": 1,  # pin 1 = VCC
                "oled_ssd1306": 2,  # pin 2 = VCC
                "servo": 2,  # pin 2 = VCC
                "relay": 1,  # pin 1 = VCC
                "soil_moisture": 1,  # pin 1 = VCC
                "mq2": 1,  # pin 1 = VCC
                "ir_receiver": 3,  # pin 3 = VCC
            }
            
            # Sensor GND pins (must connect to ground, not GPIO)
            SENSOR_GND_PINS = {
                "dht11": 4, "dht22": 4,  # pin 4 = GND
                "hcsr04": 4,  # pin 4 = GND
                "pir": 3,  # pin 3 = GND
                "bmp280": 2,  # pin 2 = GND
                "oled_ssd1306": 1,  # pin 1 = GND
                "servo": 1,  # pin 1 = GND
                "relay": 2,  # pin 2 = GND
                "soil_moisture": 2,  # pin 2 = GND
                "mq2": 2,  # pin 2 = GND
                "ir_receiver": 2,  # pin 2 = GND
            }
            
            fixed_wires = []
            for wire in wires:
                from_comp = wire.get("from", {}).get("component", "")
                from_pin = wire.get("from", {}).get("pin", 0)
                to_comp = wire.get("to", {}).get("component", "")
                to_pin = wire.get("to", {}).get("pin", 0)
                
                from_type = comp_types.get(from_comp, "")
                to_type = comp_types.get(to_comp, "")
                
                # Check 1: Sensor VCC connecting to ESP32 GPIO (WRONG!)
                if from_type in SENSOR_VCC_PINS and from_pin == SENSOR_VCC_PINS[from_type]:
                    if to_type == "esp32" and to_pin in ESP32_GPIO_PINS:
                        warnings.append(
                            f"⚠️ POWER ERROR: {from_comp}.pin{from_pin}(VCC) → {to_comp}.pin{to_pin}(GPIO) "
                            f"| VCC harus ke power (pin1=GND atau pin2=3V3), bukan GPIO!"
                        )
                        # Auto-fix: redirect to 3V3 (pin 2)
                        wire["to"]["pin"] = 2
                        warnings.append(f"   🔧 AUTO-FIX: {to_comp}.pin{to_pin} → {to_comp}.pin2 (3V3)")
                
                # Check 2: ESP32 GPIO connecting to sensor VCC (WRONG!)
                if to_type in SENSOR_VCC_PINS and to_pin == SENSOR_VCC_PINS[to_type]:
                    if from_type == "esp32" and from_pin in ESP32_GPIO_PINS:
                        warnings.append(
                            f"⚠️ POWER ERROR: {from_comp}.pin{from_pin}(GPIO) → {to_comp}.pin{to_pin}(VCC) "
                            f"| GPIO tidak boleh ke VCC sensor!"
                        )
                        # Auto-fix: redirect to 3V3 (pin 2)
                        wire["from"]["pin"] = 2
                        warnings.append(f"   🔧 AUTO-FIX: {from_comp}.pin{from_pin} → {from_comp}.pin2 (3V3)")
                
                # Check 3: Sensor GND connecting to ESP32 GPIO (WRONG!)
                if from_type in SENSOR_GND_PINS and from_pin == SENSOR_GND_PINS[from_type]:
                    if to_type == "esp32" and to_pin in ESP32_GPIO_PINS:
                        warnings.append(
                            f"⚠️ GROUND ERROR: {from_comp}.pin{from_pin}(GND) → {to_comp}.pin{to_pin}(GPIO) "
                            f"| GND harus ke ground (pin1=GND), bukan GPIO!"
                        )
                        # Auto-fix: redirect to GND (pin 1)
                        wire["to"]["pin"] = 1
                        warnings.append(f"   🔧 AUTO-FIX: {to_comp}.pin{to_pin} → {to_comp}.pin1 (GND)")
                
                # Check 4: ESP32 GPIO connecting to sensor GND (WRONG!)
                if to_type in SENSOR_GND_PINS and to_pin == SENSOR_GND_PINS[to_type]:
                    if from_type == "esp32" and from_pin in ESP32_GPIO_PINS:
                        warnings.append(
                            f"⚠️ GROUND ERROR: {from_comp}.pin{from_pin}(GPIO) → {to_comp}.pin{to_pin}(GND) "
                            f"| GPIO tidak boleh ke GND sensor!"
                        )
                        # Auto-fix: redirect to GND (pin 1)
                        wire["from"]["pin"] = 1
                        warnings.append(f"   🔧 AUTO-FIX: {from_comp}.pin{from_pin} → {from_comp}.pin1 (GND)")
                
                fixed_wires.append(wire)
            
            return fixed_wires, warnings
        
        # Apply power wiring validation
        design.wires, power_warnings = validate_and_fix_power_wiring(design.components, design.wires)
        if power_warnings:
            print_section("⚠️ POWER WIRING VALIDATION")
            for warning in power_warnings:
                print(f"   {Colors.YELLOW}{warning}{Colors.ENDC}")
            print()
        
        # Convert to SchematicPlan
        components = []
        for comp in design.components:
            components.append(ComponentPlacement(
                type=comp["type"],
                reference=comp["reference"],
                value=comp.get("value"),
                position=Position(x=comp["position"]["x"], y=comp["position"]["y"]),
                rotation=comp.get("rotation"),
            ))
        
        wires = []
        for wire in design.wires:
            from_ref = wire["from"]
            to_ref = wire["to"]
            wires.append(WireConnection(
                **{"from": PinReference(component=from_ref["component"], pin=from_ref["pin"])},
                to=PinReference(component=to_ref["component"], pin=to_ref["pin"]),
            ))
        
        plan = SchematicPlan(
            project=design.project,
            description=design.description,
            components=components,
            wires=wires,
        )
        
        # Generate schematic
        print_section("GENERATING KICAD FILE")
        result = save_schematic(plan)
        
        if result.success:
            print_status("✅", "SUCCESS!", Colors.GREEN)
            print(f"   {Colors.BOLD}File:{Colors.ENDC} {result.file_path}")
            print(f"   {Colors.BOLD}Components:{Colors.ENDC} {result.component_count}")
            print(f"   {Colors.BOLD}Wires:{Colors.ENDC} {result.wire_count}")
            
            # Try to open in KiCad
            print_status("🚀", "Opening in KiCad...", Colors.CYAN)
            open_in_kicad(result.file_path)
            
            return True
        else:
            print_status("❌", f"FAILED: {result.message}", Colors.RED)
            if result.errors:
                for err in result.errors:
                    print(f"   • {err}")
            return False
            
    except Exception as e:
        print_status("❌", f"ERROR: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        return False


# ============================================
# WEB SEARCH WITH ReAct
# ============================================

async def do_web_search(query: str, use_react: bool = True):
    """
    Perform web search with optional ReAct reasoning.
    
    Dengan ReAct, JAWIR akan:
    1. Thought: Analisis query dan tentukan strategi search
    2. Action: Eksekusi search
    3. Observation: Evaluasi hasil
    4. Loop sampai dapat info yang cukup
    """
    
    # Get API keys untuk ReAct reasoning
    api_keys = []
    google_api_keys = os.getenv("GOOGLE_API_KEYS", "")
    if google_api_keys:
        api_keys = [k.strip() for k in google_api_keys.split(",") if k.strip()]
    if not api_keys:
        single_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if single_key:
            api_keys = [single_key]
    
    if use_react and api_keys:
        # Use ReAct pattern for smarter search
        print_section("🔍 SMART SEARCH (ReAct Mode)")
        
        gemini = GeminiWithRotation(api_keys, model="gemini-3-flash-preview")
        react_agent = ReActAgent(gemini)
        
        # Run ReAct untuk search
        result = await react_agent.run(f"Cari informasi tentang: {query}", task_type="search")
        
        # Display collected results
        if result.get("collected_info", {}).get("search_results"):
            print_section("📊 SEARCH RESULTS")
            for i, r in enumerate(result["collected_info"]["search_results"][:8], 1):
                print(f"{Colors.BOLD}[{i}] {r.get('title', 'No title')}{Colors.ENDC}")
                print(f"    {Colors.DIM}URL: {r.get('url', '')}{Colors.ENDC}")
                content = r.get('content', '')[:300]
                print(f"    {content}...")
                print()
        
        if result.get("collected_info", {}).get("components_info"):
            print_section("📦 COMPONENT INFO")
            for comp in result["collected_info"]["components_info"]:
                print(f"{Colors.BOLD}{comp['component']}:{Colors.ENDC}")
                print(f"{Colors.DIM}{comp['info'][:500]}{Colors.ENDC}")
                print()
        
        return
    
    # Fallback: Simple search tanpa ReAct
    print_section("🔍 WEB SEARCH")
    print_status("🔍", f"Searching: {query}", Colors.CYAN)
    
    try:
        search = WebSearchTool()
        results = search.search(query, max_results=8)
        
        if results:
            print_status("✅", f"Found {len(results)} results:\n", Colors.GREEN)
            for i, r in enumerate(results, 1):
                print(f"{Colors.BOLD}[{i}] {r.get('title', 'No title')}{Colors.ENDC}")
                print(f"    {Colors.DIM}URL: {r.get('url', '')}{Colors.ENDC}")
                content = r.get('content', '')[:300]
                print(f"    {content}...")
                print()
        else:
            print_status("⚠️", "No results found", Colors.YELLOW)
            
    except Exception as e:
        print_status("❌", f"Search error: {e}", Colors.RED)
        print_status("💡", "Make sure TAVILY_API_KEY is set in .env file", Colors.YELLOW)


# ============================================
# PYTHON INTERPRETER FUNCTIONS
# ============================================

# Global interpreter instance
_jawir_interpreter = None

def get_jawir_interpreter():
    """Get or create JAWIR Interpreter instance."""
    global _jawir_interpreter
    if _jawir_interpreter is None:
        try:
            # Add parent directory to path for import
            tools_dir = os.path.dirname(os.path.dirname(__file__))
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            
            from python_interpreter import JawirInterpreter
            _jawir_interpreter = JawirInterpreter()
            print_status("✅", "Python Interpreter initialized", Colors.GREEN)
        except Exception as e:
            print_status("❌", f"Failed to load interpreter: {e}", Colors.RED)
            return None
    return _jawir_interpreter


async def execute_python_code(code: str):
    """Execute Python code."""
    print_section("🐍 PYTHON EXECUTION")
    print_status("📝", f"Code: {code[:100]}{'...' if len(code) > 100 else ''}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.run_code(code)
        
        # Check status (0 = success)
        if result.get("status", 0) == 0:
            print_status("✅", "Execution successful", Colors.GREEN)
            # Check stdout
            if result.get("stdout"):
                print(f"\n{Colors.BOLD}Output:{Colors.ENDC}")
                print(result["stdout"].strip())
            # Check result value (from eval)
            if result.get("result") is not None:
                print(f"\n{Colors.BOLD}Result:{Colors.ENDC} {result['result']}")
        else:
            print_status("❌", "Execution failed", Colors.RED)
            if result.get("stderr"):
                print(f"\n{Colors.RED}{result['stderr']}{Colors.ENDC}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def install_python_package(package: str):
    """Install Python package."""
    print_section("📦 PACKAGE INSTALLATION")
    print_status("🔧", f"Installing: {package}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.install_package(package)
        
        if result.get("success"):
            print_status("✅", f"Package '{package}' installed successfully", Colors.GREEN)
        else:
            print_status("❌", f"Failed to install '{package}'", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def open_desktop_app(app_name: str):
    """Open desktop application."""
    print_section("🖥️ DESKTOP CONTROL")
    print_status("🚀", f"Opening: {app_name}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.open_app(app_name)
        
        if result.get("success"):
            print_status("✅", f"Opened: {app_name}", Colors.GREEN)
            if result.get("message"):
                print(f"   {result['message']}")
        else:
            print_status("❌", f"Failed to open: {app_name}", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
            
            # Show available apps
            available = list(interp.desktop.APPS.keys())
            print(f"\n{Colors.DIM}Available apps: {', '.join(available[:10])}...{Colors.ENDC}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def close_desktop_app(app_name: str):
    """Close desktop application."""
    print_section("🖥️ DESKTOP CONTROL")
    print_status("🔒", f"Closing: {app_name}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.close_app(app_name)
        
        if result.get("success"):
            print_status("✅", f"Closed: {app_name}", Colors.GREEN)
        else:
            print_status("❌", f"Failed to close: {app_name}", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def open_url_in_browser(url: str):
    """Open URL in browser."""
    print_section("🌐 BROWSER")
    print_status("🔗", f"Opening: {url}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.open_url(url)
        
        if result.get("success"):
            print_status("✅", "URL opened in browser", Colors.GREEN)
        else:
            print_status("❌", "Failed to open URL", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def take_screenshot():
    """Take a screenshot."""
    print_section("📸 SCREENSHOT")
    print_status("📷", "Taking screenshot...", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.screenshot()
        
        if result.get("success"):
            print_status("✅", f"Screenshot saved: {result.get('path', 'unknown')}", Colors.GREEN)
        else:
            print_status("❌", "Failed to take screenshot", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def list_running_apps():
    """List running applications."""
    print_section("📋 RUNNING APPLICATIONS")
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.list_running_apps()
        
        if result.get("success"):
            processes = result.get("processes", [])
            print_status("✅", f"Found {len(processes)} processes", Colors.GREEN)
            print()
            for proc in processes[:20]:
                print(f"   • {proc.get('name', 'unknown')} (PID: {proc.get('pid', '?')})")
            if len(processes) > 20:
                print(f"   ... and {len(processes) - 20} more")
        else:
            print_status("❌", "Failed to list processes", Colors.RED)
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def minimize_window():
    """Minimize the current window."""
    print_section("🔽 MINIMIZE WINDOW")
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        import pyautogui
        # Windows shortcut: Win + Down to minimize
        pyautogui.hotkey('win', 'down')
        print_status("✅", "Window minimized", Colors.GREEN)
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def maximize_window():
    """Maximize the current window."""
    print_section("🔼 MAXIMIZE WINDOW")
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        import pyautogui
        # Windows shortcut: Win + Up to maximize
        pyautogui.hotkey('win', 'up')
        print_status("✅", "Window maximized", Colors.GREEN)
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def search_youtube(query: str, browser: str = "chrome"):
    """Search YouTube with a query."""
    print_section("🎬 YOUTUBE SEARCH")
    print_status("🔍", f"Searching: {query}", Colors.CYAN)
    print_status("🌐", f"Browser: {browser}", Colors.DIM)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.search_youtube(query, browser=browser)
        
        if result.get("success"):
            print_status("✅", f"Opened YouTube search for: {query}", Colors.GREEN)
        else:
            print_status("❌", "Failed to search YouTube", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def search_google_web(query: str, browser: str = None):
    """Search Google with a query."""
    print_section("🔍 GOOGLE SEARCH")
    print_status("🔎", f"Searching: {query}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.search_google(query, browser=browser)
        
        if result.get("success"):
            print_status("✅", f"Opened Google search for: {query}", Colors.GREEN)
        else:
            print_status("❌", "Failed to search Google", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


# ============================================
# SPOTIFY HELPER FUNCTIONS
# ============================================

async def play_spotify_music(query: str):
    """Search and play music on Spotify."""
    print_section("🎵 SPOTIFY PLAY")
    print_status("🔍", f"Searching: {query}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.play_spotify(query)
        
        if result.get("success"):
            print_status("✅", f"Now Playing on Spotify: {query}", Colors.GREEN)
            print(f"\n   {Colors.BOLD}🎵 {result.get('message', query)}{Colors.ENDC}")
        else:
            print_status("❌", "Failed to play Spotify", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def control_spotify(action: str):
    """Control Spotify playback (play, pause, next, previous)."""
    action_display = {
        "play": "▶️ Resume",
        "pause": "⏸️ Pause",
        "next": "⏭️ Next Track",
        "previous": "⏮️ Previous Track",
        "stop": "⏹️ Stop"
    }
    
    print_status("🎵", f"Spotify: {action_display.get(action, action)}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.spotify_control(action)
        
        if result.get("success"):
            print_status("✅", result.get("message", f"Spotify {action}"), Colors.GREEN)
        else:
            print_status("❌", f"Failed to {action} Spotify", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def play_youtube_video_basic(query: str, browser: str = "chrome"):
    """Search and play YouTube video (basic, without Computer Use)."""
    print_section("▶️ YOUTUBE PLAY (Basic)")
    print_status("🔍", f"Searching: {query}", Colors.CYAN)
    print_status("🌐", f"Browser: {browser}", Colors.DIM)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.play_youtube(query, browser=browser)
        
        if result.get("success"):
            video = result.get("video", {})
            print_status("✅", f"Now Playing!", Colors.GREEN)
            print()
            print(f"   {Colors.BOLD}🎬 {video.get('title', 'Unknown')}{Colors.ENDC}")
            print(f"   {Colors.DIM}📺 Channel: {video.get('channel', 'Unknown')}{Colors.ENDC}")
            print(f"   {Colors.DIM}⏱️ Duration: {video.get('duration', 'Unknown')}{Colors.ENDC}")
            print(f"   {Colors.DIM}👁️ Views: {video.get('views', 'Unknown')}{Colors.ENDC}")
            print(f"   {Colors.DIM}🔗 {video.get('url', '')}{Colors.ENDC}")
        else:
            print_status("❌", "Failed to play video", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def list_youtube_videos(query: str, limit: int = 5):
    """List YouTube search results."""
    print_section("📋 YOUTUBE SEARCH RESULTS")
    print_status("🔍", f"Searching: {query}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.youtube_results(query, limit=limit)
        
        if result.get("success"):
            videos = result.get("videos", [])
            print_status("✅", f"Found {len(videos)} videos:\n", Colors.GREEN)
            
            for video in videos:
                idx = video.get('index', '?')
                title = video.get('title', 'Unknown')
                channel = video.get('channel', 'Unknown')
                duration = video.get('duration', '?')
                views = video.get('views', '?')
                
                print(f"   {Colors.BOLD}[{idx}] {title}{Colors.ENDC}")
                print(f"       {Colors.DIM}📺 {channel} | ⏱️ {duration} | 👁️ {views}{Colors.ENDC}")
                print()
        else:
            print_status("❌", "No videos found", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def youtube_fullscreen():
    """Toggle fullscreen for YouTube video."""
    print_section("🎬 YOUTUBE FULLSCREEN")
    
    try:
        import pyautogui
        # Press 'f' key to toggle fullscreen in YouTube
        pyautogui.press('f')
        print_status("✅", "Toggled fullscreen mode", Colors.GREEN)
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


# ============================================
# COMPUTER USE (BROWSER AUTOMATION) FUNCTIONS
# ============================================

# Global flag untuk Computer Use availability
COMPUTER_USE_AVAILABLE = False
DOWNLOAD_FOLDER = None

try:
    tools_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    computer_use_path = os.path.join(tools_dir, 'computer_use')
    if os.path.exists(computer_use_path):
        sys.path.insert(0, tools_dir)
        from computer_use import PlaywrightComputer, BrowserAgent, run_browser_task
        COMPUTER_USE_AVAILABLE = True
        # Setup download folder
        DOWNLOAD_FOLDER = os.path.join(os.path.dirname(tools_dir), 'downloads')
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
except ImportError as e:
    pass


async def run_computer_use_task(task: str, initial_url: str = "https://www.google.com", headless: bool = False):
    """
    Run browser automation task using Gemini Computer Use.
    
    Args:
        task: Natural language task description
        initial_url: Starting URL
        headless: Run browser without GUI
    """
    print_section("🖥️ COMPUTER USE (Browser Automation)")
    print_status("📋", f"Task: {task}", Colors.CYAN)
    print_status("🌐", f"Starting URL: {initial_url}", Colors.DIM)
    
    if not COMPUTER_USE_AVAILABLE:
        print_status("❌", "Computer Use module not available!", Colors.RED)
        print_status("💡", "Run: python setup_computer_use.py", Colors.YELLOW)
        print_status("📂", "Location: backend/tools/computer_use/", Colors.DIM)
        return {"success": False, "error": "Module not available"}
    
    try:
        # Check API key
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            print_status("❌", "GEMINI_API_KEY not set!", Colors.RED)
            print_status("💡", "Set: $env:GEMINI_API_KEY='your-api-key'", Colors.YELLOW)
            return {"success": False, "error": "API key not set"}
        
        print_status("🚀", "Starting browser automation...", Colors.GREEN)
        print_status("⏳", "This may take a moment...", Colors.DIM)
        print()
        
        # Run in thread to not block async
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                run_browser_task,
                task=task,
                initial_url=initial_url,
                headless=headless,
                model="gemini-3-flash-preview",
                verbose=True
            )
            result = future.result(timeout=300)  # 5 min timeout
        
        print()
        print_status("✅", "Task completed!", Colors.GREEN)
        if result:
            print(f"\n   {Colors.BOLD}📝 Result:{Colors.ENDC}")
            print(f"   {result[:500]}{'...' if len(str(result)) > 500 else ''}")
        
        return {"success": True, "result": result}
        
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)
        return {"success": False, "error": str(e)}


async def browse_with_vision(url: str, task: str = None):
    """
    Browse a website with visual understanding.
    
    Args:
        url: URL to navigate to
        task: Optional task to perform (e.g., "find contact info")
    """
    print_section("👁️ VISUAL BROWSE")
    print_status("🌐", f"URL: {url}", Colors.CYAN)
    
    if task:
        full_task = f"Go to {url} and {task}"
    else:
        full_task = f"Go to {url} and describe what you see"
    
    await run_computer_use_task(full_task, initial_url=url)


async def web_form_fill(url: str, form_data_str: str):
    """
    Fill a web form automatically using vision.
    
    Args:
        url: URL of the form page
        form_data_str: Form data as "field1=value1 field2=value2"
    """
    print_section("📝 WEB FORM FILL")
    print_status("🌐", f"URL: {url}", Colors.CYAN)
    print_status("📋", f"Data: {form_data_str}", Colors.DIM)
    
    # Parse form data
    form_fields = []
    for pair in form_data_str.split():
        if '=' in pair:
            key, value = pair.split('=', 1)
            form_fields.append(f"{key}: {value}")
    
    if not form_fields:
        print_status("❌", "No valid form data!", Colors.RED)
        print_status("💡", "Format: /webfill <url> field1=value1 field2=value2", Colors.YELLOW)
        return
    
    task = f"Go to {url}, fill the form with: {', '.join(form_fields)}, then submit"
    await run_computer_use_task(task, initial_url=url)


async def web_search_vision(query: str, engine: str = "google"):
    """
    Search web using visual browser automation.
    
    Args:
        query: Search query
        engine: Search engine (google, youtube, bing)
    """
    print_section("🔍 VISUAL WEB SEARCH")
    print_status("🔎", f"Query: {query}", Colors.CYAN)
    print_status("🌐", f"Engine: {engine}", Colors.DIM)
    
    engine_urls = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "bing": "https://www.bing.com",
        "duckduckgo": "https://duckduckgo.com",
    }
    
    url = engine_urls.get(engine.lower(), "https://www.google.com")
    task = f"Search for '{query}' and tell me the top 5 results with brief descriptions"
    
    await run_computer_use_task(task, initial_url=url)


async def web_screenshot_vision(url: str, output_path: str = None):
    """
    Take screenshot of a webpage using Playwright.
    
    Args:
        url: URL to screenshot
        output_path: Optional output path
    """
    print_section("📸 WEB SCREENSHOT")
    print_status("🌐", f"URL: {url}", Colors.CYAN)
    
    if not COMPUTER_USE_AVAILABLE:
        print_status("❌", "Computer Use module not available!", Colors.RED)
        return
    
    try:
        import os
        from datetime import datetime
        
        if not output_path:
            workspace = os.environ.get("JAWIR_WORKSPACE", "D:\\sijawir\\python_workspace")
            os.makedirs(workspace, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(workspace, f"web_screenshot_{timestamp}.png")
        
        with PlaywrightComputer(initial_url=url, headless=True) as browser:
            import time
            time.sleep(2)  # Wait for page load
            filepath = browser.screenshot_to_file(output_path)
            
            if os.path.exists(filepath):
                print_status("✅", f"Screenshot saved: {filepath}", Colors.GREEN)
            else:
                print_status("❌", "Failed to save screenshot", Colors.RED)
                
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


# ============================================
# ADVANCED COMPUTER USE FEATURES
# ============================================

def _run_journal_search_sync(query: str, journal_folder: str) -> dict:
    """Synchronous journal search - runs in thread to avoid asyncio conflict."""
    try:
        search_url = f"https://arxiv.org/search/?searchtype=all&query={query.replace(' ', '+')}&start=0"
        
        with PlaywrightComputer(
            initial_url=search_url, 
            headless=False,
            highlight_mouse=True,
            download_folder=journal_folder,
        ) as browser:
            
            browser._page.context.set_default_timeout(60000)
            browser._page.wait_for_load_state("networkidle", timeout=15000)
            
            import time as time_module
            time_module.sleep(2)
            
            # Find and click first paper
            arxiv_id = None
            paper_title = "Unknown"
            authors = "Unknown"
            
            try:
                first_paper = browser._page.query_selector("li.arxiv-result p.title a")
                if not first_paper:
                    first_paper = browser._page.query_selector("p.title a")
                if not first_paper:
                    first_paper = browser._page.query_selector("a[href*='/abs/']")
                
                if first_paper:
                    paper_title_preview = first_paper.text_content().strip()[:60]
                    print(f"  📄 Found: {paper_title_preview}...")
                    first_paper.click()
                    browser._page.wait_for_load_state("networkidle", timeout=15000)
                    time_module.sleep(1)
                else:
                    print("  🤖 Using AI to find paper...")
                    agent = BrowserAgent(
                        browser_computer=browser,
                        query="Click on the first paper title to go to its abstract page",
                        model_name="gemini-3-flash-preview",
                        verbose=True,
                        max_iterations=5
                    )
                    agent.run()
            except Exception as click_err:
                print(f"  ⚠️ Click error: {click_err}")
            
            # Extract arXiv ID
            current_url = browser._page.url
            if "arxiv.org/abs/" in current_url:
                arxiv_id = current_url.split("/abs/")[-1].split("?")[0].split("#")[0].split("v")[0]
            
            if not arxiv_id:
                import re
                page_text = browser._page.text_content("body") or ""
                match = re.search(r'arXiv:(\d{4}\.\d{4,5})', page_text)
                if match:
                    arxiv_id = match.group(1)
            
            if arxiv_id:
                print(f"  📄 arXiv ID: {arxiv_id}")
                
                try:
                    title_elem = browser._page.query_selector("h1.title")
                    if title_elem:
                        paper_title = title_elem.text_content().replace("Title:", "").strip()
                    
                    authors_elem = browser._page.query_selector("div.authors")
                    if authors_elem:
                        authors = authors_elem.text_content().replace("Authors:", "").strip()[:100]
                except:
                    pass
                
                print(f"  📝 Title: {paper_title[:70]}...")
                print(f"  👥 Authors: {authors[:50]}...")
                
                # Screenshot
                screenshot_path = os.path.join(journal_folder, f"arxiv_{arxiv_id}_abstract.png")
                browser.screenshot_to_file(screenshot_path)
                
                # Download PDF
                print(f"  📥 Downloading PDF...")
                
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                import urllib.request
                
                clean_title = "".join(c for c in paper_title if c.isalnum() or c in (' ', '-', '_')).strip()
                clean_title = clean_title[:50] if clean_title and clean_title != "Unknown" else "paper"
                filename = f"arxiv_{arxiv_id.replace('.', '_')}_{clean_title}.pdf"
                save_path = os.path.join(journal_folder, filename)
                
                urllib.request.urlretrieve(pdf_url, save_path)
                
                if os.path.exists(save_path):
                    file_size = os.path.getsize(save_path)
                    return {
                        "success": True,
                        "arxiv_id": arxiv_id,
                        "title": paper_title,
                        "authors": authors,
                        "pdf_path": save_path,
                        "pdf_url": pdf_url,
                        "screenshot": screenshot_path,
                        "file_size_kb": file_size / 1024
                    }
                else:
                    return {"success": False, "error": "Download failed"}
            else:
                return {"success": False, "error": "Paper ID not found"}
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def search_and_download_journal(query: str, source: str = "arxiv"):
    """
    Search for academic journals/papers and download PDF to local computer.
    
    Args:
        query: Search query (e.g., "Machine Learning IoT")
        source: Source website (arxiv, google_scholar)
    
    Returns:
        dict with download result
    """
    print_section("📚 JOURNAL SEARCH & DOWNLOAD")
    print_status("🔍", f"Query: {query}", Colors.CYAN)
    print_status("📖", f"Source: {source}", Colors.DIM)
    
    if not COMPUTER_USE_AVAILABLE:
        print_status("❌", "Computer Use module not available!", Colors.RED)
        print_status("💡", "Run: pip install playwright && playwright install chrome", Colors.YELLOW)
        return {"success": False, "error": "Module not available"}
    
    # Setup download folder for journals
    journal_folder = os.path.join(DOWNLOAD_FOLDER, "journals")
    os.makedirs(journal_folder, exist_ok=True)
    
    try:
        if source.lower() == "arxiv":
            print_status("🌐", f"Opening arXiv search...", Colors.DIM)
            print_status("⏳", "Searching papers...", Colors.YELLOW)
            print()
            
            # Run in thread to avoid asyncio conflict with Playwright sync API
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(_run_journal_search_sync, query, journal_folder)
                result = future.result(timeout=300)  # 5 min timeout
            
            if result.get("success"):
                print()
                print_status("✅", "PDF Downloaded Successfully!", Colors.GREEN)
                print_status("📄", f"File: {os.path.basename(result['pdf_path'])}", Colors.CYAN)
                print_status("📁", f"Location: {result['pdf_path']}", Colors.DIM)
                print_status("📊", f"Size: {result['file_size_kb']:.1f} KB", Colors.DIM)
                print_status("📸", f"Screenshot: {result['screenshot']}", Colors.DIM)
            else:
                print_status("❌", f"Failed: {result.get('error')}", Colors.RED)
            
            return result
        else:
            print_status("❌", f"Source '{source}' not supported yet", Colors.RED)
            print_status("💡", "Available: arxiv", Colors.YELLOW)
            return {"success": False, "error": "Source not supported"}
            
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def _run_youtube_play_sync(query: str, action: str) -> dict:
    """Synchronous YouTube play - runs in thread to avoid asyncio conflict."""
    try:
        with PlaywrightComputer(
            initial_url="https://www.youtube.com",
            headless=False,
            highlight_mouse=True,
        ) as browser:
            
            browser._page.context.set_default_timeout(60000)
            
            if action == "search_play":
                task = f"""
                1. Search for '{query}' in the YouTube search bar
                2. Wait for search results to load  
                3. Click on the FIRST video thumbnail to play it
                4. Wait for the video to start playing
                5. Tell me the title of the video that is now playing
                """
            elif action == "search_only":
                task = f"""
                1. Search for '{query}' in the YouTube search bar
                2. Wait for search results to load
                3. Tell me the titles of the top 5 videos in the results
                """
            else:
                task = f"Search for '{query}' and click the first video to play it"
            
            agent = BrowserAgent(
                browser_computer=browser,
                query=task,
                model_name="gemini-3-flash-preview",
                verbose=True,
                max_iterations=15
            )
            
            result = agent.run()
            
            print()
            print(f"  ✅ YouTube task completed!")
            if result:
                print(f"  📝 Result: {result[:200]}{'...' if len(str(result)) > 200 else ''}")
            
            # Check if running interactively
            import sys
            if sys.stdin.isatty():
                # Keep browser open for viewing
                print()
                print("  🎥 Video is playing. Press Enter to close browser...")
                input()
            else:
                # Non-interactive mode - wait a bit then close
                import time
                print()
                print("  🎥 Video is playing for 10 seconds...")
                time.sleep(10)
            
            return {"success": True, "result": result}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def play_youtube_video(query: str, action: str = "search_play"):
    """
    Search and play YouTube video using Computer Use.
    
    Args:
        query: Search query
        action: "search_play" (default), "search_only", "play_first"
    
    Returns:
        dict with result
    """
    print_section("🎬 YOUTUBE PLAY (Computer Use)")
    print_status("🔍", f"Query: {query}", Colors.CYAN)
    print_status("▶️", f"Action: {action}", Colors.DIM)
    
    if not COMPUTER_USE_AVAILABLE:
        print_status("❌", "Computer Use module not available!", Colors.RED)
        return {"success": False, "error": "Module not available"}
    
    try:
        print_status("🌐", "Opening YouTube...", Colors.YELLOW)
        print()
        
        # Run in thread to avoid asyncio conflict
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run_youtube_play_sync, query, action)
            result = future.result(timeout=300)  # 5 min timeout
        
        return result
            
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)
        return {"success": False, "error": str(e)}


async def download_file_from_web(url: str, filename: str = None):
    """
    Download any file from web URL.
    
    Args:
        url: Direct URL to file
        filename: Optional custom filename
    
    Returns:
        dict with download result
    """
    print_section("📥 WEB FILE DOWNLOAD")
    print_status("🔗", f"URL: {url}", Colors.CYAN)
    
    if not DOWNLOAD_FOLDER:
        print_status("❌", "Download folder not configured", Colors.RED)
        return {"success": False, "error": "Download folder not set"}
    
    try:
        import urllib.request
        from urllib.parse import urlparse, unquote
        
        # Extract filename from URL if not provided
        if not filename:
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            if not filename or filename == "":
                filename = f"download_{int(time.time())}"
        
        save_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        print_status("⏳", f"Downloading to: {save_path}", Colors.YELLOW)
        
        # Download with progress
        urllib.request.urlretrieve(url, save_path)
        
        if os.path.exists(save_path):
            file_size = os.path.getsize(save_path)
            print_status("✅", "Download complete!", Colors.GREEN)
            print_status("📄", f"File: {filename}", Colors.CYAN)
            print_status("📁", f"Location: {save_path}", Colors.DIM)
            print_status("📊", f"Size: {file_size/1024:.1f} KB", Colors.DIM)
            
            return {
                "success": True,
                "filepath": save_path,
                "filename": filename,
                "size_kb": file_size / 1024
            }
        else:
            print_status("❌", "Download failed", Colors.RED)
            return {"success": False, "error": "File not saved"}
            
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)
        return {"success": False, "error": str(e)}


def _run_browse_interact_sync(url: str, task: str) -> dict:
    """Synchronous browse & interact - runs in thread to avoid asyncio conflict."""
    try:
        with PlaywrightComputer(
            initial_url=url,
            headless=False,
            highlight_mouse=True,
            download_folder=DOWNLOAD_FOLDER,
        ) as browser:
            
            browser._page.context.set_default_timeout(60000)
            
            agent = BrowserAgent(
                browser_computer=browser,
                query=task,
                model_name="gemini-3-flash-preview",
                verbose=True,
                max_iterations=20
            )
            
            result = agent.run()
            
            # Take final screenshot
            screenshot_path = os.path.join(DOWNLOAD_FOLDER, f"browse_result_{int(time.time())}.png")
            browser.screenshot_to_file(screenshot_path)
            
            return {
                "success": True,
                "result": result,
                "screenshot": screenshot_path
            }
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def browse_and_interact(url: str, task: str):
    """
    Browse website and perform complex interactions using AI vision.
    
    Args:
        url: Starting URL
        task: Natural language description of what to do
    
    Returns:
        dict with result
    """
    print_section("🌐 BROWSE & INTERACT (AI Vision)")
    print_status("🔗", f"URL: {url}", Colors.CYAN)
    print_status("📋", f"Task: {task}", Colors.DIM)
    
    if not COMPUTER_USE_AVAILABLE:
        print_status("❌", "Computer Use module not available!", Colors.RED)
        return {"success": False, "error": "Module not available"}
    
    try:
        print_status("🚀", "Starting browser...", Colors.YELLOW)
        print()
        
        # Run in thread to avoid asyncio conflict
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run_browse_interact_sync, url, task)
            result = future.result(timeout=300)  # 5 min timeout
        
        if result.get("success"):
            print()
            print_status("✅", "Task completed!", Colors.GREEN)
            if result.get("result"):
                print_status("📝", f"Result: {str(result['result'])[:300]}...", Colors.CYAN)
            print_status("📸", f"Screenshot: {result.get('screenshot')}", Colors.DIM)
        else:
            print_status("❌", f"Failed: {result.get('error')}", Colors.RED)
        
        return result
            
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)
        return {"success": False, "error": str(e)}


async def browse_website(url: str, browser: str = None):
    """Browse a website."""
    print_section("🌐 BROWSE WEBSITE")
    print_status("🔗", f"Opening: {url}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        result = interp.browse(url, browser=browser)
        
        if result.get("success"):
            print_status("✅", f"Opened: {url}", Colors.GREEN)
        else:
            print_status("❌", "Failed to open website", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


async def generate_file(file_type: str, content: str):
    """Generate a file of specified type."""
    print_section(f"📄 FILE GENERATION ({file_type.upper()})")
    print_status("📝", f"Content: {content[:100]}{'...' if len(content) > 100 else ''}", Colors.CYAN)
    
    interp = get_jawir_interpreter()
    if not interp:
        return
    
    try:
        # Generate filename from content
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:6]
        filename = f"jawir_{file_type}_{content_hash}"
        
        # Handle different file types
        if file_type == 'word':
            result = interp.create_word(content, filename)
        elif file_type == 'pdf':
            result = interp.create_pdf(content, filename)
        elif file_type == 'txt':
            result = interp.create_txt(content, filename)
        elif file_type == 'markdown' or file_type == 'md':
            result = interp.create_markdown(content, filename)
        elif file_type == 'json':
            import json
            try:
                data = json.loads(content)
            except:
                data = {"content": content}
            result = interp.create_json(data, filename)
        elif file_type == 'excel':
            import json
            try:
                # Try to parse as JSON data
                data = json.loads(content)
            except:
                # Create simple data from content
                rows = content.split(',')
                data = [{"col": i+1, "value": row.strip()} for i, row in enumerate(rows)]
            result = interp.create_excel(data, filename)
        elif file_type == 'csv':
            import json
            try:
                # Try to parse as JSON array
                data = json.loads(content)
            except:
                # Create from comma-separated values
                rows = content.split('\n') if '\n' in content else [content]
                if len(rows) == 1:
                    # Single row: treat as headers
                    headers = [h.strip() for h in rows[0].split(',')]
                    data = [{h: "" for h in headers}]
                else:
                    # Multiple rows: first is header
                    headers = [h.strip() for h in rows[0].split(',')]
                    data = []
                    for row in rows[1:]:
                        values = [v.strip() for v in row.split(',')]
                        data.append({headers[i]: values[i] if i < len(values) else "" for i in range(len(headers))})
            result = interp.create_csv(data, filename)
        else:
            result = {"success": False, "message": f"Unknown file type: {file_type}"}
        
        if result.get("success"):
            print_status("✅", f"File created: {result.get('path', 'unknown')}", Colors.GREEN)
        else:
            print_status("❌", f"Failed to create file", Colors.RED)
            if result.get("message"):
                print(f"   {result['message']}")
    except Exception as e:
        print_status("❌", f"Error: {e}", Colors.RED)


def interactive_mode():
    """Run in interactive mode."""
    print_banner()
    print_status("🤖", "Halo! Aku JAWIR - AI Assistant Jawa Terkuat dari Ngawi!", Colors.CYAN)
    print_status("🧠", "Gemini sebagai otak, ReAct sebagai pola pikir", Colors.DIM)
    print_status("💡", "Ketik langsung atau /help untuk bantuan", Colors.DIM)
    print()
    
    # Initialize Google Workspace client (lazy load)
    gws_client = None
    
    def get_gws_client():
        nonlocal gws_client
        if gws_client is None:
            try:
                # Import from parent directory
                tools_dir = os.path.dirname(os.path.dirname(__file__))
                sys.path.insert(0, tools_dir)
                from google_workspace import GoogleWorkspaceMCP
                gws_client = GoogleWorkspaceMCP()
                print_status("✅", f"Google Workspace connected: {gws_client.user_email}", Colors.GREEN)
            except Exception as e:
                print_status("❌", f"Google Workspace not available: {e}", Colors.RED)
                return None
        return gws_client
    
    while True:
        try:
            user_input = input(f"{Colors.GREEN}JAWIR>{Colors.ENDC} ").strip()
            
            if not user_input:
                continue
            
            # Exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print_status("👋", "Goodbye!", Colors.CYAN)
                break
            
            # Help
            if user_input.lower() in ['/help', 'help', 'h', '?']:
                print_help()
                continue
            
            # Clear
            if user_input.lower() in ['/clear', 'clear', 'cls']:
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue
            
            # Google Workspace mode
            if user_input.lower() in ['/google', '/gws', '/workspace']:
                print_status("🔄", "Switching to Google Workspace mode...", Colors.CYAN)
                tools_dir = os.path.dirname(os.path.dirname(__file__))
                gws_script = os.path.join(tools_dir, "google_workspace.py")
                if os.path.exists(gws_script):
                    os.system(f'python "{gws_script}" -i')
                else:
                    print_status("❌", "Google Workspace tool not found", Colors.RED)
                print()
                continue
            
            # Gmail commands
            if user_input.lower().startswith('/gmail'):
                client = get_gws_client()
                if client:
                    parts = user_input.split()
                    action = parts[1] if len(parts) > 1 else "labels"
                    args = parts[2:] if len(parts) > 2 else []
                    
                    if action == "labels" or action == "list":
                        result = client.list_gmail_labels()
                        if result["success"]:
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    elif action == "search" and args:
                        result = client.search_gmail(" ".join(args))
                        if result["success"]:
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    else:
                        print_status("💡", "Usage: /gmail labels | /gmail search <query>", Colors.YELLOW)
                print()
                continue
            
            # Drive commands
            if user_input.lower().startswith('/drive'):
                client = get_gws_client()
                if client:
                    parts = user_input.split()
                    action = parts[1] if len(parts) > 1 else "list"
                    args = parts[2:] if len(parts) > 2 else []
                    
                    if action == "list" or action == "ls":
                        query = " ".join(args) if args else "*"
                        result = client.search_drive_files(query)
                        if result["success"]:
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    elif action == "search" and args:
                        result = client.search_drive_files(" ".join(args))
                        if result["success"]:
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    else:
                        print_status("💡", "Usage: /drive list | /drive search <query>", Colors.YELLOW)
                print()
                continue
            
            # Calendar commands
            if user_input.lower().startswith('/calendar') or user_input.lower().startswith('/cal'):
                client = get_gws_client()
                if client:
                    parts = user_input.split()
                    action = parts[1] if len(parts) > 1 else "list"
                    args = parts[2:] if len(parts) > 2 else []
                    
                    if action == "list" or action == "calendars":
                        result = client.list_calendars()
                        if result["success"]:
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    elif action == "events":
                        calendar_id = args[0] if args else "primary"
                        result = client.list_events(calendar_id)
                        if result["success"]:
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    elif action == "quick" and args:
                        result = client.quick_add_event(" ".join(args))
                        if result["success"]:
                            print_status("✅", "Event added!", Colors.GREEN)
                            print(f"\n{result['output']}")
                        else:
                            print_status("❌", f"Error: {result.get('error')}", Colors.RED)
                    else:
                        print_status("💡", "Usage: /calendar list | /calendar events | /calendar quick <text>", Colors.YELLOW)
                print()
                continue
            
            # Web search command
            if user_input.lower().startswith('/search '):
                query = user_input[8:].strip()
                if query:
                    asyncio.run(do_web_search(query))
                else:
                    print_status("⚠️", "Usage: /search <query>", Colors.YELLOW)
                print()
                continue
            
            # ==========================================
            # PYTHON INTERPRETER COMMANDS
            # ==========================================
            
            # Python code execution
            if user_input.lower().startswith('/python ') or user_input.lower().startswith('/py '):
                prefix_len = 8 if user_input.lower().startswith('/python ') else 4
                code = user_input[prefix_len:].strip()
                if code:
                    asyncio.run(execute_python_code(code))
                else:
                    print_status("⚠️", "Usage: /python <code>", Colors.YELLOW)
                print()
                continue
            
            # Pip install
            if user_input.lower().startswith('/pip '):
                cmd = user_input[5:].strip()
                if cmd.startswith('install '):
                    package = cmd[8:].strip()
                    asyncio.run(install_python_package(package))
                else:
                    print_status("⚠️", "Usage: /pip install <package>", Colors.YELLOW)
                print()
                continue
            
            # Open app
            if user_input.lower().startswith('/open '):
                app_name = user_input[6:].strip()
                if app_name:
                    asyncio.run(open_desktop_app(app_name))
                else:
                    print_status("⚠️", "Usage: /open <app_name>", Colors.YELLOW)
                print()
                continue
            
            # Close app
            if user_input.lower().startswith('/close '):
                app_name = user_input[7:].strip()
                if app_name:
                    asyncio.run(close_desktop_app(app_name))
                else:
                    print_status("⚠️", "Usage: /close <app_name>", Colors.YELLOW)
                print()
                continue
            
            # Open URL
            if user_input.lower().startswith('/url '):
                url = user_input[5:].strip()
                if url:
                    asyncio.run(open_url_in_browser(url))
                else:
                    print_status("⚠️", "Usage: /url <url>", Colors.YELLOW)
                print()
                continue
            
            # Screenshot
            if user_input.lower() in ['/screenshot', '/ss']:
                asyncio.run(take_screenshot())
                print()
                continue
            
            # Minimize window
            if user_input.lower() in ['/minimize', '/min']:
                asyncio.run(minimize_window())
                print()
                continue
            
            # Maximize window
            if user_input.lower() in ['/maximize', '/max']:
                asyncio.run(maximize_window())
                print()
                continue
            
            # ==========================================
            # SPOTIFY COMMANDS
            # ==========================================
            
            # Spotify play music
            if user_input.lower().startswith('/spotify '):
                query = user_input[9:].strip()
                if query:
                    asyncio.run(play_spotify_music(query))
                else:
                    print_status("⚠️", "Usage: /spotify <query>", Colors.YELLOW)
                print()
                continue
            
            # Spotify control commands
            if user_input.lower() in ['/pause', '/stop']:
                asyncio.run(control_spotify('pause'))
                print()
                continue
            
            if user_input.lower() in ['/resume', '/play']:
                # If just /play without query, resume playback
                asyncio.run(control_spotify('play'))
                print()
                continue
            
            if user_input.lower() in ['/next', '/skip']:
                asyncio.run(control_spotify('next'))
                print()
                continue
            
            if user_input.lower() in ['/prev', '/previous', '/back']:
                asyncio.run(control_spotify('previous'))
                print()
                continue
            
            # ==========================================
            # YOUTUBE COMMANDS
            # ==========================================
            
            # YouTube search
            if user_input.lower().startswith('/youtube ') or user_input.lower().startswith('/yt '):
                prefix_len = 9 if user_input.lower().startswith('/youtube ') else 4
                args = user_input[prefix_len:].strip()
                if args:
                    # Check if first word is a browser name
                    parts = args.split(maxsplit=1)
                    browsers = ['chrome', 'firefox', 'edge']
                    if len(parts) > 1 and parts[0].lower() in browsers:
                        browser = parts[0].lower()
                        query = parts[1]
                    else:
                        browser = "chrome"  # Default to chrome
                        query = args
                    asyncio.run(search_youtube(query, browser=browser))
                else:
                    print_status("⚠️", "Usage: /youtube <query> atau /yt chrome <query>", Colors.YELLOW)
                print()
                continue
            
            # YouTube play - search and play first result
            if user_input.lower().startswith('/play '):
                args = user_input[6:].strip()
                if args:
                    # Check if first word is a browser name
                    parts = args.split(maxsplit=1)
                    browsers = ['chrome', 'firefox', 'edge']
                    if len(parts) > 1 and parts[0].lower() in browsers:
                        browser = parts[0].lower()
                        query = parts[1]
                    else:
                        browser = "chrome"
                        query = args
                    asyncio.run(play_youtube_video(query, browser=browser))
                else:
                    print_status("⚠️", "Usage: /play <query> atau /play chrome <query>", Colors.YELLOW)
                print()
                continue
            
            # YouTube list search results
            if user_input.lower().startswith('/ytlist ') or user_input.lower().startswith('/videos '):
                prefix_len = 8
                query = user_input[prefix_len:].strip()
                if query:
                    asyncio.run(list_youtube_videos(query))
                else:
                    print_status("⚠️", "Usage: /ytlist <query>", Colors.YELLOW)
                print()
                continue
            
            # YouTube Chrome - force Chrome browser
            if user_input.lower().startswith('/ytchrome '):
                query = user_input[10:].strip()
                if query:
                    asyncio.run(search_youtube(query, browser="chrome"))
                else:
                    print_status("⚠️", "Usage: /ytchrome <query>", Colors.YELLOW)
                print()
                continue
            
            # YouTube Edge - force Edge browser
            if user_input.lower().startswith('/ytedge '):
                query = user_input[8:].strip()
                if query:
                    asyncio.run(search_youtube(query, browser="edge"))
                else:
                    print_status("⚠️", "Usage: /ytedge <query>", Colors.YELLOW)
                print()
                continue
            
            # YouTube Fullscreen
            if user_input.lower() in ['/ytfullscreen', '/fullscreen']:
                asyncio.run(youtube_fullscreen())
                print()
                continue
            
            # ==========================================
            # COMPUTER USE (BROWSER AUTOMATION) COMMANDS
            # ==========================================
            
            # Computer Use - Natural language browser task
            if user_input.lower().startswith('/cu ') or user_input.lower().startswith('/computeruse '):
                prefix_len = 4 if user_input.lower().startswith('/cu ') else 13
                task = user_input[prefix_len:].strip()
                if task:
                    asyncio.run(run_computer_use_task(task))
                else:
                    print_status("⚠️", "Usage: /cu <natural language task>", Colors.YELLOW)
                    print_status("💡", "Example: /cu search python tutorials on youtube", Colors.DIM)
                print()
                continue
            
            # Visual browse with task
            if user_input.lower().startswith('/vbrowse '):
                args = user_input[9:].strip()
                parts = args.split(' ', 1)
                url = parts[0] if parts else ""
                task = parts[1] if len(parts) > 1 else None
                if url:
                    asyncio.run(browse_with_vision(url, task))
                else:
                    print_status("⚠️", "Usage: /vbrowse <url> [task]", Colors.YELLOW)
                    print_status("💡", "Example: /vbrowse github.com/google find trending repos", Colors.DIM)
                print()
                continue
            
            # Web form fill
            if user_input.lower().startswith('/webfill '):
                args = user_input[9:].strip()
                parts = args.split(' ', 1)
                url = parts[0] if parts else ""
                form_data = parts[1] if len(parts) > 1 else ""
                if url and form_data:
                    asyncio.run(web_form_fill(url, form_data))
                else:
                    print_status("⚠️", "Usage: /webfill <url> field1=value1 field2=value2", Colors.YELLOW)
                    print_status("💡", "Example: /webfill login.com username=john password=secret", Colors.DIM)
                print()
                continue
            
            # Visual web search
            if user_input.lower().startswith('/vsearch '):
                args = user_input[9:].strip()
                # Check for engine flag
                engine = "google"
                query = args
                if args.startswith('--youtube ') or args.startswith('-yt '):
                    engine = "youtube"
                    query = args.split(' ', 1)[1] if ' ' in args else ""
                elif args.startswith('--bing ') or args.startswith('-b '):
                    engine = "bing"
                    query = args.split(' ', 1)[1] if ' ' in args else ""
                
                if query:
                    asyncio.run(web_search_vision(query, engine))
                else:
                    print_status("⚠️", "Usage: /vsearch [--youtube|-yt] <query>", Colors.YELLOW)
                    print_status("💡", "Example: /vsearch python machine learning tutorial", Colors.DIM)
                print()
                continue
            
            # Web screenshot
            if user_input.lower().startswith('/webshot '):
                url = user_input[9:].strip()
                if url:
                    asyncio.run(web_screenshot_vision(url))
                else:
                    print_status("⚠️", "Usage: /webshot <url>", Colors.YELLOW)
                print()
                continue
            
            # ==========================================
            # ADVANCED COMPUTER USE COMMANDS
            # ==========================================
            
            # Journal Search & Download
            if user_input.lower().startswith('/journal '):
                query = user_input[9:].strip()
                if query:
                    asyncio.run(search_and_download_journal(query))
                else:
                    print_status("⚠️", "Usage: /journal <search query>", Colors.YELLOW)
                    print_status("💡", "Example: /journal Machine Learning IoT", Colors.DIM)
                    print_status("💡", "Example: /journal Deep Learning Computer Vision", Colors.DIM)
                print()
                continue
            
            # YouTube Play with Computer Use
            if user_input.lower().startswith('/ytplay '):
                query = user_input[8:].strip()
                if query:
                    asyncio.run(play_youtube_video(query))
                else:
                    print_status("⚠️", "Usage: /ytplay <search query>", Colors.YELLOW)
                    print_status("💡", "Example: /ytplay lofi hip hop music", Colors.DIM)
                    print_status("💡", "Example: /ytplay arduino tutorial beginner", Colors.DIM)
                print()
                continue
            
            # YouTube Search Only (no auto-play)
            if user_input.lower().startswith('/ytsearch '):
                query = user_input[10:].strip()
                if query:
                    asyncio.run(play_youtube_video(query, action="search_only"))
                else:
                    print_status("⚠️", "Usage: /ytsearch <query>", Colors.YELLOW)
                print()
                continue
            
            # Download file from URL
            if user_input.lower().startswith('/download '):
                args = user_input[10:].strip()
                parts = args.split(' ', 1)
                url = parts[0] if parts else ""
                filename = parts[1] if len(parts) > 1 else None
                if url:
                    asyncio.run(download_file_from_web(url, filename))
                else:
                    print_status("⚠️", "Usage: /download <url> [filename]", Colors.YELLOW)
                    print_status("💡", "Example: /download https://arxiv.org/pdf/2301.00001.pdf paper.pdf", Colors.DIM)
                print()
                continue
            
            # Browse and Interact with AI
            if user_input.lower().startswith('/interact '):
                args = user_input[10:].strip()
                parts = args.split(' ', 1)
                url = parts[0] if parts else ""
                task = parts[1] if len(parts) > 1 else "describe what you see on this page"
                if url:
                    asyncio.run(browse_and_interact(url, task))
                else:
                    print_status("⚠️", "Usage: /interact <url> <task>", Colors.YELLOW)
                    print_status("💡", "Example: /interact github.com find trending Python repositories", Colors.DIM)
                print()
                continue
            
            # Google search
            if user_input.lower().startswith('/google '):
                query = user_input[8:].strip()
                if query:
                    asyncio.run(search_google_web(query))
                else:
                    print_status("⚠️", "Usage: /google <search query>", Colors.YELLOW)
                print()
                continue
            
            # Browse website
            if user_input.lower().startswith('/browse '):
                url = user_input[8:].strip()
                if url:
                    asyncio.run(browse_website(url))
                else:
                    print_status("⚠️", "Usage: /browse <website>", Colors.YELLOW)
                print()
                continue
            
            # Generate file commands
            if user_input.lower().startswith('/word '):
                content = user_input[6:].strip()
                if content:
                    asyncio.run(generate_file('word', content))
                else:
                    print_status("⚠️", "Usage: /word <content>", Colors.YELLOW)
                print()
                continue
            
            if user_input.lower().startswith('/pdf '):
                content = user_input[5:].strip()
                if content:
                    asyncio.run(generate_file('pdf', content))
                else:
                    print_status("⚠️", "Usage: /pdf <content>", Colors.YELLOW)
                print()
                continue
            
            if user_input.lower().startswith('/txt '):
                content = user_input[5:].strip()
                if content:
                    asyncio.run(generate_file('txt', content))
                else:
                    print_status("⚠️", "Usage: /txt <content>", Colors.YELLOW)
                print()
                continue
            
            if user_input.lower().startswith('/md ') or user_input.lower().startswith('/markdown '):
                prefix_len = 4 if user_input.lower().startswith('/md ') else 10
                content = user_input[prefix_len:].strip()
                if content:
                    asyncio.run(generate_file('markdown', content))
                else:
                    print_status("⚠️", "Usage: /md <content>", Colors.YELLOW)
                print()
                continue
            
            if user_input.lower().startswith('/json '):
                content = user_input[6:].strip()
                if content:
                    asyncio.run(generate_file('json', content))
                else:
                    print_status("⚠️", "Usage: /json <json_data>", Colors.YELLOW)
                print()
                continue
            
            # Excel file
            if user_input.lower().startswith('/excel '):
                content = user_input[7:].strip()
                if content:
                    asyncio.run(generate_file('excel', content))
                else:
                    print_status("⚠️", "Usage: /excel <data>", Colors.YELLOW)
                print()
                continue
            
            # CSV file
            if user_input.lower().startswith('/csv '):
                content = user_input[5:].strip()
                if content:
                    asyncio.run(generate_file('csv', content))
                else:
                    print_status("⚠️", "Usage: /csv <data>", Colors.YELLOW)
                print()
                continue
            
            # List running apps
            if user_input.lower() in ['/apps', '/processes', '/ps']:
                asyncio.run(list_running_apps())
                print()
                continue
            
            # ==========================================
            # END SLASH COMMANDS
            # ==========================================
            
            # Research command (for schematic with deep research)
            if user_input.lower().startswith('/research '):
                topic = user_input[10:].strip()
                if topic:
                    asyncio.run(generate_schematic(topic, research_mode=True))
                else:
                    print_status("⚠️", "Usage: /research <topic>", Colors.YELLOW)
                print()
                continue
            
            # Schematic-only mode (explicit)
            if user_input.lower().startswith('/schematic ') or user_input.lower().startswith('/kicad '):
                prefix_len = 11 if user_input.lower().startswith('/schematic ') else 7
                request = user_input[prefix_len:].strip()
                if request:
                    asyncio.run(generate_schematic(request, research_mode=False))
                else:
                    print_status("⚠️", "Usage: /schematic <description>", Colors.YELLOW)
                print()
                continue
            
            # ==========================================
            # UNIFIED ReAct MODE - Natural Language Request
            # ==========================================
            # Semua request TANPA slash command akan diproses oleh ReAct Agent
            # Gemini sebagai otak akan memutuskan tool yang tepat
            
            print_status("🧠", "Processing with ReAct Agent (Gemini as brain)...", Colors.CYAN)
            asyncio.run(run_jawir_react(user_input, task_type="auto"))
            print()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted{Colors.ENDC}")
            break
        except EOFError:
            break


def print_help():
    """Print help message."""
    help_text = f"""
{Colors.BOLD}{Colors.CYAN}JAWIR OS - AI Assistant dari Ngawi{Colors.ENDC}
{Colors.DIM}{'─' * 70}{Colors.ENDC}

JAWIR adalah AI Assistant Jawa Terkuat dengan fitur {Colors.BOLD}Open Interpreter{Colors.ENDC}.
Menggunakan {Colors.BOLD}ReAct Pattern{Colors.ENDC} untuk hasil optimal.

{Colors.BOLD}🧠 ReAct Pattern (Natural Language):{Colors.ENDC}
  Ketik langsung dalam bahasa natural, JAWIR otomatis pilih tool!
  Contoh: {Colors.GREEN}putar lagu jazz di spotify{Colors.ENDC}
  Contoh: {Colors.GREEN}buka chrome dan cari tutorial python{Colors.ENDC}
  Contoh: {Colors.GREEN}buatkan dokumen word tentang IoT{Colors.ENDC}

{Colors.BOLD}{'═' * 70}{Colors.ENDC}
{Colors.BOLD}                    📋 SLASH COMMANDS{Colors.ENDC}
{Colors.BOLD}{'═' * 70}{Colors.ENDC}

{Colors.BOLD}🎵 SPOTIFY (Music Player):{Colors.ENDC}
  {Colors.CYAN}/spotify <query>{Colors.ENDC}    - 🔥 Search & PLAY musik di Spotify!
  {Colors.CYAN}/pause{Colors.ENDC}              - Pause musik
  {Colors.CYAN}/resume{Colors.ENDC}             - Resume/play musik
  {Colors.CYAN}/next{Colors.ENDC}               - Skip ke lagu berikutnya
  {Colors.CYAN}/prev{Colors.ENDC}               - Kembali ke lagu sebelumnya
  {Colors.CYAN}/stop{Colors.ENDC}               - Stop musik
  Contoh: {Colors.GREEN}/spotify bohemian rhapsody queen{Colors.ENDC}

{Colors.BOLD}🎬 YOUTUBE (Video Player):{Colors.ENDC}
  {Colors.CYAN}/yt <query>{Colors.ENDC}         - Search YouTube
  {Colors.CYAN}/play <query>{Colors.ENDC}       - 🔥 Search & PLAY video langsung!
  {Colors.CYAN}/ytlist <query>{Colors.ENDC}     - List hasil pencarian
  Contoh: {Colors.GREEN}/play tutorial arduino{Colors.ENDC}

{Colors.BOLD}🖥️ DESKTOP CONTROL:{Colors.ENDC}
  {Colors.CYAN}/open <app>{Colors.ENDC}         - Buka aplikasi desktop
  {Colors.CYAN}/close <app>{Colors.ENDC}        - Tutup aplikasi
  {Colors.CYAN}/url <url>{Colors.ENDC}          - Buka URL di browser
  {Colors.CYAN}/screenshot{Colors.ENDC}         - Ambil screenshot layar
  {Colors.CYAN}/apps{Colors.ENDC}               - List aplikasi yang berjalan
  
  {Colors.DIM}Apps: chrome, firefox, edge, spotify, vlc, calculator, notepad,
  vscode, word, excel, powerpoint, kicad, explorer, cmd, powershell{Colors.ENDC}

{Colors.BOLD}🐍 PYTHON INTERPRETER:{Colors.ENDC}
  {Colors.CYAN}/python <code>{Colors.ENDC}      - Execute Python code
  {Colors.CYAN}/py <code>{Colors.ENDC}          - Alias untuk /python
  {Colors.CYAN}/pip install <pkg>{Colors.ENDC}  - Install Python package
  Contoh: {Colors.GREEN}/python print("Hello JAWIR!"){Colors.ENDC}

{Colors.BOLD}🌐 WEB BROWSING:{Colors.ENDC}
  {Colors.CYAN}/google <query>{Colors.ENDC}     - Search Google
  {Colors.CYAN}/browse <website>{Colors.ENDC}   - Buka website
  {Colors.CYAN}/search <query>{Colors.ENDC}     - Web search (Tavily)

{Colors.BOLD}�️ COMPUTER USE (Gemini Vision Browser Automation):{Colors.ENDC}
  {Colors.CYAN}/cu <task>{Colors.ENDC}          - 🔥 Browser automation dengan natural language!
  {Colors.CYAN}/vbrowse <url> [task]{Colors.ENDC} - Visual browse dengan tugas spesifik
  {Colors.CYAN}/webfill <url> <data>{Colors.ENDC} - Isi form web otomatis
  {Colors.CYAN}/vsearch <query>{Colors.ENDC}    - Visual web search
  {Colors.CYAN}/webshot <url>{Colors.ENDC}      - Screenshot halaman web
  
  Contoh:
  {Colors.GREEN}/cu search python tutorials on youtube and click first video{Colors.ENDC}
  {Colors.GREEN}/vbrowse github.com/google find trending repositories{Colors.ENDC}
  {Colors.GREEN}/webfill login.com username=john password=secret{Colors.ENDC}
  {Colors.GREEN}/vsearch --youtube arduino beginner tutorial{Colors.ENDC}
  
  {Colors.DIM}Computer Use menggunakan Gemini Vision untuk "melihat" browser
  dan melakukan aksi seperti manusia (click, type, scroll, dll){Colors.ENDC}


{Colors.BOLD}📚 JOURNAL & RESEARCH (Auto Download!):{Colors.ENDC}
  {Colors.CYAN}/journal <query>{Colors.ENDC}    - 🔥 Search & DOWNLOAD jurnal dari arXiv!
  {Colors.CYAN}/download <url>{Colors.ENDC}     - Download file dari URL
  {Colors.CYAN}/interact <url> <task>{Colors.ENDC} - Browse & interact dengan AI
  
  Contoh:
  {Colors.GREEN}/journal Machine Learning IoT{Colors.ENDC}
  {Colors.GREEN}/journal Deep Learning Computer Vision{Colors.ENDC}
  {Colors.GREEN}/download https://arxiv.org/pdf/2301.00001.pdf{Colors.ENDC}
  {Colors.GREEN}/interact github.com find trending Python repos{Colors.ENDC}
  
  {Colors.DIM}Jurnal di-download otomatis ke folder: jawirv2/downloads/journals{Colors.ENDC}

{Colors.BOLD}🎬 YOUTUBE PLAY (Computer Use):{Colors.ENDC}
  {Colors.CYAN}/ytplay <query>{Colors.ENDC}     - 🔥 Search & PLAY video YouTube!
  {Colors.CYAN}/ytsearch <query>{Colors.ENDC}   - Search tanpa auto-play
  
  Contoh:
  {Colors.GREEN}/ytplay lofi hip hop music{Colors.ENDC}
  {Colors.GREEN}/ytplay tutorial arduino beginner{Colors.ENDC}
  
  {Colors.DIM}Browser terbuka, AI search & play video otomatis{Colors.ENDC}

{Colors.BOLD}�📄 FILE GENERATION:{Colors.ENDC}
  {Colors.CYAN}/word <content>{Colors.ENDC}     - Create Word (.docx)
  {Colors.CYAN}/pdf <content>{Colors.ENDC}      - Create PDF
  {Colors.CYAN}/txt <content>{Colors.ENDC}      - Create text file
  {Colors.CYAN}/md <content>{Colors.ENDC}       - Create Markdown
  {Colors.CYAN}/json <data>{Colors.ENDC}        - Create JSON
  {Colors.CYAN}/excel <data>{Colors.ENDC}       - Create Excel (.xlsx)
  {Colors.CYAN}/csv <data>{Colors.ENDC}         - Create CSV

{Colors.BOLD}📧 GOOGLE WORKSPACE:{Colors.ENDC}
  {Colors.CYAN}/gmail labels{Colors.ENDC}       - List Gmail labels
  {Colors.CYAN}/gmail search <q>{Colors.ENDC}   - Search emails
  {Colors.CYAN}/drive list{Colors.ENDC}         - List Drive files
  {Colors.CYAN}/calendar events{Colors.ENDC}    - List events

{Colors.BOLD}🔧 KICAD (Schematic):{Colors.ENDC}
  {Colors.CYAN}/schematic <desc>{Colors.ENDC}   - Generate schematic KiCad
  {Colors.CYAN}/research <topic>{Colors.ENDC}   - Deep research + schematic

{Colors.BOLD}⚙️ OTHER:{Colors.ENDC}
  {Colors.CYAN}/help{Colors.ENDC}  /clear  exit

{Colors.DIM}JAWIR OS © 2026 - AI Assistant Jawa Terkuat dari Ngawi 🇮🇩{Colors.ENDC}
"""
    print(help_text)



def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JAWIR OS - AI Assistant Jawa Terkuat dari Ngawi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
JAWIR adalah AI Assistant dengan berbagai tools:

Tools:
  🔧 KiCad Tool      : Generate schematic dari deskripsi
  🔍 Web Search Tool : Cari info komponen, datasheet, tutorial  
  🔬 Research Tool   : Deep research sebelum desain
  📧 Google Workspace: Gmail, Drive, Calendar, Sheets, Forms

Examples:
  python kicad_cli.py -i                           (interactive - akses semua tools)
  python kicad_cli.py "ESP32 dengan LED"           (KiCad tool)
  python kicad_cli.py -s "ESP32 DHT11 wiring"      (Web Search tool)
  python kicad_cli.py -r "IoT weather station"     (Research + KiCad tool)
  python kicad_cli.py -g                           (Google Workspace mode)
        """
    )
    parser.add_argument(
        'request',
        nargs='?',
        help='Deskripsi rangkaian (menggunakan KiCad tool)'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode - akses semua tools JAWIR'
    )
    parser.add_argument(
        '-r', '--research',
        action='store_true',
        help='🔬 Research tool - riset dulu sebelum generate schematic'
    )
    parser.add_argument(
        '-s', '--search',
        type=str,
        help='🔍 Web Search tool - cari info komponen/tutorial'
    )
    parser.add_argument(
        '-g', '--google',
        action='store_true',
        help='📧 Google Workspace mode - Gmail, Drive, Calendar, Sheets, Forms'
    )
    
    args = parser.parse_args()
    
    # Google Workspace mode
    if args.google:
        tools_dir = os.path.dirname(os.path.dirname(__file__))
        gws_script = os.path.join(tools_dir, "google_workspace.py")
        if os.path.exists(gws_script):
            os.system(f'python "{gws_script}" -i')
        else:
            print_status("❌", "Google Workspace tool not found", Colors.RED)
        return
    
    # Web search only mode
    if args.search:
        print_banner()
        asyncio.run(do_web_search(args.search))
        return
    
    # Interactive mode
    if args.interactive or (args.request is None and not args.search):
        interactive_mode()
        return
    
    # Direct generation with optional research
    print_banner()
    success = asyncio.run(generate_schematic(args.request, research_mode=args.research))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
