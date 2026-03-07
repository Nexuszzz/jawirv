"""
JAWIR OS - API Key Rotator
Manages multiple Gemini API keys with automatic rotation on rate limit.
"""

import logging
import threading
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger("jawir.api_rotator")


class APIKeyRotator:
    """
    Thread-safe API key rotator with rate limit handling.
    
    Features:
    - Round-robin rotation
    - Automatic skip of rate-limited keys
    - Permanent disable for leaked/invalid keys
    - Cooldown period for exhausted keys
    - Thread-safe for concurrent requests
    """
    
    def __init__(self, api_keys: list[str], cooldown_minutes: int = 1):
        """
        Initialize rotator with list of API keys.
        
        Args:
            api_keys: List of Gemini API keys
            cooldown_minutes: Minutes to wait before retrying rate-limited key
        """
        self.api_keys = [k.strip() for k in api_keys if k.strip()]
        self.cooldown_minutes = cooldown_minutes
        self.current_index = 0
        self.lock = threading.Lock()
        
        # Track rate-limited keys: {key: datetime when cooldown expires}
        self.rate_limited: dict[str, datetime] = {}
        
        # Track permanently disabled keys (leaked/invalid)
        self.disabled_keys: set[str] = set()
        
        # Stats
        self.request_counts: dict[str, int] = {k: 0 for k in self.api_keys}
        self.error_counts: dict[str, int] = {k: 0 for k in self.api_keys}
        
        logger.info(f"🔑 API Key Rotator initialized with {len(self.api_keys)} keys")
    
    def get_key(self) -> str:
        """
        Get the next available API key.
        Skips rate-limited and disabled keys and rotates automatically.
        
        Returns:
            Available API key
            
        Raises:
            RuntimeError: If all keys are rate-limited or disabled
        """
        with self.lock:
            now = datetime.now()
            attempts = 0
            
            while attempts < len(self.api_keys):
                key = self.api_keys[self.current_index]
                
                # Check if key is permanently disabled
                if key in self.disabled_keys:
                    self.current_index = (self.current_index + 1) % len(self.api_keys)
                    attempts += 1
                    continue
                
                # Check if key is rate-limited
                if key in self.rate_limited:
                    if now < self.rate_limited[key]:
                        # Still in cooldown, skip
                        self.current_index = (self.current_index + 1) % len(self.api_keys)
                        attempts += 1
                        continue
                    else:
                        # Cooldown expired, remove from rate-limited
                        del self.rate_limited[key]
                        logger.info(f"🔓 Key #{self.current_index + 1} cooldown expired, back in rotation")
                
                # Track usage
                self.request_counts[key] += 1
                
                # Rotate for next call
                self.current_index = (self.current_index + 1) % len(self.api_keys)
                
                logger.debug(f"🔑 Using key #{self.api_keys.index(key) + 1} (requests: {self.request_counts[key]})")
                return key
            
            # Check how many keys are still usable
            usable_keys = len(self.api_keys) - len(self.disabled_keys)
            if usable_keys == 0:
                raise RuntimeError("All API keys are disabled (leaked/invalid). Please add new keys.")
            
            # All usable keys are rate-limited
            min_wait = min(self.rate_limited.values())
            wait_seconds = (min_wait - now).total_seconds()
            
            logger.warning(f"⚠️ All {usable_keys} usable keys are rate-limited. Shortest wait: {wait_seconds:.0f}s")
            
            # Return the key with shortest cooldown anyway
            for key, expires in sorted(self.rate_limited.items(), key=lambda x: x[1]):
                if key not in self.disabled_keys:
                    return key
            
            raise RuntimeError("No API keys available")
    
    def mark_disabled(self, key: str, reason: str = ""):
        """
        Permanently disable a key (leaked, invalid, etc).
        
        Args:
            key: The API key to disable
            reason: Reason for disabling
        """
        with self.lock:
            self.disabled_keys.add(key)
            self.error_counts[key] += 1
            
            key_index = self.api_keys.index(key) + 1 if key in self.api_keys else "?"
            remaining = len(self.api_keys) - len(self.disabled_keys)
            logger.error(f"🚫 Key #{key_index} DISABLED: {reason}. Remaining keys: {remaining}")
    
    def mark_rate_limited(self, key: str, retry_after_seconds: int = 60):
        """
        Mark a key as rate-limited.
        
        Args:
            key: The API key that hit rate limit
            retry_after_seconds: Seconds to wait before retrying (from API response)
        """
        with self.lock:
            cooldown = max(retry_after_seconds, self.cooldown_minutes * 60)
            expires = datetime.now() + timedelta(seconds=cooldown)
            self.rate_limited[key] = expires
            self.error_counts[key] += 1
            
            key_index = self.api_keys.index(key) + 1 if key in self.api_keys else "?"
            logger.warning(f"🔒 Key #{key_index} rate-limited, cooldown: {cooldown}s")
    
    def get_stats(self) -> dict:
        """Get usage statistics for all keys."""
        with self.lock:
            now = datetime.now()
            return {
                "total_keys": len(self.api_keys),
                "active_keys": len(self.api_keys) - len(self.rate_limited) - len(self.disabled_keys),
                "rate_limited_keys": len(self.rate_limited),
                "disabled_keys": len(self.disabled_keys),
                "keys": [
                    {
                        "index": i + 1,
                        "requests": self.request_counts[k],
                        "errors": self.error_counts[k],
                        "status": "disabled" if k in self.disabled_keys else ("rate_limited" if k in self.rate_limited else "active"),
                        "cooldown_remaining": max(0, (self.rate_limited.get(k, now) - now).total_seconds()) if k in self.rate_limited else 0
                    }
                    for i, k in enumerate(self.api_keys)
                ]
            }


# Global rotator instance (will be initialized from settings)
_rotator: Optional[APIKeyRotator] = None


def init_rotator(api_keys: list[str]) -> APIKeyRotator:
    """Initialize the global API key rotator."""
    global _rotator
    _rotator = APIKeyRotator(api_keys)
    return _rotator


def get_rotator() -> Optional[APIKeyRotator]:
    """Get the global rotator instance."""
    return _rotator


def get_api_key() -> str:
    """
    Convenience function to get next API key.
    Falls back to first key if rotator not initialized.
    """
    if _rotator is None:
        raise RuntimeError("API Key Rotator not initialized. Call init_rotator() first.")
    return _rotator.get_key()


def mark_key_rate_limited(key: str, retry_after: int = 60):
    """Convenience function to mark key as rate-limited."""
    if _rotator:
        _rotator.mark_rate_limited(key, retry_after)


def mark_key_disabled(key: str, reason: str = ""):
    """Convenience function to permanently disable a key."""
    if _rotator:
        _rotator.mark_disabled(key, reason)
