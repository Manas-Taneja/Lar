# modules/fastpath/desktop.py
import subprocess
import urllib.parse
import string
import time
from shutil import which  # <-- NEW IMPORT

# --- NEW Helper Function ---
def _launch_spotify() -> bool:
    """
    Tries to launch Spotify using common install methods.
    Returns True on success, False on failure.
    """
    # Try native
    if which("spotify"):
        try:
            subprocess.Popen(["spotify"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Desktop] Launched Spotify (native).")
            return True
        except Exception:
            pass
    # Try Flatpak
    if which("flatpak"):
        try:
            subprocess.Popen(["flatpak", "run", "com.spotify.Client"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Desktop] Launched Spotify (flatpak).")
            return True
        except Exception:
            pass
    # Try Snap
    if which("snap"):
        try:
            subprocess.Popen(["snap", "run", "spotify"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[Desktop] Launched Spotify (snap).")
            return True
        except Exception:
            pass
    
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
    "spotify": [] # <-- MODIFIED: Now handled by _launch_spotify
}

def handle_program_launch(text: str) -> str:
    """Launches a program from the PROGRAM_REGISTRY."""
    for trigger, command_list in PROGRAM_REGISTRY.items():
        if trigger in text:
            
            if trigger == "spotify":
                try:
                    status_cmd_str = "playerctl --player=spotify status"
                    status_result = subprocess.run(
                        status_cmd_str,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=2,
                        check=False
                    )

                    if status_result.returncode == 0:
                        return "Spotify is already running."

                    print("[Desktop] Spotify not running. Launching...")
                    
                    # --- MODIFIED: Use new multi-launch strategy ---
                    launched = _launch_spotify()
                    if not launched:
                        print("[Desktop] All launch methods failed.")
                        return "I tried to open Spotify, but couldn't find a valid launch command."

                    print("[Desktop] Waiting for Spotify to become responsive...")
                    max_wait_seconds = 30
                    for i in range(max_wait_seconds):
                        time.sleep(1)
                        status_check = subprocess.run(
                            status_cmd_str,
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=1,
                            check=False
                        )
                        if status_check.returncode == 0:
                            print(f"[Desktop] Spotify is now responsive after {i+1} seconds.")
                            return "Opening Spotify."
                    
                    print(f"[Desktop] Waited {max_wait_seconds}s, Spotify is still not responsive.")

                    # --- MODIFIED: Add xdg-open fallback ---
                    print("[Desktop] Trying xdg-open fallback...")
                    try:
                        subprocess.Popen(["xdg-open", "spotify:home"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print("[Desktop] Triggered Spotify via xdg-open; giving it 5s...")
                        for _ in range(5):
                            time.sleep(1)
                            status_check = subprocess.run(status_cmd_str, shell=True, capture_output=True, text=True, timeout=1, check=False)
                            if status_check.returncode == 0:
                                print("[Desktop] Spotify became responsive after xdg-open.")
                                return "Opening Spotify."
                    except Exception as e:
                        print(f"[Desktop] xdg-open fallback failed: {e}")
                        pass
                    
                    return "I tried to open Spotify, but it's not responding."
                    
                except FileNotFoundError:
                    return "Error: 'playerctl' command not found."
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
                search_url = f"https://search.brave.com/search?q={encoded_query}"
                
                subprocess.Popen(["brave", search_url])
                return f"Searching for {query}."
            except Exception as e:
                return f"An error occurred while searching: {e}"
    return "I'm not sure what to search for."