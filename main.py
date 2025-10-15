import sys
import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import signal
import threading
import time

# --- Corrected and Consolidated Imports ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        
    import config
    from modules.tts import speak
    from modules.asr import transcribe_audio
    from modules.core_logic import process_prompt
    from modules.utils import play_sound, ACK_START_SOUND, humanize_text, sanitize_text_for_tts

except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# --- Graceful Exit Setup ---
stop_event = threading.Event()

def signal_handler(sig, frame):
    print("\nInterrupt received, shutting down...")
    stop_event.set()

signal.signal(signal.SIGINT, signal_handler)

# --- Audio Recording Settings ---
SILENCE_THRESHOLD = 40
SILENCE_DURATION = 1.0
MIC_DEVICE_INDEX = None

def listen_for_speech():
    """
    Records audio from the microphone using a more reliable VAD logic.
    """
    print("\nListening...")
    audio_queue = []
    is_speaking = False
    silence_start_time = None

    def callback(indata, frames, time, status):
        nonlocal is_speaking, silence_start_time
        if stop_event.is_set():
            raise sd.CallbackStop

        volume_norm = np.linalg.norm(indata) * 10

        if volume_norm > SILENCE_THRESHOLD:
            if not is_speaking:
                print("Speech detected, recording...")
                is_speaking = True
            silence_start_time = None
            audio_queue.append(indata.copy())
        elif is_speaking:
            if silence_start_time is None:
                silence_start_time = time.currentTime
            
            if (time.currentTime - silence_start_time) > SILENCE_DURATION:
                is_speaking = False
                raise sd.CallbackStop
            audio_queue.append(indata.copy())

    try:
        # --- THIS IS THE FIX ---
        # Changed channels from 1 to 2 to match your microphone's capabilities.
        with sd.InputStream(samplerate=config.SAMPLE_RATE, channels=2, dtype='int16', 
                            device=MIC_DEVICE_INDEX, callback=callback):
            while is_speaking or len(audio_queue) == 0:
                if stop_event.is_set():
                    break
                sd.sleep(100)
    except Exception as e:
        if not stop_event.is_set():
             print(f"An error occurred during recording: {e}")
        return None

    if not audio_queue or stop_event.is_set():
        return None

    print("Recording finished.")
    recording = np.concatenate(audio_queue, axis=0)
    write(config.RECORDING_PATH, config.SAMPLE_RATE, recording)
    return config.RECORDING_PATH


# This block is for testing this module directly
if __name__ == "__main__":
    sd.default.device = 8 
    speak("Lar is online and ready for direct testing.")
    audio_file = listen_for_speech()
    if audio_file:
        user_prompt = transcribe_audio(audio_file).lower()
        if user_prompt:
            print(f"You: {user_prompt}")
            response = process_prompt(user_prompt)
            sanitized_response = sanitize_text_for_tts(response)
            humanized_response = humanize_text(sanitized_response)
            speak(humanized_response)