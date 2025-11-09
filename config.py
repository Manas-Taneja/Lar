import os
from dotenv import load_dotenv

load_dotenv()
# --- Project Root ---
# Get the absolute path of the project's root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Audio Settings ---
RECORDING_PATH = os.path.join(PROJECT_ROOT, "audio", "prompt.wav")
SAMPLE_RATE = 16000

# --- ASR ---
RECORDING_PATH = os.path.join(os.getcwd(), "assets", "audio", "temp_recording.wav")
SAMPLE_RATE = 16000 # Sarvam API works best with 16kHz
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# --- TTS (Piper) ---
PIPER_PATH = os.path.join(PROJECT_ROOT, "tools", "piper", "piper")
PIPER_MODEL_PATH = os.path.join(PROJECT_ROOT, "tools", "piper", "en_GB-cori-medium.onnx")
PIPER_CONFIG_PATH = os.path.join(PROJECT_ROOT, "tools", "piper", "en_GB-cori-medium.onnx.json")

# --- LLM ---
# The model name for the Gemini API
LLM_MODEL_NAME = "gemini-2.5-flash"

# --- Voice Activity Detection (VAD) Settings ---
SILENCE_THRESHOLD = 2000000
SILENCE_DURATION = 1.0
MIC_DEVICE_INDEX = 8

# --- Wake Word (Porcupine) Settings ---
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "YOUR_PICOVOICE_ACCESS_KEY_HERE")

# Path to the .ppn keyword file
PORCUPINE_KEYWORD_PATH = os.path.join(PROJECT_ROOT, "assets", "keywords", "heylar_linux.ppn")

# Sensitivity of the wake word engine (float between 0 and 1)
PORCUPINE_SENSITIVITY = 0.5