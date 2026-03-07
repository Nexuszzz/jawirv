"""
Standalone test for KiCad Generator V2
Tests the core generator without external dependencies.
"""

import os
import sys

# Direct imports
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from generator_v2 import SchematicGenerator
from library_v2 import get_component, get_available_components


def test_esp32_hcsr04_rotary_dht11():
    """
    Generate the exact schematic user requested:
    ESP32 + HC-SR04 + Rotary Encoder + DHT11
    """
    print("=" * 60)
    print("  ESP32 + HC-SR04 + Rotary Encoder + DHT11")
    print("=" * 60)
    
    gen = SchematicGenerator()
    
    # Layout: ESP32 in center-right, sensors on left
    esp_x, esp_y = 200.0, 100.0
    
    # ESP32
    esp32 = gen.add_component("esp32", esp_x, esp_y)
    print(f"Added: ESP32 at ({esp_x}, {esp_y}) - ref: {esp32.reference}")
    
    # DHT11 - upper left
    dht11 = gen.add_component("dht11", 80, 60)
    print(f"Added: DHT11 at (80, 60) - ref: {dht11.reference}")
    
    # HC-SR04 - middle left
    hcsr04 = gen.add_component("hcsr04", 80, 100)
    print(f"Added: HC-SR04 at (80, 100) - ref: {hcsr04.reference}")
    
    # Rotary Encoder - lower left
    rotary = gen.add_component("rotary_encoder", 80, 150)
    print(f"Added: Rotary Encoder at (80, 150) - ref: {rotary.reference}")
    
    # Power symbols
    vcc = gen.add_component("vcc", 40, 50)
    gnd = gen.add_component("gnd", 40, 180)
    print(f"Added: VCC at (40, 50), GND at (40, 180)")
    
    # ===== WIRING =====
    print("\n--- Wiring ---")
    
    # DHT11 connections:
    # VCC (pin 1) -> ESP32 3V3 (pin 2)
    # DATA (pin 2) -> ESP32 IO4 (pin 26)
    # GND (pin 4) -> ESP32 GND (pin 1)
    gen.add_wire_between_pins(dht11, 1, esp32, 2)  # VCC->3V3
    gen.add_wire_between_pins(dht11, 2, esp32, 26)  # DATA->IO4
    gen.add_wire_between_pins(dht11, 4, esp32, 1)   # GND->GND
    print("  DHT11: VCC->3V3, DATA->IO4, GND->GND1")
    
    # HC-SR04 connections:
    # VCC (pin 1) -> VCC
    # TRIG (pin 2) -> ESP32 IO5 (pin 29)
    # ECHO (pin 3) -> ESP32 IO18 (pin 30)
    # GND (pin 4) -> GND
    gen.add_wire_between_pins(hcsr04, 1, vcc, 1)   # VCC
    gen.add_wire_between_pins(hcsr04, 2, esp32, 29) # TRIG->IO5
    gen.add_wire_between_pins(hcsr04, 3, esp32, 30) # ECHO->IO18
    gen.add_wire_between_pins(hcsr04, 4, gnd, 1)    # GND
    print("  HC-SR04: VCC->VCC, TRIG->IO5, ECHO->IO18, GND->GND")
    
    # Rotary Encoder connections:
    # A (pin 1) -> ESP32 IO19 (pin 31)
    # C/Common (pin 2) -> GND
    # B (pin 3) -> ESP32 IO21 (pin 33)
    # S1 (pin 4) -> ESP32 IO22 (pin 36)
    # S2 (pin 5) -> GND
    gen.add_wire_between_pins(rotary, 1, esp32, 31)  # A->IO19
    gen.add_wire_between_pins(rotary, 2, gnd, 1)     # C->GND
    gen.add_wire_between_pins(rotary, 3, esp32, 33)  # B->IO21
    gen.add_wire_between_pins(rotary, 4, esp32, 36)  # S1->IO22
    gen.add_wire_between_pins(rotary, 5, gnd, 1)     # S2->GND
    print("  Rotary: A->IO19, C->GND, B->IO21, S1->IO22, S2->GND")
    
    # Generate schematic
    content = gen.generate()
    
    # Verify components are in output
    checks = [
        ("ESP32 symbol", "RF_Module:ESP32-WROOM-32" in content),
        ("DHT11 symbol", "Sensor:DHT11" in content),
        ("HC-SR04 symbol", "Sensor_Proximity:HC-SR04" in content),
        ("Rotary encoder symbol", "Device:RotaryEncoder_Switch" in content),
        ("U1 reference", 'Reference" "U1"' in content),
        ("U2 reference", 'Reference" "U2"' in content),
        ("U3 reference", 'Reference" "U3"' in content),
        ("SW1 reference", 'Reference" "SW1"' in content),
        ("Wire segments", "(wire" in content),
        ("Symbol instances", "(symbol_instances" in content),
    ]
    
    print("\n--- Verification ---")
    all_pass = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if not passed:
            all_pass = False
    
    # Save to file
    output_path = os.path.join(current_dir, "test_esp32_sensor_hub.kicad_sch")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n📁 Saved to: {output_path}")
    
    # Also save to KiCad_Projects directory
    kicad_dir = "D:/sijawir/KiCad_Projects/esp32_sensor_hub_test"
    os.makedirs(kicad_dir, exist_ok=True)
    kicad_path = os.path.join(kicad_dir, "esp32_sensor_hub.kicad_sch")
    with open(kicad_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📁 Saved to: {kicad_path}")
    
    # Statistics
    print(f"\n📊 Components: {len(gen.components)}")
    print(f"🔌 Wires: {len(gen.wires)}")
    
    if all_pass:
        print("\n✅ TEST PASSED - Open in KiCad to verify visually!")
    else:
        print("\n❌ TEST FAILED - Some checks failed")
    
    return all_pass


def print_pin_positions():
    """Print actual pin positions for debugging."""
    print("\n" + "=" * 60)
    print("  PIN POSITIONS REFERENCE")
    print("=" * 60)
    
    gen = SchematicGenerator()
    
    # Add test components at origin for reference
    esp32 = gen.add_component("esp32", 0, 0)
    dht11 = gen.add_component("dht11", 0, 0)
    hcsr04 = gen.add_component("hcsr04", 0, 0)
    rotary = gen.add_component("rotary_encoder", 0, 0)
    
    components = [
        ("ESP32", esp32, [1, 2, 26, 29, 30, 31, 33, 36]),
        ("DHT11", dht11, [1, 2, 4]),
        ("HC-SR04", hcsr04, [1, 2, 3, 4]),
        ("Rotary Encoder", rotary, [1, 2, 3, 4, 5]),
    ]
    
    for name, comp, pins in components:
        print(f"\n{name} at (0,0):")
        for pin in pins:
            pos = comp.get_pin_position(pin)
            pin_def = next((p for p in comp.definition.pins if p.number == pin or str(p.number) == str(pin)), None)
            pin_name = pin_def.name if pin_def else "?"
            print(f"  Pin {pin} ({pin_name}): {pos}")


if __name__ == "__main__":
    print_pin_positions()
    print("\n")
    test_esp32_hcsr04_rotary_dht11()
