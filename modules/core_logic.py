# modules/core_logic.py

from modules.fastpath import COMMANDS
from modules.llm_handler import query_llm

def process_prompt(user_prompt: str) -> str:
    """
    Takes a transcribed prompt and returns a response from fastpath or LLM.
    This is the central routing logic for the assistant.
    """
    response = None
    
    # --- New, Flexible Fastpath Router Logic ---
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            # Check if all keywords in the tuple are in the prompt
            if all(keyword in user_prompt for keyword in keyword_tuple):
                response = function(user_prompt)
                break # Exit the inner loop once a match is found
        if response:
            break # Exit the outer loop if a response was generated

    # --- LLM Fallback ---
    if response is None:
        response = query_llm(user_prompt)

    return response