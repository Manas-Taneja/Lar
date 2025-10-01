import subprocess
import sys
import os
import sounddevice as sd
import numpy as np
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

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes an audio file using whisper.cpp and returns the text.
    """
    if not os.path.exists(audio_path):
        return "ERROR: Audio file not found."

    print("Transcribing audio...")
    command = [
        config.WHISPER_CPP_PATH,
        '-m', config.WHISPER_MODEL_PATH,
        '-f', audio_path,
        '--output-txt'  # Tell whisper.cpp to output a .txt file
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        
        # Read the transcription from the generated .txt file
        transcription_path = f"{audio_path}.txt"
        with open(transcription_path, 'r') as f:
            transcription = f.read().strip()
            
        # Clean up the generated text file
        os.remove(transcription_path)
        
        print(f"Transcription: '{transcription}'")
        return transcription
        
    except subprocess.CalledProcessError as e:
        print(f"Error during transcription: {e.stderr}")
        return ""
    except FileNotFoundError:
        print("Error: whisper.cpp executable not found at the specified path.")
        return ""

def record_audio(file_path: str, duration=5, samplerate=config.SAMPLE_RATE):
    """Records audio from the default microphone and saves it to a file."""
    print(f"Recording for {duration} seconds... Speak now!")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    write(file_path, samplerate, recording)  # Save as WAV file
    print(f"Recording saved to {file_path}")

if __name__ == '__main__':
    print("--- Testing ASR Module ---")
    audio_file = config.RECORDING_PATH
    
    # 1. Record audio from the microphone
    record_audio(audio_file, duration=5)
    
    # 2. Transcribe the recorded audio
    transcribed_text = transcribe_audio(audio_file)
    
    if transcribed_text:
        print(f"\nSUCCESS: You said: '{transcribed_text}'")
    else:
        print("\nFAILURE: Transcription failed.")