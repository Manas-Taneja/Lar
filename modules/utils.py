# modules/utils.py
import soundfile as sf
import sounddevice as sd
import os
import random

# --- Robust Path Setup ---
try:
    # This setup helps locate the project root from within the /modules directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
except NameError:
    # Fallback for environments where __file__ is not defined
    project_root = os.path.abspath(os.path.join(os.getcwd()))


# --- Sound Playback Function (from Phase 1) ---
ACK_START_SOUND = os.path.join(project_root, "assets", "audio", "ack_start.wav")

def play_sound(sound_path: str):
    """
    Plays a WAV file using sounddevice.
    """
    if not os.path.exists(sound_path):
        return
    try:
        data, fs = sf.read(sound_path, dtype='float32')
        sd.play(data, fs)
        sd.wait()
    except Exception as e:
        print(f"Error playing sound: {e}")


# --- Humanizer Function (New) ---
FILLER_WORDS = [
    "Hmmmm,",
    "Umm,",
    "Okay, so,",
    "Well,",
    "Right,",
    "So,",
    "Let me see,",
    "Alright,",
    "Let me think,"
]

THINKING_PHRASES = [
    "Let me see",
    "Okay, one moment,",
    "Let me think about that,",
    "Hmmm, just a second,",
    "Processing that for you,"
]

def humanize_text(text: str, chance: float = 1) -> str:
    """
    Adds a conversational filler word to the beginning of a text string
    based on a given probability (default 50%).
    """
    if not text:
        return ""
        
    if random.random() < chance:
        filler = random.choice(FILLER_WORDS)
        return f"{filler} {text}"
    return text

def sanitize_text_for_tts(text: str) -> str:
    """
    Removes or replaces characters from a string to make it
    more TTS-friendly.
    """
    if not text:
        return ""
    
    replacements = {
        '**': '',
        '*': '',
        '...': ',',
        ':': ',',
        ';': '.'
    }
    
    sanitized_text = text
    for old, new in replacements.items():
        sanitized_text = sanitized_text.replace(old, new)
    
    return sanitized_text.strip()