import sys
import os
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import signal
import threading
import time

# --- Robust Path Setup for Modules ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    from modules.llm_handler import query_llm
    from modules.tts import speak
    from modules.asr import transcribe_audio
    import config
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
SILENCE_THRESHOLD = 40  # Keep the threshold you settled on
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

        float_data = indata.astype(np.float32) / 32768.0
        volume_norm = np.sqrt(np.mean(float_data**2)) * 500

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
        with sd.InputStream(samplerate=config.SAMPLE_RATE, channels=1, dtype='int16', 
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

    print("Recording finished.") # This message should now appear reliably.
    recording = np.concatenate(audio_queue, axis=0)
    write(config.RECORDING_PATH, config.SAMPLE_RATE, recording)
    return config.RECORDING_PATH


if __name__ == "__main__":
    # We need to import the fastpath commands
    from modules.fastpath import COMMANDS

    speak("Lar is online and ready.")
    
    while not stop_event.is_set():
        audio_file = listen_for_speech()
        
        if stop_event.is_set():
            break

        if audio_file:
            user_prompt = transcribe_audio(audio_file).lower() # Convert to lowercase for matching
            
            if user_prompt and user_prompt.strip():
                print(f"You: {user_prompt}")
                
                response = None
                # --- Fastpath Router Logic ---
                for trigger, function in COMMANDS.items():
                    if trigger in user_prompt:
                        response = function(user_prompt)
                        break # Exit loop once a command is matched
                
                # --- LLM Fallback ---
                if response is None:
                    response = query_llm(user_prompt)

                speak(response)
            else:
                print("Could not understand audio, please try again.")
    
    print("\nShutting down.")
    speak("Lar is shutting down. Goodbye.")