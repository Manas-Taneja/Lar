# lar.py
import sys
import os
import signal
import random

# --- Project Path Setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# --- Audio Recording Settings ---
SILENCE_THRESHOLD = 40
SILENCE_DURATION = 1.0
MIC_DEVICE_INDEX = 8 

# --- Module Imports ---
try:
    from main import listen_for_speech, stop_event, signal_handler
    from modules.asr import transcribe_audio
    from modules.llm_handler import query_llm_stream
    from modules.core_logic import get_prompt_handler_type, process_prompt
    # --- New Import ---
    from modules.post_llm_tools import run_post_llm_actions
    from modules.tts import TTS_Server
    from modules.utils import THINKING_PHRASES, humanize_text
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main_loop(tts_server):
    """Handles the primary, continuous voice interaction loop."""
    tts_server.speak("Lar is online and ready.")
    
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
        
        print(f"You: {user_prompt}")
        handler_type = get_prompt_handler_type(user_prompt)

        if handler_type == 'llm':
            tts_server.speak(random.choice(THINKING_PHRASES))
            
            is_first_sentence = True
            sentence_generator = query_llm_stream(user_prompt)
            
            for sentence in sentence_generator:
                if is_first_sentence:
                    final_sentence = humanize_text(sentence)
                    is_first_sentence = False
                else:
                    final_sentence = sentence
                
                tts_server.speak(final_sentence)
            
            # --- ADDED: Run post-LLM actions ---
            run_post_llm_actions(user_prompt)

        elif handler_type == 'fastpath':
            response_text = process_prompt(user_prompt) 
            if response_text:
                tts_server.speak(response_text)

if __name__ == "__main__":
    import sounddevice as sd
    sd.default.device = MIC_DEVICE_INDEX

    signal.signal(signal.SIGINT, signal_handler)
    
    tts_server = TTS_Server()
    
    try:
        print("Starting Lar in command-line mode...")
        main_loop(tts_server)
    finally:
        tts_server.shutdown()
        print("Lar has shut down.")