# chainlit_app.py
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
    from modules.tts import TTS_Server
    from modules.asr import transcribe_audio
    from modules.core_logic import process_prompt, get_prompt_handler_type
    # --- New/Modified Imports ---
    from modules.llm_handler import query_llm_stream
    from modules.post_llm_tools import run_post_llm_actions
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
    if not main_loop:
        main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(main_loop)
        
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
            
            # --- CORRECTED: LLM Streaming Logic ---
            is_first_sentence = True
            sentence_generator = query_llm_stream(user_prompt)
            
            for sentence in sentence_generator:
                if is_first_sentence:
                    final_sentence = humanize_text(sentence)
                    is_first_sentence = False
                else:
                    final_sentence = sentence
                
                # Send sentence to Chainlit UI as it's generated
                asyncio.run_coroutine_threadsafe(
                    cl.Message(content=final_sentence, author="Lar").send(), main_loop
                )
                tts_server.speak(final_sentence)
            
            # --- ADDED: Run post-LLM action ---
            run_post_llm_actions(user_prompt)

        elif handler_type == 'fastpath':
            # --- Fastpath Logic (Original) ---
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
    
    if tts_server is None:
        tts_server = TTS_Server()

    if cl.user_session.get("voice_thread") is None:
        # Ensure the loop runs in a context with an event loop
        loop = asyncio.get_event_loop()
        cl.user_session.set("main_loop", loop)
        
        thread = threading.Thread(target=voice_loop, daemon=True)
        thread.start()
        cl.user_session.set('voice_thread', thread)
        
    asyncio.run(cl.Message(content="Lar is online. I'm listening...").send())
    tts_server.speak("Lar is online and ready.")

@cl.on_message
async def main(message: cl.Message):
    """Handles text-based input from the Chainlit UI."""
    user_prompt = message.content
    
    handler_type = get_prompt_handler_type(user_prompt)
    
    if handler_type == 'llm':
        # --- CORRECTED: LLM Streaming for Text ---
        msg = cl.Message(content="", author="Lar")
        await msg.send()
        
        sentence_generator = query_llm_stream(user_prompt)
        full_response = "" # Accumulate for TTS
        
        for sentence in sentence_generator:
            sanitized = sanitize_text_for_tts(sentence)
            # No filler words for text responses
            final_sentence_part = humanize_text(sanitized, chance=0.0) 
            
            await msg.stream_token(final_sentence_part + " ")
            full_response += final_sentence_part + " "
        
        await msg.update()
        
        # Speak the full response at the end for text
        tts_server.speak(full_response)
        
        # --- ADDED: Run post-LLM action ---
        run_post_llm_actions(user_prompt)

    elif handler_type == 'fastpath':
        # --- Fastpath Logic (Original) ---
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