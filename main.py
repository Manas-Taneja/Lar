import sys
import os
import numpy as np
from scipy.io.wavfile import write
import signal
import threading
import time
import queue
import pyaudio
import pvporcupine
import struct
import traceback
import config

# --- Corrected and Consolidated Imports ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        
    import config
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

def run_wake_word_listener_thread(
    asr_queue: queue.Queue, 
    stop_event: threading.Event, 
    tts_is_speaking_event: threading.Event, 
    mic_device_index: int
):
    """
    Listens for the wake word and then records a command using VAD,
    all on a single, continuous PyAudio stream.
    Includes a "follow-up" mode to avoid repeating the wake word.
    """

    # --- MODIFIED: Added new state ---
    STATE_WAITING_FOR_WAKE_WORD = 1
    STATE_RECORDING_COMMAND = 2
    STATE_WAITING_FOR_FOLLOW_UP = 3 # <-- NEW STATE
    
    # --- NEW: Follow-up timer constant ---
    FOLLOW_UP_TIMEOUT_DURATION = 5.0 # 5 seconds

    pa = None
    porcupine = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(
            access_key=config.PICOVOICE_ACCESS_KEY,
            keyword_paths=[config.PORCUPINE_KEYWORD_PATH],
            sensitivities=[config.PORCUPINE_SENSITIVITY]
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=mic_device_index
        )

        print(f"Wake word listener started (listening for 'Hey Lar')...")

        current_state = STATE_WAITING_FOR_WAKE_WORD
        command_audio_buffer = []
        silence_start_time = None
        wake_word_time = None  # Track when wake word was detected for timeout
        
        # --- NEW: Follow-up timer ---
        follow_up_timer_start = None

        is_speaking = False
        was_tts_speaking = False  # Track if TTS was speaking to detect when it resumes

        while not stop_event.is_set():
            # 1. Read a frame of audio
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_struct = struct.unpack_from("h" * porcupine.frame_length, pcm)

            # 2. Check if TTS is speaking. If so, ignore all audio.
            if tts_is_speaking_event.is_set():
                was_tts_speaking = True
                continue  # Skip all processing while TTS is active

            if was_tts_speaking:
                print("TTS finished. Resuming listener...") # Use original string
                was_tts_speaking = False  # Reset the flag

            # 3. Process audio based on state
            if current_state == STATE_WAITING_FOR_WAKE_WORD:
                keyword_index = porcupine.process(pcm_struct)
                if keyword_index >= 0:
                    print("Wake word detected! Listening for command...")
                    command_audio_buffer.clear()
                    silence_start_time = None
                    wake_word_time = time.time()  # Track when wake word was detected
                    is_speaking = False
                    current_state = STATE_RECORDING_COMMAND

            elif current_state == STATE_RECORDING_COMMAND:
                # This logic is identical to your old file
                frame_int16 = np.array(pcm_struct, dtype=np.int16)
                frame_np = frame_int16.astype(np.float32) / 32768.0
                command_audio_buffer.append(frame_np)
                volume_norm = np.linalg.norm(frame_int16) * 10
                
                # --- RESTORED DEBUG PRINT ---
                # This lets us see if your mic volume is too low
                if len(command_audio_buffer) % 100 == 0:  # Print every 100 frames
                    print(f"[DEBUG] Volume norm: {volume_norm:.2f}, Threshold: {config.SILENCE_THRESHOLD}, Buffer size: {len(command_audio_buffer)}")
                # --- END RESTORED DEBUG ---

                if volume_norm > config.SILENCE_THRESHOLD:
                    if not is_speaking:
                        is_speaking = True
                        print("Speech detected, recording...", end="", flush=True)
                    print(".", end="", flush=True)
                    silence_start_time = None
                    wake_word_time = None
                else:
                    # Silence detected
                    if is_speaking:
                        if silence_start_time is None:
                            silence_start_time = time.time()

                        if (time.time() - silence_start_time) > config.SILENCE_DURATION:
                            print("\nCommand recorded (silence detected).")
                            full_command_audio = np.concatenate(command_audio_buffer)
                            full_command_audio = (full_command_audio * 32767).astype(np.int16)
                            asr_queue.put(full_command_audio)

                            # --- MODIFIED: Go to FOLLOW_UP state ---
                            print(f"Listening for follow-up ({FOLLOW_UP_TIMEOUT_DURATION}s)...")
                            command_audio_buffer.clear()
                            is_speaking = False
                            silence_start_time = None
                            wake_word_time = None
                            follow_up_timer_start = time.time() # Start follow-up timer
                            current_state = STATE_WAITING_FOR_FOLLOW_UP
                            # --- END MODIFICATION ---
                            
                    elif not is_speaking:
                        if wake_word_time and (time.time() - wake_word_time) > 3.0:
                            print("\nNo command detected, timing out.")
                            command_audio_buffer.clear()
                            is_speaking = False
                            silence_start_time = None
                            wake_word_time = None
                            current_state = STATE_WAITING_FOR_WAKE_WORD
                            print("Listening for wake word...")
            
            # --- NEW STATE HANDLER ---
            elif current_state == STATE_WAITING_FOR_FOLLOW_UP:
                # 1. Check for timeout
                if (time.time() - follow_up_timer_start) > FOLLOW_UP_TIMEOUT_DURATION:
                    print("Follow-up window closed. Listening for wake word...")
                    follow_up_timer_start = None
                    current_state = STATE_WAITING_FOR_WAKE_WORD
                    continue

                # 2. Check for speech (VAD)
                frame_int16 = np.array(pcm_struct, dtype=np.int16)
                volume_norm = np.linalg.norm(frame_int16) * 10
                
                if volume_norm > config.SILENCE_THRESHOLD:
                    # Speech detected! Go back to recording state
                    print("Follow-up detected! Listening for command...")
                    
                    frame_np = frame_int16.astype(np.float32) / 32768.0
                    command_audio_buffer.clear()
                    command_audio_buffer.append(frame_np)

                    silence_start_time = None
                    wake_word_time = None
                    is_speaking = True # We are already speaking
                    follow_up_timer_start = None # Clear follow-up timer
                    current_state = STATE_RECORDING_COMMAND
            # --- END NEW STATE HANDLER ---

    except Exception as e:
        print("--- WAKE WORD LISTENER CRITICAL ERROR ---")
        traceback.print_exc()
        print("-----------------------------------------")
    finally:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        if pa:
            pa.terminate()
        if porcupine:
            porcupine.delete()


# --- Test Block (Unchanged from your file) ---
if __name__ == "__main__":
    tts = TTS_Server()
    test_asr_queue = queue.Queue()
    test_tts_is_speaking_event = threading.Event()
    
    try:
        tts.speak("Lar is online and ready for direct testing.")
        
        audio_thread = threading.Thread(
            target=run_wake_word_listener_thread,
            args=(test_asr_queue, stop_event, test_tts_is_speaking_event, config.MIC_DEVICE_INDEX),
            daemon=True
        )
        audio_thread.start()
        
        while not stop_event.is_set():
            try:
                recording = test_asr_queue.get(timeout=1.0)
                user_prompt = transcribe_audio(recording).lower()
                if user_prompt:
                    print(f"You: {user_prompt}")
                    response = process_prompt(user_prompt)
                    if response:
                        sanitized_response = sanitize_text_for_tts(response)
                        humanized_response = humanize_text(sanitized_response)
                        tts.speak(humanized_response)
            except queue.Empty:
                continue
    finally:
        tts.shutdown()