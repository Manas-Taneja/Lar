# modules/fastpath/__init__.py

# Import handlers from the new modules
from .system import handle_time_query
from .desktop import handle_program_launch, handle_web_search
# --- MODIFIED IMPORTS ---
from .music import (
    handle_volume_control,  # <-- This is the NEW Spotify volume
    handle_system_volume,   # <-- This is the OLD system volume
    handle_media_control
)
from .web_api import handle_weather_query, handle_news_query

# --- Master Command Registry (for multi-word commands) ---
COMMANDS = {
    handle_time_query: [
        ("what", "time"), 
        ("current", "time"), 
        ("the", "time")
    ],
    
    handle_media_control: [
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
        ("top", "story")
    ],

    # --- NEW: System Volume Triggers ---
    handle_system_volume: [
        ("system", "mute"),
        ("system", "unmute"),
        ("master", "volume"),
    ]
}

# --- MODIFIED: Single-Word Exact-Match Triggers ---
SINGLE_WORD_TRIGGERS = {
    "play": handle_media_control,
    "pause": handle_media_control,
    "resume": handle_media_control,
    "stop": handle_media_control,
    "next": handle_media_control,
    "previous": handle_media_control,
    "headlines": handle_news_query,
    
    # --- MODIFIED: Point to Spotify ---
    "mute": handle_volume_control,
    "unmute": handle_volume_control,
}

# --- MODIFIED: Prefix Command Registry ---
PREFIX_COMMANDS = {
    "play": handle_media_control,
    "open": handle_program_launch,
    "launch": handle_program_launch,
    "look up": handle_web_search,
    "search for": handle_web_search,

    # --- NEW: Spotify Volume Triggers ---
    "volume up": handle_volume_control,
    "volume down": handle_volume_control,
    "turn up": handle_volume_control,
    "turn down": handle_volume_control,
    "set volume to": handle_volume_control,

    # --- NEW: System Volume Triggers ---
    "system volume up": handle_system_volume,
    "system volume down": handle_system_volume,
    "set system volume to": handle_system_volume,
}