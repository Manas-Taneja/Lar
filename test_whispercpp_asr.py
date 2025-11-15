# test_whispercpp_asr.py
# A standalone script to test whisper.cpp with a live microphone and VAD.

import pyaudio
import numpy as np
import wave
import time
import sys
import os
import tempfile
from scipy.io.wavfile import write
import threading
import subprocess #<-- Added for whisper.cpp

# --- 1. Load Project Config (for settings) ---
try:
    # Add project root to path to find 'config'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    import config
    print("Importing project config...")
    
    # VAD Settings from config
    SILENCE_THRESHOLD = config.SILENCE_THRESHOLD
    SILENCE_DURATION = config.SILENCE_DURATION
    SAMPLE_RATE = config.SAMPLE_RATE
    MIC_DEVICE_INDEX = config.MIC_DEVICE_INDEX
    
    print(f"Loaded config: SR={SAMPLE_RATE}, MicIdx={MIC_DEVICE_INDEX}")
    print(f"VAD: Threshold={SILENCE_THRESHOLD}, Duration={SILENCE_DURATION}s")

except ImportError:
    print("Error: config.py not found.")
    sys.exit(1)
except AttributeError:
     print("Error: config.py is missing required variables.")
     sys.exit(1)


# --- 2. Initialize whisper.cpp Configuration ---
print("\nInitializing ASR (whisper.cpp, distil-large-v3.5)...")

WHISPER_CPP_DIR = os.path.join(config.PROJECT_ROOT, "whisper.cpp")
WHISPER_CPP_MAIN = os.path.join(WHISPER_CPP_DIR, "build", "bin", "whisper-cli")
WHISPER_MODEL_PATH = os.path.join(WHISPER_CPP_DIR, "models", "ggml-distil-large-v3.5.bin")

# Check if the model and executable exist
if not os.path.exists(WHISPER_CPP_MAIN):
    print(f"FATAL: whisper.cpp executable not found at {WHISPER_CPP_MAIN}")
    sys.exit(1)

if not os.path.exists(WHISPER_MODEL_PATH):
    print(f"FATAL: Whisper model not found at {WHISPER_MODEL_PATH}")
    sys.exit(1)

print("\n✅ ASR (whisper.cpp) initialized successfully.")


# --- 3. VAD (Voice Activity Detection) Logic ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK = 1024 # Number of frames per buffer
NUM_SILENT_CHUNKS = int((SILENCE_DURATION * SAMPLE_RATE) / CHUNK)

stop_event = threading.Event()

def transcribe_with_whispercpp(audio_data_np: np.ndarray):
    """
    Takes a numpy array of audio data, saves it to a temp file,
    and transcribes it with the whisper.cpp model.
    """
    if audio_data_np.size == 0:
        print("Received empty audio data.")
        return

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    try:
        write(temp_file.name, SAMPLE_RATE, audio_data_np)
        temp_file.close()
        audio_file_path = temp_file.name
        
    except Exception as e:
        print(f"ASR Error: Failed to write numpy array to temp file: {e}")
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        return

    start_time = time.time()
    
    # --- THIS IS THE TEST ---
    # We will print the file path so we can test it manually
    print(f"\n[DEBUG] Test file saved at: {audio_file_path}")
    print(f"[DEBUG] Manual test command:")
    print(f"./build/bin/whisper-cli -l en -m ./models/ggml-distil-large-v3.5.bin -otxt {audio_file_path}\n")
    # --- END TEST ---

    command = [
        WHISPER_CPP_MAIN,
        "-l", "en",
        "-m", WHISPER_MODEL_PATH,
        "-otxt",
        audio_file_path  # File as positional argument, not -f
    ]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        
        transcript_file_path = f"{audio_file_path}.txt"
        
        if os.path.exists(transcript_file_path):
            with open(transcript_file_path, 'r', encoding='utf-8') as f:
                transcript = f.read().strip()
            os.unlink(transcript_file_path)
        else:
            transcript = result.stdout.strip() # Fallback

        if transcript:
            end_time = time.time()
            print("\n" + "-"*30)
            print(f"Transcription: {transcript.strip()}")
            print(f"(Time: {end_time - start_time:.2f}s)")
            print("-"*30 + "\n")
        else:
            print("ASR Warning: Received empty transcript from whisper.cpp.")
        
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during whisper.cpp ASR:")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        print(f"Command: {' '.join(command)}")
    except Exception as e:
        print(f"An unknown error occurred during whisper.cpp ASR: {e}")
        import traceback
        traceback.print_exc()
    finally:
       # --- MODIFIED ---
        # We are *not* deleting the file, so we can test it.
        # if os.path.exists(audio_file_path):
        #     try:
        #         os.unlink(audio_file_path)
        #     except Exception as e:
        #         print(f"Warning: Failed to delete temp file {audio_file_path}: {e}")
        pass

def record_and_transcribe():
    """
    Listens for speech using VAD and sends it to the transcriber.
    """
    p = pyaudio.PyAudio()
    audio_stream = None

    try:
        # Check device capabilities first
        device_info = p.get_device_info_by_index(MIC_DEVICE_INDEX)
        print(f"Opening device: {device_info['name']}")
        print(f"  Max input channels: {device_info['maxInputChannels']}")
        print(f"  Default sample rate: {device_info['defaultSampleRate']}")
        
        # Verify device supports our requirements
        if device_info['maxInputChannels'] < CHANNELS:
            print(f"FATAL: Device only supports {device_info['maxInputChannels']} input channels, but {CHANNELS} requested")
            p.terminate()
            return
        
        # Try to open with explicit parameters
        try:
            audio_stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK,
                input_device_index=MIC_DEVICE_INDEX
            )
        except IOError as e:
            # If opening with device index fails, try without specifying device (use default)
            print(f"Warning: Failed to open device {MIC_DEVICE_INDEX}, trying default device...")
            print(f"  Error: {e}")
            audio_stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            print("  Using default input device instead")
    except IOError as e:
        print(f"FATAL: Could not open audio stream: {e}")
        print(f"  Tried: {CHANNELS} channels, {SAMPLE_RATE} Hz, device {MIC_DEVICE_INDEX}")
        p.terminate()
        return
    except Exception as e:
        print(f"FATAL: Unexpected error opening audio stream: {e}")
        import traceback
        traceback.print_exc()
        p.terminate()
        return

    print("\n--- Starting Test ---")
    print("Listening... (Speak to begin recording)")

    silent_chunks = 0
    is_speaking = False
    audio_buffer = []

    while not stop_event.is_set():
        try:
            pcm_data = audio_stream.read(CHUNK, exception_on_overflow=False)
            np_data = np.frombuffer(pcm_data, dtype=np.int16)
            
            volume = np.linalg.norm(np_data) * 10
            
            if volume > SILENCE_THRESHOLD:
                if not is_speaking:
                    is_speaking = True
                    print(f"\n(Volume: {int(volume)})\tSpeech detected, recording...", end="", flush=True)
                
                print(".", end="", flush=True)
                silent_chunks = 0
                audio_buffer.append(np_data)
                
            elif is_speaking:
                silent_chunks += 1
                audio_buffer.append(np_data)
                
                if silent_chunks > NUM_SILENT_CHUNKS:
                    print("\nCommand recorded (silence detected). Transcribing...")
                    full_command_audio = np.concatenate(audio_buffer)
                    
                    threading.Thread(
                        target=transcribe_with_whispercpp,
                        args=(full_command_audio,)
                    ).start()
                    
                    is_speaking = False
                    silent_chunks = 0
                    audio_buffer.clear()
                    print("Listening... (Speak to begin recording)")

        except KeyboardInterrupt:
            print("\nInterrupt received, shutting down...")
            stop_event.set()
        except IOError as e:
            if e.errno == -9988:
                print("Audio overflow, skipping chunk.")
            else:
                raise

    # Cleanup
    print("Stopping audio stream...")
    audio_stream.stop_stream()
    audio_stream.close()
    p.terminate()

# --- 4. Run the Test ---
if __name__ == "__main__":
    record_and_transcribe()