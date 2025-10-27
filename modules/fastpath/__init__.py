# modules/fastpath/__init__.py

# Import handlers from the new modules
from .system import handle_time_query
from .desktop import handle_program_launch, handle_web_search
from .music import handle_volume_control, handle_media_control
from .web_api import handle_weather_query, handle_news_query

# --- Master Command Registry ---
# This dictionary now builds itself from the imported handlers.
COMMANDS = {
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
        ("open", "cursor"), ("launch", "cursor")
    ],
    
    handle_web_search: [
        ("look", "up"),
        ("search", "for")
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
        # --- NEW: Single-word triggers for broader matching ---
        ("play",), ("pause",), ("resume",), ("stop",), ("next",), ("previous",),
        
        # --- Original triggers (still useful) ---
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