# modules/fastpath/system.py
import datetime
import pytz

def handle_time_query(text: str) -> str:
    """Gets the current time for the IST time zone and formats it."""
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.datetime.now(ist)
    formatted_time = now.strftime("%I:%M %p") # e.g., "03:48 PM"
    return f"The current time is {formatted_time}."