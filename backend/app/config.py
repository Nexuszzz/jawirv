"""
JAWIR OS - Configuration Module
Pydantic Settings for environment variable management.
"""

from functools import lru_cache
from typing import Literal
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the backend directory (where .env lives)
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # API Keys - Support multiple keys for rotation (paid tier only)
    google_api_keys: str = ""  # Comma-separated list of keys
    google_api_key: str = ""   # Legacy single key fallback (optional)
    tavily_api_key: str = ""   # Optional, for web search
    
    # GoWA (WhatsApp) Configuration
    gowa_base_url: str = "http://13.55.23.245:3000"
    gowa_username: str = "admin"
    gowa_password: str = "jawir2026"
    
    # Server Configuration
    ws_port: int = 8000
    environment: Literal["development", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    
    # Database
    database_url: str = "sqlite:///./jawir.db"
    
    # Agent Configuration
    max_retry_count: int = 3
    max_context_words: int = 25000
    
    # Function Calling (Gemini native tool calling)
    use_function_calling: bool = False  # Set True to enable Gemini function calling
    
    # Gemini Model
    gemini_model: str = "gemini-3-pro-preview"
    
    # Deep Research Settings
    deep_research_breadth: int = 4
    deep_research_depth: int = 2
    
    # Safety Guards
    safe_mode: bool = True  # Default safe - prevents destructive tool actions
    allow_destructive_actions: bool = False  # Must be explicitly enabled
    
    # IoT Configuration (MQTT Bridge)
    iot_enabled: bool = False  # Feature flag - safe default
    iot_mqtt_host: str = ""
    iot_mqtt_port: int = 8883
    iot_mqtt_user: str = ""
    iot_mqtt_pass: str = ""
    iot_mqtt_use_tls: bool = True
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def all_google_api_keys(self) -> list[str]:
        """Get all available Google API keys as a list."""
        keys = []
        
        # First add keys from comma-separated list
        if self.google_api_keys:
            keys.extend([k.strip() for k in self.google_api_keys.split(",") if k.strip()])
        
        # Add legacy single key if not already included
        if self.google_api_key and self.google_api_key not in keys:
            keys.append(self.google_api_key)
        
        return keys


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid re-reading .env file on every call.
    """
    return Settings()


# Export settings instance for easy import
settings = get_settings()
