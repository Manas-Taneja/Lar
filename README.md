# Lar - Your Personal Voice Assistant

Lar is a Python-based, voice-activated AI assistant that listens to your voice, transcribes it in real time, and responds intelligently to your prompts. It's designed to be a modular and extensible platform for creating your own personalized voice assistant.

## Features

- **Voice-Activated**: Listens for your voice and automatically starts recording when it detects speech.
- **Real-Time Transcription**: Uses a local Whisper.cpp model for fast and accurate speech-to-text.
- **Intelligent Responses**: Powered by Google's Gemini family of models to provide helpful and conversational answers.
- **Fastpath Commands**: Bypasses the LLM for common commands to give you instant responses for actions like checking the time or weather.
- **"Humanized" TTS**: Adds filler words and natural pauses to make the text-to-speech output sound more human and less robotic.
- **Modular Architecture**: Built with a clean and organized structure, making it easy to add new features and integrations.

## Getting Started

Follow these instructions to get Lar up and running on your local machine.

### Prerequisites

- Python 3.10+
- A working microphone
- `ffmpeg` installed on your system

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd Lar
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API keys:**
    - Create a `.env` file in the root of the project.
    - Add your Google API key to the `.env` file:
      ```
      GOOGLE_API_KEY="your-api-key-here"
      ```

5.  **Download the TTS and ASR models:**
    - Instructions on where to download the Piper and Whisper models will be added here.

### Running Lar

To run the main application, execute the following command:

```bash
python main.py
```

## Key Components

The project is organized into the following modules:

-   `main.py`: The main entry point for the application. It handles the main loop, listening for voice input, and orchestrating the other modules.
-   `config.py`: Contains all the configuration settings for the project, such as API keys, model paths, and audio settings.
-   `modules/asr.py`: Handles the automatic speech recognition (ASR) using the Whisper.cpp model.
-   `modules/tts.py`: Manages the text-to-speech (TTS) engine, converting the AI's responses into spoken words.
-   `modules/llm_handler.py`: Interfaces with the Google Gemini API to generate intelligent responses.
-   `modules/core_logic.py`: Contains the core logic for processing user prompts and routing them to the appropriate handler (either the fastpath or the LLM).
-   `modules/fastpath.py`: Defines a set of simple commands that can be handled without needing to call the LLM.
-   `modules/utils.py`: A collection of utility functions used throughout the project.

## Configuration

All the settings for Lar are located in the `config.py` file. Here, you can change the paths to your models, set the sample rate for your microphone, and more.
