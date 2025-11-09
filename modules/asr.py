# modules/asr.py
import sys
import os
import time
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

def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribes audio using the Sarvam.ai Speech-to-Text API.
    """
    if not client:
        print("ASR Error: Sarvam.ai client not initialized.")
        return ""
        
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
                language_code="en-IN" # <-- MODIFIED
            )
        
        transcript = response.transcript
        
        if transcript:
            end_time = time.time()
            print(f"Transcription: '{transcript}' (Time: {end_time - start_time:.2f}s)")
            return transcript.strip()
        else:
            print("ASR Warning: Received empty transcript from API.")
            return ""

    except Exception as e:
        print(f"An error occurred during Sarvam.ai ASR: {e}")
        return ""

if __name__ == '__main__':
    # Test block
    print("--- Testing ASR (Sarvam.ai) Module ---")
    if os.path.exists(config.RECORDING_PATH):
        transcription = transcribe_audio(config.RECORDING_PATH)
        print(f"Test Transcription: {transcription}")
    else:
        print(f"Test file not found at {config.RECORDING_PATH}. Run main.py to create one.")