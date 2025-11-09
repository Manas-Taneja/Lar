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
    # --- MODIFIED IMPORT ---
    # We only import the server class for the test block
    from modules.tts import TTS_Server
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

def listen_for_speech(threshold: int, duration: float, device_index: int | None):
    """
    Records audio from the microphone using a more reliable VAD logic.
    Accepts VAD parameters directly.
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

        if volume_norm > threshold:
            if not is_speaking:
                print("Speech detected, recording...")
                is_speaking = True
            silence_start_time = None
            audio_queue.append(indata.copy())
        elif is_speaking:
            if silence_start_time is None:
                silence_start_time = time.currentTime
            
            if (time.currentTime - silence_start_time) > duration:
                is_speaking = False
                raise sd.CallbackStop
            audio_queue.append(indata.copy())

    try:
        with sd.InputStream(samplerate=config.SAMPLE_RATE, channels=2, dtype='int16', 
                            device=device_index, callback=callback):
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


# --- UPDATED TEST BLOCK ---
# This block is for testing this module directly
if __name__ == "__main__":
    SILENCE_THRESHOLD = 2000000
    SILENCE_DURATION = 1.0
    MIC_DEVICE_INDEX = 8
    
    sd.default.device = MIC_DEVICE_INDEX

    # Initialize TTS Server for the test
    tts = TTS_Server()
    
    try:
        tts.speak("Lar is online and ready for direct testing.")
        
        audio_file = listen_for_speech(
            threshold=SILENCE_THRESHOLD, 
            duration=SILENCE_DURATION, 
            device_index=MIC_DEVICE_INDEX
        )
        
        if audio_file:
            user_prompt = transcribe_audio(audio_file).lower()
            if user_prompt:
                print(f"You: {user_prompt}")
                response = process_prompt(user_prompt)
                sanitized_response = sanitize_text_for_tts(response)
                humanized_response = humanize_text(sanitized_response)
                tts.speak(humanized_response)
    finally:
        # Ensure server is shut down after test
        tts.shutdown()