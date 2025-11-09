# modules/fastpath/desktop.py
import subprocess
import urllib.parse
import string
import time
from shutil import which

# --- REMOVED: No longer import the check from music.py ---
# We are abandoning this check during launch.

# --- Helper Function (Unchanged) ---
def _launch_spotify() -> bool:
    """
    Tries to launch Spotify using common install methods.
    Returns True on success, False on failure.
    """
    if which("spotify"):
        try:
            subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Desktop] Launched Spotify (native).")
            return True
        except Exception: pass
    if which("flatpak"):
        try:
            subprocess.Popen(["flatpak", "run", "com.spotify.Client"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Desktop] Launched Spotify (flatpak).")
            return True
        except Exception: pass
    if which("snap"):
        try:
            subprocess.Popen(["snap", "run", "spotify"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Desktop] Launched Spotify (snap).")
            return True
        except Exception: pass
    
    print("[Desktop] Could not find launch command for Spotify (native/flatpak/snap).")
    return False

# --- Program Launch Logic (MODIFIED) ---
PROGRAM_REGISTRY = {
    "firefox": ["brave"],
    "browser": ["brave"],
    "brave": ["brave"],
    "terminal": ["gnome-terminal"],
    "console": ["gnome-terminal"],
    "code": ["cursor"],
    "visual studio": ["cursor"],
    "cursor": ["cursor"],
    "spotify": [] # Handled by special logic
}

def handle_program_launch(text: str) -> str:
    """Launches a program from the PROGRAM_REGISTRY."""
    for trigger, command_list in PROGRAM_REGISTRY.items():
        if trigger in text:
            
            if trigger == "spotify":
                try:
                    # --- MODIFIED: Simplified Launch ---
                    print("[Desktop] Attempting to launch Spotify...")
                    
                    launched = _launch_spotify()
                    
                    if not launched:
                        # Try xdg-open fallback
                        print("[Desktop] Launch failed. Trying xdg-open fallback...")
                        try:
                            subprocess.Popen(["xdg-open", "spotify:home"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            launched = True
                        except Exception as e:
                            print(f"[Desktop] xdg-open fallback failed: {e}")
                            return "I tried to open Spotify, but all launch methods failed."
                    
                    # Give Spotify time to open
                    print("[Desktop] Giving Spotify 5 seconds to launch...")
                    time.sleep(5) 
                    
                    return "Opening Spotify."
                    
                except Exception as e:
                    return f"An error occurred while launching Spotify: {e}"
            
            else:
                # Original logic for other programs
                try:
                    subprocess.Popen(command_list)
                    return f"Opening {trigger}."
                except FileNotFoundError:
                    return f"Error: The command '{command_list[0]}' was not found on your system."
                except Exception as e:
                    return f"An error occurred: {e}"
                    
    return "I'm not sure which program to open."

# --- Web Search Logic (Unchanged) ---
SEARCH_TRIGGERS = [
    "look up",
    "search for"
]
def handle_web_search(text: str) -> str:
    """Performs a web search using Brave."""
    for trigger in SEARCH_TRIGGERS:
        if trigger in text:
            try:
                query_start_index = text.find(trigger) + len(trigger)
                query = text[query_start_index:].strip()
                query = query.strip(string.punctuation + " ")
                
                if not query:
                    return "What would you like me to search for?"
                
                encoded_query = urllib.parse.quote_plus(query)
                search_url = f"httpsExamples.com/search?q={encoded_query}" # Placeholder, use your preferred search
                subprocess.Popen(["brave", search_url])
                return f"Searching for {query}."
            except Exception as e:
                return f"An error occurred while searching: {e}"
    return "I'm not sure what to search for."