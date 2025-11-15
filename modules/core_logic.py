# modules/core_logic.py
import sys

# --- MODIFIED IMPORTS ---
try:
    from modules.fastpath import COMMANDS, SINGLE_WORD_TRIGGERS, PREFIX_COMMANDS
except ImportError as e:
    print(f"FATAL: core_logic.py could not import from modules.fastpath: {e}")
    sys.exit(1)

def get_prompt_handler_type(user_prompt: str) -> str:
    """
    Checks the prompt against fastpath commands to determine the handler type.
    Returns 'fastpath' or 'llm'.
    """
    clean_prompt = user_prompt.strip(" .?!,").lower()
    
    # 1. Check for single-word exact matches
    if clean_prompt in SINGLE_WORD_TRIGGERS:
        return 'fastpath'
    
    # 2. Check for prefix commands
    #    We check longer prefixes first (e.g., "search for" before "search")
    for prefix in sorted(PREFIX_COMMANDS.keys(), key=len, reverse=True):
        # --- THIS IS THE FIX ---
        # Check if the prompt IS the prefix OR starts with the prefix + space
        if clean_prompt == prefix or clean_prompt.startswith(prefix + " "):
            return 'fastpath'
        # --- END FIX ---
            
    # 3. Check multi-word keyword commands
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            if all(keyword in clean_prompt for keyword in keyword_tuple):
                return 'fastpath'
                
    # If no match, it's an LLM prompt
    return 'llm'

def process_prompt(user_prompt: str) -> str | None:
    """
    Processes the prompt against the fastpath command registry.
    Returns the command's response string or None if no match is found.
    """
    clean_prompt = user_prompt.strip(" .?!,").lower()
    
    # 1. Check for single-word exact matches
    if clean_prompt in SINGLE_WORD_TRIGGERS:
        function = SINGLE_WORD_TRIGGERS[clean_prompt]
        return function(user_prompt)
    
    # 2. Check for prefix commands
    for prefix in sorted(PREFIX_COMMANDS.keys(), key=len, reverse=True):
        # --- THIS IS THE FIX ---
        # Check if the prompt IS the prefix OR starts with the prefix + space
        if clean_prompt == prefix or clean_prompt.startswith(prefix + " "):
            function = PREFIX_COMMANDS[prefix]
            return function(user_prompt)
        # --- END FIX ---
            
    # 3. Check multi-word keyword commands
    for function, keyword_tuples in COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            if all(keyword in clean_prompt for keyword in keyword_tuple):
                return function(user_prompt)
    
    # If no fastpath command matched, return None
    return None