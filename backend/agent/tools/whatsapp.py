"""
JAWIR OS - WhatsApp Tools via GoWA API
========================================
Tools untuk WhatsApp: check nomor, list chats, send message, list contacts/groups.
"""

import logging
from typing import Optional, List
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.whatsapp")


# ============================================
# INPUT SCHEMAS
# ============================================

class WhatsAppCheckNumberInput(BaseModel):
    """Input schema for checking phone number."""
    phone: str = Field(
        description="Nomor telepon yang mau dicek (format: 628xxx atau 628xxx@s.whatsapp.net). Contoh: 6281234567890"
    )


class WhatsAppListChatsInput(BaseModel):
    """Input schema for listing chats (no parameters needed)."""
    pass


class WhatsAppSendMessageInput(BaseModel):
    """Input schema for sending message."""
    phone: str = Field(
        description="Nomor tujuan (format: 628xxx atau JID lengkap). Contoh: 6281234567890"
    )
    message: str = Field(
        description="Isi pesan yang mau dikirim"
    )
    mentions: Optional[List[str]] = Field(
        default=None,
        description="List nomor yang mau di-mention (ghost mention). Gunakan '@everyone' untuk mention semua member grup. Contoh: ['628xxx', '628yyy'] atau ['@everyone']"
    )


class WhatsAppListContactsInput(BaseModel):
    """Input schema for listing contacts (no parameters needed)."""
    pass


class WhatsAppListGroupsInput(BaseModel):
    """Input schema for listing groups (no parameters needed)."""
    pass


class WhatsAppSendFileInput(BaseModel):
    """Input schema for sending file."""
    phone: str = Field(
        description="Nomor tujuan atau JID grup (format: 628xxx atau xxx@g.us). Contoh: 6281234567890 atau 120363375754063203@g.us"
    )
    file_path: str = Field(
        description="Path lengkap file yang mau dikirim. Contoh: C:/Users/user/Downloads/dokumen.pdf"
    )
    caption: Optional[str] = Field(
        default=None,
        description="Caption/keterangan untuk file (opsional)"
    )


class WhatsAppGetMessagesInput(BaseModel):
    """Input schema for getting chat messages."""
    chat_jid: str = Field(
        description="JID chat atau grup untuk diambil pesannya. Format: 628xxx@s.whatsapp.net untuk personal atau 120363xxx@g.us untuk grup. Bisa didapat dari whatsapp_list_chats."
    )
    limit: int = Field(
        default=10,
        description="Jumlah pesan terakhir yang mau diambil (max 100, default 10)"
    )
    search: Optional[str] = Field(
        default=None,
        description="Cari pesan dengan kata kunci tertentu (opsional)"
    )


# ============================================
# TOOL FACTORIES
# ============================================

def create_whatsapp_check_number_tool() -> StructuredTool:
    """Create tool untuk cek nomor WhatsApp valid."""
    
    async def _check_number(phone: str) -> str:
        """Check if phone number is registered on WhatsApp."""
        try:
            from tools.gowa_client import GoWAClient
            
            gowa = GoWAClient()
            result = gowa.check_number(phone=phone)
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Error cek nomor: {error_msg}"
            
            results = result.get("results", {})
            
            if not results:
                return f"❌ Nomor {phone} tidak terdaftar di WhatsApp"
            
            # Parse hasil (results is a dict, not array)
            is_registered = results.get("is_on_whatsapp", False)
            
            if is_registered:
                info = f"✅ Nomor {phone} terdaftar di WhatsApp\n"
                info += f"📱 Status: Aktif\n"
                return info
            else:
                return f"❌ Nomor {phone} tidak terdaftar di WhatsApp"
                
        except Exception as e:
            logger.error(f"Error check WhatsApp number: {e}", exc_info=True)
            return f"❌ Error cek nomor WhatsApp: {str(e)}"
    
    return StructuredTool.from_function(
        func=_check_number,
        coroutine=_check_number,
        name="whatsapp_check_number",
        description=(
            "Cek apakah nomor telepon terdaftar di WhatsApp. "
            "Gunakan untuk validasi nomor sebelum kirim pesan. "
            "Format nomor: 628xxx (tanpa + atau 0). "
            "Contoh: whatsapp_check_number(phone='6281234567890')"
        ),
        args_schema=WhatsAppCheckNumberInput,
    )


def create_whatsapp_list_chats_tool() -> StructuredTool:
    """Create tool untuk list percakapan WhatsApp."""
    
    async def _list_chats() -> str:
        """Get list of chat conversations (personal + groups)."""
        try:
            from tools.gowa_client import GoWAClient
            
            gowa = GoWAClient()
            result = gowa.list_chats()
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Error list chats: {error_msg}"
            
            results = result.get("results", {})
            
            # results is a dict with 'data' key and optional 'pagination'
            if isinstance(results, dict):
                chats = results.get("data", [])
                pagination = results.get("pagination", {})
                total = pagination.get("total", len(chats)) if pagination else len(chats)
            elif isinstance(results, list):
                chats = results
                total = len(chats)
            else:
                chats = []
                total = 0
            
            if not chats:
                return "📭 Tidak ada percakapan WhatsApp"
            
            # Format output
            output = f"📱 Daftar Percakapan WhatsApp ({len(chats)} ditampilkan, {total} total):\n\n"
            
            for i, chat in enumerate(chats[:50], 1):  # Limit 50 chat teratas
                jid = chat.get("jid", chat.get("JID", ""))
                name = chat.get("name", chat.get("Name", "Unknown"))
                last_msg_time = chat.get("last_message_time", chat.get("LastMessageTime", ""))
                
                # Tentukan tipe chat
                if "@g.us" in jid:
                    chat_type = "👥 Grup"
                elif "@broadcast" in jid:
                    chat_type = "📢 Broadcast"
                else:
                    chat_type = "👤 Personal"
                
                output += f"{i}. {chat_type} - {name}\n"
                output += f"   JID: {jid}\n"
                
                if last_msg_time:
                    output += f"   🕐 Last: {last_msg_time}\n"
                
                output += "\n"
            
            if total > len(chats):
                output += f"... dan {total - len(chats)} chat lainnya\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error list WhatsApp chats: {e}", exc_info=True)
            return f"❌ Error list chats: {str(e)}"
    
    return StructuredTool.from_function(
        func=_list_chats,
        coroutine=_list_chats,
        name="whatsapp_list_chats",
        description=(
            "List semua percakapan WhatsApp (personal chat + grup). "
            "Menampilkan nama kontak/grup, JID, jumlah pesan unread. "
            "Gunakan untuk lihat siapa aja yang chat atau cari chat tertentu. "
            "Contoh: whatsapp_list_chats()"
        ),
        args_schema=WhatsAppListChatsInput,
    )


def create_whatsapp_send_message_tool() -> StructuredTool:
    """Create tool untuk kirim pesan WhatsApp."""
    
    async def _send_message(
        phone: str, 
        message: str, 
        mentions: Optional[List[str]] = None
    ) -> str:
        """Send text message via WhatsApp."""
        try:
            from tools.gowa_client import GoWAClient
            
            gowa = GoWAClient()
            result = gowa.send_message(
                phone=phone, 
                message=message, 
                mentions=mentions
            )
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Gagal kirim pesan: {error_msg}"
            
            msg_id = result.get("results", {}).get("message_id", "")
            
            output = f"✅ Pesan berhasil dikirim ke {phone}\n"
            if msg_id:
                output += f"📨 Message ID: {msg_id}\n"
            
            if mentions:
                output += f"👥 Mentions: {', '.join(mentions)}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error send WhatsApp message: {e}", exc_info=True)
            return f"❌ Error kirim pesan: {str(e)}"
    
    return StructuredTool.from_function(
        func=_send_message,
        coroutine=_send_message,
        name="whatsapp_send_message",
        description=(
            "Kirim pesan WhatsApp ke nomor atau grup. "
            "Format nomor: 628xxx (tanpa +). Untuk grup: gunakan JID lengkap (xxx@g.us). "
            "Bisa mention orang dengan parameter mentions=['628xxx'] atau mention semua dengan ['@everyone']. "
            "Contoh: whatsapp_send_message(phone='6281234567890', message='Halo!', mentions=['@everyone'])"
        ),
        args_schema=WhatsAppSendMessageInput,
    )


def create_whatsapp_list_contacts_tool() -> StructuredTool:
    """Create tool untuk list kontak WhatsApp."""
    
    async def _list_contacts() -> str:
        """Get list of WhatsApp contacts."""
        try:
            from tools.gowa_client import GoWAClient
            
            gowa = GoWAClient()
            result = gowa.list_contacts()
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Error list kontak: {error_msg}"
            
            results = result.get("results", {})
            
            # results is a dict with 'data' key containing the array
            if isinstance(results, dict):
                contacts = results.get("data", [])
            elif isinstance(results, list):
                contacts = results
            else:
                contacts = []
            
            if not contacts:
                return "📭 Tidak ada kontak WhatsApp"
            
            # Format output
            output = f"📞 Daftar Kontak WhatsApp ({len(contacts)} kontak):\n\n"
            
            for i, contact in enumerate(contacts[:100], 1):  # Limit 100 kontak
                jid = contact.get("jid", contact.get("JID", ""))
                name = contact.get("name", contact.get("Name", "Unknown"))
                verified_name = contact.get("verified_name", contact.get("VerifiedName", ""))
                
                display_name = name if name else jid
                output += f"{i}. {display_name}\n"
                output += f"   📱 JID: {jid}\n"
                
                if verified_name and verified_name != name:
                    output += f"   ✅ Verified: {verified_name}\n"
                
                output += "\n"
            
            if len(contacts) > 100:
                output += f"... dan {len(contacts) - 100} kontak lainnya\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error list WhatsApp contacts: {e}", exc_info=True)
            return f"❌ Error list kontak: {str(e)}"
    
    return StructuredTool.from_function(
        func=_list_contacts,
        coroutine=_list_contacts,
        name="whatsapp_list_contacts",
        description=(
            "List semua kontak WhatsApp yang tersimpan. "
            "Menampilkan nama, JID, dan verified name (jika ada). "
            "Gunakan untuk cari nomor kontak atau lihat daftar kontak. "
            "Contoh: whatsapp_list_contacts()"
        ),
        args_schema=WhatsAppListContactsInput,
    )


def create_whatsapp_list_groups_tool() -> StructuredTool:
    """Create tool untuk list grup WhatsApp."""
    
    async def _list_groups() -> str:
        """Get list of WhatsApp groups (max 500)."""
        try:
            from tools.gowa_client import GoWAClient
            
            gowa = GoWAClient()
            result = gowa.list_groups()
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Error list grup: {error_msg}"
            
            results = result.get("results", {})
            
            # results is a dict with 'data' key containing the array
            if isinstance(results, dict):
                groups = results.get("data", [])
            elif isinstance(results, list):
                groups = results
            else:
                groups = []
            
            if not groups:
                return "📭 Tidak ada grup WhatsApp"
            
            # Format output
            output = f"👥 Daftar Grup WhatsApp ({len(groups)} grup):\n\n"
            
            for i, group in enumerate(groups[:100], 1):  # Limit 100 grup
                # GoWA uses PascalCase keys: JID, Name, OwnerJID, Topic, Participants
                jid = group.get("JID", group.get("jid", ""))
                name = group.get("Name", group.get("name", "Unknown Group"))
                participants = group.get("Participants", group.get("participants", []))
                owner_jid = group.get("OwnerJID", group.get("owner_jid", ""))
                topic = group.get("Topic", group.get("topic", ""))
                
                output += f"{i}. {name}\n"
                output += f"   🔗 JID: {jid}\n"
                
                if isinstance(participants, list):
                    output += f"   👤 Members: {len(participants)}\n"
                
                if topic:
                    output += f"   📝 Topic: {topic}\n"
                
                if owner_jid:
                    output += f"   👑 Owner: {owner_jid}\n"
                
                output += "\n"
            
            if len(groups) > 100:
                output += f"... dan {len(groups) - 100} grup lainnya\n"
            
            output += "\n⚠️ Note: Max 500 grup (WhatsApp limitation)\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error list WhatsApp groups: {e}", exc_info=True)
            return f"❌ Error list grup: {str(e)}"
    
    return StructuredTool.from_function(
        func=_list_groups,
        coroutine=_list_groups,
        name="whatsapp_list_groups",
        description=(
            "List semua grup WhatsApp yang diikuti (max 500 grup). "
            "Menampilkan nama grup, JID, jumlah member, owner. "
            "Gunakan untuk cari grup atau lihat daftar grup. "
            "Contoh: whatsapp_list_groups()"
        ),
        args_schema=WhatsAppListGroupsInput,
    )


def create_whatsapp_send_file_tool() -> StructuredTool:
    """Create tool untuk kirim file via WhatsApp."""
    
    async def _send_file(
        phone: str,
        file_path: str,
        caption: Optional[str] = None,
    ) -> str:
        """Send file/document via WhatsApp."""
        try:
            import os
            from tools.gowa_client import GoWAClient
            
            # Normalize path
            file_path = os.path.normpath(file_path)
            
            if not os.path.isfile(file_path):
                # Try common locations
                common_dirs = [
                    os.path.expanduser("~/Downloads"),
                    os.path.expanduser("~/Documents"),
                    os.path.expanduser("~/Desktop"),
                ]
                found = False
                filename = os.path.basename(file_path)
                for d in common_dirs:
                    candidate = os.path.join(d, filename)
                    if os.path.isfile(candidate):
                        file_path = candidate
                        found = True
                        break
                
                if not found:
                    return f"❌ File tidak ditemukan: {file_path}"
            
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            gowa = GoWAClient()
            result = gowa.send_file(
                phone=phone,
                file_path=file_path,
                caption=caption,
            )
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Gagal kirim file: {error_msg}"
            
            msg_id = result.get("results", {}).get("message_id", "")
            
            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / 1024 / 1024:.1f} MB"
            
            output = f"✅ File berhasil dikirim ke {phone}\n"
            output += f"📎 File: {file_name} ({size_str})\n"
            if msg_id:
                output += f"📨 Message ID: {msg_id}\n"
            if caption:
                output += f"💬 Caption: {caption}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error send file via WhatsApp: {e}", exc_info=True)
            return f"❌ Error kirim file: {str(e)}"
    
    return StructuredTool.from_function(
        func=_send_file,
        coroutine=_send_file,
        name="whatsapp_send_file",
        description=(
            "Kirim file/dokumen via WhatsApp ke nomor atau grup. "
            "Bisa kirim PDF, RAR, ZIP, DOCX, XLSX, gambar, video, dll. "
            "Butuh path lengkap file di komputer lokal. Max 100MB. "
            "Format nomor: 628xxx. Untuk grup: gunakan JID (xxx@g.us). "
            "Contoh: whatsapp_send_file(phone='6281234567890', file_path='C:/Users/user/Downloads/laporan.pdf', caption='Ini laporannya')"
        ),
        args_schema=WhatsAppSendFileInput,
    )


def create_whatsapp_get_messages_tool() -> StructuredTool:
    """Create tool untuk ambil pesan dari chat/grup."""
    
    async def _get_messages(
        chat_jid: str,
        limit: int = 10,
        search: Optional[str] = None,
    ) -> str:
        """Get messages from a WhatsApp chat or group."""
        try:
            from tools.gowa_client import GoWAClient
            
            gowa = GoWAClient()
            result = gowa.get_chat_messages(
                chat_jid=chat_jid,
                limit=min(limit, 100),
                search=search,
            )
            
            if result.get("code") != "SUCCESS":
                error_msg = result.get("message", "Unknown error")
                return f"❌ Error ambil pesan: {error_msg}"
            
            results = result.get("results", {})
            
            # Extract messages
            if isinstance(results, dict):
                messages = results.get("data", [])
                pagination = results.get("pagination", {})
                total = pagination.get("total", len(messages))
            else:
                messages = []
                total = 0
            
            if not messages:
                return f"📭 Tidak ada pesan di chat {chat_jid}"
            
            # Format output
            output = f"💬 Pesan dari Chat ({len(messages)} pesan terbaru, {total} total):\n"
            output += f"📍 JID: {chat_jid}\n\n"
            
            for i, msg in enumerate(messages, 1):
                sender_jid = msg.get("sender_jid", msg.get("SenderJID", ""))
                content = msg.get("content", msg.get("Content", ""))
                is_from_me = msg.get("is_from_me", msg.get("IsFromMe", False))
                timestamp = msg.get("timestamp", msg.get("Timestamp", ""))
                media_type = msg.get("media_type", msg.get("MediaType"))
                
                # Format sender
                if is_from_me:
                    sender_label = "👤 Kamu"
                else:
                    # Ambil nomor aja dari JID
                    sender_number = sender_jid.split("@")[0] if "@" in sender_jid else sender_jid
                    sender_label = f"👥 {sender_number}"
                
                output += f"[{i}] {sender_label}\n"
                
                if content:
                    # Trim panjang content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    output += f"   💬 {content}\n"
                elif media_type:
                    output += f"   📎 [{media_type.upper()}]\n"
                else:
                    output += f"   📎 [MEDIA]\n"
                
                if timestamp:
                    # Ambil waktu aja, skip tanggal jika hari ini
                    time_part = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp
                    output += f"   🕐 {time_part}\n"
                
                output += "\n"
            
            if search:
                output += f"\n🔍 Filtered by: '{search}'\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error get WhatsApp messages: {e}", exc_info=True)
            return f"❌ Error ambil pesan: {str(e)}"
    
    return StructuredTool.from_function(
        func=_get_messages,
        coroutine=_get_messages,
        name="whatsapp_get_messages",
        description=(
            "Ambil/baca pesan dari chat atau grup WhatsApp. "
            "Menampilkan isi pesan, pengirim, waktu. Max 100 pesan terakhir. "
            "Bisa search dengan keyword. Gunakan untuk lihat isi percakapan, cek balasan member, baca pesan. "
            "WAJIB pakai JID lengkap dari whatsapp_list_chats (format: 628xxx@s.whatsapp.net atau 120363xxx@g.us). "
            "Contoh: whatsapp_get_messages(chat_jid='120363375754063203@g.us', limit=10)"
        ),
        args_schema=WhatsAppGetMessagesInput,
    )


# ============================================
# REGISTRY
# ============================================

def get_whatsapp_tools() -> List[StructuredTool]:
    """
    Get all WhatsApp tools.
    
    Returns:
        List of 5 WhatsApp tools
    """
    return [
        create_whatsapp_check_number_tool(),
        create_whatsapp_list_chats_tool(),
        create_whatsapp_get_messages_tool(),
        create_whatsapp_send_message_tool(),
        create_whatsapp_send_file_tool(),
        create_whatsapp_list_contacts_tool(),
        create_whatsapp_list_groups_tool(),
    ]
