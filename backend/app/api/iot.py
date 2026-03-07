"""
JAWIR OS - IoT REST API Router
================================
REST endpoints for IoT device state and control.
Used by frontend IoTPanel to display real-time data.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger("jawir.api.iot")

router = APIRouter(prefix="/api/iot", tags=["IoT"])


class ControlRequest(BaseModel):
    """Request body for device control."""
    action: str
    value: Optional[str] = None


@router.get("/devices")
async def list_devices(include_offline: bool = Query(True, description="Include offline devices")):
    """
    Get all IoT devices with current state.
    Returns device list and stats for dashboard display.
    """
    try:
        from services.iot_state import iot_state
        
        devices = iot_state.get_all_devices()
        if not include_offline:
            devices = [d for d in devices if d.online]
        
        # Convert to dict for JSON serialization
        device_list = []
        for d in devices:
            device_dict = d.model_dump()
            # Ensure enum values are strings
            if hasattr(d, 'device_type'):
                device_dict['device_type'] = str(d.device_type.value) if hasattr(d.device_type, 'value') else str(d.device_type)
            if hasattr(d, 'mode'):
                device_dict['mode'] = str(d.mode.value) if hasattr(d.mode, 'value') else str(d.mode)
            if hasattr(d, 'speed'):
                device_dict['speed'] = str(d.speed.value) if hasattr(d.speed, 'value') else str(d.speed)
            device_list.append(device_dict)
        
        return {
            "success": True,
            "devices": device_list,
            "stats": iot_state.get_stats(),
        }
        
    except Exception as e:
        logger.error(f"Error listing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/{device_id}")
async def get_device(device_id: str):
    """
    Get single device state by ID.
    Returns detailed device state for device card display.
    """
    try:
        from services.iot_state import iot_state
        
        device = iot_state.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
        
        device_dict = device.model_dump()
        # Ensure enum values are strings
        if hasattr(device, 'device_type'):
            device_dict['device_type'] = str(device.device_type.value) if hasattr(device.device_type, 'value') else str(device.device_type)
        if hasattr(device, 'mode'):
            device_dict['mode'] = str(device.mode.value) if hasattr(device.mode, 'value') else str(device.mode)
        if hasattr(device, 'speed'):
            device_dict['speed'] = str(device.speed.value) if hasattr(device.speed, 'value') else str(device.speed)
        
        return {
            "success": True,
            "device": device_dict,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/{device_id}/control")
async def control_device(device_id: str, request: ControlRequest):
    """
    Send control command to device via MQTT.
    Supports fan speed/mode control and fire detector buzzer control.
    """
    try:
        from services.iot_bridge import get_iot_bridge
        from services.iot_state import iot_state
        
        bridge = get_iot_bridge()
        if not bridge:
            raise HTTPException(status_code=503, detail="IoT bridge not available")
        
        if not bridge.is_connected():
            raise HTTPException(status_code=503, detail="MQTT not connected")
        
        action = request.action
        value = request.value
        success = False
        message = ""
        
        # Handle fan control
        if device_id == "fan-01":
            if action == "set_speed":
                if value not in ("off", "low", "med", "high"):
                    raise HTTPException(status_code=400, detail=f"Invalid speed: {value}")
                success = bridge.publish_fan_control(speed=value)
                message = f"Fan speed set to {value}"
            elif action == "set_mode":
                if value not in ("manual", "auto"):
                    raise HTTPException(status_code=400, detail=f"Invalid mode: {value}")
                success = bridge.publish_fan_control(mode=value)
                message = f"Fan mode set to {value}"
            elif action == "turn_on":
                speed = value if value in ("low", "med", "high") else "low"
                success = bridge.publish_fan_control(mode="manual", speed=speed)
                message = f"Fan turned on at {speed}"
            elif action == "turn_off":
                success = bridge.publish_fan_control(speed="off")
                message = "Fan turned off"
            else:
                raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
        # Handle fire detector control
        elif device_id == "fire-detector-01":
            if action in ("buzzer_off", "reset"):
                success = bridge.publish_fire_command("BUZZER_OFF")
                message = "Alarm buzzer turned off"
                # Also update local state
                iot_state.update_device(device_id, alarm_active=False)
            elif action == "buzzer_on":
                success = bridge.publish_fire_command("BUZZER_ON")
                message = "Alarm buzzer turned on"
            else:
                raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
        
        else:
            raise HTTPException(status_code=404, detail=f"Unknown device: {device_id}")
        
        # Log event
        iot_state.add_event(device_id, f"control_{action}", {"value": value, "success": success})
        
        return {
            "success": success,
            "action": action,
            "value": value,
            "message": message,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(
    limit: int = Query(20, ge=1, le=100, description="Max events to return"),
    device_id: Optional[str] = Query(None, description="Filter by device ID")
):
    """
    Get recent IoT events.
    Returns event history for activity feed display.
    """
    try:
        from services.iot_state import iot_state
        
        events = iot_state.get_events(limit=limit, device_id=device_id)
        
        event_list = []
        for e in events:
            event_list.append({
                "device_id": e.device_id,
                "event_type": e.event_type,
                "payload": e.payload,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            })
        
        return {
            "success": True,
            "events": event_list,
            "count": len(event_list),
        }
        
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))
