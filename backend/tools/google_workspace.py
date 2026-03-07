#!/usr/bin/env python
"""
JAWIR OS - Google Workspace Integration Tool
==========================================================
Tool untuk mengakses Google Workspace (Gmail, Drive, Calendar, Sheets, Forms)
melalui MCP Server.

AVAILABLE TOOLS:
- 📧 Gmail      : Baca, kirim, search email
- 📁 Drive      : Upload, download, search file
- 📅 Calendar   : Buat event, lihat jadwal
- 📊 Sheets     : Baca, tulis spreadsheet
- 📝 Forms      : Buat, lihat form responses

Usage:
    python google_workspace.py -i                              (interactive mode)
    python google_workspace.py --gmail-labels                  (list Gmail labels)
    python google_workspace.py --gmail-search "from:google"    (search emails)
    python google_workspace.py --drive-list                    (list Drive files)
    python google_workspace.py --calendar-list                 (list calendars)

Commands in Interactive Mode:
    /gmail <action>     - 📧 Gmail operations
    /drive <action>     - 📁 Drive operations
    /calendar <action>  - 📅 Calendar operations
    /sheets <action>    - 📊 Sheets operations
    /forms <action>     - 📝 Forms operations
    /help               - Show help
    /clear              - Clear screen
    exit                - Exit
"""

import os
import sys
import asyncio
import argparse
import json
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path

# Setup path
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

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
    MAGENTA = '\033[35m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


def print_banner():
    """Print JAWIR Google Workspace banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
     ██╗ █████╗ ██╗    ██╗██╗██████╗      ██████╗ ███████╗
     ██║██╔══██╗██║    ██║██║██╔══██╗    ██╔═══██╗██╔════╝
     ██║███████║██║ █╗ ██║██║██████╔╝    ██║   ██║███████╗
██   ██║██╔══██║██║███╗██║██║██╔══██╗    ██║   ██║╚════██║
╚█████╔╝██║  ██║╚███╔███╔╝██║██║  ██║    ╚██████╔╝███████║
 ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝
{Colors.ENDC}
{Colors.MAGENTA}            ━━━ Google Workspace Integration ━━━{Colors.ENDC}
{Colors.YELLOW}          AI Assistant dari Ngawi - Jawa Terkuat!{Colors.ENDC}
{Colors.DIM}  ════════════════════════════════════════════════════════════{Colors.ENDC}
{Colors.DIM}  Tools: 📧 Gmail | 📁 Drive | 📅 Calendar | 📊 Sheets | 📝 Forms | 📄 Docs{Colors.ENDC}
"""
    print(banner)


def print_status(icon: str, message: str, color: str = Colors.ENDC):
    """Print status message with icon."""
    print(f"{color}{icon} {message}{Colors.ENDC}")


def print_section(title: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'═' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}  {title}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'═' * 60}{Colors.ENDC}\n")


def print_table(headers: List[str], rows: List[List[str]], max_width: int = 50):
    """Print formatted table."""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], min(len(str(cell)), max_width))
    
    # Print header
    header_line = " │ ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(f"{Colors.BOLD}{header_line}{Colors.ENDC}")
    print("─" * (sum(col_widths) + 3 * (len(headers) - 1)))
    
    # Print rows
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell_str = str(cell)[:max_width]
            if i < len(col_widths):
                cells.append(cell_str.ljust(col_widths[i]))
            else:
                cells.append(cell_str)
        print(" │ ".join(cells))


# ============================================
# GOOGLE WORKSPACE MCP CLIENT
# ============================================

class GoogleWorkspaceMCP:
    """
    Client untuk Google Workspace MCP Server.
    Menggunakan CLI mode untuk eksekusi tool.
    """
    
    def __init__(self, user_email: str = None):
        self.user_email = user_email or os.getenv("USER_GOOGLE_EMAIL", "hazzikiraju@gmail.com")
        self.mcp_path = self._find_mcp_path()
        self.tools_enabled = ["gmail", "drive", "calendar", "sheets", "forms", "docs"]
        
        if not self.mcp_path:
            raise ValueError("Google Workspace MCP not found. Please check installation.")
    
    def _find_mcp_path(self) -> Optional[str]:
        """Find the Google Workspace MCP installation path."""
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), 
                        "google_workspace_mcp"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))), 
                        "google_workspace_mcp"),
            "D:\\jawirv2\\google_workspace_mcp",
        ]
        
        for path in possible_paths:
            if os.path.exists(os.path.join(path, "main.py")):
                return path
        
        return None
    
    def _run_cli_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run MCP tool via CLI.
        
        Args:
            tool_name: Name of the tool to run
            params: Parameters for the tool
        
        Returns:
            dict with result or error
        """
        if params is None:
            params = {}
        
        # Always include user email
        params["user_google_email"] = self.user_email
        
        # Find Python executable - use same venv as backend
        python_exe = sys.executable  # Use current Python interpreter
        
        # Build command
        cmd = [
            python_exe, "main.py",
            "--single-user",
            "--tools", *self.tools_enabled,
            "--cli", tool_name
        ]
        
        # Prepare input JSON
        input_json = json.dumps(params)
        
        try:
            # Run command
            env = os.environ.copy()
            env["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                cmd,
                input=input_json,
                capture_output=True,
                text=True,
                cwd=self.mcp_path,
                env=env,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            # Parse output
            output = result.stdout.strip()
            
            # Check for errors
            if result.returncode != 0 or "Error:" in output:
                return {
                    "success": False,
                    "error": result.stderr or output,
                    "output": output
                }
            
            return {
                "success": True,
                "output": output,
                "raw": result.stdout
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== GMAIL ====================
    
    def list_gmail_labels(self) -> Dict[str, Any]:
        """List all Gmail labels."""
        return self._run_cli_tool("list_gmail_labels")
    
    def search_gmail(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search Gmail messages."""
        return self._run_cli_tool("search_gmail_messages", {
            "query": query,
            "page_size": max_results
        })
    
    def get_gmail_message(self, message_id: str) -> Dict[str, Any]:
        """Get a specific Gmail message."""
        return self._run_cli_tool("get_gmail_message", {
            "message_id": message_id
        })
    
    def send_email(self, to: str, subject: str, body: str, 
                   cc: str = None, bcc: str = None) -> Dict[str, Any]:
        """Send an email."""
        params = {
            "to": to,
            "subject": subject,
            "body": body
        }
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        return self._run_cli_tool("send_gmail_message", params)
    
    def create_gmail_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create a Gmail draft."""
        return self._run_cli_tool("draft_gmail_message", {
            "to": to,
            "subject": subject,
            "body": body
        })
    
    # ==================== DRIVE ====================
    
    def search_drive_files(self, query: str = "*") -> Dict[str, Any]:
        """Search files in Google Drive."""
        return self._run_cli_tool("search_drive_files", {
            "query": query
        })
    
    def get_drive_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get info about a Drive file."""
        return self._run_cli_tool("get_drive_file_content", {
            "file_id": file_id
        })
    
    def create_drive_file(self, file_name: str, content: str, 
                          folder_id: str = "root") -> Dict[str, Any]:
        """Create a file in Drive with content."""
        return self._run_cli_tool("create_drive_file", {
            "file_name": file_name,
            "content": content,
            "folder_id": folder_id
        })
    
    def create_drive_folder(self, folder_name: str, parent_id: str = "root") -> Dict[str, Any]:
        """Create a folder in Drive."""
        return self._run_cli_tool("create_drive_file", {
            "file_name": folder_name,
            "mime_type": "application/vnd.google-apps.folder",
            "folder_id": parent_id,
            "content": ""  # Empty content for folder
        })
    
    def list_drive_items(self, folder_id: str = "root") -> Dict[str, Any]:
        """List items in a Drive folder."""
        return self._run_cli_tool("list_drive_items", {
            "folder_id": folder_id
        })
    
    def upload_drive_file(self, file_path: str, name: str = None, 
                          folder_id: str = None) -> Dict[str, Any]:
        """Upload a file to Drive."""
        # Note: This MCP doesn't have direct upload, use create_drive_file with fileUrl
        params = {"file_name": name or os.path.basename(file_path)}
        if folder_id:
            params["folder_id"] = folder_id
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                params["content"] = f.read()
        except:
            # Binary file - use file URL
            params["fileUrl"] = f"file://{os.path.abspath(file_path)}"
        return self._run_cli_tool("create_drive_file", params)
    
    def download_drive_file(self, file_id: str, destination: str) -> Dict[str, Any]:
        """Download a file from Drive."""
        return self._run_cli_tool("download_drive_file", {
            "file_id": file_id,
            "destination": destination
        })
    
    # ==================== CALENDAR ====================
    
    def list_calendars(self) -> Dict[str, Any]:
        """List all calendars."""
        return self._run_cli_tool("list_calendars")
    
    def list_events(self, calendar_id: str = "primary", 
                    max_results: int = 10) -> Dict[str, Any]:
        """List events from a calendar."""
        return self._run_cli_tool("get_events", {
            "calendar_id": calendar_id,
            "max_results": max_results
        })
    
    # Alias for list_events
    def list_calendar_events(self, calendar_id: str = "primary", 
                             max_results: int = 10) -> Dict[str, Any]:
        """Alias for list_events."""
        return self.list_events(calendar_id, max_results)
    
    def create_event(self, summary: str, start_time: str, end_time: str,
                     description: str = None, location: str = None,
                     calendar_id: str = "primary") -> Dict[str, Any]:
        """Create a calendar event."""
        params = {
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time,
            "calendar_id": calendar_id
        }
        if description:
            params["description"] = description
        if location:
            params["location"] = location
        return self._run_cli_tool("create_event", params)
    
    # Alias for create_event
    def add_calendar_event(self, summary: str, start_time: str, end_time: str,
                           description: str = None, location: str = None,
                           calendar_id: str = "primary") -> Dict[str, Any]:
        """Alias for create_event."""
        return self.create_event(summary, start_time, end_time, description, location, calendar_id)
    
    def quick_add_event(self, text: str, calendar_id: str = "primary") -> Dict[str, Any]:
        """Quick add event using natural language. Parses text and creates event."""
        from datetime import datetime, timedelta
        import re
        
        # Parse natural language text
        # Example: "Meeting besok jam 10 pagi" or "Lunch at 2pm tomorrow"
        now = datetime.now()
        summary = text
        
        # Default 1 hour event
        start_dt = now + timedelta(hours=1)
        end_dt = start_dt + timedelta(hours=1)
        
        # Try to parse time from text
        time_patterns = [
            (r'jam (\d{1,2})\s*(pagi|siang|sore|malam)?', 'id'),
            (r'(\d{1,2}):(\d{2})\s*(am|pm)?', 'en'),
            (r'(\d{1,2})\s*(am|pm)', 'en'),
        ]
        
        for pattern, lang in time_patterns:
            match = re.search(pattern, text.lower())
            if match:
                if lang == 'id':
                    hour = int(match.group(1))
                    period = match.group(2) if match.group(2) else ''
                    if period in ['sore', 'malam'] and hour < 12:
                        hour += 12
                    elif period == 'pagi' and hour == 12:
                        hour = 0
                else:
                    hour = int(match.group(1))
                    if len(match.groups()) >= 2 and match.group(2):
                        minute = int(match.group(2)) if match.group(2).isdigit() else 0
                    else:
                        minute = 0
                    period = match.groups()[-1] if match.groups()[-1] in ['am', 'pm'] else ''
                    if period == 'pm' and hour < 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0
                
                start_dt = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                break
        
        # Check for "besok" or "tomorrow"
        if 'besok' in text.lower() or 'tomorrow' in text.lower():
            start_dt = start_dt + timedelta(days=1)
        
        end_dt = start_dt + timedelta(hours=1)
        
        # Format times with timezone
        start_time = start_dt.strftime('%Y-%m-%dT%H:%M:%S+07:00')
        end_time = end_dt.strftime('%Y-%m-%dT%H:%M:%S+07:00')
        
        return self.create_event(summary, start_time, end_time, calendar_id=calendar_id)
    
    # ==================== SHEETS ====================
    
    def get_spreadsheet_info(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Get spreadsheet info."""
        return self._run_cli_tool("get_spreadsheet_info", {
            "spreadsheet_id": spreadsheet_id
        })
    
    def read_sheet_values(self, spreadsheet_id: str, range: str) -> Dict[str, Any]:
        """Read values from a sheet."""
        return self._run_cli_tool("read_sheet_values", {
            "spreadsheet_id": spreadsheet_id,
            "range_name": range  # MCP uses range_name, not range
        })
    
    def write_sheet_values(self, spreadsheet_id: str, range: str, 
                           values: List[List[Any]]) -> Dict[str, Any]:
        """Write values to a sheet."""
        # MCP tool is modify_sheet_values, not write_sheet_values
        return self._run_cli_tool("modify_sheet_values", {
            "spreadsheet_id": spreadsheet_id,
            "range_name": range,  # MCP uses range_name, not range
            "values": values
        })
    
    def create_spreadsheet(self, title: str) -> Dict[str, Any]:
        """Create a new spreadsheet."""
        return self._run_cli_tool("create_spreadsheet", {
            "title": title
        })
    
    # ==================== FORMS ====================
    
    def create_form(self, title: str, description: str = None) -> Dict[str, Any]:
        """Create a new form."""
        params = {"title": title}
        if description:
            params["description"] = description
        return self._run_cli_tool("create_form", params)
    
    def get_form(self, form_id: str) -> Dict[str, Any]:
        """Get form details."""
        return self._run_cli_tool("get_form", {
            "form_id": form_id
        })
    
    def list_form_responses(self, form_id: str) -> Dict[str, Any]:
        """List form responses."""
        return self._run_cli_tool("list_form_responses", {
            "form_id": form_id
        })
    
    def batch_update_form(self, form_id: str, requests: List[Dict]) -> Dict[str, Any]:
        """
        Batch update a form (add/update/delete questions).
        
        Args:
            form_id: The form ID to update
            requests: List of request objects, each can contain:
                - createItem: Add a new question/item
                - updateItem: Update existing item
                - deleteItem: Delete an item
                - moveItem: Move an item
                - updateFormInfo: Update form info
                - updateSettings: Update form settings
        """
        return self._run_cli_tool("batch_update_form", {
            "form_id": form_id,
            "requests": requests
        })
    
    def add_form_questions(self, form_id: str, questions: List[Dict]) -> Dict[str, Any]:
        """
        Add multiple choice questions to a form.
        
        Args:
            form_id: The form ID
            questions: List of question dicts with:
                - title: Question text
                - options: List of option strings
                - correct: The correct answer (optional, for quiz mode)
                - points: Point value (optional, for quiz mode)
        """
        requests = []
        for idx, q in enumerate(questions):
            choices = [{'value': opt} for opt in q.get('options', [])]
            
            question_item = {
                'title': q.get('title', f'Question {idx+1}'),
                'questionItem': {
                    'question': {
                        'required': q.get('required', True),
                        'choiceQuestion': {
                            'type': 'RADIO',
                            'options': choices,
                            'shuffle': q.get('shuffle', True)
                        }
                    }
                }
            }
            
            # Add grading if correct answer provided
            if q.get('correct'):
                question_item['questionItem']['question']['grading'] = {
                    'pointValue': q.get('points', 10),
                    'correctAnswers': {
                        'answers': [{'value': q['correct']}]
                    }
                }
            
            requests.append({
                'createItem': {
                    'item': question_item,
                    'location': {'index': idx}
                }
            })
        
        return self.batch_update_form(form_id, requests)
    
    def enable_quiz_mode(self, form_id: str, description: str = None) -> Dict[str, Any]:
        """Enable quiz mode on a form."""
        requests = [
            {
                'updateSettings': {
                    'settings': {
                        'quizSettings': {
                            'isQuiz': True
                        }
                    },
                    'updateMask': 'quizSettings.isQuiz'
                }
            }
        ]
        if description:
            requests.insert(0, {
                'updateFormInfo': {
                    'info': {'description': description},
                    'updateMask': 'description'
                }
            })
        return self.batch_update_form(form_id, requests)

    # ==================== DOCS ====================
    
    def search_docs(self, query: str, page_size: int = 10) -> Dict[str, Any]:
        """Search for Google Docs by name."""
        return self._run_cli_tool("search_docs", {
            "query": query,
            "page_size": page_size
        })
    
    def get_doc_content(self, document_id: str) -> Dict[str, Any]:
        """Get the content of a Google Doc."""
        return self._run_cli_tool("get_doc_content", {
            "document_id": document_id
        })
    
    def create_doc(self, title: str, content: str = "") -> Dict[str, Any]:
        """Create a new Google Doc."""
        params = {"title": title}
        if content:
            params["content"] = content
        return self._run_cli_tool("create_doc", params)
    
    def modify_doc_text(self, document_id: str, start_index: int, 
                        text: str = None, end_index: int = None,
                        bold: bool = None, italic: bool = None,
                        underline: bool = None, font_size: int = None) -> Dict[str, Any]:
        """Modify text in a Google Doc - insert/replace text and/or apply formatting."""
        params = {
            "document_id": document_id,
            "start_index": start_index
        }
        if text is not None:
            params["text"] = text
        if end_index is not None:
            params["end_index"] = end_index
        if bold is not None:
            params["bold"] = bold
        if italic is not None:
            params["italic"] = italic
        if underline is not None:
            params["underline"] = underline
        if font_size is not None:
            params["font_size"] = font_size
        return self._run_cli_tool("modify_doc_text", params)
    
    def find_and_replace_doc(self, document_id: str, find_text: str, replace_text: str,
                             match_case: bool = False) -> Dict[str, Any]:
        """Find and replace text in a Google Doc."""
        return self._run_cli_tool("find_and_replace_doc", {
            "document_id": document_id,
            "find_text": find_text,
            "replace_text": replace_text,
            "match_case": match_case
        })
    
    def insert_doc_image(self, document_id: str, image_url: str, 
                         location_index: int = 1, width: int = None, height: int = None) -> Dict[str, Any]:
        """Insert an image into a Google Doc."""
        params = {
            "document_id": document_id,
            "image_url": image_url,
            "location_index": location_index
        }
        if width:
            params["width"] = width
        if height:
            params["height"] = height
        return self._run_cli_tool("insert_doc_image", params)
    
    def export_doc_to_pdf(self, document_id: str, output_folder_id: str = None) -> Dict[str, Any]:
        """Export a Google Doc to PDF."""
        params = {"document_id": document_id}
        if output_folder_id:
            params["output_folder_id"] = output_folder_id
        return self._run_cli_tool("export_doc_to_pdf", params)
    
    def list_docs_in_folder(self, folder_id: str = "root", page_size: int = 20) -> Dict[str, Any]:
        """List Google Docs in a folder."""
        return self._run_cli_tool("list_docs_in_folder", {
            "folder_id": folder_id,
            "page_size": page_size
        })
    
    def batch_update_doc(self, document_id: str, requests: List[Dict]) -> Dict[str, Any]:
        """Apply batch updates to a Google Doc."""
        return self._run_cli_tool("batch_update_doc", {
            "document_id": document_id,
            "requests": requests
        })


# ============================================
# CLI HANDLERS
# ============================================

def handle_gmail_command(mcp: GoogleWorkspaceMCP, action: str, args: List[str]):
    """Handle Gmail commands."""
    print_section("📧 GMAIL")
    
    if action == "labels" or action == "list":
        print_status("📋", "Fetching Gmail labels...", Colors.CYAN)
        result = mcp.list_gmail_labels()
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "search":
        if not args:
            print_status("⚠️", "Usage: /gmail search <query>", Colors.YELLOW)
            return
        query = " ".join(args)
        print_status("🔍", f"Searching: {query}", Colors.CYAN)
        result = mcp.search_gmail(query)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "send":
        # Interactive email sending
        print_status("✉️", "Compose new email:", Colors.CYAN)
        to = input(f"  To: ").strip()
        subject = input(f"  Subject: ").strip()
        print("  Body (end with empty line):")
        body_lines = []
        while True:
            line = input("  ")
            if not line:
                break
            body_lines.append(line)
        body = "\n".join(body_lines)
        
        print_status("📤", "Sending email...", Colors.CYAN)
        result = mcp.send_email(to, subject, body)
        if result["success"]:
            print_status("✅", "Email sent successfully!", Colors.GREEN)
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "draft":
        print_status("📝", "Create draft:", Colors.CYAN)
        to = input(f"  To: ").strip()
        subject = input(f"  Subject: ").strip()
        print("  Body (end with empty line):")
        body_lines = []
        while True:
            line = input("  ")
            if not line:
                break
            body_lines.append(line)
        body = "\n".join(body_lines)
        
        print_status("💾", "Creating draft...", Colors.CYAN)
        result = mcp.create_gmail_draft(to, subject, body)
        if result["success"]:
            print_status("✅", "Draft created!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    else:
        print_status("⚠️", f"Unknown action: {action}", Colors.YELLOW)
        print_status("💡", "Available: labels, search, send, draft", Colors.DIM)


def handle_drive_command(mcp: GoogleWorkspaceMCP, action: str, args: List[str]):
    """Handle Drive commands."""
    print_section("📁 GOOGLE DRIVE")
    
    if action == "list" or action == "ls":
        query = " ".join(args) if args else "*"
        print_status("📂", f"Listing files: {query}", Colors.CYAN)
        result = mcp.search_drive_files(query)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "search":
        if not args:
            print_status("⚠️", "Usage: /drive search <query>", Colors.YELLOW)
            return
        query = " ".join(args)
        print_status("🔍", f"Searching: {query}", Colors.CYAN)
        result = mcp.search_drive_files(query)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "mkdir":
        print_status("⚠️", "Create folder not supported by MCP server", Colors.YELLOW)
        print_status("💡", "Use Google Drive web interface to create folders", Colors.DIM)
    
    elif action == "create":
        # Create a file with content
        if not args:
            print_status("⚠️", "Usage: /drive create <filename> [content]", Colors.YELLOW)
            return
        file_name = args[0]
        content = " ".join(args[1:]) if len(args) > 1 else ""
        if not content:
            content = input("  File content: ").strip()
        if not content:
            print_status("❌", "Content is required", Colors.RED)
            return
        print_status("📝", f"Creating file: {file_name}", Colors.CYAN)
        result = mcp.create_drive_file(file_name, content)
        if result["success"]:
            print_status("✅", "File created!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "upload":
        if not args:
            print_status("⚠️", "Usage: /drive upload <file_path>", Colors.YELLOW)
            return
        file_path = args[0]
        if not os.path.exists(file_path):
            print_status("❌", f"File not found: {file_path}", Colors.RED)
            return
        print_status("📤", f"Uploading: {file_path}", Colors.CYAN)
        result = mcp.upload_drive_file(file_path)
        if result["success"]:
            print_status("✅", "File uploaded!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "info":
        if not args:
            print_status("⚠️", "Usage: /drive info <file_id>", Colors.YELLOW)
            return
        file_id = args[0]
        print_status("ℹ️", f"Getting info for: {file_id}", Colors.CYAN)
        result = mcp.get_drive_file_info(file_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    else:
        print_status("⚠️", f"Unknown action: {action}", Colors.YELLOW)
        print_status("💡", "Available: list, search, create, upload, info", Colors.DIM)


def handle_calendar_command(mcp: GoogleWorkspaceMCP, action: str, args: List[str]):
    """Handle Calendar commands."""
    print_section("📅 GOOGLE CALENDAR")
    
    if action == "list" or action == "calendars":
        print_status("📅", "Listing calendars...", Colors.CYAN)
        result = mcp.list_calendars()
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "events":
        calendar_id = args[0] if args else "primary"
        print_status("📋", f"Listing events from: {calendar_id}", Colors.CYAN)
        result = mcp.list_events(calendar_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "add" or action == "create":
        print_status("➕", "Create new event:", Colors.CYAN)
        summary = input(f"  Title: ").strip()
        start_time = input(f"  Start (YYYY-MM-DDTHH:MM:SS): ").strip()
        end_time = input(f"  End (YYYY-MM-DDTHH:MM:SS): ").strip()
        description = input(f"  Description (optional): ").strip() or None
        location = input(f"  Location (optional): ").strip() or None
        
        print_status("📅", "Creating event...", Colors.CYAN)
        result = mcp.create_event(summary, start_time, end_time, description, location)
        if result["success"]:
            print_status("✅", "Event created!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "quick":
        if not args:
            print_status("⚠️", "Usage: /calendar quick <event description>", Colors.YELLOW)
            print_status("💡", "Example: /calendar quick Meeting with John tomorrow at 3pm", Colors.DIM)
            return
        text = " ".join(args)
        print_status("⚡", f"Quick adding: {text}", Colors.CYAN)
        result = mcp.quick_add_event(text)
        if result["success"]:
            print_status("✅", "Event added!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    else:
        print_status("⚠️", f"Unknown action: {action}", Colors.YELLOW)
        print_status("💡", "Available: list, events, add, quick", Colors.DIM)


def handle_sheets_command(mcp: GoogleWorkspaceMCP, action: str, args: List[str]):
    """Handle Sheets commands."""
    print_section("📊 GOOGLE SHEETS")
    
    if action == "info":
        if not args:
            print_status("⚠️", "Usage: /sheets info <spreadsheet_id>", Colors.YELLOW)
            return
        spreadsheet_id = args[0]
        print_status("📊", f"Getting spreadsheet info...", Colors.CYAN)
        result = mcp.get_spreadsheet_info(spreadsheet_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "read":
        if len(args) < 2:
            print_status("⚠️", "Usage: /sheets read <spreadsheet_id> <range>", Colors.YELLOW)
            print_status("💡", "Example: /sheets read abc123 Sheet1!A1:D10", Colors.DIM)
            return
        spreadsheet_id = args[0]
        range_str = args[1]
        print_status("📖", f"Reading {range_str}...", Colors.CYAN)
        result = mcp.read_sheet_values(spreadsheet_id, range_str)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "create":
        if not args:
            title = input("  Spreadsheet title: ").strip()
        else:
            title = " ".join(args)
        print_status("📝", f"Creating spreadsheet: {title}", Colors.CYAN)
        result = mcp.create_spreadsheet(title)
        if result["success"]:
            print_status("✅", "Spreadsheet created!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    else:
        print_status("⚠️", f"Unknown action: {action}", Colors.YELLOW)
        print_status("💡", "Available: info, read, create", Colors.DIM)


def handle_forms_command(mcp: GoogleWorkspaceMCP, action: str, args: List[str]):
    """Handle Forms commands."""
    print_section("📝 GOOGLE FORMS")
    
    if action == "get" or action == "info":
        if not args:
            print_status("⚠️", "Usage: /forms get <form_id>", Colors.YELLOW)
            return
        form_id = args[0]
        print_status("📝", f"Getting form info...", Colors.CYAN)
        result = mcp.get_form(form_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "responses":
        if not args:
            print_status("⚠️", "Usage: /forms responses <form_id>", Colors.YELLOW)
            return
        form_id = args[0]
        print_status("📋", f"Listing responses...", Colors.CYAN)
        result = mcp.list_form_responses(form_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "create":
        title = " ".join(args) if args else input("  Form title: ").strip()
        description = input("  Description (optional): ").strip() or None
        print_status("📝", f"Creating form: {title}", Colors.CYAN)
        result = mcp.create_form(title, description)
        if result["success"]:
            print_status("✅", "Form created!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "quiz":
        # Create quiz with questions
        title = " ".join(args) if args else input("  Quiz title: ").strip()
        if not title:
            print_status("⚠️", "Quiz title is required!", Colors.YELLOW)
            return
            
        description = input("  Description (optional): ").strip() or None
        
        # Create form first
        print_status("📝", f"Creating quiz: {title}", Colors.CYAN)
        result = mcp.create_form(title, description)
        if not result["success"]:
            print_status("❌", f"Error creating form: {result.get('error', 'Unknown error')}", Colors.RED)
            return
        
        # Extract form ID from output
        output = result.get('output', '')
        form_id = None
        for line in output.split('\n'):
            if 'Form ID:' in line:
                form_id = line.split('Form ID:')[1].strip()
                break
        
        if not form_id:
            print_status("⚠️", "Could not extract form ID from response", Colors.YELLOW)
            print(f"Output: {output}")
            return
        
        # Enable quiz mode
        print_status("🎯", "Enabling quiz mode...", Colors.CYAN)
        result = mcp.enable_quiz_mode(form_id, description)
        if result["success"]:
            print_status("✅", "Quiz mode enabled!", Colors.GREEN)
        else:
            print_status("⚠️", f"Warning: {result.get('error', 'Unknown')}", Colors.YELLOW)
        
        # Add questions interactively
        questions = []
        print(f"\n{Colors.BOLD}Add questions (empty title to finish):{Colors.ENDC}\n")
        
        q_num = 1
        while True:
            q_title = input(f"  Question {q_num}: ").strip()
            if not q_title:
                break
            
            options = []
            print("    Options (empty to finish, prefix correct answer with *):")
            correct = None
            opt_num = 1
            while True:
                opt = input(f"      {chr(64+opt_num)}. ").strip()
                if not opt:
                    break
                if opt.startswith('*'):
                    opt = opt[1:].strip()
                    correct = opt
                options.append(opt)
                opt_num += 1
            
            if len(options) >= 2:
                points = input("    Points (default: 10): ").strip()
                questions.append({
                    'title': f"{q_num}. {q_title}",
                    'options': options,
                    'correct': correct,
                    'points': int(points) if points.isdigit() else 10
                })
                q_num += 1
            else:
                print_status("⚠️", "Need at least 2 options!", Colors.YELLOW)
        
        if questions:
            print_status("📤", f"Adding {len(questions)} questions...", Colors.CYAN)
            result = mcp.add_form_questions(form_id, questions)
            if result["success"]:
                print_status("✅", f"Added {len(questions)} questions!", Colors.GREEN)
            else:
                print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
        
        # Print final URLs
        print(f"\n{Colors.GREEN}{'═'*50}{Colors.ENDC}")
        print(f"{Colors.BOLD}Quiz Created Successfully!{Colors.ENDC}")
        print(f"{Colors.GREEN}{'═'*50}{Colors.ENDC}")
        print(f"  Form ID: {form_id}")
        print(f"  Questions: {len(questions)}")
        print(f"\n  {Colors.CYAN}Edit:{Colors.ENDC} https://docs.google.com/forms/d/{form_id}/edit")
        print(f"  {Colors.CYAN}Share:{Colors.ENDC} https://docs.google.com/forms/d/{form_id}/viewform\n")
    
    elif action == "add-questions":
        if not args:
            print_status("⚠️", "Usage: /forms add-questions <form_id>", Colors.YELLOW)
            return
        form_id = args[0]
        
        # Add questions interactively
        questions = []
        print(f"\n{Colors.BOLD}Add questions (empty title to finish):{Colors.ENDC}\n")
        
        q_num = 1
        while True:
            q_title = input(f"  Question {q_num}: ").strip()
            if not q_title:
                break
            
            options = []
            print("    Options (empty to finish, prefix correct answer with *):")
            correct = None
            opt_num = 1
            while True:
                opt = input(f"      {chr(64+opt_num)}. ").strip()
                if not opt:
                    break
                if opt.startswith('*'):
                    opt = opt[1:].strip()
                    correct = opt
                options.append(opt)
                opt_num += 1
            
            if len(options) >= 2:
                points = input("    Points (default: 10): ").strip()
                questions.append({
                    'title': f"{q_num}. {q_title}",
                    'options': options,
                    'correct': correct,
                    'points': int(points) if points.isdigit() else 10
                })
                q_num += 1
            else:
                print_status("⚠️", "Need at least 2 options!", Colors.YELLOW)
        
        if questions:
            print_status("📤", f"Adding {len(questions)} questions...", Colors.CYAN)
            result = mcp.add_form_questions(form_id, questions)
            if result["success"]:
                print_status("✅", f"Added {len(questions)} questions!", Colors.GREEN)
            else:
                print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    else:
        print_status("⚠️", f"Unknown action: {action}", Colors.YELLOW)
        print_status("💡", "Available: get, responses, create, quiz, add-questions", Colors.DIM)


def handle_docs_command(mcp: GoogleWorkspaceMCP, action: str, args: List[str]):
    """Handle Google Docs commands."""
    print_section("📄 GOOGLE DOCS")
    
    if action == "search":
        if not args:
            print_status("⚠️", "Usage: /docs search <query>", Colors.YELLOW)
            return
        query = " ".join(args)
        print_status("🔍", f"Searching docs: {query}", Colors.CYAN)
        result = mcp.search_docs(query)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "list":
        folder_id = args[0] if args else "root"
        print_status("📋", f"Listing docs in folder...", Colors.CYAN)
        result = mcp.list_docs_in_folder(folder_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "get" or action == "read":
        if not args:
            print_status("⚠️", "Usage: /docs get <document_id>", Colors.YELLOW)
            return
        doc_id = args[0]
        print_status("📄", f"Reading document: {doc_id}", Colors.CYAN)
        result = mcp.get_doc_content(doc_id)
        if result["success"]:
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "create":
        title = " ".join(args) if args else input("  Document title: ").strip()
        if not title:
            print_status("⚠️", "Title is required!", Colors.YELLOW)
            return
        
        print("  Initial content (empty line to finish):")
        content_lines = []
        while True:
            line = input("  ")
            if not line:
                break
            content_lines.append(line)
        content = "\n".join(content_lines)
        
        print_status("📝", f"Creating document: {title}", Colors.CYAN)
        result = mcp.create_doc(title, content)
        if result["success"]:
            print_status("✅", "Document created!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "export-pdf":
        if not args:
            print_status("⚠️", "Usage: /docs export-pdf <document_id>", Colors.YELLOW)
            return
        doc_id = args[0]
        folder_id = args[1] if len(args) > 1 else None
        print_status("📥", f"Exporting to PDF...", Colors.CYAN)
        result = mcp.export_doc_to_pdf(doc_id, folder_id)
        if result["success"]:
            print_status("✅", "PDF exported!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "find-replace":
        if len(args) < 3:
            print_status("⚠️", "Usage: /docs find-replace <doc_id> <find> <replace>", Colors.YELLOW)
            return
        doc_id = args[0]
        find_text = args[1]
        replace_text = args[2]
        print_status("🔄", f"Finding and replacing...", Colors.CYAN)
        result = mcp.find_and_replace_doc(doc_id, find_text, replace_text)
        if result["success"]:
            print_status("✅", "Find/replace completed!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    elif action == "insert-image":
        if len(args) < 2:
            print_status("⚠️", "Usage: /docs insert-image <doc_id> <image_url>", Colors.YELLOW)
            return
        doc_id = args[0]
        image_url = args[1]
        print_status("🖼️", f"Inserting image...", Colors.CYAN)
        result = mcp.insert_doc_image(doc_id, image_url)
        if result["success"]:
            print_status("✅", "Image inserted!", Colors.GREEN)
            print(f"\n{result['output']}")
        else:
            print_status("❌", f"Error: {result.get('error', 'Unknown error')}", Colors.RED)
    
    else:
        print_status("⚠️", f"Unknown action: {action}", Colors.YELLOW)
        print_status("💡", "Available: search, list, get, create, export-pdf, find-replace, insert-image", Colors.DIM)


# ============================================
# INTERACTIVE MODE
# ============================================

def print_help():
    """Print help message."""
    help_text = f"""
{Colors.BOLD}{Colors.MAGENTA}JAWIR OS - Google Workspace Integration{Colors.ENDC}
{Colors.DIM}{'─' * 55}{Colors.ENDC}

Akses Google Workspace (Gmail, Drive, Calendar, Sheets, Forms, Docs) dengan mudah.

{Colors.BOLD}📧 GMAIL COMMANDS:{Colors.ENDC}
  {Colors.CYAN}/gmail labels{Colors.ENDC}          - List semua labels
  {Colors.CYAN}/gmail search <query>{Colors.ENDC} - Search emails
  {Colors.CYAN}/gmail send{Colors.ENDC}            - Compose & send email
  {Colors.CYAN}/gmail draft{Colors.ENDC}           - Create draft

{Colors.BOLD}📁 DRIVE COMMANDS:{Colors.ENDC}
  {Colors.CYAN}/drive list{Colors.ENDC}            - List semua files
  {Colors.CYAN}/drive search <query>{Colors.ENDC} - Search files
  {Colors.CYAN}/drive create <name> <content>{Colors.ENDC} - Create text file
  {Colors.CYAN}/drive upload <path>{Colors.ENDC}  - Upload file
  {Colors.CYAN}/drive info <file_id>{Colors.ENDC} - Get file info

{Colors.BOLD}📅 CALENDAR COMMANDS:{Colors.ENDC}
  {Colors.CYAN}/calendar list{Colors.ENDC}         - List calendars
  {Colors.CYAN}/calendar events{Colors.ENDC}       - List upcoming events
  {Colors.CYAN}/calendar add{Colors.ENDC}          - Create event (interactive)
  {Colors.CYAN}/calendar quick <text>{Colors.ENDC}- Quick add event

{Colors.BOLD}📊 SHEETS COMMANDS:{Colors.ENDC}
  {Colors.CYAN}/sheets info <id>{Colors.ENDC}      - Get spreadsheet info
  {Colors.CYAN}/sheets read <id> <range>{Colors.ENDC} - Read cell values
  {Colors.CYAN}/sheets create <title>{Colors.ENDC} - Create spreadsheet

{Colors.BOLD}📝 FORMS COMMANDS:{Colors.ENDC}
  {Colors.CYAN}/forms get <id>{Colors.ENDC}        - Get form details
  {Colors.CYAN}/forms responses <id>{Colors.ENDC} - List form responses
  {Colors.CYAN}/forms create <title>{Colors.ENDC} - Create new form
  {Colors.CYAN}/forms quiz <title>{Colors.ENDC}   - Create quiz with questions (interactive)
  {Colors.CYAN}/forms add-questions <id>{Colors.ENDC} - Add questions to existing form

{Colors.BOLD}📄 DOCS COMMANDS:{Colors.ENDC}
  {Colors.CYAN}/docs search <query>{Colors.ENDC}   - Search documents
  {Colors.CYAN}/docs list [folder_id]{Colors.ENDC} - List docs in folder
  {Colors.CYAN}/docs get <doc_id>{Colors.ENDC}     - Read document content
  {Colors.CYAN}/docs create <title>{Colors.ENDC}   - Create new document (interactive)
  {Colors.CYAN}/docs export-pdf <doc_id>{Colors.ENDC} - Export document to PDF
  {Colors.CYAN}/docs find-replace <id> <find> <replace>{Colors.ENDC} - Find & replace text
  {Colors.CYAN}/docs insert-image <id> <url>{Colors.ENDC} - Insert image into doc

{Colors.BOLD}Other Commands:{Colors.ENDC}
  {Colors.CYAN}/help{Colors.ENDC}   - Show this help
  {Colors.CYAN}/clear{Colors.ENDC}  - Clear screen
  {Colors.CYAN}/status{Colors.ENDC} - Check MCP connection
  {Colors.CYAN}exit{Colors.ENDC}    - Exit

{Colors.DIM}JAWIR OS © 2026 - Google Workspace Integration 🇮🇩{Colors.ENDC}
"""
    print(help_text)


def check_status(mcp: GoogleWorkspaceMCP):
    """Check MCP connection status."""
    print_section("🔗 CONNECTION STATUS")
    
    print_status("📍", f"MCP Path: {mcp.mcp_path}", Colors.CYAN)
    print_status("👤", f"User Email: {mcp.user_email}", Colors.CYAN)
    print_status("🔧", f"Enabled Tools: {', '.join(mcp.tools_enabled)}", Colors.CYAN)
    
    # Quick test
    print_status("🔄", "Testing connection...", Colors.YELLOW)
    result = mcp.list_calendars()
    
    if result["success"]:
        print_status("✅", "Connection OK!", Colors.GREEN)
    else:
        print_status("❌", f"Connection failed: {result.get('error', 'Unknown')}", Colors.RED)


def interactive_mode():
    """Run in interactive mode."""
    print_banner()
    
    try:
        mcp = GoogleWorkspaceMCP()
        print_status("✅", f"Connected as: {mcp.user_email}", Colors.GREEN)
    except Exception as e:
        print_status("❌", f"Failed to initialize: {e}", Colors.RED)
        print_status("💡", "Make sure Google Workspace MCP is installed and configured", Colors.YELLOW)
        return
    
    print_status("💡", "Ketik /help untuk melihat commands, atau /status untuk cek koneksi", Colors.DIM)
    print()
    
    while True:
        try:
            user_input = input(f"{Colors.MAGENTA}JAWIR-GWS>{Colors.ENDC} ").strip()
            
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
            
            # Status
            if user_input.lower() in ['/status', 'status']:
                check_status(mcp)
                print()
                continue
            
            # Parse command
            parts = user_input.split()
            command = parts[0].lower()
            action = parts[1].lower() if len(parts) > 1 else "list"
            args = parts[2:] if len(parts) > 2 else []
            
            # Route to handlers
            if command in ['/gmail', 'gmail']:
                handle_gmail_command(mcp, action, args)
            elif command in ['/drive', 'drive']:
                handle_drive_command(mcp, action, args)
            elif command in ['/calendar', 'calendar', '/cal', 'cal']:
                handle_calendar_command(mcp, action, args)
            elif command in ['/sheets', 'sheets', '/sheet', 'sheet']:
                handle_sheets_command(mcp, action, args)
            elif command in ['/forms', 'forms', '/form', 'form']:
                handle_forms_command(mcp, action, args)
            elif command in ['/docs', 'docs', '/doc', 'doc']:
                handle_docs_command(mcp, action, args)
            else:
                print_status("⚠️", f"Unknown command: {command}", Colors.YELLOW)
                print_status("💡", "Available: /gmail, /drive, /calendar, /sheets, /forms, /docs", Colors.DIM)
            
            print()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted{Colors.ENDC}")
            break
        except EOFError:
            break


# ============================================
# MAIN
# ============================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="JAWIR OS - Google Workspace Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
JAWIR OS Google Workspace Tool - Akses Gmail, Drive, Calendar, Sheets, Forms

Examples:
  python google_workspace.py -i                           (interactive mode)
  python google_workspace.py --gmail-labels               (list Gmail labels)
  python google_workspace.py --gmail-search "from:google" (search emails)
  python google_workspace.py --drive-list                 (list Drive files)
  python google_workspace.py --calendar-list              (list calendars)
  python google_workspace.py --calendar-events            (list upcoming events)
        """
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode - akses semua tools'
    )
    parser.add_argument(
        '--email',
        type=str,
        default=None,
        help='Google email to use (default: from env or hazzikiraju@gmail.com)'
    )
    
    # Gmail arguments
    parser.add_argument('--gmail-labels', action='store_true', help='List Gmail labels')
    parser.add_argument('--gmail-search', type=str, help='Search Gmail with query')
    
    # Drive arguments
    parser.add_argument('--drive-list', action='store_true', help='List Drive files')
    parser.add_argument('--drive-search', type=str, help='Search Drive files')
    
    # Calendar arguments
    parser.add_argument('--calendar-list', action='store_true', help='List calendars')
    parser.add_argument('--calendar-events', action='store_true', help='List upcoming events')
    
    args = parser.parse_args()
    
    # Initialize MCP client
    try:
        mcp = GoogleWorkspaceMCP(user_email=args.email)
    except Exception as e:
        print_status("❌", f"Failed to initialize: {e}", Colors.RED)
        sys.exit(1)
    
    # Handle specific commands
    if args.gmail_labels:
        print_banner()
        handle_gmail_command(mcp, "labels", [])
        return
    
    if args.gmail_search:
        print_banner()
        handle_gmail_command(mcp, "search", args.gmail_search.split())
        return
    
    if args.drive_list:
        print_banner()
        handle_drive_command(mcp, "list", [])
        return
    
    if args.drive_search:
        print_banner()
        handle_drive_command(mcp, "search", args.drive_search.split())
        return
    
    if args.calendar_list:
        print_banner()
        handle_calendar_command(mcp, "list", [])
        return
    
    if args.calendar_events:
        print_banner()
        handle_calendar_command(mcp, "events", [])
        return
    
    # Default to interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()
