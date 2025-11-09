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