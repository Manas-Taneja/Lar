# modules/asr.py
import sys
import os
import time
import tempfile
import numpy as np
import subprocess
from scipy.io.wavfile import write

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

# --- whisper.cpp Configuration ---
print("Initializing ASR (whisper.cpp, distil-large-v3.5)...")

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

print("✅ ASR (whisper.cpp) initialized successfully.")


def transcribe_audio(audio_input: str | np.ndarray) -> str:
    """
    Transcribes audio using the local whisper.cpp executable.
    Accepts either a file path (str) or a numpy array (np.ndarray).
    """
    
    # Handle numpy array input
    if isinstance(audio_input, np.ndarray):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        try:
            write(temp_file.name, config.SAMPLE_RATE, audio_input)
            temp_file.close()
            audio_file_path = temp_file.name
            should_delete = True
        except Exception as e:
            print(f"ASR Error: Failed to write numpy array to temp file: {e}")
            return ""
    else:
        # Handle file path input
        audio_file_path = audio_input
        should_delete = False
        if not os.path.exists(audio_file_path):
            print(f"ASR Error: Audio file not found at {audio_file_path}")
            return ""

    start_time = time.time()

    # --- whisper.cpp Command (Corrected) ---
    command = [
        WHISPER_CPP_MAIN,
        "-l", "en",
        "-m", WHISPER_MODEL_PATH,
        "-otxt",
        "--no-context",
        "-f", audio_file_path  # <-- FIX 1: The -f flag
    ]
    
    # --- Environment Fix (Corrected) ---
    custom_env = os.environ.copy()
    custom_env["LD_LIBRARY_PATH"] = custom_env.get("LD_LIBRARY_PATH", "") + ":/usr/lib/x86_64-linux-gnu/" # <-- FIX 2: The GPU path
    
    try:
        # Run the C++ binary with the fixed environment
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            env=custom_env  # <-- FIX 3: Passing the environment
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
            print(f"Transcription: '{transcript}' (Time: {end_time - start_time:.2f}s)")
            result = transcript
        else:
            print("ASR Warning: Received empty transcript from whisper.cpp.")
            result = ""
        
        return result

    except subprocess.CalledProcessError as e:
        print(f"An error occurred during whisper.cpp ASR:")
        print(f"STDERR: {e.stderr}")
        return ""
    except Exception as e:
        print(f"An unknown error occurred during whisper.cpp ASR: {e}")
        return ""
    finally:
        # Clean up temporary file if we created it
        if should_delete and os.path.exists(audio_file_path):
            try:
                os.unlink(audio_file_path)
            except Exception as e:
                print(f"Warning: Failed to delete temp file {audio_file_path}: {e}")

if __name__ == '__main__':
    # Test block
    print("--- Testing ASR (whisper.cpp) Module ---")
    test_file_path = os.path.join(WHISPER_CPP_DIR, "samples", "jfk.wav")
    
    if os.path.exists(test_file_path):
        print(f"Transcribing test file: {test_file_path}")
        transcription = transcribe_audio(test_file_path)
        print(f"Test Transcription: {transcription}")
    else:
        print(f"Test file not found at {test_file_path}. Cannot run test.")