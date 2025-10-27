# modules/fastpath/desktop.py
import subprocess
import urllib.parse

# --- Program Launch Logic ---
PROGRAM_REGISTRY = {
    "firefox": "brave",
    "browser": "brave",
    "brave": "brave",
    "terminal": "gnome-terminal",
    "console": "gnome-terminal",
    "code": "cursor",
    "visual studio": "cursor",
    "cursor": "cursor"
}

def handle_program_launch(text: str) -> str:
    """Launches a program from the PROGRAM_REGISTRY."""
    for trigger, command in PROGRAM_REGISTRY.items():
        if trigger in text:
            try:
                subprocess.Popen([command])
                return f"Opening {trigger}."
            except FileNotFoundError:
                return f"Error: The command '{command}' was not found on your system."
            except Exception as e:
                return f"An error occurred: {e}"
    return "I'm not sure which program to open."

# --- Web Search Logic ---
SEARCH_TRIGGERS = [
    "look up",
    "search for"
]

def handle_web_search(text: str) -> str:
    """Performs a web search using Brave."""
    for trigger in SEARCH_TRIGGERS:
        if trigger in text:
            try:
                query_start_index = text.find(trigger) + len(trigger)
                query = text[query_start_index:].strip()
                if not query:
                    return "What would you like me to search for?"
                
                encoded_query = urllib.parse.quote_plus(query)
                search_url = f"https://search.brave.com/search?q={encoded_query}"
                subprocess.Popen(["brave", search_url])
                return f"Searching for {query}."
            except Exception as e:
                return f"An error occurred while searching: {e}"
    return "I'm not sure what to search for."