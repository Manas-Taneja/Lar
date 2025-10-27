# modules/core_logic.py

# --- MODIFIED IMPORT ---
# Import from the new fastpath package's __init__.py
from modules.fastpath import COMMANDS 

def get_prompt_handler_type(user_prompt: str) -> str:
    """
    Checks the prompt against the fastpath commands to determine the handler type.
    Returns 'fastpath' or 'llm'.
    """
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            if all(keyword in user_prompt for keyword in keyword_tuple):
                return 'fastpath'
    return 'llm'

def process_prompt(user_prompt: str) -> str | None:
    """
    Processes the prompt against the fastpath command registry.
    Returns the command's response string or None if no match is found.
    """
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            if all(keyword in user_prompt for keyword in keyword_tuple):
                # Execute the matched function and return its result
                return function(user_prompt)
    
    # If no fastpath command matched, return None
    return None