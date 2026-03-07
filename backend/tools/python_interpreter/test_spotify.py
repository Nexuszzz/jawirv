"""
Test Spotify Play - Evaluasi Sistematis
"""
import subprocess
import time
import urllib.parse

print("=== TEST: Spotify Search URI + Space to Play ===")
print()

# Step 1: Open Spotify with search URI
query = "bohemian rhapsody queen"
encoded = urllib.parse.quote(query)
uri = f"spotify:search:{encoded}"
print(f"1. Opening Spotify search: {uri}")
subprocess.Popen(["start", uri], shell=True)

# Step 2: Wait for search results to load
print("2. Waiting 3 seconds for search results...")
time.sleep(3)

# Step 3: Focus Spotify window
print("3. Focusing Spotify window...")
result = subprocess.run(
    ["powershell", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('Spotify')"],
    capture_output=True
)
time.sleep(0.5)

# Step 4: Press Space to play
print("4. Pressing SPACE to play...")
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.press("space")
    print("   Space pressed!")
except Exception as e:
    print(f"   Error: {e}")

print()
print("Done! Check if music is playing.")
