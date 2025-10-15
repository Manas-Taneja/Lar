import chainlit as cl
import asyncio
import threading
import os
import sys
import random

# --- Corrected and Consolidated Imports ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path:
        sys.path.append(script_dir)
        
    import config
    from modules.tts import speak
    from modules.asr import transcribe_audio
    from modules.llm_handler import query_llm
    # Import the fastpath function directly instead of the dictionary
    from modules.fastpath import handle_time_query 
    from modules.utils import humanize_text, sanitize_text_for_tts, THINKING_PHRASES
    from main import listen_for_speech, stop_event

except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def get_response(user_prompt: str, is_voice_input: bool = False) -> str:
    """
    Central function to get a response from either the fastpath or the LLM.
    This replaces the fragile 'for' loop with a robust 'if' block.
    """
    # --- Robust Fastpath Router ---
    if "what's the time" in user_prompt or \
       "what is the time" in user_prompt or \
       "time right now" in user_prompt:
        return handle_time_query(user_prompt)
    
    # --- LLM Fallback ---
    # Only speak a "thinking" phrase if the input was from voice
    if is_voice_input:
        speak(random.choice(THINKING_PHRASES))
        
    return query_llm(user_prompt)

def voice_loop():
    """Handles the continuous voice interaction loop in a background thread."""
    main_loop = asyncio.get_event_loop()
    while not stop_event.is_set():
        audio_file = listen_for_speech()
        if stop_event.is_set() or not audio_file:
            continue
            
        user_prompt = transcribe_audio(audio_file).lower()
        if not user_prompt or not user_prompt.strip():
            continue

        asyncio.run_coroutine_threadsafe(
            cl.Message(content=user_prompt, author="You").send(), main_loop
        )
        
        # Call the new, robust response function
        response_text = get_response(user_prompt, is_voice_input=True)

        sanitized_response = sanitize_text_for_tts(response_text)
        final_response = humanize_text(sanitized_response)
        
        asyncio.run_coroutine_threadsafe(
            cl.Message(content=final_response, author="Lar").send(), main_loop
        )
        speak(final_response)

@cl.on_chat_start
def start():
    """Initializes the application and starts the voice loop."""
    import sounddevice as sd
    sd.default.device = 8 
    
    if cl.user_session.get("voice_thread") is None:
        thread = threading.Thread(target=voice_loop, daemon=True)
        thread.start()
        cl.user_session.set('voice_thread', thread)
        
    asyncio.run(cl.Message(content="Lar is online. I'm listening...").send())
    speak("Lar is online and ready.")

@cl.on_message
async def main(message: cl.Message):
    """Handles text-based input from the Chainlit UI."""
    user_prompt = message.content
    
    # Call the new, robust response function
    response_text = get_response(user_prompt, is_voice_input=False)

    sanitized_response = sanitize_text_for_tts(response_text)
    final_response = humanize_text(sanitized_response)
    
    await cl.Message(content=final_response, author="Lar").send()
    
    speak(final_response)

@cl.on_chat_end
def end():
    """Handles the shutdown signal."""
    stop_event.set()