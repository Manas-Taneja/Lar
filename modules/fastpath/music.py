# modules/fastpath/music.py
import subprocess
import re

# --- Volume Control Logic ---
def handle_volume_control(text: str) -> str:
    """Controls system volume using pactl or amixer."""
    text_lower = text.lower()
    
    # Check for mute/unmute
    if "mute" in text_lower:
        if "unmute" in text_lower or "un mute" in text_lower:
            try:
                # Try pactl first (PulseAudio)
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], 
                             check=False, capture_output=True)
                return "Unmuted."
            except Exception:
                try:
                    # Fallback to amixer (ALSA)
                    subprocess.run(["amixer", "set", "Master", "unmute"], 
                                 check=False, capture_output=True)
                    return "Unmuted."
                except Exception as e:
                    return f"Error unmuting: {e}"
        else:
            try:
                # Try pactl first
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], 
                             check=False, capture_output=True)
                return "Muted."
            except Exception:
                try:
                    # Fallback to amixer
                    subprocess.run(["amixer", "set", "Master", "mute"], 
                                 check=False, capture_output=True)
                    return "Muted."
                except Exception as e:
                    return f"Error muting: {e}"
    
    # Check for volume up/down
    if "turn up" in text_lower or "volume up" in text_lower or "increase" in text_lower:
        try:
            # Try pactl
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"], 
                         check=False, capture_output=True)
            return "Volume increased."
        except Exception:
            try:
                # Fallback to amixer
                subprocess.run(["amixer", "set", "Master", "10%+"], 
                             check=False, capture_output=True)
                return "Volume increased."
            except Exception as e:
                return f"Error increasing volume: {e}"
    
    if "turn down" in text_lower or "volume down" in text_lower or "decrease" in text_lower:
        try:
            # Try pactl
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"], 
                         check=False, capture_output=True)
            return "Volume decreased."
        except Exception:
            try:
                # Fallback to amixer
                subprocess.run(["amixer", "set", "Master", "10%-"], 
                             check=False, capture_output=True)
                return "Volume decreased."
            except Exception as e:
                return f"Error decreasing volume: {e}"
    
    # Check for set volume with a number
    if "set volume" in text_lower or "volume to" in text_lower:
        # Try to extract a number
        numbers = re.findall(r'\d+', text_lower)
        if numbers:
            volume = int(numbers[0])
            # Clamp to 0-100
            volume = max(0, min(100, volume))
            try:
                # Try pactl
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{volume}%"], 
                             check=False, capture_output=True)
                return f"Volume set to {volume}%."
            except Exception:
                try:
                    # Fallback to amixer
                    subprocess.run(["amixer", "set", "Master", f"{volume}%"], 
                                 check=False, capture_output=True)
                    return f"Volume set to {volume}%."
                except Exception as e:
                    return f"Error setting volume: {e}"
    
    # Generic volume query
    if "volume" in text_lower:
        return "Volume control ready. Say 'turn up', 'turn down', 'mute', or 'set volume to X'."
    
    return "I'm not sure what volume action you want."

# --- Media Control Logic ---
def handle_media_control(text: str) -> str:
    """Controls media playback using playerctl."""
    text_lower = text.lower()
    
    # Map commands to playerctl actions
    command_map = {
        "play": "play",
        "pause": "pause",
        "resume": "play",  # Resume is same as play
        "stop": "stop",
        "next": "next",
        "previous": "previous",
        "last": "previous"  # Last song is previous
    }
    
    # Find the matching command
    for keyword, action in command_map.items():
        if keyword in text_lower:
            try:
                # Try to control Spotify first
                result = subprocess.run(
                    ["playerctl", "--player=spotify", action],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False
                )
                
                if result.returncode == 0:
                    if action == "play":
                        return "Playing."
                    elif action == "pause":
                        return "Paused."
                    elif action == "stop":
                        return "Stopped."
                    elif action == "next":
                        return "Next track."
                    elif action == "previous":
                        return "Previous track."
                
                # If Spotify control failed, try any player
                result = subprocess.run(
                    ["playerctl", action],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False
                )
                
                if result.returncode == 0:
                    if action == "play":
                        return "Playing."
                    elif action == "pause":
                        return "Paused."
                    elif action == "stop":
                        return "Stopped."
                    elif action == "next":
                        return "Next track."
                    elif action == "previous":
                        return "Previous track."
                else:
                    return f"Could not {action} media. Is a media player running?"
                    
            except FileNotFoundError:
                return "Error: 'playerctl' command not found. Please install playerctl."
            except subprocess.TimeoutExpired:
                return f"Timeout while trying to {action} media."
            except Exception as e:
                return f"Error controlling media: {e}"
    
    # Toggle command
    if "toggle" in text_lower:
        try:
            # Try Spotify first
            result = subprocess.run(
                ["playerctl", "--player=spotify", "play-pause"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            
            if result.returncode == 0:
                return "Toggled playback."
            
            # Try any player
            result = subprocess.run(
                ["playerctl", "play-pause"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False
            )
            
            if result.returncode == 0:
                return "Toggled playback."
            else:
                return "Could not toggle media. Is a media player running?"
                
        except FileNotFoundError:
            return "Error: 'playerctl' command not found. Please install playerctl."
        except subprocess.TimeoutExpired:
            return "Timeout while trying to toggle media."
        except Exception as e:
            return f"Error toggling media: {e}"
    
    return "I'm not sure what media action you want."
