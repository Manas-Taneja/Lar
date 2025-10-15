import chainlit as cl
import asyncio
import threading
import os
import sys
import random

# --- Project Path Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
except NameError:
    script_dir = os.getcwd()
    if script_dir not in sys.path:
        sys.path.append(script_dir)

# --- Audio Recording Settings ---
SILENCE_THRESHOLD = 40
SILENCE_DURATION = 1.0
MIC_DEVICE_INDEX = 8

# --- Module Imports ---
try:
    import config
    # --- CORRECTED IMPORT ---
    from modules.tts import TTS_Server
    from modules.asr import transcribe_audio
    from modules.core_logic import process_prompt, get_prompt_handler_type
    from modules.utils import humanize_text, sanitize_text_for_tts, THINKING_PHRASES
    from main import listen_for_speech, stop_event
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# --- Global TTS Server Instance ---
tts_server = None

def voice_loop():
    """Handles the continuous voice interaction loop in a background thread."""
    global tts_server
    main_loop = asyncio.get_event_loop()
    while not stop_event.is_set():
        audio_file = listen_for_speech(
            threshold=SILENCE_THRESHOLD,
            duration=SILENCE_DURATION,
            device_index=MIC_DEVICE_INDEX
        )
        if stop_event.is_set() or not audio_file:
            continue
            
        user_prompt = transcribe_audio(audio_file).lower()
        if not user_prompt or not user_prompt.strip():
            continue

        asyncio.run_coroutine_threadsafe(
            cl.Message(content=user_prompt, author="You").send(), main_loop
        )
        
        handler_type = get_prompt_handler_type(user_prompt)

        if handler_type == 'llm':
            tts_server.speak(random.choice(THINKING_PHRASES))
        
        response_text = process_prompt(user_prompt)
        sanitized_response = sanitize_text_for_tts(response_text)
        final_response = humanize_text(sanitized_response)
        
        asyncio.run_coroutine_threadsafe(
            cl.Message(content=final_response, author="Lar").send(), main_loop
        )
        tts_server.speak(final_response)

@cl.on_chat_start
def start():
    """Initializes the application and starts the voice loop."""
    global tts_server
    import sounddevice as sd
    sd.default.device = MIC_DEVICE_INDEX
    
    # Initialize TTS Server if it's not already running
    if tts_server is None:
        tts_server = TTS_Server()

    if cl.user_session.get("voice_thread") is None:
        thread = threading.Thread(target=voice_loop, daemon=True)
        thread.start()
        cl.user_session.set('voice_thread', thread)
        
    asyncio.run(cl.Message(content="Lar is online. I'm listening...").send())
    tts_server.speak("Lar is online and ready.")

@cl.on_message
async def main(message: cl.Message):
    """Handles text-based input from the Chainlit UI."""
    user_prompt = message.content
    
    response_text = process_prompt(user_prompt)
    sanitized_response = sanitize_text_for_tts(response_text)
    final_response = humanize_text(sanitized_response, chance=0.0)
    
    await cl.Message(content=final_response, author="Lar").send()
    
    tts_server.speak(final_response)

@cl.on_chat_end
def end():
    """Handles the shutdown signal."""
    global tts_server
    stop_event.set()
    if tts_server:
        tts_server.shutdown()
        tts_server = None