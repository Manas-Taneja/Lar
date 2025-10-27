# modules/fastpath/media.py
import subprocess
import re

# --- Silent Volume Control Logic ---
def handle_volume_control(text: str) -> str | None:
    """Controls Spotify's volume using playerctl. Returns None on success."""
    # ... (code unchanged) ...
    cmd_base = ["playerctl", "--player=spotify", "volume"]
    
    try:
        if "toggle mute" in text:
            subprocess.Popen(["playerctl", "--player=spotify", "mute"])
            return None
        elif "unmute" in text:
            subprocess.Popen(cmd_base + ["0.5"]) 
            return None
        elif "mute" in text:
            subprocess.Popen(cmd_base + ["0"]) 
            return None
        match = re.search(r"(set volume to|set to|to) (\d{1,3})", text)
        if match:
            percentage = int(match.group(2))
            if percentage > 100: percentage = 100
            if percentage < 0: percentage = 0
            volume_float = f"{percentage / 100.0}"
            subprocess.Popen(cmd_base + [volume_float])
            return None
        if "turn it up" in text or "volume up" in text:
            subprocess.Popen(cmd_base + ["0.05+"]) 
            return None
        if "turn it down" in text or "volume down" in text:
            subprocess.Popen(cmd_base + ["0.05-"])
            return None
        if "max volume" in text or "full volume" in text:
            subprocess.Popen(cmd_base + ["1.0"])
            return None
    except FileNotFoundError:
        return "Error: playerctl not found. Please ensure it is installed."
    except Exception as e:
        return "I couldn't control Spotify. Is it running?"
    return None

# --- UPDATED: Silent Media Control Logic ---
MEDIA_COMMANDS = {
    "play": ["playerctl", "--player=spotify", "play"],
    "pause": ["playerctl", "--player=spotify", "pause"],
    "stop": ["playerctl", "--player=spotify", "stop"],
    "next": ["playerctl", "--player=spotify", "next"],
    "previous": ["playerctl", "--player=spotify", "previous"],
    "toggle": ["playerctl", "--player=spotify", "play-pause"]
}

GENERIC_PLAY_TERMS = [
    "play",
    "resume",
    "play music",
    "play spotify",
    "resume music"
]

def handle_media_control(text: str) -> str | None: # <-- Return type changed
    """Controls Spotify using playerctl. Returns None on success."""
    cmd = None
    action = None # <-- Changed: Default to None for silent success

    if "next" in text:
        cmd = MEDIA_COMMANDS["next"]
    elif "previous" in text or "last" in text:
        cmd = MEDIA_COMMANDS["previous"]
    elif "play" in text and "pause" in text:
        cmd = MEDIA_COMMANDS["toggle"]
    elif "pause" in text:
        cmd = MEDIA_COMMANDS["pause"]
    elif "stop" in text:
        cmd = MEDIA_COMMANDS["stop"]
        
    elif "play" in text or "resume" in text:
        is_generic_play = False
        for term in GENERIC_PLAY_TERMS:
            if text == term:
                is_generic_play = True
                break
        
        if is_generic_play:
            cmd = MEDIA_COMMANDS["play"]
        else:
            if "play" in text:
                query_start_index = text.find("play") + len("play")
            elif "resume" in text:
                query_start_index = text.find("resume") + len("resume")
                
            query = text[query_start_index:].strip()
            
            if query:
                uri = f"spotify:search:{query}"
                cmd = ["playerctl", "--player=spotify", "open", uri]
            else:
                cmd = MEDIA_COMMANDS["play"]
                
    else:
        if any(kw in text for kw in ["music", "spotify", "song", "track"]):
             cmd = MEDIA_COMMANDS["toggle"]
        else:
            # No command matched, return an error message to be spoken
            return "Sorry, I'm not sure what media command to run."

    # --- Execute the command ---
    try:
        subprocess.Popen(cmd)
        return action # <-- This will return None on success
    except FileNotFoundError:
        return "Error: playerctl not found. Please install it."
    except Exception as e:
        print(f"Media control error: {e}")
        return "I couldn't control Spotify. Is it running?"