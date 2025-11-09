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

def run_wake_word_listener_thread(
    asr_queue: queue.Queue, 
    stop_event: threading.Event, 
    tts_is_speaking_event: threading.Event, 
    mic_device_index: int
):
    """
    Listens for the wake word and then records a command using VAD,
    all on a single, continuous PyAudio stream.
    """

    STATE_WAITING_FOR_WAKE_WORD = 1
    STATE_RECORDING_COMMAND = 2

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

        print(f"Wake word listener started (listening for 'Jarvis')...")

        current_state = STATE_WAITING_FOR_WAKE_WORD
        command_audio_buffer = []
        silence_start_time = None
        wake_word_time = None  # Track when wake word was detected for timeout
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

            # --- THIS IS THE NEW FEEDBACK ---
            if was_tts_speaking:
                print("TTS finished. Resuming wake word listener...")
                was_tts_speaking = False  # Reset the flag
            # --- END NEW FEEDBACK ---

            # 3. Process audio based on state
            if current_state == STATE_WAITING_FOR_WAKE_WORD:
                keyword_index = porcupine.process(pcm_struct)
                if keyword_index >= 0:
                    print("Wake word detected! Listening for command...")
                    # --- Optional: Play activation sound ---
                    # from modules.utils import play_sound, ACK_START_SOUND
                    # play_sound(ACK_START_SOUND) 

                    command_audio_buffer.clear()
                    silence_start_time = None
                    wake_word_time = time.time()  # Track when wake word was detected
                    is_speaking = False
                    current_state = STATE_RECORDING_COMMAND

            elif current_state == STATE_RECORDING_COMMAND:
                # Convert frame to numpy array for VAD analysis
                # Use int16 directly for VAD (matches original logic)
                frame_int16 = np.array(pcm_struct, dtype=np.int16)
                
                # Also store normalized float32 for final audio output
                frame_np = frame_int16.astype(np.float32) / 32768.0
                command_audio_buffer.append(frame_np)

                # Calculate volume norm using int16 values (matches original logic)
                # Original code: volume_norm = np.linalg.norm(indata) * 10
                # where indata was int16 or float32 depending on dtype
                # For int16 values, norm * 10 gives us the scale we need
                volume_norm = np.linalg.norm(frame_int16) * 10
                
                # Debug: print volume occasionally
                if len(command_audio_buffer) % 100 == 0:  # Print every 100 frames
                    print(f"[DEBUG] Volume norm: {volume_norm:.2f}, Threshold: {config.SILENCE_THRESHOLD}, Buffer size: {len(command_audio_buffer)}")

                # Use original threshold - it was designed for int16 values
                if volume_norm > config.SILENCE_THRESHOLD:
                    # --- SPEECH DETECTED ---
                    if not is_speaking:
                        is_speaking = True
                        print("Speech detected, recording...", end="", flush=True)
                    
                    # Real-time feedback: print a dot for each speech frame
                    print(".", end="", flush=True)
                    
                    silence_start_time = None
                    wake_word_time = None  # Clear timeout since speech was detected
                else:
                    # Silence detected
                    if is_speaking:
                        # We were speaking, now silence - start timer
                        if silence_start_time is None:
                            silence_start_time = time.time()

                        if (time.time() - silence_start_time) > config.SILENCE_DURATION:
                            # VAD has triggered (end of speech)
                            print("\nCommand recorded (silence detected).")

                            # Combine all frames into one array
                            full_command_audio = np.concatenate(command_audio_buffer)

                            # Convert float32 to int16 for ASR compatibility
                            full_command_audio = np.clip(full_command_audio, -1.0, 1.0)
                            full_command_audio = (full_command_audio * 32767).astype(np.int16)

                            # Send to ASR
                            asr_queue.put(full_command_audio)

                            # Reset state
                            command_audio_buffer.clear()
                            is_speaking = False
                            silence_start_time = None
                            wake_word_time = None
                            current_state = STATE_WAITING_FOR_WAKE_WORD
                            print("Listening for wake word...")
                    # If not speaking yet, continue recording (waiting for speech to start)
                    elif not is_speaking:
                        # Timeout after 3 seconds if no speech detected after wake word
                        if wake_word_time and (time.time() - wake_word_time) > 3.0:
                            print("\nNo command detected, timing out.")
                            command_audio_buffer.clear()
                            is_speaking = False
                            silence_start_time = None
                            wake_word_time = None
                            current_state = STATE_WAITING_FOR_WAKE_WORD
                            print("Listening for wake word...")

    except Exception as e:
        print("--- WAKE WORD LISTENER CRITICAL ERROR ---")
        print(f"An error occurred, which is likely a PICOVOICE configuration issue.")
        print(f"Please check your PICOVOICE_ACCESS_KEY and PORCUPINE_KEYWORD_PATH in config.py")
        traceback.print_exc()  # This will print the full error stack
        print("-----------------------------------------")
    finally:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        if pa:
            pa.terminate()
        if porcupine:
            porcupine.delete()


# --- UPDATED TEST BLOCK ---
# This block is for testing the wake word listener
if __name__ == "__main__":
    # Initialize TTS Server for the test
    tts = TTS_Server()
    test_asr_queue = queue.Queue()
    test_tts_is_speaking_event = threading.Event()  # Dummy event for testing
    
    try:
        tts.speak("Lar is online and ready for direct testing.")
        
        # Start the wake word listener thread
        audio_thread = threading.Thread(
            target=run_wake_word_listener_thread,
            args=(test_asr_queue, stop_event, test_tts_is_speaking_event, config.MIC_DEVICE_INDEX),
            daemon=True
        )
        audio_thread.start()
        
        # Wait for audio and process it
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
        # Ensure server is shut down after test
        tts.shutdown()