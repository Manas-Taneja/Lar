import subprocess
import sys
import os
import soundfile as sf
import sounddevice as sd

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
    Synthesizes text to an audio file using Piper, then plays it using
    the sounddevice library, avoiding command-line players.
    """
    if not text:
        print("TTS: Received empty text. Nothing to speak.")
        return

    print(f"Lar: {text}")
    
    output_path = "output.wav"

    piper_command = [
        config.PIPER_PATH,
        '--model', config.PIPER_MODEL_PATH,
        '--output_file', output_path
    ]

    try:
        # 1. Generate the audio file from text using Piper
        piper_process = subprocess.Popen(piper_command, stdin=subprocess.PIPE)
        piper_process.communicate(input=text.encode('utf-8'))
        
        if not os.path.exists(output_path):
            print("ERROR: Piper failed to generate the audio file.")
            return

        # 2. Play the audio file using pure Python libraries
        data, fs = sf.read(output_path, dtype='float32')
        sd.play(data, fs)
        sd.wait()  # Wait until the sound has finished playing

    except Exception as e:
        print(f"An error occurred during TTS: {e}")

if __name__ == '__main__':
    print("--- Testing TTS Module (Pure Python Playback) ---")
    test_sentence = "If you can hear this, the pure Python audio playback is working."
    speak(test_sentence)