"""
Debug script untuk test Spotify play
"""
import subprocess
import time

try:
    import pyautogui
    import pyperclip
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("pyautogui not available!")

def test_spotify_play():
    if not PYAUTOGUI_AVAILABLE:
        return
    
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.1
    
    print("=== DEBUG SPOTIFY PLAY ===")
    print("Starting in 3 seconds... Watch Spotify window!")
    time.sleep(3)
    
    # 1. Bring Spotify to foreground using PowerShell
    print("Step 1: Focusing Spotify window...")
    ps_cmd = '(New-Object -ComObject WScript.Shell).AppActivate("Spotify")'
    result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True)
    print(f"  AppActivate result: returncode={result.returncode}")
    time.sleep(1)
    
    # 2. Try Ctrl+L to focus search bar
    print("Step 2: Pressing Ctrl+L to focus search...")
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.5)
    
    # 3. Clear existing text
    print("Step 3: Clearing search bar (Ctrl+A)...")
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.2)
    
    # 4. Type/Paste the query
    query = "stairway to heaven led zeppelin"
    print(f"Step 4: Typing query: '{query}'")
    pyperclip.copy(query)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    
    # 5. Press Enter to search
    print("Step 5: Pressing Enter to search...")
    pyautogui.press('enter')
    print("  Waiting 3 seconds for search results...")
    time.sleep(3)
    
    # 6. Re-focus Spotify (it might lose focus)
    print("Step 6: Re-focusing Spotify...")
    subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)
    time.sleep(0.5)
    
    # 7. Try different navigation strategies
    print("Step 7: Trying navigation strategy...")
    
    # Strategy A: Tab to first song section, then Enter
    print("  7a: Tab x3 then Enter...")
    for _ in range(3):
        pyautogui.press('tab')
        time.sleep(0.1)
    pyautogui.press('enter')
    time.sleep(1)
    
    print("\n=== TEST COMPLETE ===")
    print("Is music playing? (y/n)")

def test_spotify_uri_play():
    """Test direct URI play method"""
    print("\n=== TEST SPOTIFY URI METHOD ===")
    
    # Method: Use spotify:search: URI then keyboard
    query = "stairway to heaven"
    import urllib.parse
    encoded = urllib.parse.quote(query)
    uri = f"spotify:search:{encoded}"
    
    print(f"Opening URI: {uri}")
    subprocess.Popen(["start", uri], shell=True)
    time.sleep(3)
    
    if PYAUTOGUI_AVAILABLE:
        pyautogui.FAILSAFE = False
        
        # Focus and play
        ps_cmd = '(New-Object -ComObject WScript.Shell).AppActivate("Spotify")'
        subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)
        time.sleep(0.5)
        
        print("Pressing Tab and Enter to play first result...")
        for _ in range(2):
            pyautogui.press('tab')
            time.sleep(0.1)
        pyautogui.press('enter')
    
    print("=== URI TEST COMPLETE ===")

if __name__ == "__main__":
    print("Choose test:")
    print("1. Ctrl+L search method")
    print("2. URI method")
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "1":
        test_spotify_play()
    elif choice == "2":
        test_spotify_uri_play()
    else:
        print("Running both...")
        test_spotify_play()
        time.sleep(2)
        test_spotify_uri_play()
