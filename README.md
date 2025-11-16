# Lar - Your Personal Voice Assistant

Lar is a Python-based, voice-activated AI assistant with wake word detection. It uses a multi-threaded, queue-based architecture for low-latency voice interactions. The assistant listens for a wake word, records your command, transcribes it, and responds intelligently.

## Features

- **Wake Word Detection**: Uses Picovoice Porcupine for hands-free activation (e.g., "Jarvis" or "Hey Lar")
- **Low-Latency Architecture**: Multi-threaded, queue-based design allows parallel processing of audio collection, ASR, and logic processing
- **Local Speech Recognition**: Uses whisper.cpp with distil-large-v3.5 model for fast, accurate, offline speech-to-text
- **Intelligent Responses**: Powered by Google's Gemini 2.5 Flash model with conversational history support
- **Fastpath Commands**: Bypasses the LLM for common commands to give instant responses (time, weather, media control, volume control, etc.)
- **"Humanized" TTS**: Adds filler words and natural pauses to make the text-to-speech output sound more human
- **Self-Trigger Prevention**: Automatically mutes microphone during TTS output to prevent feedback loops
- **Modular Architecture**: Clean, organized structure making it easy to add new features

## Architecture

Lar uses a multi-threaded, producer-consumer architecture:

- **Wake Word Listener Thread**: Continuously listens for wake word using Porcupine
- **VAD Command Recorder**: Records a single command after wake word detection using Voice Activity Detection
- **ASR Worker Thread**: Transcribes audio from queue in parallel
- **Logic Worker Thread**: Processes prompts and routes to fastpath or LLM
- **TTS Worker Thread**: Speaks responses as they're generated

This parallel processing dramatically reduces perceived latency compared to a serial architecture.

## Getting Started

### Prerequisites

- Python 3.10+
- A working microphone
- Picovoice Access Key (free at https://console.picovoice.ai/)
- Google API Key (for Gemini LLM)
- CMake and build tools (for building whisper.cpp)
- CUDA-capable GPU (optional, for faster transcription)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Lar
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up whisper.cpp:**
   - Clone whisper.cpp into the project root:
     ```bash
     git clone https://github.com/ggerganov/whisper.cpp.git
     cd whisper.cpp
     ```
   - Build whisper.cpp:
     ```bash
     mkdir build && cd build
     cmake ..
     make -j$(nproc)
     ```
   - Download the distil-large-v3.5 model:
     ```bash
     cd ..
     bash ./models/download-ggml-model.sh distil-large-v3.5
     ```
   - Verify the build:
     ```bash
     ./build/bin/whisper-cli --help
     ```
   - The model should be at `whisper.cpp/models/ggml-distil-large-v3.5.bin`

5. **Set up your API keys:**
   - Create a `.env` file in the root of the project
   - Add your API keys:
     ```
     GOOGLE_API_KEY=your-google-api-key-here
     PICOVOICE_ACCESS_KEY=your-picovoice-access-key-here
     ```

6. **Download the wake word keyword file:**
   - Download a built-in keyword file (e.g., "Jarvis") from: https://github.com/Picovoice/porcupine/tree/master/resources/keyword_files/linux
   - Place it in `assets/keywords/` directory
   - Update `PORCUPINE_KEYWORD_PATH` in `config.py` if using a different filename

7. **Configure microphone device:**
   - Run `python3 check_mic_index.py` to list available input devices
   - Find your microphone in the list and note its index
   - Update `MIC_DEVICE_INDEX` in `config.py` with the correct index

### Running Lar

To run the main application:

```bash
python3 lar.py
```

The assistant will:
1. Initialize all components
2. Start listening for the wake word
3. When wake word is detected, listen for your command
4. Process and respond to your command
5. Return to listening for the next wake word

## Configuration

All settings are in `config.py`:

- **Audio Settings**: Sample rate, recording paths
- **VAD Settings**: Silence threshold and duration for voice activity detection
- **Microphone**: Device index (use `check_mic_index.py` to find the correct index)
- **Wake Word**: Picovoice access key and keyword file path
- **ASR**: whisper.cpp executable and model paths (configured automatically)
- **TTS**: Piper model paths
- **LLM**: Gemini model name

## Key Components

- **`lar.py`**: Main orchestrator - starts worker threads and handles TTS output
- **`main.py`**: Wake word listener and VAD command recorder using PyAudio and Porcupine
- **`config.py`**: Centralized configuration for all settings
- **`modules/asr.py`**: Speech-to-text using local whisper.cpp (accepts numpy arrays or file paths)
- **`modules/tts.py`**: Text-to-speech using Piper
- **`modules/llm_handler.py`**: Interfaces with Google Gemini API with conversational history support
- **`modules/core_logic.py`**: Routes prompts to fastpath or LLM, prevents greedy word matching
- **`modules/fastpath/`**: Fast command handlers (time, weather, media control, volume control, etc.)
- **`modules/post_llm_tools.py`**: Post-LLM action execution for delegated tasks
- **`modules/utils.py`**: Utility functions (text sanitization, humanization, etc.)

## Troubleshooting

### Wake word not detected
- Check that `PICOVOICE_ACCESS_KEY` is set correctly in `.env`
- Verify the keyword file exists at the path specified in `config.py`
- Try adjusting `PORCUPINE_SENSITIVITY` in `config.py` (0.0 to 1.0)

### No audio input after wake word
- Run `python3 check_mic_index.py` to verify microphone index
- Check that `MIC_DEVICE_INDEX` in `config.py` matches your microphone
- Verify microphone permissions

### TTS not working
- Check that Piper model files exist in `tools/piper/`
- Verify model paths in `config.py`

### ASR errors
- Verify whisper.cpp is built and the executable exists at `whisper.cpp/build/bin/whisper-cli`
- Check that the model file exists at `whisper.cpp/models/ggml-distil-large-v3.5.bin`
- If you see "FATAL: whisper.cpp executable not found", rebuild whisper.cpp following step 4 in Installation
- If transcription is slow, ensure CUDA is properly configured for GPU acceleration
- Test whisper.cpp manually: `./whisper.cpp/build/bin/whisper-cli -m ./whisper.cpp/models/ggml-distil-large-v3.5.bin -f <audio_file.wav>`

## Development

The codebase is organized for easy extension:

- Add new fastpath commands in `modules/fastpath/`
- Modify routing logic in `modules/core_logic.py`
- Customize LLM behavior in `modules/llm_handler.py`
- Adjust VAD sensitivity in `config.py`
