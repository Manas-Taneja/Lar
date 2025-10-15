import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    import config
    # Import the sanitizer to clean text before yielding it
    from modules.utils import sanitize_text_for_tts
except ImportError:
    print("Error: config.py not found.")
    sys.exit(1)

load_dotenv()

model = None
chat = None
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("ERROR: GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    
    # --- SIMPLIFIED SYSTEM PROMPT ---
    # This is much shorter to reduce the initial processing delay (TTFT).
    system_instruction = "You are Lar, a helpful AI assistant. Your tone is conversational and natural. Use commas to connect related ideas within a sentence. Keep your responses concise and to the point, typically one or two sentences in total."
    
    model = genai.GenerativeModel(
        model_name=config.LLM_MODEL_NAME,
        system_instruction=system_instruction
    )
    
    chat = model.start_chat(history=[])
    print("LLM Handler initialized successfully.")

except Exception as e:
    print(f"Failed to initialize LLM Handler: {e}")

def query_llm(prompt: str) -> str:
    """
    Non-streaming LLM call. Returns the full response text.
    """
    if not chat:
        return "ERROR: LLM chat session not initialized."
    try:
        response = chat.send_message(prompt)
        return response.text.strip()
    except Exception as e:
        return f"An error occurred while querying the LLM: {e}"

def query_llm_stream(prompt: str):
    """
    Sends a prompt and streams the response, yielding complete, sanitized sentences.
    This is now a generator function.
    """
    if not chat:
        yield "ERROR: LLM chat session not initialized."
        return
    
    try:
        response_stream = chat.send_message(prompt, stream=True)
        sentence_buffer = ""
        
        for chunk in response_stream:
            sentence_buffer += chunk.text
            
            # Use a simple split based on common sentence terminators
            if any(p in sentence_buffer for p in ['.', '?', '!']):
                # Process buffer into speakable parts
                # Preserve terminators by replacing them before splitting
                processed_buffer = sentence_buffer.replace('?', '?|').replace('!', '!|').replace('.', '.|')
                parts = processed_buffer.split('|')
                
                # Yield all complete sentences
                for i in range(len(parts) - 1):
                    sentence_to_yield = parts[i].strip()
                    if sentence_to_yield:
                        yield sanitize_text_for_tts(sentence_to_yield)
                
                # The last part is the new, incomplete sentence
                sentence_buffer = parts[-1]
                
        # Yield any remaining text after the loop
        if sentence_buffer.strip():
            yield sanitize_text_for_tts(sentence_buffer.strip())
            
    except Exception as e:
        yield f"An error occurred during LLM stream: {e}"