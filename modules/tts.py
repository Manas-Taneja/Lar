# modules/tts.py

import subprocess
import sys
import os
import soundfile as sf
import sounddevice as sd
import uuid

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

def speak(text: str):
    """
    Synthesizes text to a temporary WAV file using the Piper CLI
    and plays it. This is the most reliable method.
    """
    if not text:
        print("TTS: Received empty text. Nothing to speak.")
        return

    print(f"Lar: {text}")
    
    # Generate a unique path for the temporary audio file
    temp_file_path = os.path.join(project_root, "audio", f"output_{uuid.uuid4()}.wav")
    
    # Build the command to call the Piper executable
    piper_command = [
        config.PIPER_PATH,
        '--model', config.PIPER_MODEL_PATH,
        '--output_file', temp_file_path
    ]

    try:
        # 1. Generate the audio file by calling the Piper CLI
        # We pipe the text into the process's standard input.
        subprocess.run(piper_command, input=text.encode('utf-8'), check=True)
        
        # 2. Play the generated file (the method we know works)
        if os.path.exists(temp_file_path):
            data, fs = sf.read(temp_file_path)
            sd.play(data, fs)
            sd.wait()

    except subprocess.CalledProcessError as e:
        print(f"Error: Piper CLI failed to generate audio. Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
    except Exception as e:
        print(f"An error occurred during TTS: {e}")
    finally:
        # 3. Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == '__main__':
    print("--- Testing TTS Module (CLI-based, Robust Method) ---")
    speak("If you can hear this, the command-line based TTS is working.")