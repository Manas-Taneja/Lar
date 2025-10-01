import sys
import os

try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    import config
except ImportError:
    print("Error: config.py not found.")
    sys.exit(1)

import google.generativeai as genai
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- One-time Initialization ---
model = None
chat = None
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("ERROR: GOOGLE_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    
    system_instruction = "You are Lar, a helpful and concise AI assistant. Your responses should be direct and to the point."
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
    Sends a prompt to the ongoing chat session and returns the response.

    Args:
        prompt: The text prompt to send to the language model.

    Returns:
        The text response from the model, or an error message string.
    """

    if not chat:
        return "ERROR: LLM chat session not initialized."
    
    try:
        response = chat.send_message(prompt)
        return response.text.strip()

    except Exception as e:
        error_message = f"An error occurred while querying the LLM: {e}"
        print(error_message)
        return error_message


if __name__ == '__main__':
    if chat:
        print(f"--- Testing LLM Handler with model: {config.LLM_MODEL_NAME} ---")
        test_prompt = "Explain the concept of inertia in one simple sentence."
        
        print(f"Sending prompt: '{test_prompt}'")
        response = query_llm(test_prompt)
        print("\nReceived response:")
        print(response)

        print("\n--- Testing followup ---")
        test_prompt_2 = "Give me a real world example."
        print(f"Sending prompt: '{test_prompt_2}'")
        response_2 = query_llm(test_prompt_2)
        print("\nReceived response:")
        print(response_2)