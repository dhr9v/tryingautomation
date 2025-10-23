import os
import time
import pyautogui
import webbrowser
import platform

PLAYLIST_NAME = "seedhe maut"
BRAVE_APP_NAME = "Brave"
DISCORD_APP_NAME = "Discord"
SPOTIFY_APP_NAME = "Spotify"
VSCODE_APP_NAME = "Visual Studio Code"
WHATSAPP_APP_NAME = "WhatsApp"

SPOTIFY_SEARCH_BAR_COORDS = (887, 31)
PLAYLIST_COORDS = (909, 398)

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

def open_application(app_name: str, wait_time: int = 3) -> bool:
    print(f"\n[INFO] Attempting to open application: '{app_name}'...")
    if platform.system() == "Windows":
        pyautogui.press('win')
    elif platform.system() == "Darwin":
        pyautogui.hotkey('command', 'space')
    else:
        pyautogui.press('super')
    time.sleep(1)
    pyautogui.write(app_name, interval=0.05)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(wait_time)
    try:
        app_windows = pyautogui.getWindowsWithTitle(app_name)
        if app_windows:
            app_windows[0].maximize()
            app_windows[0].activate()
        time.sleep(0.5)
    except Exception:
        pass
    return True

def spotify_play_playlist(playlist_name: str):
    print(f"\n[INFO] Starting Spotify automation for playlist: '{playlist_name}'")
    open_application(SPOTIFY_APP_NAME, wait_time=2)
    time.sleep(2)
    search_x, search_y = SPOTIFY_SEARCH_BAR_COORDS
    print("[ACTION] Clicking the top search bar at (887, 31)...")
    pyautogui.moveTo(search_x, search_y, duration=0.2)
    pyautogui.doubleClick()
    time.sleep(0.5)
    print(f"[ACTION] Searching for playlist: '{playlist_name}'...")
    pyautogui.write(playlist_name, interval=0.1)
    time.sleep(1.5)
    pyautogui.press('enter')
    time.sleep(1)
    playlist_x, playlist_y = PLAYLIST_COORDS
    print("[ACTION] Clicking on the playlist result at (909, 398) to start playing.")
    pyautogui.moveTo(playlist_x, playlist_y, duration=0.2)
    pyautogui.click()
    time.sleep(1)
    print("[ACTION] Minimizing all windows (Win + D).")
    if platform.system() == "Windows":
        pyautogui.hotkey('win', 'd')
    elif platform.system() == "Darwin":
        pyautogui.hotkey('fn', 'f11')
    print(f"[SUCCESS] Automation complete. '{playlist_name}' should now be playing and desktop is shown.")

def open_browser(app_name: str):
    print(f"\n[INFO] Opening {app_name}")
    open_application(app_name, wait_time=2)
    print(f"[SUCCESS] {app_name} is open.")

def start_my_day_automation():
    print("\n" + "="*50)
    print("        🚀 DAILY STARTUP AUTOMATION SCRIPT 🚀")
    print("="*50)
    open_browser(BRAVE_APP_NAME)
    open_application(DISCORD_APP_NAME)
    open_application(VSCODE_APP_NAME)
    open_application(WHATSAPP_APP_NAME)
    spotify_play_playlist(PLAYLIST_NAME)
    print("\n" + "="*50)
    print("        ✅ ALL DAILY APPS LAUNCHED AND READY ✅")
    print("="*50)

if __name__ == "__main__":
    try:
        start_my_day_automation()
    except pyautogui.FailSafeException:
        print("\n\n[FAILSAFE] Operation cancelled by user. Move mouse to any corner to stop PyAutoGUI.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Automation failed: {e}")
