"""
JAWIR OS - KiCad Schematic Templates
Pre-made circuit templates for common circuits.

AI bisa langsung pakai template atau modifikasi sesuai kebutuhan.
"""

from .schemas import (
    SchematicPlan,
    ComponentPlacement,
    WireConnection,
    PinReference,
    PowerLabel,
    Position,
)


# ============================================
# TEMPLATE DEFINITIONS
# ============================================

TEMPLATES: dict[str, SchematicPlan] = {
    # ----------------------------------------
    # LED INDICATOR - Simple LED with resistor
    # ----------------------------------------
    "led_indicator": SchematicPlan(
        project="led_indicator",
        description="Simple LED indicator with 330 ohm current limiting resistor",
        components=[
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="330",
                position=Position(x=127, y=80),
            ),
            ComponentPlacement(
                type="led",
                reference="D1",
                value="Red",
                position=Position(x=127, y=100),
                rotation=90,
            ),
        ],
        wires=[
            # VCC to R1 pin 1
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="R1", pin=1),
            ),
            # R1 pin 2 to LED anode (pin 2)
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="D1", pin=2),
            ),
            # LED cathode (pin 1) to GND
            WireConnection(
                **{"from": PinReference(component="D1", pin=1)},
                to=PinReference(component="GND", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="VCC", x=127, y=65),
            PowerLabel(name="GND", x=127, y=115),
        ],
        open_kicad=False,
    ),
    
    # ----------------------------------------
    # VOLTAGE DIVIDER - Basic voltage divider
    # ----------------------------------------
    "voltage_divider": SchematicPlan(
        project="voltage_divider",
        description="Basic voltage divider with two resistors",
        components=[
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="10k",
                position=Position(x=127, y=80),
            ),
            ComponentPlacement(
                type="resistor",
                reference="R2",
                value="10k",
                position=Position(x=127, y=105),
            ),
        ],
        wires=[
            # VCC to R1 pin 1
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="R1", pin=1),
            ),
            # R1 pin 2 to R2 pin 1 (VOUT node)
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="R2", pin=1),
            ),
            # R2 pin 2 to GND
            WireConnection(
                **{"from": PinReference(component="R2", pin=2)},
                to=PinReference(component="GND", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="VIN", x=127, y=65),
            PowerLabel(name="VOUT", x=140, y=92),
            PowerLabel(name="GND", x=127, y=120),
        ],
        open_kicad=False,
    ),
    
    # ----------------------------------------
    # ESP32 BASIC - ESP32 with power connections
    # ----------------------------------------
    "esp32_basic": SchematicPlan(
        project="esp32_basic",
        description="ESP32-WROOM-32 with power connections and decoupling caps",
        components=[
            ComponentPlacement(
                type="esp32",
                reference="U1",
                value="ESP32-WROOM-32",
                position=Position(x=127, y=100),
            ),
            ComponentPlacement(
                type="capacitor",
                reference="C1",
                value="100nF",
                position=Position(x=100, y=75),
            ),
            ComponentPlacement(
                type="capacitor_polarized",
                reference="C2",
                value="10uF",
                position=Position(x=90, y=75),
            ),
        ],
        wires=[
            # VCC to C1
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="C1", pin=1),
            ),
            # VCC to C2
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="C2", pin=1),
            ),
            # VCC to ESP32 3V3 (pin 2)
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="U1", pin=2),
            ),
            # C1 to GND
            WireConnection(
                **{"from": PinReference(component="C1", pin=2)},
                to=PinReference(component="GND", pin=1),
            ),
            # C2 to GND
            WireConnection(
                **{"from": PinReference(component="C2", pin=2)},
                to=PinReference(component="GND", pin=1),
            ),
            # ESP32 GND (pin 1) to GND
            WireConnection(
                **{"from": PinReference(component="U1", pin=1)},
                to=PinReference(component="GND", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="+3V3", x=85, y=55),
            PowerLabel(name="GND", x=85, y=135),
        ],
        open_kicad=False,
    ),
    
    # ----------------------------------------
    # ARDUINO LED - Arduino with LED blink
    # ----------------------------------------
    "arduino_led": SchematicPlan(
        project="arduino_led",
        description="Arduino UNO with LED on pin 13",
        components=[
            ComponentPlacement(
                type="arduino_uno",
                reference="A1",
                value="Arduino UNO R3",
                position=Position(x=100, y=100),
            ),
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="220",
                position=Position(x=150, y=85),
            ),
            ComponentPlacement(
                type="led",
                reference="D1",
                value="Red",
                position=Position(x=175, y=85),
                rotation=0,  # Horizontal
            ),
        ],
        wires=[
            # Arduino D13 to R1
            WireConnection(
                **{"from": PinReference(component="A1", pin=13)},
                to=PinReference(component="R1", pin=1),
            ),
            # R1 to LED anode
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="D1", pin=2),
            ),
            # LED cathode to GND
            WireConnection(
                **{"from": PinReference(component="D1", pin=1)},
                to=PinReference(component="GND", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="GND", x=195, y=85),
        ],
        open_kicad=False,
    ),
    
    # ----------------------------------------
    # DHT11 SENSOR - Temperature/humidity sensor
    # ----------------------------------------
    "dht11_sensor": SchematicPlan(
        project="dht11_sensor",
        description="DHT11 temperature/humidity sensor with pull-up resistor",
        components=[
            ComponentPlacement(
                type="dht11",
                reference="U1",
                value="DHT11",
                position=Position(x=127, y=100),
            ),
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="10k",
                position=Position(x=100, y=85),
            ),
        ],
        wires=[
            # VCC to DHT11 VCC (pin 1)
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="U1", pin=1),
            ),
            # VCC to R1 (pull-up)
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="R1", pin=1),
            ),
            # R1 to DHT11 DATA (pin 2)
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="U1", pin=2),
            ),
            # DHT11 GND (pin 4) to GND
            WireConnection(
                **{"from": PinReference(component="U1", pin=4)},
                to=PinReference(component="GND", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="+5V", x=90, y=65),
            PowerLabel(name="GND", x=127, y=125),
            PowerLabel(name="DATA", x=145, y=100),
        ],
        open_kicad=False,
    ),
    
    # ----------------------------------------
    # NPN SWITCH - Basic NPN transistor switch
    # ----------------------------------------
    "npn_switch": SchematicPlan(
        project="npn_switch",
        description="NPN transistor switch for load control",
        components=[
            ComponentPlacement(
                type="npn",
                reference="Q1",
                value="BC547",
                position=Position(x=127, y=100),
            ),
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="1k",
                position=Position(x=100, y=100),
            ),
            ComponentPlacement(
                type="resistor",
                reference="R2",
                value="10k",
                position=Position(x=100, y=115),
            ),
        ],
        wires=[
            # Input to R1
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="R1", pin=1),
            ),
            # R1 to Base (Q1 pin 1)
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="Q1", pin=1),
            ),
            # Base to R2 (bias)
            WireConnection(
                **{"from": PinReference(component="Q1", pin=1)},
                to=PinReference(component="R2", pin=1),
            ),
            # R2 to GND
            WireConnection(
                **{"from": PinReference(component="R2", pin=2)},
                to=PinReference(component="GND", pin=1),
            ),
            # Emitter to GND
            WireConnection(
                **{"from": PinReference(component="Q1", pin=3)},
                to=PinReference(component="GND", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="CTRL", x=85, y=85),
            PowerLabel(name="LOAD", x=145, y=80),
            PowerLabel(name="GND", x=127, y=130),
        ],
        open_kicad=False,
    ),
    
    # ----------------------------------------
    # RELAY DRIVER - Relay with transistor driver
    # ----------------------------------------
    "relay_driver": SchematicPlan(
        project="relay_driver",
        description="Relay with NPN transistor driver and flyback diode",
        components=[
            ComponentPlacement(
                type="npn",
                reference="Q1",
                value="BC547",
                position=Position(x=127, y=110),
            ),
            ComponentPlacement(
                type="resistor",
                reference="R1",
                value="1k",
                position=Position(x=100, y=110),
            ),
            ComponentPlacement(
                type="relay_1ch",
                reference="K1",
                value="5V Relay",
                position=Position(x=160, y=90),
            ),
            ComponentPlacement(
                type="diode",
                reference="D1",
                value="1N4148",
                position=Position(x=145, y=80),
                rotation=90,
            ),
        ],
        wires=[
            # Control input to R1
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="R1", pin=1),
            ),
            # R1 to transistor base
            WireConnection(
                **{"from": PinReference(component="R1", pin=2)},
                to=PinReference(component="Q1", pin=1),
            ),
            # Transistor emitter to GND
            WireConnection(
                **{"from": PinReference(component="Q1", pin=3)},
                to=PinReference(component="GND", pin=1),
            ),
            # Transistor collector to relay coil
            WireConnection(
                **{"from": PinReference(component="Q1", pin=2)},
                to=PinReference(component="K1", pin=2),
            ),
            # VCC to relay VCC
            WireConnection(
                **{"from": PinReference(component="VCC", pin=1)},
                to=PinReference(component="K1", pin=1),
            ),
            # Flyback diode across coil
            WireConnection(
                **{"from": PinReference(component="K1", pin=1)},
                to=PinReference(component="D1", pin=2),
            ),
            WireConnection(
                **{"from": PinReference(component="K1", pin=2)},
                to=PinReference(component="D1", pin=1),
            ),
        ],
        labels=[
            PowerLabel(name="+5V", x=100, y=60),
            PowerLabel(name="CTRL", x=85, y=110),
            PowerLabel(name="GND", x=127, y=140),
        ],
        open_kicad=False,
    ),
}


# ============================================
# TEMPLATE ACCESS FUNCTIONS
# ============================================

def get_template(template_name: str) -> SchematicPlan | None:
    """Get template by name (case-insensitive)."""
    return TEMPLATES.get(template_name.lower())


def get_available_templates() -> list[str]:
    """Get list of available template names."""
    return list(TEMPLATES.keys())


def get_template_descriptions() -> dict[str, str]:
    """Get dict of template name -> description."""
    return {name: plan.description or "" for name, plan in TEMPLATES.items()}


def get_template_info_for_ai() -> str:
    """Get template information formatted for AI prompts."""
    lines = ["TEMPLATE TERSEDIA:"]
    
    for name, plan in TEMPLATES.items():
        comp_count = len(plan.components)
        comp_types = ", ".join(c.type for c in plan.components[:3])
        if len(plan.components) > 3:
            comp_types += ", ..."
        lines.append(f"- {name}: {plan.description} ({comp_count} komponen: {comp_types})")
    
    return "\n".join(lines)
