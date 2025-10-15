# modules/asr.py

import sys
import os
from faster_whisper import WhisperModel

# --- Robust Path Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    import config
except ImportError:
    print("Error: config.py not found.")
    sys.exit(1)

# --- One-time Model Initialization ---
# This is a major optimization. We load the model once when the module is imported.
# On first run, faster-whisper will download the model to a cache.
model = None
try:
    print("Initializing ASR model... (This may take a moment on first run)")
    model = WhisperModel(config.WHISPER_MODEL_NAME, device="cpu", compute_type="int8")
    print("ASR model initialized.")
except Exception as e:
    print(f"Failed to initialize ASR model: {e}")
    

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes an audio file using faster-whisper.
    """
    if not model:
        return "ERROR: ASR model not initialized."
    if not os.path.exists(audio_path):
        return "ERROR: Audio file not found."

    print("Transcribing audio...")
    try:
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        # Join all transcribed segments into a single string
        transcription = "".join(segment.text for segment in segments).strip()

        print(f"Transcription: '{transcription}'")
        return transcription
    except Exception as e:
        print(f"Error during transcription: {e}")
        return ""