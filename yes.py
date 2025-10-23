import os
import sys
import time
import re
import pyautogui
import pygetwindow as gw
import keyboard
import speech_recognition as sr
from dotenv import load_dotenv
import google.generativeai as genai  # Gemini API client

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# ------------------ Config ------------------
SPOTIFY_APP_NAME = "Spotify"
SPOTIFY_SEARCH_BAR_COORDS = (887, 31)
SPOTIFY_TOP_SONG_COORDS = (996, 237)
BRAVE_APP_NAME = "Brave"
BRAVE_SEARCH_BAR_COORDS = (420, 72)
YOUTUBE_TOP_VIDEO_COORDS = (665, 360)
WHATSAPP_TOP_CONTACT_COORDS = (225, 243)

# ------------------ System Folders & Memory ------------------
SYSTEM_FOLDERS = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
    "videos": os.path.join(os.path.expanduser("~"), "Videos"),
    "music": os.path.join(os.path.expanduser("~"), "Music")
}

last_folder_path = None

# ------------------ Voice Input ------------------
def get_voice_input_continuous():
    r = sr.Recognizer()
    mic = sr.Microphone()
    print("Calibrating microphone...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=2)
    print("Listening continuously (say 'Friday')...")
    while True:
        if keyboard.is_pressed("esc"):
            return None
        try:
            with mic as source:
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                text = r.recognize_google(audio)
                if text.lower().strip().startswith("friday"):
                    return text
        except Exception:
            continue

def get_voice_input_button():
    r = sr.Recognizer()
    mic = sr.Microphone()
    max_retries = 3
    retries = 0
    while retries < max_retries:
        print("Hold SPACE to speak...")
        while True:
            time.sleep(0.01)
            if keyboard.is_pressed("esc"):
                return None
            if keyboard.is_pressed("space"):
                with mic as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio = r.listen(source, timeout=30, phrase_time_limit=10)
                    try:
                        text = r.recognize_google(audio)
                        return text
                    except Exception:
                        retries += 1
                        break

# ------------------ Gemini Helpers ------------------
def ask_gemini_for_command(command: str) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
You are a desktop assistant. Analyze this command and return JSON with:
{{ "action": "<open_app/play_song/open_website/open_folder/play_youtube/send_message/exit>", "target": "<app/song/URL/folder/video>", "message_app": "<whatsapp/discord>", "recipient": "<name>", "message": "<text>" }}
User command: {command}
"""
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        import json
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            return json.loads(text[json_start:json_end])
    except Exception as e:
        print(f"[Gemini Error] Could not interpret command: {e}")
    return {"action": "unknown", "raw_text": command}

def ask_gemini_for_url(command: str) -> str:
    model = genai.GenerativeModel("gemini-2.5-flash")
    url = ""
    try:
        prompt = f"Extract official website URL from: {command}. Respond only with JSON: {{'url': '<full URL>'}}"
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        import json
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            result = json.loads(text[json_start:json_end])
            url = result.get("url", "")
    except:
        pass

    if not url:
        try:
            explicit_prompt = f"Send only the full URL for the {command} website."
            resp = model.generate_content(explicit_prompt)
            url = resp.text.strip()
        except:
            url = ""

    url = url.strip().strip('"').strip("'")
    url = re.sub(r"\s+", "", url)
    url = url.rstrip(".")
    if url and not url.startswith("http"):
        url = "https://" + url
    return url

# ------------------ App / Folder / Brave / Spotify / YouTube / Messaging ------------------
def open_app_windows_search(app_name: str):
    windows = gw.getWindowsWithTitle(app_name)
    if windows:
        try:
            windows[0].activate()
            return
        except:
            pass
    pyautogui.hotkey('win')
    time.sleep(0.5)
    pyautogui.write(app_name)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)

def open_folder(folder_name: str):
    global last_folder_path
    folder_name_lower = folder_name.lower()
    if folder_name_lower in SYSTEM_FOLDERS:
        folder_path = SYSTEM_FOLDERS[folder_name_lower]
    elif last_folder_path:  # Subfolder of last opened folder
        folder_path = os.path.join(last_folder_path, folder_name)
    else:  # Fallback to Windows search
        pyautogui.hotkey('win')
        time.sleep(0.5)
        pyautogui.write(folder_name)
        pyautogui.press('enter')
        time.sleep(1)
        return

    if os.path.exists(folder_path):
        os.startfile(folder_path)
        last_folder_path = folder_path
        print(f"📂 Opened folder: {folder_path}")
    else:
        print(f"❌ Folder not found: {folder_path}")
        # fallback to Windows search
        pyautogui.hotkey('win')
        time.sleep(0.5)
        pyautogui.write(folder_name)
        pyautogui.press('enter')
        time.sleep(1)

def open_brave_website(url: str):
    # Check if Brave is already open
    windows = gw.getWindowsWithTitle(BRAVE_APP_NAME)
    if windows:
        # Activate the first Brave window and open a new tab
        try:
            windows[0].activate()
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 't')  # Open new tab
            time.sleep(0.5)
        except:
            # fallback if activation fails
            pyautogui.hotkey('win')
            time.sleep(0.5)
            pyautogui.write(BRAVE_APP_NAME)
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)
    else:
        # No Brave window, open via Windows search
        pyautogui.hotkey('win')
        time.sleep(0.5)
        pyautogui.write(BRAVE_APP_NAME)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2)
    
    # Click on the address bar and enter the URL
    pyautogui.click(*BRAVE_SEARCH_BAR_COORDS)
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    pyautogui.write(url, interval=0.02)
    pyautogui.press('enter')
    time.sleep(2)



def perform_spotify_search(query: str):
    try:
        spotify_windows = gw.getWindowsWithTitle(SPOTIFY_APP_NAME)
        if spotify_windows:
            spotify_windows[0].activate()
        time.sleep(1.5)
    except:
        pass

    # Press Ctrl+K to open Spotify search
    pyautogui.hotkey('ctrl', 'k')
    time.sleep(0.5)
    pyautogui.write(query, interval=0.05)
    time.sleep(1)  # Wait for search results to load
    pyautogui.hotkey('shift', 'enter')  # Play the first search result
    time.sleep(1)
    pyautogui.press('escape')  


def open_spotify_song(song_name: str):
    open_app_windows_search(SPOTIFY_APP_NAME)
    perform_spotify_search(song_name)

def open_youtube_video(video_query: str):
    open_brave_website("https://www.youtube.com")
    time.sleep(2)
    pyautogui.press('/')  # YouTube search bar
    time.sleep(0.5)
    pyautogui.write(video_query, interval=0.02)
    pyautogui.press('enter')
    time.sleep(2)
    pyautogui.click(*YOUTUBE_TOP_VIDEO_COORDS)
    time.sleep(1)

def send_whatsapp_message(recipient: str, message: str):
    open_app_windows_search("WhatsApp")
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'f')  # Search in WhatsApp
    time.sleep(0.5)
    pyautogui.write(recipient)
    time.sleep(1)
    pyautogui.click(*WHATSAPP_TOP_CONTACT_COORDS)
    time.sleep(0.5)
    pyautogui.write(message)
    pyautogui.press('enter')
    print(f"✅ Message sent to {recipient} on WhatsApp.")

def send_discord_message(recipient: str, message: str):
    open_app_windows_search("Discord")
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'k')  # Discord search shortcut
    time.sleep(0.5)
    pyautogui.write(recipient)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.write(message)
    pyautogui.press('enter')
    print(f"✅ Message sent to {recipient} on Discord.")

# ------------------ Fallbacks ------------------
def fallback_google_search(command: str):
    url = f"https://www.google.com/search?q={command.replace(' ', '+')}"
    open_brave_website(url)

def fallback_open_website(command: str):
    url = ask_gemini_for_url(command)
    if url:
        open_brave_website(url)
    else:
        fallback_google_search(command)

# ------------------ Command Execution ------------------
def execute_command(command: str):
    parsed = ask_gemini_for_command(command)
    action = parsed.get("action")
    target = parsed.get("target")
    message_app = parsed.get("message_app")
    recipient = parsed.get("recipient")
    message = parsed.get("message")

    if action == "open_app":
        open_app_windows_search(target)
    elif action == "play_song":
        open_spotify_song(target)
    elif action == "open_website":
        fallback_open_website(target)
    elif action == "open_folder":
        open_folder(target)
    elif action == "play_youtube":
        open_youtube_video(target)
    elif action == "send_message":
        if message_app.lower() == "whatsapp":
            send_whatsapp_message(recipient, message)
        elif message_app.lower() == "discord":
            send_discord_message(recipient, message)
        else:
            print("❌ Unknown messaging app. Cannot send message.")
    elif action == "exit":
        print("👋 Exiting FRIDAY...")
        sys.exit(0)
    else:
        print(f"❌ Unknown action. Gemini returned: {parsed}. Using fallback Google search.")
        fallback_google_search(command)

# ------------------ Main Loop ------------------
def main():
    print("="*60)
    print("🤖 FRIDAY - Voice Controlled Assistant (Gemini + PyAutoGUI + Messaging + Folder Memory)")
    print("="*60)
    print("Select Input Mode:\n1 - Continuous Voice\n2 - Button Voice\n3 - Typing")
    input_mode = None
    while True:
        choice = input("Choice (1/2/3): ").strip()
        if choice == "1":
            input_mode = "voice_continuous"
            break
        elif choice == "2":
            input_mode = "voice_button"
            break
        elif choice == "3":
            input_mode = "typing"
            break
    print("\nCommands examples: 'open downloads', 'open aiml-projects', 'play seed by aurora', 'message dhruv on whatsapp you are so cool', 'exit'\n")
    
    while True:
        try:
            if input_mode == "voice_continuous":
                cmd = get_voice_input_continuous()
                if not cmd:
                    continue
            elif input_mode == "voice_button":
                cmd = get_voice_input_button()
                if not cmd:
                    continue
            else:
                cmd = input("Command: ").strip()
            execute_command(cmd)
        except KeyboardInterrupt:
            print("\n⚠️ Exiting...")
            sys.exit(0)
        except Exception as e:
            print(f"[Error] {e}")

if __name__ == "__main__":
    main()
