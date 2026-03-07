"""
JAWIR OS - Google Workspace Tools
===================================
Tools untuk Gmail, Google Drive, dan Google Calendar.
"""

import logging
from typing import Optional, List
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.google")


# ============================================
# INPUT SCHEMAS
# ============================================

class GmailSearchInput(BaseModel):
    """Input schema for Gmail search."""
    query: str = Field(description="Gmail search query. Contoh: 'from:boss@company.com' atau 'subject:meeting'")
    max_results: int = Field(default=5, description="Jumlah email maksimal", ge=1, le=20)


class GmailSendInput(BaseModel):
    """Input schema for sending email."""
    to: str = Field(description="Alamat email tujuan")
    subject: str = Field(description="Subject email")
    body: str = Field(description="Isi body email")


class DriveSearchInput(BaseModel):
    """Input schema for Google Drive search."""
    query: str = Field(description="Search query untuk file di Google Drive. Contoh: 'laporan keuangan' atau 'presentation Q4'")


class DriveListInput(BaseModel):
    """Input schema for listing Drive folder contents."""
    folder_id: str = Field(default="root", description="ID folder Google Drive. Default 'root' untuk root folder.")


class CalendarListEventsInput(BaseModel):
    """Input schema for listing calendar events."""
    calendar_id: str = Field(default="primary", description="Calendar ID. Default 'primary' untuk kalender utama.")
    max_results: int = Field(default=10, description="Jumlah event maksimal", ge=1, le=50)


class CalendarCreateEventInput(BaseModel):
    """Input schema for creating a calendar event."""
    summary: str = Field(description="Judul event. Contoh: 'Meeting Tim' atau 'Deadline Proyek'")
    start_time: str = Field(description="Waktu mulai format ISO 8601. Contoh: '2024-12-25T09:00:00+07:00'")
    end_time: str = Field(description="Waktu selesai format ISO 8601. Contoh: '2024-12-25T10:00:00+07:00'")
    description: str = Field(default="", description="Deskripsi event (opsional)")
    location: str = Field(default="", description="Lokasi event (opsional)")


# ============================================
# TOOL FACTORIES
# ============================================

def create_gmail_search_tool() -> StructuredTool:
    """Create Gmail search tool wrapping GoogleWorkspaceMCP."""

    async def _gmail_search(query: str, max_results: int = 5) -> str:
        """Search Gmail for emails matching query."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.search_gmail(query, max_results=max_results)

            if not result.get("success"):
                return f"Error searching Gmail: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return f"Tidak ditemukan email untuk query: '{query}'"

            return f"Hasil pencarian Gmail untuk '{query}':\n{output[:3000]}"
        except Exception as e:
            return f"Error Gmail search: {str(e)}"

    return StructuredTool.from_function(
        func=_gmail_search,
        coroutine=_gmail_search,
        name="gmail_search",
        description=(
            "Search email di Gmail. Gunakan untuk mencari email berdasarkan pengirim, "
            "subject, atau keyword. Contoh query: 'from:john@example.com', 'subject:meeting', "
            "'is:unread', 'has:attachment'."
        ),
        args_schema=GmailSearchInput,
    )


def create_gmail_send_tool() -> StructuredTool:
    """Create Gmail send email tool."""

    async def _gmail_send(to: str, subject: str, body: str) -> str:
        """Send email via Gmail."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.send_email(to=to, subject=subject, body=body)

            if result.get("success"):
                return f"✅ Email berhasil dikirim ke {to} dengan subject '{subject}'"
            else:
                return f"❌ Gagal mengirim email: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error mengirim email: {str(e)}"

    return StructuredTool.from_function(
        func=_gmail_send,
        coroutine=_gmail_send,
        name="gmail_send",
        description=(
            "Kirim email via Gmail. Gunakan ketika user ingin mengirim email ke seseorang. "
            "Butuh: alamat tujuan, subject, dan body email."
        ),
        args_schema=GmailSendInput,
    )


def create_drive_search_tool() -> StructuredTool:
    """Create Google Drive search tool."""

    async def _drive_search(query: str) -> str:
        """Search files in Google Drive."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.search_drive_files(query=query)

            if not result.get("success"):
                return f"Error searching Drive: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return f"Tidak ditemukan file untuk: '{query}'"

            return f"Hasil pencarian Google Drive:\n{output[:3000]}"
        except Exception as e:
            return f"Error Drive search: {str(e)}"

    return StructuredTool.from_function(
        func=_drive_search,
        coroutine=_drive_search,
        name="drive_search",
        description=(
            "Search file di Google Drive. Gunakan untuk mencari dokumen, spreadsheet, "
            "presentasi, atau file lainnya di Drive. Contoh: 'laporan keuangan', 'meeting notes'."
        ),
        args_schema=DriveSearchInput,
    )


def create_drive_list_tool() -> StructuredTool:
    """Create Google Drive list folder contents tool."""

    async def _drive_list(folder_id: str = "root") -> str:
        """List contents of a Google Drive folder."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.list_drive_items(folder_id=folder_id)

            if not result.get("success"):
                return f"Error listing Drive: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return "Folder kosong atau tidak ada item."

            return f"Isi Google Drive folder:\n{output[:3000]}"
        except Exception as e:
            return f"Error Drive list: {str(e)}"

    return StructuredTool.from_function(
        func=_drive_list,
        coroutine=_drive_list,
        name="drive_list",
        description=(
            "Lihat isi folder di Google Drive. Gunakan untuk melihat daftar file dan folder. "
            "Default menampilkan root folder."
        ),
        args_schema=DriveListInput,
    )


def create_calendar_list_tool() -> StructuredTool:
    """Create Google Calendar list events tool."""

    async def _calendar_list(calendar_id: str = "primary", max_results: int = 10) -> str:
        """List upcoming calendar events."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.list_events(calendar_id=calendar_id, max_results=max_results)

            if not result.get("success"):
                return f"Error listing events: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return "Tidak ada event mendatang."

            return f"Event kalender:\n{output[:3000]}"
        except Exception as e:
            return f"Error Calendar list: {str(e)}"

    return StructuredTool.from_function(
        func=_calendar_list,
        coroutine=_calendar_list,
        name="calendar_list_events",
        description=(
            "Lihat jadwal/event di Google Calendar. Gunakan ketika user bertanya tentang "
            "jadwal hari ini, minggu ini, atau event mendatang."
        ),
        args_schema=CalendarListEventsInput,
    )


def create_calendar_create_tool() -> StructuredTool:
    """Create Google Calendar create event tool."""

    async def _calendar_create(
        summary: str, start_time: str, end_time: str,
        description: str = "", location: str = ""
    ) -> str:
        """Create a calendar event."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.create_event(
                summary=summary,
                start_time=start_time,
                end_time=end_time,
                description=description or None,
                location=location or None,
            )

            if result.get("success"):
                return f"✅ Event '{summary}' berhasil dibuat ({start_time} - {end_time})"
            else:
                return f"❌ Gagal membuat event: {result.get('error', 'Unknown error')}"
        except Exception as e:
            return f"❌ Error membuat event: {str(e)}"

    return StructuredTool.from_function(
        func=_calendar_create,
        coroutine=_calendar_create,
        name="calendar_create_event",
        description=(
            "Buat event baru di Google Calendar. Gunakan ketika user ingin membuat jadwal meeting, "
            "reminder, atau event. Butuh: judul, waktu mulai, waktu selesai (format ISO 8601)."
        ),
        args_schema=CalendarCreateEventInput,
    )


# ============================================
# SHEETS TOOLS
# ============================================

class SheetsReadInput(BaseModel):
    """Input schema for reading Google Sheets."""
    spreadsheet_id: str = Field(description="ID spreadsheet Google Sheets")
    range: str = Field(default="Sheet1!A1:Z100", description="Range sel yang dibaca. Contoh: 'Sheet1!A1:D10'")


class SheetsWriteInput(BaseModel):
    """Input schema for writing to Google Sheets."""
    spreadsheet_id: str = Field(description="ID spreadsheet Google Sheets")
    range: str = Field(description="Range sel untuk ditulis. Contoh: 'Sheet1!A1'")
    values: str = Field(description="Data yang ditulis, format JSON array 2D. Contoh: '[[\"A\",\"B\"],[1,2]]'")


class SheetsCreateInput(BaseModel):
    """Input schema for creating Google Sheets."""
    title: str = Field(description="Judul spreadsheet baru")


def create_sheets_read_tool() -> StructuredTool:
    """Create Google Sheets read tool."""

    async def _sheets_read(spreadsheet_id: str, range: str = "Sheet1!A1:Z100") -> str:
        """Read data from Google Sheets."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.read_sheet_values(spreadsheet_id=spreadsheet_id, range=range)

            if not result.get("success"):
                return f"Error reading sheet: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return f"Tidak ada data di range {range}"

            return f"Data dari Sheets:\n{output[:4000]}"
        except Exception as e:
            return f"Error Sheets read: {str(e)}"

    return StructuredTool.from_function(
        func=_sheets_read,
        coroutine=_sheets_read,
        name="sheets_read",
        description=(
            "Baca data dari Google Sheets. Gunakan untuk melihat isi spreadsheet. "
            "Butuh spreadsheet_id dan range (contoh: 'Sheet1!A1:D10')."
        ),
        args_schema=SheetsReadInput,
    )


def create_sheets_write_tool() -> StructuredTool:
    """Create Google Sheets write tool."""

    async def _sheets_write(spreadsheet_id: str, range: str, values: str) -> str:
        """Write data to Google Sheets."""
        try:
            import json
            parsed_values = json.loads(values)

            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.write_sheet_values(
                spreadsheet_id=spreadsheet_id,
                range=range,
                values=parsed_values
            )

            if result.get("success"):
                return f"✅ Data berhasil ditulis ke {range}"
            else:
                return f"❌ Gagal menulis: {result.get('error', 'Unknown error')}"
        except json.JSONDecodeError:
            return "❌ Format values tidak valid. Gunakan JSON array 2D, contoh: [[\"A\",\"B\"],[1,2]]"
        except Exception as e:
            return f"❌ Error Sheets write: {str(e)}"

    return StructuredTool.from_function(
        func=_sheets_write,
        coroutine=_sheets_write,
        name="sheets_write",
        description=(
            "Tulis data ke Google Sheets. Gunakan untuk mengisi spreadsheet. "
            "Values harus format JSON array 2D."
        ),
        args_schema=SheetsWriteInput,
    )


def create_sheets_create_tool() -> StructuredTool:
    """Create Google Sheets create tool."""

    async def _sheets_create(title: str) -> str:
        """Create a new Google Sheets spreadsheet."""
        try:
            import re
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.create_spreadsheet(title=title)

            if result.get("success"):
                output = result.get("output", "")
                # Parse ID from MCP output: "...ID: {id} | URL: {url}..."
                sheet_id = ""
                url = ""
                id_match = re.search(r'ID:\s*([^\s|]+)', output)
                if id_match:
                    sheet_id = id_match.group(1)
                url_match = re.search(r'URL:\s*(https://[^\s|]+)', output)
                if url_match:
                    url = url_match.group(1)
                return f"✅ Spreadsheet '{title}' berhasil dibuat!\nID: {sheet_id}\nURL: {url}"
            else:
                return f"❌ Gagal membuat spreadsheet: {result.get('error', result.get('output', 'Unknown error'))}"
        except Exception as e:
            return f"❌ Error Sheets create: {str(e)}"

    return StructuredTool.from_function(
        func=_sheets_create,
        coroutine=_sheets_create,
        name="sheets_create",
        description=(
            "Buat spreadsheet Google Sheets baru. Gunakan ketika user ingin membuat file spreadsheet baru."
        ),
        args_schema=SheetsCreateInput,
    )


# ============================================
# DOCS TOOLS
# ============================================

class DocsReadInput(BaseModel):
    """Input schema for reading Google Docs."""
    document_id: str = Field(description="ID dokumen Google Docs")


class DocsCreateInput(BaseModel):
    """Input schema for creating Google Docs."""
    title: str = Field(description="Judul dokumen baru")
    content: str = Field(default="", description="Isi dokumen (opsional)")


def create_docs_read_tool() -> StructuredTool:
    """Create Google Docs read tool."""

    async def _docs_read(document_id: str) -> str:
        """Read content from Google Docs."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.get_doc_content(document_id=document_id)

            if not result.get("success"):
                return f"Error reading doc: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return "Dokumen kosong."

            return f"Isi dokumen:\n{output[:5000]}"
        except Exception as e:
            return f"Error Docs read: {str(e)}"

    return StructuredTool.from_function(
        func=_docs_read,
        coroutine=_docs_read,
        name="docs_read",
        description=(
            "Baca isi Google Docs. Gunakan untuk melihat konten dokumen. "
            "Butuh document_id dari URL dokumen."
        ),
        args_schema=DocsReadInput,
    )


def create_docs_create_tool() -> StructuredTool:
    """Create Google Docs create tool."""

    async def _docs_create(title: str, content: str = "") -> str:
        """Create a new Google Docs document."""
        try:
            import re
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.create_doc(title=title, content=content or None)

            if result.get("success"):
                output = result.get("output", "")
                # Parse ID from MCP output: "...(ID: {id})...Link: {url}"
                doc_id = ""
                url = ""
                id_match = re.search(r'\(ID:\s*([^)]+)\)', output)
                if id_match:
                    doc_id = id_match.group(1)
                url_match = re.search(r'Link:\s*(https://[^\s]+)', output)
                if url_match:
                    url = url_match.group(1)
                return f"✅ Dokumen '{title}' berhasil dibuat!\nID: {doc_id}\nURL: {url}"
            else:
                return f"❌ Gagal membuat dokumen: {result.get('error', result.get('output', 'Unknown error'))}"
        except Exception as e:
            return f"❌ Error Docs create: {str(e)}"

    return StructuredTool.from_function(
        func=_docs_create,
        coroutine=_docs_create,
        name="docs_create",
        description=(
            "Buat dokumen Google Docs baru. Gunakan ketika user ingin membuat file dokumen baru."
        ),
        args_schema=DocsCreateInput,
    )


# ============================================
# FORMS TOOLS
# ============================================

class FormsReadInput(BaseModel):
    """Input schema for reading Google Forms responses."""
    form_id: str = Field(description="ID form Google Forms")


class FormsCreateInput(BaseModel):
    """Input schema for creating Google Forms."""
    title: str = Field(description="Judul form baru")
    description: str = Field(default="", description="Deskripsi form (opsional)")


def create_forms_read_tool() -> StructuredTool:
    """Create Google Forms read responses tool."""

    async def _forms_read(form_id: str) -> str:
        """Read responses from Google Forms."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.get_form(form_id=form_id)

            if not result.get("success"):
                return f"Error reading form: {result.get('error', 'Unknown error')}"

            output = result.get("output", "")
            if not output.strip():
                return "Belum ada respons di form ini."

            return f"Respons form:\n{output[:4000]}"
        except Exception as e:
            return f"Error Forms read: {str(e)}"

    return StructuredTool.from_function(
        func=_forms_read,
        coroutine=_forms_read,
        name="forms_read",
        description=(
            "Baca respons dari Google Forms. Gunakan untuk melihat jawaban yang masuk ke form."
        ),
        args_schema=FormsReadInput,
    )


def create_forms_create_tool() -> StructuredTool:
    """Create Google Forms create tool."""

    async def _forms_create(title: str, description: str = "") -> str:
        """Create a new Google Forms."""
        try:
            import re
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            result = gws.create_form(title=title, description=description or None)

            if result.get("success"):
                output = result.get("output", "")
                # Parse ID from MCP output: "...Form ID: {id}. Edit URL: {url}..."
                form_id = ""
                url = ""
                id_match = re.search(r'Form ID:\s*([^.\s]+)', output)
                if id_match:
                    form_id = id_match.group(1)
                url_match = re.search(r'Edit URL:\s*(https://[^\s.]+[^\s]*)', output)
                if url_match:
                    url = url_match.group(1).rstrip('.')
                return f"✅ Form '{title}' berhasil dibuat!\nID: {form_id}\nURL: {url}"
            else:
                return f"❌ Gagal membuat form: {result.get('error', result.get('output', 'Unknown error'))}"
        except Exception as e:
            return f"❌ Error Forms create: {str(e)}"

    return StructuredTool.from_function(
        func=_forms_create,
        coroutine=_forms_create,
        name="forms_create",
        description=(
            "Buat Google Forms baru. Gunakan ketika user ingin membuat form/survey baru."
        ),
        args_schema=FormsCreateInput,
    )


class FormsAddQuestionInput(BaseModel):
    """Input schema for adding question to Google Forms."""
    form_id: str = Field(description="ID form yang akan ditambahkan pertanyaan")
    question: str = Field(description="Teks pertanyaan yang akan ditambahkan")
    question_type: str = Field(
        default="text",
        description="Tipe pertanyaan: text (jawaban singkat), paragraph (jawaban panjang), multiple_choice (pilihan ganda), checkbox (centang), dropdown (dropdown)"
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="Daftar opsi jawaban untuk multiple_choice, checkbox, atau dropdown. Contoh: ['Opsi A', 'Opsi B', 'Opsi C']"
    )
    required: bool = Field(default=False, description="Apakah pertanyaan wajib dijawab")


def create_forms_add_question_tool() -> StructuredTool:
    """Create Google Forms add question tool."""

    async def _forms_add_question(
        form_id: str,
        question: str,
        question_type: str = "text",
        options: Optional[List[str]] = None,
        required: bool = False,
    ) -> str:
        """Add a question to an existing Google Forms."""
        try:
            from tools.google_workspace import GoogleWorkspaceMCP
            gws = GoogleWorkspaceMCP()
            
            # Build the createItem request based on question type
            question_item = {
                "required": required,
            }
            
            # Map question type to Google Forms API format
            if question_type == "text":
                question_item["textQuestion"] = {"paragraph": False}
            elif question_type == "paragraph":
                question_item["textQuestion"] = {"paragraph": True}
            elif question_type in ["multiple_choice", "checkbox", "dropdown"]:
                if not options:
                    options = ["Opsi 1", "Opsi 2", "Opsi 3"]
                
                choice_type = {
                    "multiple_choice": "RADIO",
                    "checkbox": "CHECKBOX",
                    "dropdown": "DROP_DOWN",
                }[question_type]
                
                question_item["choiceQuestion"] = {
                    "type": choice_type,
                    "options": [{"value": opt} for opt in options],
                }
            else:
                # Default to text
                question_item["textQuestion"] = {"paragraph": False}
            
            # Build batch update request
            request = {
                "requests": [{
                    "createItem": {
                        "item": {
                            "title": question,
                            "questionItem": {
                                "question": question_item,
                            },
                        },
                        "location": {"index": 0},  # Add at the end
                    }
                }]
            }
            
            # Call batch_update_form via MCP
            result = gws.batch_update_form(form_id=form_id, requests=request["requests"])
            
            if result.get("success"):
                return f"✅ Pertanyaan '{question[:50]}...' berhasil ditambahkan ke form {form_id}"
            else:
                return f"❌ Gagal menambah pertanyaan: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"❌ Error menambah pertanyaan: {str(e)}"

    return StructuredTool.from_function(
        func=_forms_add_question,
        coroutine=_forms_add_question,
        name="forms_add_question",
        description=(
            "Tambahkan pertanyaan ke Google Forms yang sudah ada. "
            "Gunakan setelah forms_create untuk menambahkan soal/pertanyaan. "
            "Tipe pertanyaan: text, paragraph, multiple_choice, checkbox, dropdown."
        ),
        args_schema=FormsAddQuestionInput,
    )
