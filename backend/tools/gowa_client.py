"""
Robust GoWA Client - HTTP Wrapper for go-whatsapp-web-multidevice API
======================================================================
Features:
- Automatic device status checking
- Retry logic for transient errors  
- Connection health monitoring
- Detailed error messages
- Device session caching
"""

import httpx
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class GoWAError(Exception):
    """Base exception for GoWA client errors"""
    pass


class DeviceNotLoggedInError(GoWAError):
    """Device not logged in to WhatsApp"""
    pass


class GoWAConnectionError(GoWAError):
    """Cannot connect to GoWA server"""
    pass


class GoWAClient:
    """
    Robust client untuk Go-WhatsApp-Web-Multidevice REST API.
    
    Features:
    - Automatic Basic Auth
    - Device status checking
    - Retry logic (3 attempts)
    - Health monitoring
    - Detailed error handling
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize GoWA client.
        
        Args:
            base_url: Base URL GoWA server (default dari settings)
            username: Username basic auth (default dari settings)
            password: Password basic auth (default dari settings)  
            timeout: Request timeout in seconds (default 30)
            max_retries: Max retry attempts for failed requests (default 3)
        """
        self.base_url = (base_url or settings.gowa_base_url).rstrip("/")
        self.username = username or settings.gowa_username
        self.password = password or settings.gowa_password
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Cache device status
        self._device_cache: Optional[Dict[str, Any]] = None
        self._device_cache_time: float = 0
        self._device_cache_ttl: int = 60  # Cache 60 seconds
        
        logger.info(f"GoWA Client initialized: {self.base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to GoWA API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc)
            endpoint: API endpoint (e.g., "/user/check")
            params: Query parameters
            json_data: JSON body for POST requests
            headers: Additional headers
            retry_count: Current retry attempt (internal use)
            
        Returns:
            Response JSON as dict
            
        Raises:
            GoWAConnectionError: Cannot connect to server
            GoWAError: Other API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                    auth=httpx.BasicAuth(self.username, self.password),
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to GoWA server at {self.base_url}"
            logger.error(f"{error_msg}: {str(e)}")
            
            # Retry on connection errors
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, json_data, headers, retry_count + 1)
            
            raise GoWAConnectionError(error_msg)
            
        except httpx.TimeoutException as e:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(error_msg)
            
            # Retry on timeout
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                logger.info(f"Retrying in {wait_time}s... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(wait_time)
                return self._make_request(method, endpoint, params, json_data, headers, retry_count + 1)
            
            return {
                "code": "TIMEOUT",
                "message": error_msg,
                "results": None,
            }
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            response_text = e.response.text
            
            # Handle specific error codes
            if status_code == 401:
                error_msg = "Unauthorized: Invalid username/password"
            elif status_code == 403:
                error_msg = "Forbidden: Access denied"
            elif status_code == 404:
                error_msg = f"Not found: {endpoint}"
            elif status_code == 500:
                error_msg = "GoWA server internal error"
            else:
                error_msg = f"HTTP {status_code}"
            
            logger.error(f"{error_msg}: {response_text[:200]}")
            
            return {
                "code": "HTTP_ERROR",
                "message": f"{error_msg}: {response_text[:200]}",
                "status_code": status_code,
                "results": None,
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "code": "ERROR",
                "message": f"Request failed: {str(e)}",
                "results": None,
            }
    
    def check_health(self) -> Tuple[bool, str]:
        """
        Check if GoWA server is reachable.
        
        Returns:
            (is_healthy, message)
        """
        try:
            response = self._make_request("GET", "/user/check", params={"phone": "628"})
            return True, "GoWA server is reachable"
        except GoWAConnectionError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
    
    def get_devices(self) -> Dict[str, Any]:
        """
        Get all registered devices.
        
        Returns:
            {
                "code": "SUCCESS" | "ERROR",
                "message": str,
                "results": [
                    {
                        "device": str,  # e.g., "628xxx@s.whatsapp.net"
                        "name": str,
                        "jid": str,
                        "status": str,  # "connected" | "disconnected"
                    }
                ]
            }
        """
        return self._make_request("GET", "/app/devices")
    
    def is_device_logged_in(self) -> Tuple[bool, Optional[str]]:
        """
        Check if any device is logged in.
        
        Returns:
            (is_logged_in, device_jid)
        """
        # Check cache first
        now = time.time()
        if self._device_cache and (now - self._device_cache_time) < self._device_cache_ttl:
            devices = self._device_cache.get("results", [])
            if devices:
                return True, devices[0].get("device")
            return False, None
        
        # Fetch from API
        try:
            response = self.get_devices()
            self._device_cache = response
            self._device_cache_time = now
            
            if response.get("code") == "SUCCESS":
                devices = response.get("results", [])
                if devices:
                    device_jid = devices[0].get("device")
                    logger.info(f"Device logged in: {device_jid}")
                    return True, device_jid
            
            logger.warning("No device logged in to GoWA")
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking device status: {str(e)}")
            return False, None
    
    def check_number(self, phone: str) -> Dict[str, Any]:
        """
        Check if phone number is registered on WhatsApp.
        
        Args:
            phone: Phone number in international format (e.g., "628123456789")
            
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": [
                    {
                        "exists": bool,
                        "jid": str,  # e.g., "628xxx@s.whatsapp.net"
                    }
                ]
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        return self._make_request(
            method="GET",
            endpoint="/user/check",
            params={"phone": phone},
        )
    
    def list_contacts(self) -> Dict[str, Any]:
        """
        Get list of all contacts.
        
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": [
                    {
                        "name": str,
                        "jid": str,
                        "phone": str,
                    }
                ]
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        return self._make_request("GET", "/user/my/contacts")
    
    def list_groups(self) -> Dict[str, Any]:
        """
        Get list of joined groups (max 500).
        
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": [
                    {
                        "jid": str,
                        "name": str,
                        "participants": int,
                    }
                ]
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        return self._make_request("GET", "/user/my/groups")
    
    def list_chats(self) -> Dict[str, Any]:
        """
        Get list of all chats (personal + group conversations).
        
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": [
                    {
                        "jid": str,
                        "name": str,
                        "last_message": str,
                        "timestamp": int,
                        "unread_count": int,
                    }
                ]
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        # Endpoint is /chats (verified from openapi.yaml)
        return self._make_request("GET", "/chats", params={"limit": 50})
    
    def get_chat_messages(
        self,
        chat_jid: str,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get messages from a specific chat conversation.
        
        Args:
            chat_jid: Chat JID (phone@s.whatsapp.net or groupid@g.us)
            limit: Max messages to return (default 20, max 100)
            offset: Number of messages to skip for pagination (default 0)
            search: Search messages by text content (optional)
            
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": {
                    "data": [
                        {
                            "id": str,
                            "chat_jid": str,
                            "sender_jid": str,
                            "content": str,
                            "timestamp": str,
                            "is_from_me": bool,
                            "media_type": str | None,
                        }
                    ],
                    "pagination": {
                        "limit": int,
                        "offset": int,
                        "total": int,
                    }
                }
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        params = {
            "limit": min(limit, 100),  # API max is 100
            "offset": offset,
        }
        
        if search:
            params["search"] = search
        
        return self._make_request("GET", f"/chat/{chat_jid}/messages", params=params)
    
    def send_message(
        self,
        phone: str,
        message: str,
        mentions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send text message to WhatsApp contact or group.
        
        Args:
            phone: Recipient phone number or group JID
            message: Message text to send
            mentions: List of phone numbers to mention (optional)
            
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": {
                    "message_id": str,
                    "status": str,
                }
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        payload = {
            "phone": phone,
            "message": message,
        }
        
        if mentions:
            payload["mentions"] = mentions
        
        return self._make_request(
            method="POST",
            endpoint="/send/message",
            json_data=payload,
        )
    
    def send_image(
        self,
        phone: str,
        image_url: str,
        caption: Optional[str] = None,
        mentions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send image to WhatsApp contact or group.
        
        Args:
            phone: Recipient phone number or group JID
            image_url: URL of image to send
            caption: Image caption (optional)
            mentions: List of phone numbers to mention (optional)
            
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": {
                    "message_id": str,
                    "status": str,
                }
            }
        """
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        payload = {
            "phone": phone,
            "image": image_url,
        }
        
        if caption:
            payload["caption"] = caption
        if mentions:
            payload["mentions"] = mentions
        
        return self._make_request(
            method="POST",
            endpoint="/send/image",
            json_data=payload,
        )
    
    def send_file(
        self,
        phone: str,
        file_path: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send file/document to WhatsApp contact or group via multipart upload.
        
        Args:
            phone: Recipient phone number or group JID
            file_path: Local file path to send
            caption: File caption (optional)
            
        Returns:
            {
                "code": "SUCCESS" | "ERROR" | "DEVICE_NOT_LOGGED_IN",
                "message": str,
                "results": {
                    "message_id": str,
                    "status": str,
                }
            }
        """
        import os
        
        # Check device first
        is_logged_in, device_jid = self.is_device_logged_in()
        if not is_logged_in:
            return {
                "code": "DEVICE_NOT_LOGGED_IN",
                "message": "Device not logged in to WhatsApp. Please scan QR code at http://13.55.23.245:3000",
                "results": None,
            }
        
        # Validate file exists
        if not os.path.isfile(file_path):
            return {
                "code": "FILE_NOT_FOUND",
                "message": f"File not found: {file_path}",
                "results": None,
            }
        
        # Get file size (limit 100MB)
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            return {
                "code": "FILE_TOO_LARGE",
                "message": f"File too large: {file_size / 1024 / 1024:.1f}MB (max 100MB)",
                "results": None,
            }
        
        file_name = os.path.basename(file_path)
        url = f"{self.base_url}/send/file"
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_name, f)}
                data = {"phone": phone}
                if caption:
                    data["caption"] = caption
                
                with httpx.Client(timeout=120) as client:  # Longer timeout for file upload
                    response = client.post(
                        url,
                        files=files,
                        data=data,
                        auth=httpx.BasicAuth(self.username, self.password),
                    )
                    response.raise_for_status()
                    return response.json()
                    
        except httpx.ConnectError as e:
            error_msg = f"Cannot connect to GoWA server at {self.base_url}"
            logger.error(f"{error_msg}: {str(e)}")
            raise GoWAConnectionError(error_msg)
            
        except httpx.TimeoutException:
            return {
                "code": "TIMEOUT",
                "message": f"File upload timeout (file: {file_name}, size: {file_size / 1024:.0f}KB)",
                "results": None,
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "code": "HTTP_ERROR",
                "message": f"HTTP {e.response.status_code}: {e.response.text[:200]}",
                "results": None,
            }
            
        except Exception as e:
            logger.error(f"Error sending file: {str(e)}")
            return {
                "code": "ERROR",
                "message": f"Failed to send file: {str(e)}",
                "results": None,
            }
