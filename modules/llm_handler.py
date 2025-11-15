# modules/llm_handler.py
import requests
import json
import sys
import os

# --- Robust Path Setup ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    # Import sanitize_text_for_tts from utils, not a local copy
    from modules.utils import sanitize_text_for_tts
except ImportError:
    print("Error: Could not import from modules. Check paths.")
    sys.exit(1)

# --- Ollama Configuration ---
OLLAMA_API_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "lar-model"
SYSTEM_PROMPT = "You are Lar, a helpful AI assistant. Your tone is conversational and natural. Use commas to connect related ideas within a sentence. Keep your responses concise and to the point, typically one or two sentences in total."

print(f"LLM Handler (Ollama) initialized. Model: {OLLAMA_MODEL}")

def query_llm_stream(prompt: str, history: list) -> iter:
    """
    Sends a prompt and streams the response from Ollama, yielding sentences.
    This function is a GENERATOR.
    It takes the prompt and the CURRENT history as arguments.
    It yields sentences one by one.
    It RETURNS the UPDATED history.
    """
    
    # 1. Create a local copy of the history and add the system prompt
    #    (This is safer for threaded applications than a global history)
    local_history = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    local_history.extend(history)
    local_history.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": local_history,
        "stream": True
    }

    sentence_buffer = ""
    full_response_text = ""

    try:
        with requests.post(OLLAMA_API_URL, json=payload, stream=True) as response:
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        chunk_text = chunk.get('message', {}).get('content', '')
                        
                        if not chunk_text:
                            continue

                        sentence_buffer += chunk_text
                        full_response_text += chunk_text

                        # Use the same sentence-splitting logic
                        if any(p in sentence_buffer for p in ['.', '?', '!']):
                            processed_buffer = sentence_buffer.replace('?', '?|').replace('!', '!|').replace('.', '.|')
                            parts = processed_buffer.split('|')
                            
                            for i in range(len(parts) - 1):
                                sentence_to_yield = parts[i].strip()
                                if sentence_to_yield:
                                    yield sanitize_text_for_tts(sentence_to_yield)
                            
                            sentence_buffer = parts[-1]
                            
                    except json.JSONDecodeError:
                        print(f"Warning: Received non-JSON line from Ollama: {line}")

        # Yield any remaining text
        if sentence_buffer.strip():
            yield sanitize_text_for_tts(sentence_buffer.strip())
            
        # 2. Add the complete response to the history
        local_history.append({"role": "assistant", "content": full_response_text.strip()})
        
        # 3. Return the updated history (minus the system prompt)
        #    The logic_worker will capture this in StopIteration.value
        return local_history[1:] # Return history without system prompt

    except requests.exceptions.ConnectionError:
        yield "ERROR: Could not connect to Ollama server."
    except Exception as e:
        yield f"An error occurred during LLM stream: {e}"