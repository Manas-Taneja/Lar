# modules/core_logic.py

# --- MODIFIED IMPORT ---
# Import from the new fastpath package's __init__.py
from modules.fastpath import COMMANDS 

# Single-word exact-match triggers to prevent greedy word matching
SINGLE_WORD_TRIGGERS = {
    ("play",), ("pause",), ("stop",), ("resume",), ("next",), ("previous",),
    ("mute",), ("unmute",), ("headlines",)
}

def get_prompt_handler_type(user_prompt: str) -> str:
    """
    Checks the prompt against the fastpath commands to determine the handler type.
    Returns 'fastpath' or 'llm'.
    
    First checks for single-word exact matches to prevent greedy word matching.
    Then checks multi-word commands.
    """
    # Clean and normalize the prompt
    clean_prompt = user_prompt.strip(" .?!,").lower()
    prompt_words = clean_prompt.split()
    
    # First check for single-word exact matches
    if tuple(prompt_words) in SINGLE_WORD_TRIGGERS:
        return 'fastpath'
    
    # Then check multi-word commands
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            # Skip single-word triggers (already checked above)
            if len(keyword_tuple) == 1:
                continue
            # Check if all keywords in the tuple are present in the prompt
            if all(keyword in clean_prompt for keyword in keyword_tuple):
                return 'fastpath'
    return 'llm'

def process_prompt(user_prompt: str) -> str | None:
    """
    Processes the prompt against the fastpath command registry.
    Returns the command's response string or None if no match is found.
    """
    # Clean and normalize the prompt
    clean_prompt = user_prompt.strip(" .?!,").lower()
    prompt_words = clean_prompt.split()
    
    # First check for single-word exact matches
    if tuple(prompt_words) in SINGLE_WORD_TRIGGERS:
        # Find the matching function for this single-word trigger
        for function, keyword_tuples in COMMANDS.items():
            for keyword_tuple in keyword_tuples:
                if keyword_tuple == tuple(prompt_words):
                    return function(user_prompt)
    
    # Then check multi-word commands
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            # Skip single-word triggers (already checked above)
            if len(keyword_tuple) == 1:
                continue
            if all(keyword in clean_prompt for keyword in keyword_tuple):
                # Execute the matched function and return its result
                return function(user_prompt)
    
    # If no fastpath command matched, return None
    return None