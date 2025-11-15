# modules/fastpath/music.py
import subprocess
import re
import sys
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- Robust Path Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    if project_root not in sys.path:
        sys.path.append(project_root)
    import config
except ImportError:
    print("Error: music.py could not import config.")
    sys.exit(1)

# --- Global Spotipy Client ---
sp = None

def init_spotipy():
    """Initializes the global Spotipy client (sp) using OAuth."""
    global sp
    if sp:
        return True 

    if not all([config.SPOTIPY_CLIENT_ID, config.SPOTIPY_CLIENT_SECRET, config.SPOTIPY_REDIRECT_URI]):
        print("[Spotify] Error: Missing SPOTIPY credentials in config.py or .env")
        return False

    try:
        auth_manager = SpotifyOAuth(
            client_id=config.SPOTIPY_CLIENT_ID,
            client_secret=config.SPOTIPY_CLIENT_SECRET,
            redirect_uri=config.SPOTIPY_REDIRECT_URI,
            scope=config.SPOTIPY_SCOPE,
            cache_path=config.SPOTIPY_CACHE_PATH
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        sp.me() 
        print("[Spotify] Spotipy client initialized and authenticated successfully.")
        return True
    except Exception as e:
        print(f"[Spotify] Failed to initialize Spotipy: {e}")
        return False

# --- NEW: Spotify Volume Control ---
def handle_volume_control(text: str) -> str:
    """Controls Spotify volume using the Spotipy API."""
    global sp
    
    if not sp:
        if not init_spotipy():
             return "Sorry, I can't connect to Spotify. Please check my configuration."

    text_lower = text.lower()

    try:
        # Get current playback state to find current volume
        playback = sp.current_playback()
        if not playback or not playback.get('device'):
            return "No active Spotify device found."
            
        current_volume = playback['device']['volume_percent']
        new_volume = current_volume

        # --- Relative Volume ---
        if "turn up" in text_lower or "volume up" in text_lower or "increase" in text_lower:
            new_volume = min(100, current_volume + 10)
            sp.volume(new_volume)
            return f"Spotify volume set to {new_volume}%."
        
        if "turn down" in text_lower or "volume down" in text_lower or "decrease" in text_lower:
            new_volume = max(0, current_volume - 10)
            sp.volume(new_volume)
            return f"Spotify volume set to {new_volume}%."

        # --- Mute / Unmute ---
        if "mute" in text_lower:
             if "unmute" in text_lower or "un mute" in text_lower:
                 # We'll just set it to a reasonable 50%
                 sp.volume(50) 
                 return "Spotify unmuted."
             else:
                 sp.volume(0)
                 return "Spotify muted."

        # --- Absolute Volume ---
        if "set volume" in text_lower or "volume to" in text_lower:
            numbers = re.findall(r'\d+', text_lower)
            if numbers:
                volume = int(numbers[0])
                new_volume = max(0, min(100, volume))
                sp.volume(new_volume)
                return f"Spotify volume set to {new_volume}%."
        
        return "Not sure what Spotify volume action you want."

    except spotipy.exceptions.SpotifyException as e:
        if e.reason == 'NO_ACTIVE_DEVICE':
            return "No active Spotify device found."
        return f"Spotify error: {e.reason}"
    except Exception as e:
        print(f"[Spotify] Volume Error: {e}")
        return "An error occurred controlling Spotify volume."

# --- RENAMED: System Volume Control ---
def handle_system_volume(text: str) -> str:
    """Controls MASTER system volume using pactl or amixer."""
    text_lower = text.lower()
    
    # Check for mute/unmute
    if "mute" in text_lower:
        if "unmute" in text_lower or "un mute" in text_lower:
            try:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=False, capture_output=True)
                return "System unmuted."
            except Exception:
                try:
                    subprocess.run(["amixer", "set", "Master", "unmute"], check=False, capture_output=True)
                    return "System unmuted."
                except Exception as e:
                    return f"Error unmuting system: {e}"
        else:
            try:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], check=False, capture_output=True)
                return "System muted."
            except Exception:
                try:
                    subprocess.run(["amixer", "set", "Master", "mute"], check=False, capture_output=True)
                    return "System muted."
                except Exception as e:
                    return f"Error muting system: {e}"
    
    # Check for volume up/down
    if "turn up" in text_lower or "volume up" in text_lower or "increase" in text_lower:
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"], check=False, capture_output=True)
            return "System volume increased."
        except Exception:
            try:
                subprocess.run(["amixer", "set", "Master", "10%+"], check=False, capture_output=True)
                return "System volume increased."
            except Exception as e:
                return f"Error increasing system volume: {e}"
    
    if "turn down" in text_lower or "volume down" in text_lower or "decrease" in text_lower:
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"], check=False, capture_output=True)
            return "System volume decreased."
        except Exception:
            try:
                subprocess.run(["amixer", "set", "Master", "10%-"], check=False, capture_output=True)
                return "System volume decreased."
            except Exception as e:
                return f"Error decreasing system volume: {e}"
    
    # Check for set volume with a number
    if "set volume" in text_lower or "volume to" in text_lower:
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            volume = int(numbers[0])
            volume = max(0, min(100, volume))
            try:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"], check=False, capture_output=True)
                return f"System volume set to {volume}%."
            except Exception:
                try:
                    subprocess.run(["amixer", "set", "Master", f"{volume}%"], check=False, capture_output=True)
                    return f"System volume set to {volume}%."
                except Exception as e:
                    return f"Error setting system volume: {e}"
    
    return "I'm not sure what system volume action you want."

# --- Media Control Logic (Unchanged, uses Spotipy) ---
def handle_media_control(text: str) -> str:
    """Controls Spotify playback using the Spotipy API."""
    global sp
    
    if not sp:
        if not init_spotipy():
             return "Sorry, I can't connect to Spotify. Please check my configuration."

    text_lower = text.lower().strip(" .?!,")

    try:
        if text_lower.startswith("play "):
            query = text_lower[len("play "):].strip()
            if query:
                print(f"[Spotify] Searching for track: '{query}'")
                results = sp.search(q=query, limit=1, type='track')
                tracks = results['tracks']['items']
                
                if not tracks:
                    return f"Sorry, I couldn't find '{query}' on Spotify."
                
                track_uri = tracks[0]['uri']
                track_name = tracks[0]['name']
                sp.start_playback(uris=[track_uri])
                return f"Playing {track_name}."
            
            else:
                sp.start_playback()
                return "Playing."

        elif text_lower == "play":
            sp.start_playback()
            return "Playing."

        elif text_lower == "resume":
            sp.start_playback()
            return "Playing."
            
        elif text_lower == "pause":
            sp.pause_playback()
            return "Paused."
            
        elif text_lower == "stop":
            sp.pause_playback()
            return "Stopped."
            
        elif text_lower == "next":
            sp.next_track()
            return "Next track."
            
        elif text_lower == "previous" or text_lower == "last song":
            sp.previous_track()
            return "Previous track."
            
        elif "toggle" in text_lower:
            state = sp.current_playback()
            if state and state['is_playing']:
                sp.pause_playback()
                return "Paused."
            else:
                sp.start_playback()
                return "Playing."

    except spotipy.exceptions.SpotifyException as e:
        if e.reason == 'NO_ACTIVE_DEVICE':
            return "I can't control Spotify. Please open Spotify on one of your devices."
        if e.reason == 'PREMIUM_REQUIRED':
            return "Sorry, Spotify search-and-play requires a Premium account."
        if "token expired" in str(e):
             print("[Spotify] Token expired. Re-authenticating...")
             sp = None
             return handle_media_control(text) 
        return f"Spotify error: {e.reason}"
    except Exception as e:
        if "browser" in str(e):
             return "Please check your browser to log into Spotify."
        print(f"[Spotify] Unknown error: {e}")
        return "An unknown error occurred with Spotify."

    return "I'm not sure what media action you want."