# modules/post_llm_tools.py
import subprocess

# --- Media Control Logic (Moved from fastpath) ---

MEDIA_COMMANDS = {
    "play": ["playerctl", "--player=spotify", "play"],
    "pause": ["playerctl", "--player=spotify", "pause"],
    "stop": ["playerctl", "--player=spotify", "stop"],
    "next": ["playerctl", "--player=spotify", "next"],
    "previous": ["playerctl", "--player=spotify", "previous"],
    "toggle": ["playerctl", "--player=spotify", "play-pause"]
}

def execute_media_control(text: str):
    """
    Finds and executes a media command based on keywords.
    This function does NOT return a string, as TTS is handled by the LLM.
    """
    cmd = None
    action = ""
    
    if "next" in text:
        cmd = MEDIA_COMMANDS["next"]
        action = "Executing: Next track."
    elif "previous" in text or "last" in text:
        cmd = MEDIA_COMMANDS["previous"]
        action = "Executing: Previous track."
    elif "play" in text and "pause" in text:
        cmd = MEDIA_COMMANDS["toggle"]
        action = "Executing: Toggle play/pause."
    elif "play" in text or "resume" in text:
         cmd = MEDIA_COMMANDS["play"]
         action = "Executing: Play."
    elif "pause" in text:
        cmd = MEDIA_COMMANDS["pause"]
        action = "Executing: Pause."
    elif "stop" in text:
        cmd = MEDIA_COMMANDS["stop"]
        action = "Executing: Stop."
    else:
        # Check for generic keywords if no specific command found
        if any(kw in text for kw in ["music", "spotify", "song", "track"]):
             cmd = MEDIA_COMMANDS["toggle"]
             action = "Executing: Toggle play/pause."

    if cmd:
        try:
            print(action)
            subprocess.Popen(cmd)
        except Exception as e:
            print(f"Post-LLM media control error: {e}")

# --- Post-LLM Tool Registry ---

# Maps a function to a list of keyword tuples.
POST_LLM_COMMANDS = {
    execute_media_control: [
        ("play", "music"),
        ("pause", "music"),
        ("resume", "music"),
        ("stop", "music"),
        ("next", "song"),
        ("previous", "song"),
        ("last", "song"),
        ("next", "track"),
        ("previous", "track"),
        ("toggle", "music"),
        ("play", "spotify"),
        ("pause", "spotify"),
    ]
}

def run_post_llm_actions(user_prompt: str):
    """
    Iterates through registered post-LLM commands and executes the first match.
    """
    for function, keyword_tuples in POST_LLM_COMMANDS.items():
        for keyword_tuple in keyword_tuples:
            if all(keyword in user_prompt for keyword in keyword_tuple):
                # Execute the matched function
                function(user_prompt)
                return # Stop after first match