import os
from dotenv import load_dotenv
import pyautogui
import time
import sys
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 🚨 CRITICAL CHANGE: Call load_dotenv() immediately
load_dotenv() 

# --- Configuration ---
# Coordinates for actions *inside* Spotify (assuming it opens maximized/fixed)
SEARCH_BAR_COORDS = (887, 31)
TOP_SONG_COORDS = (996, 237) 
LIKED_SONGS_PLAYLIST_COORDS = (909, 398)
APP_NAME = "Spotify" # Application name to type in Windows Search

# Gemini Configuration
MODEL_NAME = 'gemini-2.5-flash' 

# PyAutoGUI Setup
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True 

# --- PyAutoGUI Helper Functions (Tools for Gemini) ---

def open_application(app_name: str) -> bool:
    """Opens an application using the Windows Start Menu/Search."""
    print(f"\n[AGENT] Opening application: '{app_name}'")
    
    # 1. Open Windows/Start Search Menu (Win Key)
    pyautogui.press('win')
    time.sleep(1) # Give time for the start menu to appear

    # 2. Type the application name
    pyautogui.write(app_name, interval=0.05)
    time.sleep(1) # Give time for search results to appear

    # 3. Press Enter to launch the top result
    pyautogui.press('enter')
    time.sleep(4) # **CRITICAL** Wait longer for Spotify to fully launch and load
    
    # Optional: Try to maximize the window after launch for consistent coordinates
    try:
        spotify_windows = pyautogui.getWindowsWithTitle(APP_NAME)
        if spotify_windows:
            spotify_windows[0].maximize()
        time.sleep(1)
    except Exception as e:
        print(f"[ERROR] Could not maximize Spotify window after launch: {e}")
        # The script will proceed even if maximizing fails
        
    return True # We assume launch was successful

def perform_search(query: str, search_coords: tuple):
    """Activates Spotify, clicks the search bar, and types the internal query."""
    print(f"[AGENT] Performing Spotify internal search for: '{query}'")
    
    # 1. Activate Spotify Window (Use the window handle as before, or re-open)
    # Since we now ensure it's open, just try to activate it for safety
    try:
        spotify_windows = pyautogui.getWindowsWithTitle(APP_NAME)
        if spotify_windows:
            spotify_windows[0].activate()
        time.sleep(1.5) 
    except Exception as e:
        print(f"[ERROR] Could not activate Spotify window. {e}")
        return False

    # 2. Click the Search Bar
    search_x, search_y = search_coords
    pyautogui.moveTo(search_x, search_y, duration=0.1)
    pyautogui.click() 
    time.sleep(0.5)

    # 3. Clear text and type
    if sys.platform.startswith('win'):
        pyautogui.hotkey('ctrl', 'a')
    elif sys.platform.startswith('darwin'):
        pyautogui.hotkey('command', 'a')
    pyautogui.press('delete')
    time.sleep(0.2)
    pyautogui.write(query, interval=0.05)
    time.sleep(1.5) # Wait for search results to load
    return True


# --- Tool Functions (Modified to include opening the app first) ---

def play_song(song_name: str) -> str:
    """
    Launches Spotify, searches for a song, and clicks the top song coordinate to start playback.

    Args:
        song_name: The name of the song to search for (e.g., 'Bohemian Rhapsody').

    Returns:
        A success message indicating the song is playing.
    """
    # 🌟 NEW STEP: Launch Spotify first
    open_application(APP_NAME)

    # Perform the internal search
    if not perform_search(song_name, SEARCH_BAR_COORDS):
        return "Spotify not responsive."

    # Click the Top Song Result
    song_x, song_y = TOP_SONG_COORDS
    pyautogui.moveTo(song_x, song_y, duration=0.1)
    pyautogui.click() 
    time.sleep(1)

    return f"Successfully launched Spotify and clicked the top result for '{song_name}'. Playback should start now."


def open_playlist(playlist_name: str) -> str:
    """
    Launches Spotify, searches for a playlist, and clicks the designated playlist coordinate.

    Args:
        playlist_name: The name of the playlist to search for (e.g., 'Liked Songs').

    Returns:
        A success message indicating the playlist has been opened.
    """
    # 🌟 NEW STEP: Launch Spotify first
    open_application(APP_NAME)
    
    # Perform the internal search
    if not perform_search(playlist_name, SEARCH_BAR_COORDS):
        return "Spotify not responsive."
        
    # Press Enter to finalize the search/filter for the playlist
    pyautogui.press('enter')
    time.sleep(1.5)

    # Click the Playlist Coordinate
    playlist_x, playlist_y = LIKED_SONGS_PLAYLIST_COORDS
    pyautogui.moveTo(playlist_x, playlist_y, duration=0.1)
    pyautogui.click()
    time.sleep(1)
    
    return f"Successfully launched Spotify and navigated to the playlist '{playlist_name}'."

# --- Gemini Agent Logic (Remains the same as the corrected version) ---

def run_spotify_agent():
    """Main loop for the text-based Gemini Agent."""

    # Check for API Key
    if 'GEMINI_API_KEY' not in os.environ:
        print("ERROR: The GEMINI_API_KEY environment variable is not set.")
        print("Please ensure your .env file is present and has the key, and you've run 'pip install python-dotenv'.")
        sys.exit(1)

    # 1. Initialize Gemini Client
    client = genai.Client()
    
    # Define the functions as tools
    tools = [play_song, open_playlist]

    print("-" * 50)
    print("✨ Spotify Voice Agent Activated (Text Commands) ✨")
    print(f"Using Model: {MODEL_NAME}")
    print(f"Available commands: 'Play [song name]' or 'Open [playlist name]'")
    print("Type 'quit' to exit.")
    print("-" * 50)

    while True:
        user_prompt = input("You: ")
        if user_prompt.lower() == 'quit':
            print("Agent shutting down. Goodbye!")
            break

        try:
            # 2. Call the Model with the User's Prompt and Tools
            response = client.models.generate_content(
                model=MODEL_NAME, 
                contents=[user_prompt],
                config=types.GenerateContentConfig(
                    tools=tools
                )
            )

            # 3. Check for a Function Call
            if response.function_calls:
                for function_call in response.function_calls:
                    
                    # Get the function name and arguments
                    function_name = function_call.name
                    args = dict(function_call.args)
                    
                    print(f"[AGENT] Model wants to call: {function_name}({args})")

                    # Get the actual Python function
                    tool_function = next((f for f in tools if f.__name__ == function_name), None)

                    if tool_function:
                        # 4. Execute the Python Function (Includes launching the app now)
                        function_result = tool_function(**args)
                        print(f"[AGENT] Function result: {function_result}")

                        # 5. Send the function result back to the Model to generate a natural language response
                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=[
                                types.Content(role="user", parts=[types.Part.from_text(user_prompt)]),
                                types.Content(role="function", parts=[types.Part.from_text(function_result)], name=function_name),
                            ]
                        )

                        print(f"Jarvis: {response.text}")

                    else:
                        print(f"[AGENT] Error: Unknown function {function_name}")
            else:
                # If no function call, just print the model's text response
                print(f"Jarvis: {response.text}")
        
        except APIError as e:
            print(f"\n[ERROR] Gemini API Error: {e}")
            print("Please check your GEMINI_API_KEY and network connection.")
        except Exception as e:
            print(f"\n[ERROR] An unexpected error occurred during API call: {e}")
        
        print("-" * 50)

# --- Execute Script ---
if __name__ == "__main__":
    try:
        run_spotify_agent()
    except Exception as e:
        print(f"\nCritical script error: {e}")