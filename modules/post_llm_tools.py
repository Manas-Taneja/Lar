# modules/post_llm_tools.py
import subprocess
import re

# --- MODIFIED: Import all fastpath handlers ---
# We will re-use the functions you've already built.
from modules.fastpath import (
    handle_time_query,
    handle_program_launch,
    handle_web_search,
    handle_volume_control,
    handle_media_control,
    handle_weather_query,
    handle_news_query
)

# --- MODIFIED: Post-LLM Tool Registry ---

# This registry now maps the *actual* fastpath functions
# to the keywords that should trigger them *after* an LLM response.
# This allows the LLM to "delegate" tasks.
# The keyword list is copied from modules/fastpath/__init__.py for simplicity.
POST_LLM_COMMANDS = {
    # Note: Time is usually handled by LLM, but we add it for completeness.
    handle_time_query: [
        ("what", "time"), 
        ("current", "time"), 
        ("the", "time")
    ],
    
    handle_program_launch: [
        ("open", "firefox"), ("launch", "firefox"),
        ("open", "browser"), ("launch", "browser"),
        ("open", "brave"), ("launch", "brave"),
        ("open", "terminal"), ("launch", "terminal"),
        ("open", "console"), ("launch", "console"),
        ("open", "code"), ("launch", "code"),
        ("open", "visual studio"), ("launch", "visual studio"),
        ("open", "cursor"), ("launch", "cursor"),
        ("open", "spotify"), ("launch", "spotify")
    ],
    
    handle_web_search: [
        ("look", "up"),
        ("search", "for"),
        ("find", "information on") # Added an extra trigger
    ],
    
    handle_volume_control: [
        ("volume",),
        ("set", "volume"),
        ("turn", "up"),
        ("turn", "down"),
        ("mute",),
        ("unmute",)
    ],
    
    handle_media_control: [
        # --- Using the same comprehensive list from fastpath ---
        ("play",), ("pause",), ("resume",), ("stop",), ("next",), ("previous",),
        ("play", "music"), ("pause", "music"),
        ("resume", "music"), ("stop", "music"),
        ("next", "song"), ("previous", "song"),
        ("last", "song"), ("next", "track"),
        ("previous", "track"), ("toggle", "music"),
        ("play", "spotify"), ("pause", "spotify"),
    ],
    
    handle_weather_query: [
        ("what", "weather"),
        ("today's", "forecast"),
        ("the", "weather")
    ],
    
    handle_news_query: [
        ("what", "news"),
        ("headlines",),
        ("top", "story")
    ]
}

def run_post_llm_actions(user_prompt: str):
    """
    Iterates through registered commands and executes the first match
    by calling the appropriate fastpath handler.

    These functions (e.g., handle_media_control) now return None or an 
    error string, which we will *not* speak, as the LLM has 
    already handled the verbal response.
    """
    prompt = user_prompt.lower()
    
    for function, keyword_tuples in POST_LLM_COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            if all(keyword in prompt for keyword in keyword_tuple):
                print(f"[Post-LLM] Matched prompt '{prompt}'")
                print(f"[Post-LLM] Executing tool: {function.__name__}")
                try:
                    # Execute the matched function from fastpath
                    # We don't need the return value for TTS.
                    function(prompt)
                except Exception as e:
                    print(f"[Post-LLM] Error executing {function.__name__}: {e}")
                return # Stop after first match