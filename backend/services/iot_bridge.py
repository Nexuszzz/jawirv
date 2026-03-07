"""
JAWIR OS - IoT MQTT Bridge Service
====================================
Persistent MQTT connection to HiveMQ Cloud for IoT device communication.
Handles subscriptions, message parsing, and command publishing.
"""

import asyncio
import json
import logging
import ssl
from datetime import datetime
from typing import Optional

logger = logging.getLogger("jawir.iot.bridge")

# Try to import paho-mqtt (sync, more common) first, fallback message if not found
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not installed. IoT MQTT bridge disabled.")


class IoTMQTTBridge:
    """
    MQTT Bridge for IoT devices.
    Maintains persistent connection to HiveMQ Cloud.
    """
    
    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Topic patterns
        self.TOPICS = {
            # Fan device
            "fan_status": "jawir/device/fan-01/status",
            "fan_control": "jawir/device/fan-01/control",
            # Fire detector (using existing topics from firmware)
            "fire_telemetry": "nimak/deteksi-api/telemetry",
            "fire_cmd": "nimak/deteksi-api/cmd",
            "fire_event": "lab/zaks/event",
            "fire_status": "lab/zaks/status",
            "fire_alert": "lab/zaks/alert",
        }
    
    def _create_client(self) -> mqtt.Client:
        """Create and configure MQTT client."""
        # Use newer callback API version
        client = mqtt.Client(
            client_id=f"jawir-os-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        
        # Set credentials
        client.username_pw_set(self.username, self.password)
        
        # Configure TLS
        if self.use_tls:
            client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
            client.tls_insecure_set(False)
        
        # Set callbacks
        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        
        return client
    
    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """Handle MQTT connection."""
        if reason_code == 0:
            logger.info(f"✅ MQTT Connected to {self.host}")
            self._connected = True
            self._update_state_connected(True)
            
            # Subscribe to all device topics
            topics = [
                (self.TOPICS["fan_status"], 0),
                (self.TOPICS["fire_telemetry"], 0),
                (self.TOPICS["fire_event"], 0),
                (self.TOPICS["fire_status"], 0),
                (self.TOPICS["fire_alert"], 0),
            ]
            client.subscribe(topics)
            logger.info(f"Subscribed to {len(topics)} topics")
        else:
            logger.error(f"MQTT Connection failed: {reason_code}")
            self._connected = False
    
    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        """Handle MQTT disconnection."""
        logger.warning(f"MQTT Disconnected: {reason_code}")
        self._connected = False
        self._update_state_connected(False)
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            topic = msg.topic
            payload_str = msg.payload.decode("utf-8")
            logger.debug(f"MQTT Message: {topic} -> {payload_str[:100]}")
            
            # Parse JSON payload
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = {"raw": payload_str}
            
            # Route to appropriate handler
            if topic == self.TOPICS["fan_status"]:
                self._handle_fan_status(payload)
            elif topic == self.TOPICS["fire_telemetry"]:
                self._handle_fire_telemetry(payload)
            elif topic == self.TOPICS["fire_status"]:
                self._handle_fire_lwt(payload)
            elif topic == self.TOPICS["fire_alert"]:
                self._handle_fire_alert(payload)
            elif topic == self.TOPICS["fire_event"]:
                self._handle_fire_event(payload)
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _update_state_connected(self, connected: bool):
        """Update IoT state manager connection status."""
        try:
            from services.iot_state import iot_state
            iot_state.set_mqtt_connected(connected)
        except ImportError:
            pass
    
    def _handle_fan_status(self, payload: dict):
        """Handle fan status update. Robust against NaN DHT."""
        try:
            from services.iot_state import iot_state, FanSpeed, FanControlMode
            
            device_id = payload.get("device_id", "fan-01")
            mode_str = payload.get("mode", "manual")
            speed_str = payload.get("speed", "off")
            temp = payload.get("temperature")
            
            # DHT robustness
            temperature = None
            if temp is not None:
                try:
                    import math
                    t_val = float(temp)
                    if not math.isnan(t_val) and -40 <= t_val <= 80:
                        temperature = t_val
                except (ValueError, TypeError):
                    pass
            
            iot_state.update_device(
                device_id,
                mode=FanControlMode(mode_str) if mode_str else FanControlMode.MANUAL,
                speed=FanSpeed(speed_str) if speed_str else FanSpeed.OFF,
                temperature=temperature,
            )
            
        except Exception as e:
            logger.error(f"Error handling fan status: {e}")
    
    def _handle_fire_telemetry(self, payload: dict):
        """Handle fire detector telemetry. Robust against NaN/null DHT readings."""
        try:
            from services.iot_state import iot_state
            
            device_id = "fire-detector-01"
            
            # DHT robustness: only accept valid float readings
            raw_temp = payload.get("t")
            raw_hum = payload.get("h")
            temperature = None
            humidity = None
            
            if raw_temp is not None:
                try:
                    t_val = float(raw_temp)
                    import math
                    if not math.isnan(t_val) and -40 <= t_val <= 80:  # DHT11 valid range
                        temperature = t_val
                except (ValueError, TypeError):
                    pass
            
            if raw_hum is not None:
                try:
                    h_val = float(raw_hum)
                    import math
                    if not math.isnan(h_val) and 0 <= h_val <= 100:
                        humidity = h_val
                except (ValueError, TypeError):
                    pass
            
            iot_state.update_device(
                device_id,
                temperature=temperature,
                humidity=humidity,
                gas_analog=payload.get("gasA", 0),
                gas_triggered=payload.get("gasD", False),
                flame_detected=payload.get("flame", False),
                alarm_active=payload.get("alarm", False),
                force_alarm=payload.get("forceAlarm", False),
            )
            
        except Exception as e:
            logger.error(f"Error handling fire telemetry: {e}")
    
    def _handle_fire_lwt(self, payload: dict):
        """Handle fire detector LWT status."""
        try:
            from services.iot_state import iot_state
            
            status = payload.get("status", "offline")
            if status == "offline":
                iot_state.set_device_offline("fire-detector-01")
            else:
                iot_state.update_device("fire-detector-01")  # Just touch to mark online
                
        except Exception as e:
            logger.error(f"Error handling fire LWT: {e}")
    
    def _handle_fire_alert(self, payload: dict):
        """Handle fire alert event."""
        try:
            from services.iot_state import iot_state
            
            device_id = "fire-detector-01"
            alert_type = payload.get("alert", "unknown")
            
            iot_state.add_event(
                device_id=device_id,
                event_type=f"alert_{alert_type}",
                payload=payload,
            )
            
            # Update alarm state
            iot_state.update_device(device_id, alarm_active=True)
            
            # Broadcast fire alert to all clients for immediate popup
            device = iot_state.get_device(device_id)
            if device and iot_state._ws_broadcast_callback:
                iot_state._ws_broadcast_callback({
                    "type": "iot_fire_alert",
                    "device_id": device_id,
                    "device_name": device.name,
                    "room": device.room,
                    "alert_type": alert_type,
                    "message": f"API terdeteksi di {device.room}!",
                })
                logger.info(f"Fire alert broadcast for {device_id}")
            
        except Exception as e:
            logger.error(f"Error handling fire alert: {e}")
    
    def _handle_fire_event(self, payload: dict):
        """Handle general fire detector events."""
        try:
            from services.iot_state import iot_state
            
            event_type = payload.get("event", "unknown")
            device_id = "fire-detector-01"
            
            iot_state.add_event(
                device_id=device_id,
                event_type=event_type,
                payload=payload,
            )
            
            # If it's an alarm event, broadcast fire alert and update state
            if "alarm" in event_type.lower() or "fire" in event_type.lower() or "flame" in event_type.lower():
                iot_state.update_device(device_id, alarm_active=True)
                
                device = iot_state.get_device(device_id)
                if device and iot_state._ws_broadcast_callback:
                    iot_state._ws_broadcast_callback({
                        "type": "iot_fire_alert",
                        "device_id": device_id,
                        "device_name": device.name,
                        "room": device.room,
                        "alert_type": event_type,
                        "message": f"API terdeteksi di {device.room}!",
                    })
                    logger.info(f"Fire event broadcast: {event_type} for {device_id}")
            
        except Exception as e:
            logger.error(f"Error handling fire event: {e}")
    
    # === Public Methods ===
    
    def connect(self) -> bool:
        """Connect to MQTT broker. Non-blocking wait with threading event."""
        if not MQTT_AVAILABLE:
            logger.error("paho-mqtt not installed")
            return False
        
        try:
            self._client = self._create_client()
            self._client.connect(self.host, self.port, keepalive=30)
            self._client.loop_start()  # Start background thread
            
            # Wait up to 5s for connection using threading.Event (no time.sleep!)
            import threading
            conn_event = threading.Event()
            original_on_connect = self._client.on_connect
            
            def _wait_connect(client, userdata, flags, reason_code, properties=None):
                original_on_connect(client, userdata, flags, reason_code, properties)
                conn_event.set()
            
            self._client.on_connect = _wait_connect
            conn_event.wait(timeout=5.0)
            self._client.on_connect = original_on_connect
            
            return self._connected
            
        except Exception as e:
            logger.error(f"MQTT connect error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("MQTT Disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self._connected
    
    def publish_fan_control(self, mode: str = None, speed: str = None) -> bool:
        """
        Publish fan control command.
        
        Args:
            mode: "manual" or "auto"
            speed: "off", "low", "med", or "high"
        """
        if not self._connected or not self._client:
            logger.warning("MQTT not connected, cannot publish")
            return False
        
        params = {}
        if mode:
            params["mode"] = mode
        if speed:
            params["speed"] = speed
        
        payload = {
            "device_id": "fan-01",
            "params": params,
        }
        
        try:
            result = self._client.publish(
                self.TOPICS["fan_control"],
                json.dumps(payload),
                qos=1,
            )
            result.wait_for_publish()
            logger.info(f"Published fan control: {params}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish fan control: {e}")
            return False
    
    def publish_fire_command(self, command: str) -> bool:
        """
        Publish fire detector command.
        
        Args:
            command: "BUZZER_ON", "BUZZER_OFF", or "THR=<value>"
        """
        if not self._connected or not self._client:
            logger.warning("MQTT not connected, cannot publish")
            return False
        
        try:
            result = self._client.publish(
                self.TOPICS["fire_cmd"],
                command,
                qos=1,
            )
            result.wait_for_publish()
            logger.info(f"Published fire command: {command}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish fire command: {e}")
            return False
    
    def get_health(self) -> dict:
        """Get MQTT bridge health status."""
        return {
            "status": "connected" if self._connected else "disconnected",
            "broker": f"{self.host}:{self.port}" if self._connected else None,
            "mqtt_available": MQTT_AVAILABLE,
        }


# Singleton instance (lazy initialized)
_bridge_instance: Optional[IoTMQTTBridge] = None


def get_iot_bridge() -> Optional[IoTMQTTBridge]:
    """Get or create IoT MQTT bridge instance."""
    global _bridge_instance
    
    if _bridge_instance is None:
        from app.config import settings
        
        if not settings.iot_enabled:
            logger.info("IoT is disabled (IOT_ENABLED=false)")
            return None
        
        if not settings.iot_mqtt_host:
            logger.warning("IoT MQTT host not configured")
            return None
        
        _bridge_instance = IoTMQTTBridge(
            host=settings.iot_mqtt_host,
            port=settings.iot_mqtt_port,
            username=settings.iot_mqtt_user,
            password=settings.iot_mqtt_pass,
            use_tls=settings.iot_mqtt_use_tls,
        )
    
    return _bridge_instance


def start_iot_bridge() -> bool:
    """Start IoT MQTT bridge if enabled."""
    bridge = get_iot_bridge()
    if bridge:
        return bridge.connect()
    return False


def stop_iot_bridge():
    """Stop IoT MQTT bridge."""
    global _bridge_instance
    if _bridge_instance:
        _bridge_instance.disconnect()
        _bridge_instance = None
