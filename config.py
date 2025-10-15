import os

# --- Project Root ---
# Get the absolute path of the project's root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# --- Audio Settings ---
RECORDING_PATH = os.path.join(PROJECT_ROOT, "audio", "prompt.wav")
SAMPLE_RATE = 16000

# --- ASR (Whisper) ---
WHISPER_MODEL_NAME = "tiny.en"

# --- TTS (Piper) ---
PIPER_PATH = os.path.join(PROJECT_ROOT, "tools", "piper", "piper")
PIPER_MODEL_PATH = os.path.join(PROJECT_ROOT, "tools", "piper", "en_GB-cori-medium.onnx")
PIPER_CONFIG_PATH = os.path.join(PROJECT_ROOT, "tools", "piper", "en_GB-cori-medium.onnx.json")

# --- LLM ---
# The model name for the Gemini API
LLM_MODEL_NAME = "gemini-2.5-flash"