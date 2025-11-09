# modules/asr.py
import sys
import os
import time
import tempfile
import numpy as np
from scipy.io.wavfile import write
from sarvamai import SarvamAI

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

# --- Sarvam.ai Client Initialization ---
client = None
if config.SARVAM_API_KEY:
    try:
        client = SarvamAI(api_subscription_key=config.SARVAM_API_KEY)
        print("Sarvam.ai ASR client initialized.")
    except Exception as e:
        print(f"Failed to initialize Sarvam.ai client: {e}")
else:
    print("Error: SARVAM_API_KEY not found in config.py or .env file.")
    sys.exit(1)

def transcribe_audio(audio_input: str | np.ndarray) -> str:
    """
    Transcribes audio using the Sarvam.ai Speech-to-Text API.
    Accepts either a file path (str) or a numpy array (np.ndarray).
    """
    if not client:
        print("ASR Error: Sarvam.ai client not initialized.")
        return ""
    
    # Handle numpy array input
    if isinstance(audio_input, np.ndarray):
        # Create a temporary file for the numpy array
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

    print("Transcribing audio via Sarvam.ai...")
    start_time = time.time()

    try:
        with open(audio_file_path, "rb") as audio_file:
            # Call the Sarvam.ai API
            response = client.speech_to_text.transcribe(
                file=audio_file,
                language_code="en-IN"
            )
        
        transcript = response.transcript
        
        if transcript:
            end_time = time.time()
            print(f"Transcription: '{transcript}' (Time: {end_time - start_time:.2f}s)")
            result = transcript.strip()
        else:
            print("ASR Warning: Received empty transcript from API.")
            result = ""
        
        return result

    except Exception as e:
        print(f"An error occurred during Sarvam.ai ASR: {e}")
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
    print("--- Testing ASR (Sarvam.ai) Module ---")
    if os.path.exists(config.RECORDING_PATH):
        transcription = transcribe_audio(config.RECORDING_PATH)
        print(f"Test Transcription: {transcription}")
    else:
        print(f"Test file not found at {config.RECORDING_PATH}. Run main.py to create one.")