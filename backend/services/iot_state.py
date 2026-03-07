"""
JAWIR OS - IoT State Management
================================
In-memory cache for IoT device states and events.
Thread-safe for concurrent access from MQTT callbacks and HTTP endpoints.
"""

import logging
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Optional
from collections import deque
from pydantic import BaseModel

logger = logging.getLogger("jawir.iot.state")


class DeviceType(str, Enum):
    """Supported IoT device types."""
    FAN = "fan"
    FIRE_DETECTOR = "fire_detector"


class FanSpeed(str, Enum):
    """Fan speed levels."""
    OFF = "off"
    LOW = "low"
    MED = "med"
    HIGH = "high"


class FanControlMode(str, Enum):
    """Fan control modes."""
    MANUAL = "manual"
    AUTO = "auto"


class IoTDevice(BaseModel):
    """Base model for IoT devices."""
    device_id: str
    device_type: DeviceType
    name: str = ""
    room: str = ""
    online: bool = False
    last_seen: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class FanState(IoTDevice):
    """State model for fan devices."""
    device_type: DeviceType = DeviceType.FAN
    mode: FanControlMode = FanControlMode.MANUAL
    speed: FanSpeed = FanSpeed.OFF
    temperature: Optional[float] = None


class FireDetectorState(IoTDevice):
    """State model for fire detector devices."""
    device_type: DeviceType = DeviceType.FIRE_DETECTOR
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    gas_analog: int = 0
    gas_triggered: bool = False
    flame_detected: bool = False
    alarm_active: bool = False
    force_alarm: bool = False


class IoTEvent(BaseModel):
    """Model for IoT events."""
    device_id: str
    event_type: str  # "flame_on", "yolo_alarm", "status_change", etc.
    payload: dict = {}
    timestamp: datetime


class IoTStateManager:
    """
    Thread-safe in-memory state manager for IoT devices.
    Singleton pattern for global access.
    """
    _instance: Optional["IoTStateManager"] = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_state()
        return cls._instance
    
    def _init_state(self):
        """Initialize internal state."""
        self._devices: dict[str, IoTDevice] = {}
        self._events: deque[IoTEvent] = deque(maxlen=200)  # Last 200 events
        self._state_lock = Lock()
        self._ws_broadcast_callback = None  # For WebSocket integration
        self._mqtt_connected = False
        self._last_mqtt_activity: Optional[datetime] = None
        
        # Pre-register known devices
        self._register_default_devices()
    
    def _register_default_devices(self):
        """Register known devices from firmware."""
        # Fan device
        self._devices["fan-01"] = FanState(
            device_id="fan-01",
            name="Kipas Ruangan",
            room="Kos",
        )
        # Fire detector device
        self._devices["fire-detector-01"] = FireDetectorState(
            device_id="fire-detector-01", 
            name="Detektor Api",
            room="Kos",
        )
        logger.info(f"Registered {len(self._devices)} default IoT devices")
    
    # === Device State ===
    
    def get_device(self, device_id: str) -> Optional[IoTDevice]:
        """Get device state by ID."""
        with self._state_lock:
            return self._devices.get(device_id)
    
    def get_all_devices(self) -> list[IoTDevice]:
        """Get all registered devices."""
        with self._state_lock:
            return list(self._devices.values())
    
    def set_ws_broadcast_callback(self, callback):
        """Set callback for WebSocket broadcasting (called from main.py)."""
        self._ws_broadcast_callback = callback
        logger.info("WebSocket broadcast callback registered for IoT state")
    
    def _broadcast_device_update(self, device: IoTDevice):
        """Broadcast device update to all connected WebSocket clients."""
        if self._ws_broadcast_callback:
            try:
                # mode='json' auto-converts datetime→ISO string and enums→values
                device_dict = device.model_dump(mode='json')
                
                self._ws_broadcast_callback({
                    "type": "iot_device_update",
                    "device": device_dict,
                    "timestamp": datetime.now().isoformat(),
                })
            except Exception as e:
                logger.error(f"Failed to broadcast IoT update: {e}")
    
    def update_device(self, device_id: str, **kwargs) -> Optional[IoTDevice]:
        """
        Update device state.
        Returns updated device or None if not found.
        """
        with self._state_lock:
            device = self._devices.get(device_id)
            if device is None:
                logger.warning(f"Device not found: {device_id}")
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(device, key):
                    setattr(device, key, value)
            
            device.last_seen = datetime.now()
            device.online = True
            
            logger.debug(f"Updated device {device_id}: {kwargs}")
        
        # Broadcast update outside the lock to avoid deadlock
        self._broadcast_device_update(device)
        return device
    
    def set_device_offline(self, device_id: str):
        """Mark device as offline."""
        with self._state_lock:
            device = self._devices.get(device_id)
            if device:
                device.online = False
                logger.info(f"Device {device_id} marked offline")
    
    # === Events ===
    
    def add_event(self, device_id: str, event_type: str, payload: dict = None):
        """Add an event to the history."""
        event = IoTEvent(
            device_id=device_id,
            event_type=event_type,
            payload=payload or {},
            timestamp=datetime.now(),
        )
        with self._state_lock:
            self._events.append(event)
        logger.info(f"IoT Event: {device_id} - {event_type}")
    
    def get_events(self, limit: int = 20, device_id: str = None) -> list[IoTEvent]:
        """Get recent events, optionally filtered by device."""
        with self._state_lock:
            events = list(self._events)
        
        if device_id:
            events = [e for e in events if e.device_id == device_id]
        
        # Return most recent first
        return list(reversed(events))[:limit]
    
    # === MQTT Connection ===
    
    def set_mqtt_connected(self, connected: bool):
        """Update MQTT connection status."""
        self._mqtt_connected = connected
        if connected:
            self._last_mqtt_activity = datetime.now()
    
    def is_mqtt_connected(self) -> bool:
        """Check if MQTT is connected."""
        return self._mqtt_connected
    
    def get_last_mqtt_activity(self) -> Optional[datetime]:
        """Get last MQTT activity timestamp."""
        return self._last_mqtt_activity
    
    # === Stats ===
    
    def get_stats(self) -> dict:
        """Get IoT statistics."""
        with self._state_lock:
            devices = list(self._devices.values())
            return {
                "total_devices": len(devices),
                "online_devices": sum(1 for d in devices if d.online),
                "active_alerts": sum(
                    1 for d in devices 
                    if isinstance(d, FireDetectorState) and d.alarm_active
                ),
                "mqtt_connected": self._mqtt_connected,
                "event_count": len(self._events),
            }


# Global instance
iot_state = IoTStateManager()
