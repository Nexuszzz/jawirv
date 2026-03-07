"""
JAWIR OS - IoT Tools for Gemini Function Calling
==================================================
5 tools for controlling IoT devices via MQTT.

Tools:
1. iot_list_devices - List all IoT devices with status
2. iot_get_device_state - Get detailed state of a device
3. iot_set_device_state - Control device (fan speed, alarm)
4. iot_get_latest_events - Get recent IoT events
5. iot_ack_or_reset_alarm - Reset fire alarm
"""

import logging
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

logger = logging.getLogger("jawir.tools.iot")


# ============================================================
# Input Schemas (Pydantic)
# ============================================================

class IoTListDevicesInput(BaseModel):
    """Input for listing IoT devices."""
    include_offline: bool = Field(
        default=True,
        description="Include offline devices in the list"
    )


class IoTGetDeviceStateInput(BaseModel):
    """Input for getting device state."""
    device_id: str = Field(
        description="Device ID (e.g., 'fan-01' or 'fire-detector-01')"
    )


class IoTSetDeviceStateInput(BaseModel):
    """Input for setting device state."""
    device_id: str = Field(
        description="Device ID (e.g., 'fan-01')"
    )
    action: str = Field(
        description="Action to perform: 'turn_on', 'turn_off', 'set_speed', 'set_mode'"
    )
    value: Optional[str] = Field(
        default=None,
        description="Value for action: speed ('low', 'med', 'high') or mode ('manual', 'auto')"
    )


class IoTGetLatestEventsInput(BaseModel):
    """Input for getting IoT events."""
    limit: int = Field(
        default=10,
        description="Maximum number of events to return (1-50)"
    )
    device_id: Optional[str] = Field(
        default=None,
        description="Filter by device ID (optional)"
    )


class IoTResetAlarmInput(BaseModel):
    """Input for resetting fire alarm."""
    device_id: str = Field(
        default="fire-detector-01",
        description="Fire detector device ID"
    )


# ============================================================
# Tool Implementations
# ============================================================

def _check_iot_enabled() -> tuple[bool, str]:
    """Check if IoT is enabled and return status."""
    try:
        from app.config import settings
        if not settings.iot_enabled:
            return False, "IoT integration is disabled (IOT_ENABLED=false)"
        return True, "ok"
    except Exception as e:
        return False, f"Error checking IoT config: {e}"


def iot_list_devices(include_offline: bool = True) -> dict:
    """
    List all registered IoT devices with their current status.
    Returns device list with online/offline status, type, and room.
    """
    enabled, msg = _check_iot_enabled()
    if not enabled:
        return {
            "success": False,
            "error": msg,
            "devices": [],
            "summary": "IoT tidak aktif",
        }
    
    try:
        from services.iot_state import iot_state
        
        devices = iot_state.get_all_devices()
        stats = iot_state.get_stats()
        
        if not include_offline:
            devices = [d for d in devices if d.online]
        
        device_list = []
        for d in devices:
            device_list.append({
                "device_id": d.device_id,
                "name": d.name,
                "type": d.device_type,
                "room": d.room,
                "online": d.online,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            })
        
        return {
            "success": True,
            "devices": device_list,
            "stats": stats,
            "summary": f"Ditemukan {len(device_list)} device IoT ({stats['online_devices']} online)",
        }
        
    except Exception as e:
        logger.error(f"Error listing IoT devices: {e}")
        return {
            "success": False,
            "error": str(e),
            "devices": [],
        }


def iot_get_device_state(device_id: str) -> dict:
    """
    Get detailed state of a specific IoT device.
    Returns all sensor readings and control state.
    """
    enabled, msg = _check_iot_enabled()
    if not enabled:
        return {"success": False, "error": msg, "device": None}
    
    try:
        from services.iot_state import iot_state, FanState, FireDetectorState
        
        device = iot_state.get_device(device_id)
        if not device:
            return {
                "success": False,
                "error": f"Device '{device_id}' tidak ditemukan",
                "device": None,
            }
        
        # Build response based on device type
        state_dict = {
            "device_id": device.device_id,
            "name": device.name,
            "type": device.device_type,
            "room": device.room,
            "online": device.online,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        }
        
        if isinstance(device, FanState):
            state_dict.update({
                "mode": device.mode,
                "speed": device.speed,
                "temperature": device.temperature,
                "summary": f"Kipas {device.name}: mode={device.mode}, speed={device.speed}, temp={device.temperature}°C",
            })
        elif isinstance(device, FireDetectorState):
            state_dict.update({
                "temperature": device.temperature,
                "humidity": device.humidity,
                "gas_analog": device.gas_analog,
                "gas_triggered": device.gas_triggered,
                "flame_detected": device.flame_detected,
                "alarm_active": device.alarm_active,
                "summary": f"Detektor {device.name}: alarm={'AKTIF' if device.alarm_active else 'off'}, temp={device.temperature}°C, gas={device.gas_analog}",
            })
        
        return {
            "success": True,
            "device": state_dict,
            "summary": state_dict.get("summary", f"Status {device_id}"),
        }
        
    except Exception as e:
        logger.error(f"Error getting device state: {e}")
        return {"success": False, "error": str(e), "device": None}


def iot_set_device_state(device_id: str, action: str, value: str = None) -> dict:
    """
    Control an IoT device.
    
    For fan-01:
      - action "turn_on": Turn fan on (speed=low or specified value)
      - action "turn_off": Turn fan off
      - action "set_speed": Set speed (value: off/low/med/high)
      - action "set_mode": Set mode (value: manual/auto)
    
    For fire-detector-01:
      - action "buzzer_on": Force buzzer on
      - action "buzzer_off": Turn buzzer off
    """
    enabled, msg = _check_iot_enabled()
    if not enabled:
        return {"success": False, "error": msg}
    
    try:
        from services.iot_bridge import get_iot_bridge
        
        bridge = get_iot_bridge()
        if not bridge:
            return {
                "success": False,
                "error": "MQTT bridge tidak tersedia",
            }
        
        if not bridge.is_connected():
            return {
                "success": False,
                "error": "MQTT tidak terhubung ke broker",
            }
        
        # Handle fan control
        if device_id == "fan-01":
            if action == "turn_on":
                speed = value if value in ("low", "med", "high") else "low"
                success = bridge.publish_fan_control(mode="manual", speed=speed)
                return {
                    "success": success,
                    "action": f"Menyalakan kipas dengan kecepatan {speed}",
                    "summary": f"Kipas dinyalakan ({speed})" if success else "Gagal menyalakan kipas",
                }
            
            elif action == "turn_off":
                success = bridge.publish_fan_control(speed="off")
                return {
                    "success": success,
                    "action": "Mematikan kipas",
                    "summary": "Kipas dimatikan" if success else "Gagal mematikan kipas",
                }
            
            elif action == "set_speed":
                if value not in ("off", "low", "med", "high"):
                    return {"success": False, "error": f"Speed tidak valid: {value}"}
                success = bridge.publish_fan_control(speed=value)
                return {
                    "success": success,
                    "action": f"Mengubah kecepatan ke {value}",
                    "summary": f"Kecepatan kipas: {value}" if success else "Gagal ubah kecepatan",
                }
            
            elif action == "set_mode":
                if value not in ("manual", "auto"):
                    return {"success": False, "error": f"Mode tidak valid: {value}"}
                success = bridge.publish_fan_control(mode=value)
                return {
                    "success": success,
                    "action": f"Mengubah mode ke {value}",
                    "summary": f"Mode kipas: {value}" if success else "Gagal ubah mode",
                }
            
            else:
                return {"success": False, "error": f"Action tidak dikenal: {action}"}
        
        # Handle fire detector control
        elif device_id == "fire-detector-01":
            if action in ("buzzer_on", "turn_on"):
                success = bridge.publish_fire_command("BUZZER_ON")
                return {
                    "success": success,
                    "action": "Menyalakan buzzer alarm",
                    "summary": "Buzzer alarm dinyalakan" if success else "Gagal",
                }
            
            elif action in ("buzzer_off", "turn_off", "reset"):
                success = bridge.publish_fire_command("BUZZER_OFF")
                return {
                    "success": success,
                    "action": "Mematikan buzzer alarm",
                    "summary": "Buzzer alarm dimatikan" if success else "Gagal",
                }
            
            else:
                return {"success": False, "error": f"Action tidak dikenal: {action}"}
        
        else:
            return {"success": False, "error": f"Device tidak dikenal: {device_id}"}
        
    except Exception as e:
        logger.error(f"Error setting device state: {e}")
        return {"success": False, "error": str(e)}


def iot_get_latest_events(limit: int = 10, device_id: str = None) -> dict:
    """
    Get latest IoT events (alerts, status changes, etc).
    Returns a list of events with timestamps.
    """
    enabled, msg = _check_iot_enabled()
    if not enabled:
        return {"success": False, "error": msg, "events": []}
    
    try:
        from services.iot_state import iot_state
        
        limit = max(1, min(50, limit))  # Clamp to 1-50
        events = iot_state.get_events(limit=limit, device_id=device_id)
        
        event_list = []
        for e in events:
            event_list.append({
                "device_id": e.device_id,
                "event_type": e.event_type,
                "payload": e.payload,
                "timestamp": e.timestamp.isoformat(),
            })
        
        return {
            "success": True,
            "events": event_list,
            "count": len(event_list),
            "summary": f"Ditemukan {len(event_list)} event IoT terbaru",
        }
        
    except Exception as e:
        logger.error(f"Error getting IoT events: {e}")
        return {"success": False, "error": str(e), "events": []}


def iot_ack_or_reset_alarm(device_id: str = "fire-detector-01") -> dict:
    """
    Acknowledge and reset fire alarm.
    Sends BUZZER_OFF command to the fire detector.
    """
    return iot_set_device_state(
        device_id=device_id,
        action="buzzer_off",
    )


# ============================================================
# Tool Factory Functions (for agent registry)
# ============================================================

def create_iot_list_devices_tool() -> StructuredTool:
    """Create the iot_list_devices tool."""
    return StructuredTool.from_function(
        func=iot_list_devices,
        name="iot_list_devices",
        description="Daftar semua device IoT yang terdaftar beserta statusnya (online/offline, tipe, lokasi). Gunakan ini untuk melihat device IoT apa saja yang tersedia.",
        args_schema=IoTListDevicesInput,
    )


def create_iot_get_device_state_tool() -> StructuredTool:
    """Create the iot_get_device_state tool."""
    return StructuredTool.from_function(
        func=iot_get_device_state,
        name="iot_get_device_state",
        description="Dapatkan status detail sebuah device IoT tertentu. Untuk kipas: mode, speed, suhu. Untuk detektor api: alarm, suhu, gas, api. Contoh device_id: 'fan-01', 'fire-detector-01'.",
        args_schema=IoTGetDeviceStateInput,
    )


def create_iot_set_device_state_tool() -> StructuredTool:
    """Create the iot_set_device_state tool."""
    return StructuredTool.from_function(
        func=iot_set_device_state,
        name="iot_set_device_state",
        description="Kontrol device IoT. Untuk kipas (fan-01): action='turn_on|turn_off|set_speed|set_mode', value='low|med|high' atau 'manual|auto'. Untuk detektor (fire-detector-01): action='buzzer_on|buzzer_off'. Contoh: nyalakan kipas → device_id='fan-01', action='turn_on', value='high'.",
        args_schema=IoTSetDeviceStateInput,
    )


def create_iot_get_latest_events_tool() -> StructuredTool:
    """Create the iot_get_latest_events tool."""
    return StructuredTool.from_function(
        func=iot_get_latest_events,
        name="iot_get_latest_events",
        description="Dapatkan event IoT terbaru (alert kebakaran, perubahan status, dll). Bisa difilter per device. Default 10 event terakhir.",
        args_schema=IoTGetLatestEventsInput,
    )


def create_iot_reset_alarm_tool() -> StructuredTool:
    """Create the iot_ack_or_reset_alarm tool."""
    return StructuredTool.from_function(
        func=iot_ack_or_reset_alarm,
        name="iot_ack_or_reset_alarm",
        description="Reset alarm kebakaran (matikan buzzer). Gunakan setelah memastikan kondisi aman. Default device: fire-detector-01.",
        args_schema=IoTResetAlarmInput,
    )


def get_iot_tools() -> list[StructuredTool]:
    """
    Get all IoT tools for registration with the agent.
    Returns empty list if IoT is disabled (graceful degradation).
    """
    try:
        from app.config import settings
        if not settings.iot_enabled:
            logger.info("IoT tools skipped (IOT_ENABLED=false)")
            return []
    except Exception:
        return []
    
    return [
        create_iot_list_devices_tool(),
        create_iot_get_device_state_tool(),
        create_iot_set_device_state_tool(),
        create_iot_get_latest_events_tool(),
        create_iot_reset_alarm_tool(),
    ]
