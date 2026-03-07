#!/usr/bin/env python
"""
JAWIR OS - Command Line Interface
==================================
Chat dengan JAWIR langsung dari terminal!

Usage:
    python jawir_cli.py                    # Interactive mode
    python jawir_cli.py "your message"     # Single message mode
    python jawir_cli.py --test             # Test all tools
"""

import asyncio
import json
import sys
import os
import argparse
import websockets
import uuid
from datetime import datetime
from pathlib import Path

# Session file for persistence
SESSION_FILE = Path.home() / ".jawir" / "session_id"

def get_session_id() -> str:
    """Get or create persistent session ID."""
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SESSION_FILE.exists():
            session_id = SESSION_FILE.read_text().strip()
            if session_id:
                return session_id
        # Create new session
        session_id = str(uuid.uuid4())
        SESSION_FILE.write_text(session_id)
        return session_id
    except Exception:
        return str(uuid.uuid4())

def clear_session_id():
    """Clear session ID file for fresh start."""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
            return True
    except Exception:
        pass
    return False


# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


# Track ReAct steps globally for display
class ReActTracker:
    """Track and display ReAct steps cumulatively."""
    
    def __init__(self):
        self.steps = []
        self.tools_executed = []
        self.current_iteration = 0
        self.start_time = None
    
    def reset(self):
        """Reset tracker for new query."""
        self.steps = []
        self.tools_executed = []
        self.current_iteration = 0
        self.start_time = datetime.now()
    
    def add_step(self, step_type: str, message: str, details: dict = None):
        """Add a step to the tracker."""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        self.steps.append({
            "type": step_type,
            "message": message,
            "details": details or {},
            "elapsed": elapsed,
        })
        
        # Track tool executions
        if step_type == "executing_tool":
            tool_name = details.get("tool", message) if details else message
            self.tools_executed.append(tool_name)
    
    def print_step(self, step_type: str, message: str, details: dict = None):
        """Print a single step with formatting."""
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        time_str = f"[{elapsed:5.1f}s]"
        
        # ============================================
        # ReAct LOOP DISPLAY:
        # ITERATION → THINKING → PLANNING → ACTION → OBSERVE → (loop)
        # ============================================
        
        if step_type == "iteration_start":
            iteration = details.get("iteration", 1) if details else 1
            max_iter = details.get("max", 7) if details else 7
            print(f"\n{Colors.BOLD}{Colors.BLUE}━━━ ReAct Loop {iteration}/{max_iter} ━━━{Colors.ENDC}")
            
        elif step_type == "thinking":
            # Show actual thought content, not generic message
            thought_preview = message if message else "Menganalisis..."
            if len(thought_preview) > 120:
                thought_preview = thought_preview[:120] + "..."
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.YELLOW}💭 THINKING:{Colors.ENDC} {thought_preview}")
            
        elif step_type == "planning":
            # Show list of tools to execute
            tools = details.get("tools", []) if details else []
            count = details.get("count", len(tools)) if details else len(tools)
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.CYAN}📋 PLANNING:{Colors.ENDC} {count} aksi direncanakan")
            for i, tool in enumerate(tools[:5], 1):
                print(f"              {Colors.DIM}├─ {i}. {tool}{Colors.ENDC}")
                
        elif step_type == "executing_tool":
            tool_name = details.get("tool", message) if details else message
            tool_idx = len(self.tools_executed)
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.GREEN}🔧 ACTION [{tool_idx}]:{Colors.ENDC} {tool_name}")
            if details and details.get("args"):
                args_str = str(details["args"])
                if len(args_str) > 80:
                    args_str = args_str[:80] + "..."
                print(f"              {Colors.DIM}└─ params: {args_str}{Colors.ENDC}")
                
        elif step_type == "observation":
            # Show result from tool
            result = message if message else "No result"
            if len(result) > 150:
                result = result[:150] + "..."
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.MAGENTA}👁️ OBSERVE:{Colors.ENDC} {result}")
            
        elif step_type == "tool_result":
            # Fallback for old format
            result_preview = message[:100] if message else "No result"
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.MAGENTA}👀 RESULT:{Colors.ENDC} {result_preview}")
            
        elif step_type == "tool_completed":
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.GREEN}✅ DONE:{Colors.ENDC} {message}")
            
        elif step_type == "tool_error":
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.RED}❌ TOOL ERROR:{Colors.ENDC} {message}")
            
        elif step_type == "done":
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.GREEN}✅ COMPLETE:{Colors.ENDC} {message}")
            
        elif step_type == "error":
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.RED}❌ ERROR:{Colors.ENDC} {message}")
            
        else:
            # Generic fallback
            print(f"{Colors.DIM}{time_str}{Colors.ENDC} {Colors.DIM}ℹ️ {step_type}:{Colors.ENDC} {message}")
    
    def print_summary(self):
        """Print summary of all steps."""
        if not self.steps:
            return
        
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        tools_count = len(self.tools_executed)
        
        print(f"\n{Colors.DIM}─── Summary: {tools_count} tools, {elapsed:.1f}s total ───{Colors.ENDC}")


# Global tracker instance
react_tracker = ReActTracker()


def print_banner():
    """Print JAWIR banner."""
    session_id = get_session_id()
    banner = f"""
{Colors.CYAN}╭──────────────────────────────────────────────────────────────────────────────╮
│   {Colors.BOLD}██╗ █████╗ ██╗    ██╗██╗██████╗ {Colors.ENDC}{Colors.CYAN}     CLI                                   │
│   {Colors.BOLD}██║██╔══██╗██║    ██║██║██╔══██╗{Colors.ENDC}{Colors.CYAN}     Just Another Wise Intelligent Resource │
│   {Colors.BOLD}██║███████║██║ █╗ ██║██║██████╔╝{Colors.ENDC}{Colors.CYAN}                                           │
│   {Colors.BOLD}██║██╔══██║██║███╗██║██║██╔══██╗{Colors.ENDC}{Colors.CYAN}                                           │
│   {Colors.BOLD}██║██║  ██║╚███╔███╔╝██║██║  ██║{Colors.ENDC}{Colors.CYAN}                                           │
│   {Colors.BOLD}╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝{Colors.ENDC}{Colors.CYAN}                                           │
│                                                                              │
│  {Colors.GREEN}Profile{Colors.CYAN} : default            {Colors.GREEN}Model{Colors.CYAN} : gemini-3-pro      {Colors.GREEN}Mode{Colors.CYAN} : AGENT ✅    │
│  {Colors.YELLOW}Tools{Colors.CYAN}   : Web ✅  Python ✅  KiCAD ✅  Desktop ✅  Google ✅             │
│  {Colors.MAGENTA}Session{Colors.CYAN} : {session_id[:8]}...        {Colors.MAGENTA}Server{Colors.CYAN} : localhost:8000              │
│                                                                              │
│  {Colors.BOLD}Quick Commands{Colors.ENDC}{Colors.CYAN}                                                             │
│   • {Colors.GREEN}/ask{Colors.CYAN}  "pertanyaan apapun"                                              │
│   • {Colors.GREEN}/web{Colors.CYAN}  "cari info terbaru tentang..."                                   │
│   • {Colors.GREEN}/py{Colors.CYAN}   "hitung faktorial 100"                                           │
│   • {Colors.GREEN}/gmail{Colors.CYAN} "cari email dari..."                                            │
│   • {Colors.GREEN}/drive{Colors.CYAN} "list file di drive"                                            │
│   • {Colors.GREEN}/open{Colors.CYAN} "notepad" atau "chrome"                                          │
│                                                                              │
│  {Colors.DIM}Tips: ketik /help • /test untuk test tools • exit untuk keluar{Colors.CYAN}        │
╰──────────────────────────────────────────────────────────────────────────────╯{Colors.ENDC}
"""
    print(banner)


def print_help():
    """Print help message."""
    help_text = f"""
{Colors.CYAN}╭──────────────────────────────────────────────────────────────────────────────╮
│  {Colors.BOLD}JAWIR CLI - Help & Commands{Colors.ENDC}{Colors.CYAN}                                                  │
╰──────────────────────────────────────────────────────────────────────────────╯{Colors.ENDC}

{Colors.BOLD}System Commands:{Colors.ENDC}
  {Colors.GREEN}exit{Colors.ENDC}      - Keluar dari CLI
  {Colors.GREEN}clear{Colors.ENDC}     - Bersihkan layar
  {Colors.GREEN}help{Colors.ENDC}      - Tampilkan bantuan ini
  {Colors.GREEN}test{Colors.ENDC}      - Test semua tools

{Colors.BOLD}Slash Commands:{Colors.ENDC}
  {Colors.CYAN}/ask{Colors.ENDC}   <pertanyaan>     - Tanya apapun ke JAWIR
  {Colors.CYAN}/web{Colors.ENDC}   <query>          - Cari di internet (Tavily)
  {Colors.CYAN}/py{Colors.ENDC}    <code>           - Jalankan kode Python
  {Colors.CYAN}/gmail{Colors.ENDC} <action>         - Operasi Gmail (search/send)
  {Colors.CYAN}/drive{Colors.ENDC} <action>         - Operasi Google Drive
  {Colors.CYAN}/calendar{Colors.ENDC} <action>      - Operasi Google Calendar
  {Colors.CYAN}/sheets{Colors.ENDC} <action>        - Operasi Google Sheets
  {Colors.CYAN}/docs{Colors.ENDC}  <action>         - Operasi Google Docs
  {Colors.CYAN}/open{Colors.ENDC}  <app>            - Buka aplikasi desktop
  {Colors.CYAN}/kicad{Colors.ENDC} <desc>           - Buat skematik elektronik

{Colors.BOLD}Available Tools (19):{Colors.ENDC}
  {Colors.YELLOW}🔍 Web Search{Colors.ENDC}      - Cari real-time di internet
  {Colors.YELLOW}🐍 Python Exec{Colors.ENDC}     - Jalankan kode Python
  {Colors.YELLOW}⚡ KiCAD{Colors.ENDC}           - Generate skematik elektronik
  {Colors.YELLOW}📧 Gmail{Colors.ENDC}           - Search & Send email
  {Colors.YELLOW}📁 Drive{Colors.ENDC}           - Search & List files
  {Colors.YELLOW}📅 Calendar{Colors.ENDC}        - Events & Schedules
  {Colors.YELLOW}📊 Sheets{Colors.ENDC}          - Read, Write, Create
  {Colors.YELLOW}📝 Docs{Colors.ENDC}            - Read & Create documents
  {Colors.YELLOW}📋 Forms{Colors.ENDC}           - Read & Create forms
  {Colors.YELLOW}🖥️ Desktop{Colors.ENDC}         - Open/Close apps, URLs

{Colors.DIM}Tip: Kamu bisa langsung ketik pertanyaan tanpa slash command{Colors.ENDC}
"""
    print(help_text)


async def send_message(message: str, timeout: int = 600, show_react: bool = True) -> str:
    """Send message to JAWIR via WebSocket with robust ReAct display.
    
    Features:
    - Ping/pong keepalive every 15 seconds
    - Cumulative step logging (no overwriting)
    - Progress tracking with timestamps
    - Extended timeout for complex queries (600s = 10 min default)
    - Graceful timeout handling with partial results
    """
    uri = "ws://localhost:8000/ws/chat"
    session_id = get_session_id()
    
    # Reset tracker for new query
    if show_react:
        react_tracker.reset()
    
    try:
        async with websockets.connect(
            uri, 
            ping_interval=20,  # Send ping every 20s
            ping_timeout=120,  # Wait 120s for pong (for long-running operations)
            close_timeout=10,
            max_size=10_000_000  # 10MB max message size
        ) as ws:
            # Send message with session_id
            msg = {
                "type": "user_message", 
                "data": {
                    "content": message,
                    "session_id": session_id,
                }
            }
            await ws.send(json.dumps(msg))
            
            # Track accumulated info for timeout recovery
            last_status = ""
            tools_started = []
            tools_completed = []
            last_activity = datetime.now()
            
            # Wait for response with progress display
            full_response = ""
            total_timeout = timeout  # 600s total
            start_time = datetime.now()
            
            while True:
                try:
                    # Shorter recv timeout for responsiveness
                    response = await asyncio.wait_for(ws.recv(), timeout=20)
                    last_activity = datetime.now()
                    data = json.loads(response)
                    msg_type = data.get("type", "")
                    
                    # ============================================
                    # Handle ReAct Status Updates (CUMULATIVE)
                    # ============================================
                    if msg_type == "agent_status" and show_react:
                        status = data.get("status", "")
                        message_text = data.get("message", "")
                        details = data.get("details", {})
                        
                        last_status = status
                        
                        # Add to tracker and print (cumulative, no clearing)
                        react_tracker.add_step(status, message_text, details)
                        react_tracker.print_step(status, message_text, details)
                        
                        # Track tools for timeout recovery
                        if status == "executing_tool":
                            tool_name = details.get("tool", message_text)
                            tools_started.append(tool_name)
                        elif status in ["tool_completed", "done"]:
                            tools_completed.append(message_text)
                        
                        continue
                    
                    # ============================================
                    # Handle Tool Result Cards
                    # ============================================
                    elif msg_type == "tool_result" and show_react:
                        tool_name = data.get("tool_name", "unknown")
                        status = data.get("status", "")
                        tool_data = data.get("data", {})
                        
                        if status == "success":
                            title = tool_data.get("title", "")[:50] if tool_data.get("title") else ""
                            msg = f"{tool_name}: {title}" if title else tool_name
                            react_tracker.add_step("tool_completed", msg, {"tool": tool_name})
                            react_tracker.print_step("tool_completed", msg, {"tool": tool_name})
                        continue
                    
                    # ============================================
                    # Handle Final Response
                    # ============================================
                    elif msg_type == "agent_response":
                        content = data.get("content", "") or data.get("data", {}).get("content", "")
                        
                        # Print summary
                        if show_react:
                            react_tracker.print_summary()
                        
                        return content
                    
                    elif msg_type == "error":
                        error_msg = data.get('message', '') or data.get('data', {}).get('message', 'Unknown error')
                        if show_react:
                            react_tracker.print_step("error", error_msg)
                        return f"Error: {error_msg}"
                    
                    elif msg_type == "stream":
                        chunk = data.get("content", "") or data.get("data", {}).get("content", "")
                        full_response += chunk
                        
                except asyncio.TimeoutError:
                    # Check total elapsed time and recent activity
                    total_elapsed = (datetime.now() - start_time).total_seconds()
                    idle_time = (datetime.now() - last_activity).total_seconds()
                    
                    # Check total timeout first
                    if total_elapsed >= total_timeout:
                        if full_response:
                            if show_react:
                                react_tracker.print_summary()
                            return full_response
                        
                        # Real timeout
                        timeout_msg = f"Timeout setelah {total_elapsed:.0f} detik"
                        if tools_started:
                            timeout_msg += f"\n\n{Colors.YELLOW}Progress sebelum timeout:{Colors.ENDC}"
                            timeout_msg += f"\n  • Tools dimulai: {', '.join(tools_started)}"
                            timeout_msg += f"\n  • Tools selesai: {', '.join(tools_completed) if tools_completed else 'belum ada'}"
                            timeout_msg += f"\n  • Status terakhir: {last_status}"
                        
                        if show_react:
                            react_tracker.print_step("error", "Timeout - query terlalu kompleks atau server lambat")
                            react_tracker.print_summary()
                        
                        return timeout_msg
                    
                    # Still within total timeout - show waiting message
                    elapsed = total_elapsed
                    print(f"{Colors.DIM}[{elapsed:5.1f}s] ⏳ Waiting for response... (last: {last_status}){Colors.ENDC}")
                    continue
                    
    except ConnectionRefusedError:
        return "Error: Cannot connect to JAWIR server. Is it running on port 8000?"
    except websockets.exceptions.ConnectionClosedError as e:
        if show_react:
            react_tracker.print_step("error", f"Connection closed: {e}")
            react_tracker.print_summary()
        if full_response:
            return full_response
        return f"Error: Connection closed unexpectedly"
    except Exception as e:
        if show_react:
            react_tracker.print_step("error", str(e))
        return f"Error: {str(e)}"


async def test_all_tools():
    """Test all JAWIR tools with various prompts."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}  🧪 JAWIR CLI - FULL TOOL TEST{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")
    
    tests = [
        # Basic Chat
        ("Halo JAWIR, siapa kamu?", "Chat Biasa"),
        
        # Web Search
        ("Cari info terbaru tentang AI di tahun 2026", "Web Search"),
        
        # Python Execution
        ("Hitung faktorial 20 pakai Python", "Python Exec"),
        
        # Desktop Control
        ("Buka aplikasi notepad", "Open App"),
        
        # Gmail
        ("Tampilkan label gmail saya", "Gmail Labels"),
        ("Cari email dari Google di inbox saya", "Gmail Search"),
        
        # Drive
        ("List 5 file terbaru di Google Drive saya", "Drive List"),
        
        # Calendar
        ("Tampilkan daftar kalender Google saya", "Calendar List"),
        
        # Sheets
        ("Buat spreadsheet baru dengan nama 'JAWIR CLI Test'", "Sheets Create"),
        
        # Docs
        ("Buat dokumen Google baru dengan judul 'JAWIR CLI Doc Test' berisi 'Hello from JAWIR CLI!'", "Docs Create"),
        
        # KiCAD (optional - takes longer)
        # ("Buat skematik LED dengan resistor 330 ohm", "KiCAD"),
    ]
    
    results = []
    
    for i, (prompt, name) in enumerate(tests, 1):
        print(f"{Colors.YELLOW}[{i}/{len(tests)}] Testing: {name}{Colors.ENDC}")
        print(f"{Colors.DIM}  Prompt: {prompt[:50]}...{Colors.ENDC}")
        
        start = datetime.now()
        response = await send_message(prompt, timeout=90)
        elapsed = (datetime.now() - start).total_seconds()
        
        # Check if successful (no error in response)
        success = not response.startswith("Error:") and not response.startswith("Timeout:")
        
        if success:
            print(f"{Colors.GREEN}  ✅ PASS ({elapsed:.1f}s){Colors.ENDC}")
            # Show truncated response
            response_preview = response[:150].replace('\n', ' ')
            print(f"{Colors.DIM}  Response: {response_preview}...{Colors.ENDC}")
        else:
            print(f"{Colors.RED}  ❌ FAIL ({elapsed:.1f}s){Colors.ENDC}")
            print(f"{Colors.RED}  {response[:100]}{Colors.ENDC}")
        
        results.append((name, success, elapsed))
        print()
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}📊 TEST SUMMARY{Colors.ENDC}")
    print(f"{'='*60}")
    
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    
    for name, ok, elapsed in results:
        status = f"{Colors.GREEN}✅{Colors.ENDC}" if ok else f"{Colors.RED}❌{Colors.ENDC}"
        print(f"  {status} {name} ({elapsed:.1f}s)")
    
    print(f"\n  {Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  {total - passed} tests failed{Colors.ENDC}")
    
    return passed == total


async def interactive_mode():
    """Run interactive chat mode."""
    print_banner()
    
    while True:
        try:
            # Get user input with styled prompt
            user_input = input(f"\n{Colors.CYAN}jawir›{Colors.ENDC} ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            cmd = user_input.lower()
            if cmd == 'exit' or cmd == '/exit' or cmd == '/quit':
                print(f"\n{Colors.CYAN}Sampai jumpa! 👋 Matur nuwun sampun ngginakaken JAWIR.{Colors.ENDC}\n")
                break
            elif cmd == 'clear' or cmd == '/clear':
                # Clear screen AND reset memory
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{Colors.YELLOW}🗑️ Clearing conversation memory...{Colors.ENDC}")
                # Send clear command to server
                clear_response = await send_message("/system:clear_memory", show_react=False)
                # Also clear local session file for new session
                clear_session_id()
                print(f"{Colors.GREEN}✅ Memory cleared! Starting fresh conversation.{Colors.ENDC}")
                print_banner()
                continue
            elif cmd == '/newsession':
                # Start completely new session
                clear_session_id()
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{Colors.GREEN}✅ New session started!{Colors.ENDC}")
                print_banner()
                continue
            elif cmd == '/memory' or cmd == '/status':
                # Show memory status
                response = await send_message("/system:memory_status", show_react=False)
                print(f"\n{Colors.CYAN}📊 Memory Status:{Colors.ENDC}")
                print(response)
                continue
            elif cmd == 'help' or cmd == '/help':
                print_help()
                continue
            elif cmd == 'tools' or cmd == '/tools':
                print_help()
                continue
            elif cmd == 'test' or cmd == '/test':
                await test_all_tools()
                continue
            
            # Handle slash commands
            if user_input.startswith('/'):
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command == '/ask':
                    user_input = args
                elif command == '/web':
                    user_input = f"Cari di internet: {args}"
                elif command == '/py' or command == '/python':
                    user_input = f"Jalankan kode Python: {args}"
                elif command == '/gmail':
                    user_input = f"Gmail: {args}"
                elif command == '/drive':
                    user_input = f"Google Drive: {args}"
                elif command == '/calendar':
                    user_input = f"Google Calendar: {args}"
                elif command == '/sheets':
                    user_input = f"Google Sheets: {args}"
                elif command == '/docs':
                    user_input = f"Google Docs: {args}"
                elif command == '/open':
                    user_input = f"Buka aplikasi: {args}"
                elif command == '/kicad':
                    user_input = f"Buat skematik KiCAD: {args}"
            
            # Send to JAWIR with progress tracking
            print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
            print(f"{Colors.BOLD}🤖 JAWIR Processing...{Colors.ENDC}")
            print(f"{Colors.DIM}{'─' * 60}{Colors.ENDC}")
            
            response = await send_message(user_input)
            
            # Print response with formatting
            print(f"\n{Colors.GREEN}┌{'─' * 70}┐{Colors.ENDC}")
            print(f"{Colors.GREEN}│{Colors.ENDC} {Colors.BOLD}JAWIR{Colors.ENDC}")
            print(f"{Colors.GREEN}├{'─' * 70}┤{Colors.ENDC}")
            
            # Word wrap response - handle multi-line properly
            import textwrap
            for paragraph in response.split('\n'):
                if paragraph.strip():
                    wrapped = textwrap.fill(paragraph, width=68)
                    for line in wrapped.split('\n'):
                        # Truncate very long lines
                        if len(line) > 68:
                            line = line[:65] + "..."
                        print(f"{Colors.GREEN}│{Colors.ENDC} {line}")
                else:
                    print(f"{Colors.GREEN}│{Colors.ENDC}")
            
            print(f"{Colors.GREEN}└{'─' * 70}┘{Colors.ENDC}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Sampai jumpa! 👋{Colors.ENDC}\n")
            break
        except EOFError:
            break


async def single_message_mode(message: str):
    """Send a single message and exit."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    response = await send_message(message)
    print(response)
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="JAWIR CLI - Chat with JAWIR from terminal")
    parser.add_argument("message", nargs="?", help="Message to send (optional)")
    parser.add_argument("--test", action="store_true", help="Test all tools")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_all_tools())
    elif args.message:
        asyncio.run(single_message_mode(args.message))
    else:
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
