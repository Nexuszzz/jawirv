"""
GoWA Client - HTTP Wrapper for go-whatsapp-web-multidevice API
================================================================
Client untuk akses REST API GoWA di VPS.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger("jawir.tools.gowa_client")


class GoWAClient:
    """Client untuk komunikasi dengan GoWA REST API."""
    
    def __init__(
        self,
        base_url: str = "http://13.55.23.245:3000",
        username: str = "admin",
        password: str = "jawir2026",
        timeout: int = 30,
    ):
        """
        Initialize GoWA client.
        
        Args:
            base_url: Base URL GoWA server (default VPS)
            username: Basic auth username
            password: Basic auth password
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)
        self.timeout = timeout
        logger.info(f"GoWA Client initialized: {self.base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GoWA API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/user/check")
            data: JSON body data
            files: Multipart files
            params: Query parameters
            
        Returns:
            Response JSON as dict
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                # Set headers dengan X-Device-Id jika multi-device
                headers = {}
                
                response = client.request(
                    method=method,
                    url=url,
                    auth=httpx.BasicAuth(self.auth[0], self.auth[1]),  # Explicit BasicAuth
                    headers=headers,
                    json=data if data else None,
                    files=files if files else None,
                    params=params if params else None,
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException as e:
            logger.error(f"GoWA API timeout: {e}")
            return {
                "code": "ERROR",
                "message": f"Request timeout after {self.timeout}s",
                "error": str(e),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"GoWA API error {e.response.status_code}: {e}")
            return {
                "code": "ERROR",
                "message": f"HTTP {e.response.status_code}",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"GoWA API exception: {e}")
            return {
                "code": "ERROR",
                "message": "Unexpected error",
                "error": str(e),
            }
    
    # ============================================
    # USER OPERATIONS
    # ============================================
    
    def check_number(self, phone: str) -> Dict[str, Any]:
        """
        Check if phone number is registered on WhatsApp.
        
        Args:
            phone: Phone number (format: 628xxx or 628xxx@s.whatsapp.net)
            
        Returns:
            {
                "code": "SUCCESS",
                "message": "Success",
                "results": [
                    {
                        "is_in_whatsapp": true,
                        "jid": "628xxx@s.whatsapp.net",
                        "verified_name": "John Doe"
                    }
                ]
            }
        """
        params = {"phone": phone}
        return self._make_request("GET", "/user/check", params=params)
    
    def get_user_info(self, phone: str) -> Dict[str, Any]:
        """
        Get user info (name, status, avatar).
        
        Args:
            phone: Phone number with @s.whatsapp.net suffix
            
        Returns:
            User info dict with verified_name, status, avatar, etc.
        """
        params = {"phone": phone}
        return self._make_request("GET", "/user/info", params=params)
    
    def list_contacts(self) -> Dict[str, Any]:
        """
        Get list of user contacts.
        
        Returns:
            {
                "code": "SUCCESS",
                "message": "Success",
                "results": [
                    {
                        "jid": "628xxx@s.whatsapp.net",
                        "name": "John Doe",
                        "verified_name": "John",
                        ...
                    }
                ]
            }
        """
        return self._make_request("GET", "/user/my/contacts")
    
    def list_groups(self) -> Dict[str, Any]:
        """
        Get list of groups (max 500 due to WhatsApp limitation).
        
        Returns:
            {
                "code": "SUCCESS",
                "message": "Success",
                "results": [
                    {
                        "jid": "120363xxx@g.us",
                        "name": "Tim Engineering",
                        "participants": [...],
                        ...
                    }
                ]
            }
        """
        return self._make_request("GET", "/user/my/groups")
    
    # ============================================
    # CHAT OPERATIONS
    # ============================================
    
    def list_chats(self) -> Dict[str, Any]:
        """
        Get list of chat conversations (personal + groups).
        
        Returns:
            {
                "code": "SUCCESS",
                "message": "Success",
                "results": [
                    {
                        "jid": "628xxx@s.whatsapp.net",
                        "name": "John Doe",
                        "unread_count": 3,
                        "last_message_time": 1234567890,
                        ...
                    }
                ]
            }
        """
        return self._make_request("GET", "/chat/conversations")
    
    def get_chat_messages(
        self, 
        phone: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get chat message history.
        
        Args:
            phone: Phone number or JID
            limit: Number of messages to retrieve (default 50)
            
        Returns:
            {
                "code": "SUCCESS",
                "message": "Success",
                "results": [
                    {
                        "id": "msgid",
                        "from": "628xxx@s.whatsapp.net",
                        "message": "Hello",
                        "timestamp": 1234567890,
                        ...
                    }
                ]
            }
        """
        params = {"limit": limit}
        return self._make_request("GET", f"/chat/{phone}/messages", params=params)
    
    # ============================================
    # SEND OPERATIONS
    # ============================================
    
    def send_message(
        self,
        phone: str,
        message: str,
        mentions: Optional[List[str]] = None,
        reply_message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send text message.
        
        Args:
            phone: Recipient phone (628xxx or 628xxx@s.whatsapp.net)
            message: Message text
            mentions: List of phones to mention (ghost mentions)
            reply_message_id: Message ID to reply to
            
        Returns:
            {
                "code": "SUCCESS",
                "message": "Success send message",
                "results": {
                    "message_id": "xxx",
                    "status": "sent"
                }
            }
        """
        data = {
            "phone": phone,
            "message": message,
        }
        
        if mentions:
            data["mentions"] = mentions
        
        if reply_message_id:
            data["reply_message_id"] = reply_message_id
        
        return self._make_request("POST", "/send/message", data=data)
    
    def send_image(
        self,
        phone: str,
        image_path: str,
        caption: str = "",
    ) -> Dict[str, Any]:
        """
        Send image with optional caption.
        
        Args:
            phone: Recipient phone
            image_path: Local path to image file
            caption: Image caption (optional)
            
        Returns:
            Response dict with message_id
        """
        image_file = Path(image_path)
        
        if not image_file.exists():
            return {
                "code": "ERROR",
                "message": f"Image not found: {image_path}",
            }
        
        with open(image_file, "rb") as f:
            files = {"image": (image_file.name, f, "image/jpeg")}
            data = {
                "phone": phone,
                "caption": caption,
            }
            
            # Multipart form-data
            return self._make_request("POST", "/send/image", data=data, files=files)
    
    def send_file(
        self,
        phone: str,
        file_path: str,
    ) -> Dict[str, Any]:
        """
        Send file/document.
        
        Args:
            phone: Recipient phone
            file_path: Local path to file
            
        Returns:
            Response dict with message_id
        """
        file = Path(file_path)
        
        if not file.exists():
            return {
                "code": "ERROR",
                "message": f"File not found: {file_path}",
            }
        
        with open(file, "rb") as f:
            files = {"file": (file.name, f, "application/octet-stream")}
            data = {"phone": phone}
            
            return self._make_request("POST", "/send/file", data=data, files=files)
    
    # ============================================
    # GROUP OPERATIONS
    # ============================================
    
    def get_group_participants(self, group_id: str) -> Dict[str, Any]:
        """
        Get list of group participants.
        
        Args:
            group_id: Group JID (xxx@g.us)
            
        Returns:
            List of participants with JID, name, role (admin/member)
        """
        return self._make_request("GET", f"/group/{group_id}/participants")
