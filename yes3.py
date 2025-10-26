import os
import sys
import time
import re
import pyautogui
import pygetwindow as gw
import keyboard
import speech_recognition as sr
import pyttsx3
from dotenv import load_dotenv
import google.generativeai as genai  # Gemini API client
import json

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# ------------------ Config ------------------
SPOTIFY_APP_NAME = "Spotify"
BRAVE_APP_NAME = "Brave"
BRAVE_SEARCH_BAR_COORDS = (420, 72)
YOUTUBE_TOP_VIDEO_COORDS = (665, 360)

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

# ------------------ Text-to-Speech ------------------
engine = pyttsx3.init()
def speak(text):
    print(f"🤖 {text}")
    engine.say(text)
    engine.runAndWait()

# ------------------ Voice Input ------------------
def get_voice_input_continuous():
    r = sr.Recognizer()
    mic = sr.Microphone(device_index=2)
    speak("Calibrating microphone...")
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=2)
    speak("Listening continuously! Say 'Friday' to give a command. Press ESC to stop.")

    while True:
        if keyboard.is_pressed("esc"):
            speak("Stopping continuous listening.")
            return None
        try:
            with mic as source:
                audio = r.listen(source)
                text = r.recognize_google(audio)
                print(f"📢 Heard: {text}")

                # Check for wake word "Friday"
                if text.lower().strip().startswith("friday"):
                    # Remove "Friday" from the start
                    command_text = text.lower().replace("friday", "", 1).strip()
                    if command_text == "":
                        speak("Yes? What should I do?")
                        audio = r.listen(source)
                        command_text = r.recognize_google(audio)
                        print(f"📢 Command after wake word: {command_text}")
                    return command_text

        except sr.UnknownValueError:
            continue  # couldn't understand, keep listening
        except sr.RequestError as e:
            speak(f"Recognition error: {e}")
            time.sleep(1)
        except Exception as e:
            speak(f"Error: {e}")
            time.sleep(1)


def get_voice_input_button():
    r = sr.Recognizer()
    mic = sr.Microphone(device_index=2)
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        speak("Hold SPACE to speak... release to stop.")
        while True:
            time.sleep(0.01)
            if keyboard.is_pressed("esc"):
                speak("Cancelled.")
                return None
            if keyboard.is_pressed("space"):
                with mic as source:
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    try:
                        audio = r.listen(source, timeout=30, phrase_time_limit=10)
                        text = r.recognize_google(audio)
                        speak(f"You said: {text}")
                        return text
                    except sr.WaitTimeoutError:
                        speak("No speech detected.")
                        retry_count += 1
                        break
                    except sr.UnknownValueError:
                        speak("Could not understand. Try again.")
                        retry_count += 1
                        break
                    except sr.RequestError as e:
                        speak(f"Recognition service error: {e}")
                        return None
                    finally:
                        while keyboard.is_pressed("space"):
                            time.sleep(0.01)
    speak(f"Failed after {max_retries} attempts.")
    return None

# ------------------ Gemini Helpers ------------------
def ask_gemini_for_command(command: str) -> dict:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
You are a desktop assistant. Analyze this command and return JSON with:
{{ "action": "<open_app/play_song/open_website/open_folder/play_youtube/send_message/exit>", 
   "target": "<app/song/URL/folder/video>", 
   "message_app": "<whatsapp/discord>", 
   "recipient": "<name>", 
   "message": "<text>" }}
User command: {command}
"""
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            return json.loads(text[json_start:json_end])
    except:
        pass
    return {"action": None, "target": None, "message_app": None, "recipient": None, "message": None}

def ask_gemini_for_url(command: str) -> str:
    model = genai.GenerativeModel("gemini-2.5-flash")
    url = ""
    try:
        prompt = f"Extract official website URL from: {command}. Respond only with JSON: {{'url': '<full URL>'}}"
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start != -1 and json_end != -1:
            result = json.loads(text[json_start:json_end])
            url = result.get("url", "")
    except:
        pass
    if not url:
        url = command.strip().replace(" ", "")
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
    folder_path = SYSTEM_FOLDERS.get(folder_name_lower, None)
    if folder_path and os.path.exists(folder_path):
        os.startfile(folder_path)
        last_folder_path = folder_path
        speak(f"Opened folder: {folder_path}")
    else:
        pyautogui.hotkey('win')
        time.sleep(0.5)
        pyautogui.write(folder_name)
        pyautogui.press('enter')
        time.sleep(1)

def open_brave_website(url: str):
    windows = gw.getWindowsWithTitle(BRAVE_APP_NAME)
    if windows:
        try:
            windows[0].activate()
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.5)
        except:
            pass
    else:
        pyautogui.hotkey('win')
        time.sleep(0.5)
        pyautogui.write(BRAVE_APP_NAME)
        pyautogui.press('enter')
        time.sleep(2)
    pyautogui.click(*BRAVE_SEARCH_BAR_COORDS)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    pyautogui.write(url, interval=0.02)
    pyautogui.press('space')
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
    pyautogui.hotkey('ctrl', 'k')
    time.sleep(0.5)
    pyautogui.write(query, interval=0.05)
    time.sleep(1)
    pyautogui.hotkey('shift', 'enter')
    time.sleep(3)
    pyautogui.press('escape')

def open_spotify_song(song_name: str):
    open_app_windows_search(SPOTIFY_APP_NAME)
    perform_spotify_search(song_name)

def open_youtube_video(video_query: str):
    open_brave_website("https://www.youtube.com")
    time.sleep(2)
    pyautogui.press('/')
    time.sleep(0.5)
    pyautogui.write(video_query, interval=0.02)
    pyautogui.press('enter')
    time.sleep(2)
    pyautogui.click(*YOUTUBE_TOP_VIDEO_COORDS)
    time.sleep(1)

def send_whatsapp_message(recipient: str, message: str):
    open_app_windows_search("WhatsApp")
    time.sleep(2)
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)
    pyautogui.write(recipient)
    time.sleep(1)
    pyautogui.press('down')
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.write(message)
    pyautogui.press('enter')
    speak(f"Message sent to {recipient} on WhatsApp.")

def send_discord_message(recipient: str, message: str):
    open_app_windows_search("Discord")
    time.sleep(5)
    pyautogui.hotkey('ctrl', 'k')
    time.sleep(0.5)
    pyautogui.write(recipient)
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.write(message)
    pyautogui.press('enter')
    speak(f"Message sent to {recipient} on Discord.")

# ------------------ Helpers ------------------
def parse_message_command(command):
    command_lower = command.lower()
    if "whatsapp" in command_lower:
        message_app = "whatsapp"
    elif "discord" in command_lower:
        message_app = "discord"
    else:
        return None, None, None
    try:
        if " on " in command_lower:
            parts = command_lower.split(" on ")
            recipient_part = parts[0].replace("message", "").strip()
            app_and_message = parts[1].strip()
            message_text = re.sub(rf"{message_app}", "", app_and_message, flags=re.IGNORECASE).strip()
            return message_app, recipient_part, message_text
    except:
        pass
    return message_app, None, None

def determine_app_or_website(command, gemini_response, mode="voice_continuous"):
    cmd_lower = command.lower()
    
    # If user explicitly said website or app
    if "website" in cmd_lower:
        speak("Detected: website")
        return "website"
    if "app" in cmd_lower:
        speak("Detected: app")
        return "app"

    # Skip for Spotify, YouTube, Messaging, Folders
    action = (gemini_response.get("action") or "").lower()
    if action in ["play_song", "play_youtube", "send_message", "open_folder"]:
        return None

    # Ask user if ambiguous
    if mode in ["voice_continuous", "voice_button"]:
        speak("Do you want the app or the website?")
        time.sleep(0.5)  # allow TTS to finish before listening
        r = sr.Recognizer()
        mic = sr.Microphone(device_index=2)
        try:
            with mic as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=8, phrase_time_limit=5)
            answer = r.recognize_google(audio).lower()
            if "app" in answer:
                speak("You chose app")
                return "app"
            elif "website" in answer:
                speak("You chose website")
                return "website"
        except sr.WaitTimeoutError:
            speak("No response detected. Skipping app/website selection.")
            return None
        except sr.UnknownValueError:
            speak("Could not understand. Skipping selection.")
            return None
        except sr.RequestError as e:
            speak(f"Recognition service error: {e}")
            return None
        except Exception as e:
            speak(f"Error: {e}")
            return None
    elif mode == "typing":
        answer = input("Do you want app or website? ").lower()
        if "app" in answer:
            speak("You chose app")
            return "app"
        elif "website" in answer:
            speak("You chose website")
            return "website"
    return None

# ------------------ Main Command Execution ------------------
def execute_command(command: str, mode="voice_continuous"):
    if not command:
        return

    gemini_response = ask_gemini_for_command(command)
    action = (gemini_response.get("action") or "").lower()
    target = gemini_response.get("target") or ""
    message_app = (gemini_response.get("message_app") or "")
    recipient = (gemini_response.get("recipient") or "")
    message = (gemini_response.get("message") or "")

    if action == "send_message" and (not message_app or not recipient or not message):
        msg_app_manual, recipient_manual, message_manual = parse_message_command(command)
        if msg_app_manual:
            message_app = msg_app_manual
            recipient = recipient_manual
            message = message_manual

    app_or_website = determine_app_or_website(command, gemini_response, mode)

    # -------- Spotify --------
    if action == "play_song":
        speak(f"Playing song on Spotify: {target}")
        open_spotify_song(target)
        return

    # -------- YouTube --------
    if action == "play_youtube":
        speak(f"Playing video on YouTube: {target}")
        open_youtube_video(target)
        return

    # -------- Messaging --------
    if action == "send_message":
        if message_app.lower() == "whatsapp":
            send_whatsapp_message(recipient, message)
        elif message_app.lower() == "discord":
            send_discord_message(recipient, message)
        else:
            speak(f"Unknown messaging app: {message_app}")
        return

    # -------- Folders --------
    if action == "open_folder":
        open_folder(target)
        return

    # -------- Normal app or website (ambiguous) --------
    if app_or_website == "app":
        speak(f"Opening app: {target}")
        open_app_windows_search(target)
        return
    elif app_or_website == "website":
        url = ask_gemini_for_url(target) or target
        speak(f"Opening website: {url}")
        open_brave_website(url)
        return

    # -------- Exit --------
    if action == "exit":
        speak("Goodbye!")
        sys.exit(0)

    # -------- Fallback --------
    speak(f"Could not process command: {command}. Searching on Google.")
    open_brave_website(f"https://www.google.com/search?q={command.replace(' ','+')}")

# ------------------ Main Loop ------------------
# ------------------ Main Loop ------------------
if __name__ == "__main__":
    speak("Friday assistant ready!")

    # -------- Mode Selection --------
    print("Select input mode:")
    print("1. Continuous voice (say 'Friday' to give commands)")
    print("2. Push-to-talk voice (hold SPACE to speak)")
    print("3. Typing input")
    mode_choice = input("Enter 1, 2, or 3: ").strip()
    if mode_choice == "1":
        mode = "voice_continuous"
    elif mode_choice == "2":
        mode = "voice_button"
    else:
        mode = "typing"
    speak(f"Mode selected: {mode.replace('_',' ')}")

    # -------- Main loop --------
    while True:
        try:
            if mode == "typing":
                command = input("Command: ")
            elif mode == "voice_continuous":
                command = get_voice_input_continuous()
            elif mode == "voice_button":
                command = get_voice_input_button()

            if not command or command.strip() == "":
                speak("I didn’t catch that, please try again.")
                continue  # keeps listening instead of stopping

            execute_command(command, mode=mode)

        except KeyboardInterrupt:
            speak("Stopping assistant. Goodbye!")
            sys.exit(0)
        except Exception as e:
            speak(f"An error occurred: {e}")
            time.sleep(1)
