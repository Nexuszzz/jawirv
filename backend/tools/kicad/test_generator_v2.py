"""
Test KiCad Generator V2 - Verifikasi output KiCad benar.
"""

import os
import sys

# Direct imports to avoid other dependencies
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from generator_v2 import SchematicGenerator, test_simple_circuit
from library_v2 import get_component, get_available_components, get_pin_position


def test_simple_led_circuit():
    """Test basic LED circuit generation."""
    print("=" * 60)
    print("TEST 1: Simple LED Circuit (VCC -> R -> LED -> GND)")
    print("=" * 60)
    
    gen = SchematicGenerator()
    
    # VCC at top
    vcc = gen.add_component("vcc", 127.0, 50.0)
    print(f"  Added VCC at (127, 50) - ref: {vcc.reference}")
    
    # Resistor
    r1 = gen.add_component("resistor", 127.0, 70.0, value="330")
    print(f"  Added Resistor at (127, 70) - ref: {r1.reference}")
    
    # LED (vertical = 90 degrees)
    led1 = gen.add_component("led", 127.0, 90.0, rotation=90, value="Red")
    print(f"  Added LED at (127, 90) - ref: {led1.reference}")
    
    # GND
    gnd = gen.add_component("gnd", 127.0, 110.0)
    print(f"  Added GND at (127, 110) - ref: {gnd.reference}")
    
    # Wiring
    wires = gen.add_wire_between_pins(vcc, 1, r1, 1)
    print(f"  Wire VCC pin 1 -> R1 pin 1: {len(wires)} segments")
    
    wires = gen.add_wire_between_pins(r1, 2, led1, 2)
    print(f"  Wire R1 pin 2 -> LED1 pin 2: {len(wires)} segments")
    
    wires = gen.add_wire_between_pins(led1, 1, gnd, 1)
    print(f"  Wire LED1 pin 1 -> GND pin 1: {len(wires)} segments")
    
    # Generate
    content = gen.generate()
    
    # Verify content
    assert "Device:R" in content, "Resistor symbol missing"
    assert "Device:LED" in content, "LED symbol missing"
    assert "power:VCC" in content, "VCC symbol missing"
    assert "power:GND" in content, "GND symbol missing"
    assert 'Reference" "R1"' in content, "R1 reference missing"
    assert 'Reference" "D1"' in content, "D1 reference missing"
    
    # Save to file for manual verification
    output_path = os.path.join(os.path.dirname(__file__), "test_output_simple.kicad_sch")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n  Output saved to: {output_path}")
    print("  ✓ TEST 1 PASSED\n")
    
    return True


def test_esp32_dht11_circuit():
    """Test ESP32 + DHT11 circuit."""
    print("=" * 60)
    print("TEST 2: ESP32 + DHT11 Circuit")
    print("=" * 60)
    
    gen = SchematicGenerator()
    
    # ESP32
    esp32 = gen.add_component("esp32", 150.0, 100.0)
    print(f"  Added ESP32 at (150, 100) - ref: {esp32.reference}")
    
    # DHT11
    dht11 = gen.add_component("dht11", 80.0, 80.0)
    print(f"  Added DHT11 at (80, 80) - ref: {dht11.reference}")
    
    # Check pin positions
    dht_vcc_pos = dht11.get_pin_position(1)
    dht_data_pos = dht11.get_pin_position(2)
    dht_gnd_pos = dht11.get_pin_position(4)
    
    print(f"  DHT11 pin positions:")
    print(f"    VCC (pin 1): {dht_vcc_pos}")
    print(f"    DATA (pin 2): {dht_data_pos}")
    print(f"    GND (pin 4): {dht_gnd_pos}")
    
    # ESP32 pin positions
    esp_3v3_pos = esp32.get_pin_position(2)  # 3V3
    esp_gnd_pos = esp32.get_pin_position(1)  # GND
    esp_io4_pos = esp32.get_pin_position(26)  # IO4
    
    print(f"  ESP32 pin positions:")
    print(f"    3V3 (pin 2): {esp_3v3_pos}")
    print(f"    GND (pin 1): {esp_gnd_pos}")
    print(f"    IO4 (pin 26): {esp_io4_pos}")
    
    # Connect DHT11 DATA to ESP32 IO4
    gen.add_wire_between_pins(dht11, 2, esp32, 26)
    
    # Generate
    content = gen.generate()
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), "test_output_esp32_dht11.kicad_sch")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n  Output saved to: {output_path}")
    print("  ✓ TEST 2 PASSED\n")
    
    return True


def test_esp32_full_circuit():
    """Test ESP32 + HC-SR04 + Rotary Encoder + DHT11."""
    print("=" * 60)
    print("TEST 3: ESP32 + HC-SR04 + Rotary Encoder + DHT11")
    print("=" * 60)
    
    gen = SchematicGenerator()
    
    # Layout: ESP32 in center, sensors around it
    esp_x, esp_y = 200.0, 120.0
    
    # ESP32
    esp32 = gen.add_component("esp32", esp_x, esp_y)
    print(f"  Added ESP32 at ({esp_x}, {esp_y}) - ref: {esp32.reference}")
    
    # DHT11 - to the left of ESP32
    dht11 = gen.add_component("dht11", esp_x - 80, esp_y - 20)
    print(f"  Added DHT11 - ref: {dht11.reference}")
    
    # HC-SR04 - above DHT11
    hcsr04 = gen.add_component("hcsr04", esp_x - 80, esp_y + 30)
    print(f"  Added HC-SR04 - ref: {hcsr04.reference}")
    
    # Rotary Encoder - to the left, below
    rotary = gen.add_component("rotary_encoder", esp_x - 80, esp_y + 80)
    print(f"  Added Rotary Encoder - ref: {rotary.reference}")
    
    # Power symbols
    vcc = gen.add_component("vcc", esp_x - 100, esp_y - 50)
    gnd = gen.add_component("gnd", esp_x - 100, esp_y + 120)
    
    # Connect DHT11 DATA to ESP32 IO4 (pin 26)
    gen.add_wire_between_pins(dht11, 2, esp32, 26)
    
    # Connect HC-SR04 TRIG to ESP32 IO5 (pin 29)
    gen.add_wire_between_pins(hcsr04, 2, esp32, 29)
    
    # Connect HC-SR04 ECHO to ESP32 IO18 (pin 30)
    gen.add_wire_between_pins(hcsr04, 3, esp32, 30)
    
    # Connect Rotary A to ESP32 IO19 (pin 31)
    gen.add_wire_between_pins(rotary, 1, esp32, 31)
    
    # Connect Rotary B to ESP32 IO21 (pin 33)
    gen.add_wire_between_pins(rotary, 3, esp32, 33)
    
    # Generate
    content = gen.generate()
    
    # Verify symbols present
    assert "RF_Module:ESP32-WROOM-32" in content, "ESP32 symbol missing"
    assert "Sensor:DHT11" in content, "DHT11 symbol missing"
    assert "Sensor_Proximity:HC-SR04" in content, "HC-SR04 symbol missing"
    assert "Device:RotaryEncoder_Switch" in content, "Rotary encoder symbol missing"
    
    # Verify references
    assert 'Reference" "U1"' in content, "U1 (ESP32) reference missing"
    assert 'Reference" "U2"' in content, "U2 (DHT11) reference missing"
    assert 'Reference" "U3"' in content, "U3 (HC-SR04) reference missing"
    assert 'Reference" "SW1"' in content, "SW1 (Rotary) reference missing"
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), "test_output_esp32_full.kicad_sch")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n  Output saved to: {output_path}")
    print("  ✓ TEST 3 PASSED\n")
    
    return True


def test_pin_positions():
    """Verify pin positions match symbol definitions."""
    print("=" * 60)
    print("TEST 4: Pin Position Verification")
    print("=" * 60)
    
    # Test resistor
    resistor = get_component("resistor")
    assert resistor is not None
    
    # Pin 1 should be at (0, -3.81) - top
    pos = get_pin_position(100, 100, resistor, 1, rotation=0)
    expected = (100, 100 - 3.81)
    assert abs(pos[0] - expected[0]) < 0.01, f"Resistor pin 1 X mismatch: {pos} vs {expected}"
    assert abs(pos[1] - expected[1]) < 0.01, f"Resistor pin 1 Y mismatch: {pos} vs {expected}"
    print(f"  Resistor pin 1 at center (100,100): {pos} ✓")
    
    # Pin 2 should be at (0, 3.81) - bottom
    pos = get_pin_position(100, 100, resistor, 2, rotation=0)
    expected = (100, 100 + 3.81)
    assert abs(pos[0] - expected[0]) < 0.01, f"Resistor pin 2 X mismatch"
    assert abs(pos[1] - expected[1]) < 0.01, f"Resistor pin 2 Y mismatch"
    print(f"  Resistor pin 2 at center (100,100): {pos} ✓")
    
    # Test LED with rotation
    led = get_component("led")
    
    # At rotation 0: pin 1 at left (-3.81, 0), pin 2 at right (3.81, 0)
    pos1 = get_pin_position(100, 100, led, 1, rotation=0)
    pos2 = get_pin_position(100, 100, led, 2, rotation=0)
    print(f"  LED rotation=0: pin1={pos1}, pin2={pos2}")
    
    # At rotation 90: pin 1 should rotate
    pos1_90 = get_pin_position(100, 100, led, 1, rotation=90)
    pos2_90 = get_pin_position(100, 100, led, 2, rotation=90)
    print(f"  LED rotation=90: pin1={pos1_90}, pin2={pos2_90}")
    
    # Test DHT11
    dht = get_component("dht11")
    pos1 = get_pin_position(100, 100, dht, 1, rotation=0)
    pos2 = get_pin_position(100, 100, dht, 2, rotation=0)
    print(f"  DHT11: VCC={pos1}, DATA={pos2}")
    
    # Expected: VCC at (-7.62, 2.54), DATA at (-7.62, 0)
    assert abs(pos1[0] - (100 - 7.62)) < 0.01, "DHT11 VCC X mismatch"
    assert abs(pos1[1] - (100 + 2.54)) < 0.01, "DHT11 VCC Y mismatch"
    
    print("  ✓ TEST 4 PASSED\n")
    return True


def test_available_components():
    """Test that all expected components are available."""
    print("=" * 60)
    print("TEST 5: Available Components")
    print("=" * 60)
    
    components = get_available_components()
    print(f"  Available: {components}")
    
    expected = [
        "resistor", "capacitor", "led", "dht11", "npn",
        "vcc", "gnd", "esp32", "conn_2pin", "conn_3pin", "conn_4pin",
        "hcsr04", "rotary_encoder", "button"
    ]
    
    for comp in expected:
        assert comp in components, f"Missing component: {comp}"
        print(f"    ✓ {comp}")
    
    print("  ✓ TEST 5 PASSED\n")
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  KICAD GENERATOR V2 - TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_available_components,
        test_pin_positions,
        test_simple_led_circuit,
        test_esp32_dht11_circuit,
        test_esp32_full_circuit,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"  RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
