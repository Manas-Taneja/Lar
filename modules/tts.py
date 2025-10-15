# modules/tts.py
import subprocess
import sys
import os

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

class TTS_Server:
    """
    Manages a persistent Piper TTS process for low-latency speech synthesis.
    """
    def __init__(self):
        self.piper_process = None
        self.aplay_process = None
        
        piper_command = [
            config.PIPER_PATH,
            '--model', config.PIPER_MODEL_PATH,
            '--output-raw'
        ]
        
        # --- MODIFICATION ---
        # Use the absolute path to aplay to avoid PATH issues.
        # Replace '/usr/bin/aplay' if your `which aplay` command showed a different path.
        aplay_command = [
            '/usr/bin/aplay', # <--- Use absolute path here
            '-r', '22050',
            '-f', 'S16_LE',
            '-c', '1'
        ]

        try:
            self.piper_process = subprocess.Popen(
                piper_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )
            self.aplay_process = subprocess.Popen(
                aplay_command,
                stdin=self.piper_process.stdout,
                stderr=subprocess.DEVNULL
            )
            print("TTS Server initialized successfully.")
        except FileNotFoundError:
            # This error is now more specific.
            print("Error: '/usr/bin/aplay' or Piper executable not found. Check the path.")
            self.shutdown()
            sys.exit(1)
        except Exception as e:
            print(f"Failed to initialize TTS Server: {e}")
            self.shutdown()
            sys.exit(1)

    def speak(self, text: str):
        """
        Sends text to the running Piper process to be spoken.
        """
        if not self.piper_process or not self.piper_process.stdin:
            print("TTS Error: Piper process is not running.")
            return
        if not text:
            return
        
        print(f"Lar: {text}")
        try:
            text_with_newline = (text + '\n').encode('utf-8')
            self.piper_process.stdin.write(text_with_newline)
            self.piper_process.stdin.flush()
        except BrokenPipeError:
            print("TTS Error: Pipe to Piper process is broken. Restarting might be necessary.")
        except Exception as e:
            print(f"An error occurred during TTS speak: {e}")

    def shutdown(self):
        """
        Terminates the Piper and aplay processes gracefully.
        """
        print("Shutting down TTS Server...")
        if self.piper_process:
            self.piper_process.terminate()
        if self.aplay_process:
            self.aplay_process.terminate()
        
        if self.piper_process:
            self.piper_process.wait()
        if self.aplay_process:
            self.aplay_process.wait()

if __name__ == '__main__':
    print("--- Testing TTS Server Module ---")
    tts = TTS_Server()
    try:
        tts.speak("If you can hear this, the persistent TTS server is working.")
        tts.speak("This second sentence should play almost instantly.")
    finally:
        tts.shutdown()