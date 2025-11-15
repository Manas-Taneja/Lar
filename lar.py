# lar.py
import sys
import os
import signal
import random
import queue
import threading
import time
import numpy as np

# --- Project Path Setup ---
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

# --- Module Imports ---
try:
    import config
    # MODIFIED: Import the listener from main.py
    from main import run_wake_word_listener_thread, stop_event, signal_handler
    from modules.asr import transcribe_audio
    from modules.llm_handler import query_llm_stream
    from modules.core_logic import get_prompt_handler_type, process_prompt
    from modules.post_llm_tools import run_post_llm_actions
    from modules.tts import TTS_Server
    from modules.utils import THINKING_PHRASES, humanize_text
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

# --- Global Queues ---
asr_queue = queue.Queue()
logic_queue = queue.Queue()
tts_queue = queue.Queue()

# --- MODIFIED: Global Chat History ---
# This variable will be managed by the logic_worker
chat_history = []

# --- Global TTS Speaking Event (for muting mic) ---
tts_is_speaking_event = threading.Event()

def asr_worker(stop_event):
    """ASR worker thread: transcribes audio from asr_queue and puts text on logic_queue."""
    while not stop_event.is_set():
        try:
            numpy_array = asr_queue.get(timeout=1.0)
            if numpy_array is None: continue # Handle potential None from queue

            text = transcribe_audio(numpy_array).lower()
            if text and text.strip():
                logic_queue.put(text)
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ASR Worker] Error: {e}")
            import traceback
            traceback.print_exc()
            continue

def logic_worker(stop_event):
    """Logic worker thread: processes prompts from logic_queue and puts responses on tts_queue."""
    global chat_history # <-- We will read and write to this global variable
    
    while not stop_event.is_set():
        try:
            user_prompt = logic_queue.get(timeout=1.0)
            print(f"You: {user_prompt}")
            
            handler_type = get_prompt_handler_type(user_prompt)
            
            if handler_type == 'fastpath':
                response_text = process_prompt(user_prompt)
                if response_text:
                    tts_queue.put(response_text)
            
            elif handler_type == 'llm':
                tts_queue.put(random.choice(THINKING_PHRASES))
                
                is_first_sentence = True
                
                # --- MODIFIED LLM CALL ---
                # 1. Pass the current history to the generator
                sentence_generator = query_llm_stream(user_prompt, history=chat_history)
                
                # 2. Iterate through the yielded sentences
                try:
                    while True:
                        sentence = next(sentence_generator)
                        if is_first_sentence:
                            final_sentence = humanize_text(sentence)
                            is_first_sentence = False
                        else:
                            final_sentence = sentence
                        
                        tts_queue.put(final_sentence)
                except StopIteration as e:
                    # 3. Capture the returned history and update the global
                    chat_history = e.value if e.value is not None else chat_history
                    print(f"[Logic Worker] History updated. Length: {len(chat_history)}")
                # --- END MODIFIED LLM CALL ---

                # Run post-LLM actions
                run_post_llm_actions(user_prompt)
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Logic Worker] Error: {e}")
            import traceback
            traceback.print_exc()
            continue

def main_loop(tts_server):
    """
    Main loop: starts worker threads and handles TTS output.
    """
    # Start the wake word listener thread
    threading.Thread(
        target=run_wake_word_listener_thread,
        args=(asr_queue, stop_event, tts_is_speaking_event, config.MIC_DEVICE_INDEX),
        daemon=True
    ).start()
    
    # Start the ASR worker thread
    threading.Thread(
        target=asr_worker,
        args=(stop_event,),
        daemon=True
    ).start()
    
    # Start the Logic worker thread
    threading.Thread(
        target=logic_worker,
        args=(stop_event,),
        daemon=True
    ).start()
    
    # Speak startup message
    tts_server.speak("Lar is online and ready.")
    
    # Main TTS loop: get sentences from tts_queue and speak them
    while not stop_event.is_set():
        sentence_to_speak = None
        try:
            sentence_to_speak = tts_queue.get(timeout=1.0)

            if sentence_to_speak:
                tts_is_speaking_event.set()
                tts_server.speak(sentence_to_speak)

        except queue.Empty:
            continue
        except Exception as e:
            print(f"TTS Worker Error: {e}")
        finally:
            if sentence_to_speak:
                # This logic is correct:
                # Wait for audio to finish playing (approx)
                # A better way would be to estimate audio length, but this is fine.
                time.sleep(0.1) 
                tts_is_speaking_event.clear()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    tts_server = TTS_Server()
    
    try:
        print("Starting Lar in command-line mode...")
        main_loop(tts_server)
    finally:
        tts_server.shutdown()
        print("Lar has shut down.")