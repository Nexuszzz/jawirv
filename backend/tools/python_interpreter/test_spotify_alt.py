"""
Alternative Spotify play method using pywinauto
"""
import subprocess
import time
import urllib.parse

def play_with_pywinauto(query):
    """Use pywinauto for more reliable window control"""
    try:
        from pywinauto import Application, Desktop
        from pywinauto.keyboard import send_keys
        
        print(f"=== PYWINAUTO METHOD ===")
        print(f"Query: {query}")
        
        # Open Spotify search via URI
        encoded = urllib.parse.quote(query)
        uri = f"spotify:search:{encoded}"
        print(f"Opening URI: {uri}")
        subprocess.Popen(["start", uri], shell=True)
        time.sleep(3)
        
        # Connect to Spotify
        try:
            app = Application(backend="uia").connect(title_re=".*Spotify.*", timeout=5)
            print("Connected to Spotify!")
            
            # Get main window
            main_window = app.window(title_re=".*Spotify.*")
            main_window.set_focus()
            time.sleep(0.5)
            
            # Send keys to navigate and play
            print("Sending Tab keys...")
            send_keys("{TAB}{TAB}{TAB}")
            time.sleep(0.3)
            
            print("Sending Enter to play...")
            send_keys("{ENTER}")
            
            print("Success!")
            return True
            
        except Exception as e:
            print(f"pywinauto error: {e}")
            return False
            
    except ImportError:
        print("pywinauto not installed!")
        return False

def play_with_keyboard_direct(query):
    """Direct keyboard method using SendInput"""
    import ctypes
    from ctypes import wintypes
    
    print(f"=== DIRECT KEYBOARD METHOD ===")
    print(f"Query: {query}")
    
    # Open Spotify search via URI
    encoded = urllib.parse.quote(query)
    uri = f"spotify:search:{encoded}"
    subprocess.Popen(["start", uri], shell=True)
    time.sleep(3)
    
    # Focus Spotify window
    user32 = ctypes.windll.user32
    
    # Find Spotify window
    def find_spotify_window():
        result = []
        def callback(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    if "Spotify" in buff.value:
                        result.append(hwnd)
            return True
        
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(WNDENUMPROC(callback), 0)
        return result[0] if result else None
    
    hwnd = find_spotify_window()
    if hwnd:
        print(f"Found Spotify window: {hwnd}")
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Send Tab and Enter using SendInput
        INPUT_KEYBOARD = 1
        KEYEVENTF_KEYUP = 0x0002
        
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
            ]
        
        class INPUT(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("ki", KEYBDINPUT)]
        
        def send_key(vk_code):
            inp = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=vk_code))
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            time.sleep(0.05)
            inp.ki.dwFlags = KEYEVENTF_KEYUP
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
            time.sleep(0.1)
        
        VK_TAB = 0x09
        VK_RETURN = 0x0D
        VK_DOWN = 0x28
        
        print("Sending Tab keys...")
        for _ in range(3):
            send_key(VK_TAB)
        
        print("Sending Down arrow...")
        send_key(VK_DOWN)
        
        print("Sending Enter...")
        send_key(VK_RETURN)
        
        return True
    else:
        print("Spotify window not found!")
        return False

if __name__ == "__main__":
    query = "stairway to heaven"
    
    print("Testing pywinauto method...")
    result1 = play_with_pywinauto(query)
    
    if not result1:
        print("\nTrying direct keyboard method...")
        play_with_keyboard_direct(query)
