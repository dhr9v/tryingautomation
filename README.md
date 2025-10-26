# 🤖 FRIDAY - Voice Assistant

A Python-based voice assistant that uses speech recognition and automation to control desktop applications and perform web tasks. Based on Google's Gemini AI, PyAutoGUI, and speech recognition.

## Features

- Voice control with wake word "Friday" (continuous listening or push-to-talk)
- Text input mode for manual commands 
- Supports English and Hindi voice commands
- Text-to-speech feedback
- Automated controls for:
  - Spotify (search and play songs)
  - YouTube (search and play videos) 
  - WhatsApp (send messages)
  - Discord (send messages)
  - Brave Browser (open websites)
  - Windows Explorer (open folders)
  - Windows applications (launch apps)
- Smart handling of ambiguous commands (app vs website)
- Fallback to Google search for unknown commands

## Requirements

- Python 3.8+
- Google Gemini API key
- Dependencies in requirements.txt:
  - python-dotenv
  - google-generativeai 
  - pyautogui
  - pygetwindow
  - keyboard
  - SpeechRecognition
  - pyttsx3

## Setup

1. Clone the repository
2. Create a `.env` file with your Gemini API key:
3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 🎤 Voice Input System

The system supports two main voice modes:

#### 1. Continuous Voice Listening (`get_voice_input_continuous`)
* **Process:** The microphone listens constantly.
* **Trigger:** The user must start their command with the **wake word** ("Friday" or "फ्राईडे").
* **Mechanism:**
    1. Calibrates for ambient noise.
    2. Listens for audio chunks.
    3. Transcribes audio using `r.recognize_google(language="hi-IN,en-US")`.
    4. If a wake word is detected, the rest of the sentence is processed as the command.

#### 2. Push-to-Talk (`get_voice_input_button`)
* **Process:** The microphone only records while the **SPACE bar** is held down.
* **Trigger:** User presses and holds `SPACE`.
* **Mechanism:**
    1. Waits for the `SPACE` key press.
    2. Records until `SPACE` is released.
    3. Transcribes the recorded audio.

---

### Running and Example Execution

#### Setup Steps (Prerequisite)

1.  Install dependencies: `pip install -r requirements.txt`
2.  Create `.env` with: `GEMINI_API_KEY="YOUR_API_KEY_HERE"`
3.  (Crucial) Determine your microphone index and update `device_index= ` in the script.



